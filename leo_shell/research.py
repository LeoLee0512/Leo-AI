"""Desktop research tasks. Native confirmations are the only admission authority."""
import os
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
import threading
import uuid

from pinn.research.storage import read, write, digest, locked
from pinn.research.evidence import contained, tree_hashes, verify_attempt, export_tree
from pinn.experiments.common import utc_now
from .research_draft import validate_draft

ID = re.compile(r"^research-[0-9a-f]{32}$")
ACTIVE = {"RUNNING", "CANCELLING"}


class ResearchService:
    def __init__(self, paths, *, confirm, draft_provider, runtime=None, command_runner=subprocess.run):
        self.paths = paths
        self.root = paths.user / "research"
        self.confirm = confirm
        self.draft_provider = draft_provider
        self.runtime_override = runtime
        self.command_runner = command_runner
        self.mutex = threading.RLock()

    def _runtime(self):
        data = self.runtime_override or read(self.paths.root / "runtime/research-runtime.json")
        result = {}
        for key in ("codeRoot", "pythonA", "pythonB"):
            path = Path(data[key])
            result[key] = str((self.paths.root / path).resolve() if not path.is_absolute() else path.resolve())
            if not Path(result[key]).exists():
                raise ValueError("RESEARCH_RUNTIME_UNAVAILABLE")
        return result

    def _directory(self, task_id):
        if not isinstance(task_id, str) or not ID.fullmatch(task_id):
            raise ValueError("TASK_ID_INVALID")
        return contained(self.root, "tasks/" + task_id)

    def _load(self, payload, *, mutation=False):
        directory = self._directory(payload.get("taskId"))
        task = read(directory / "state.json")
        if task["taskId"] != directory.name:
            raise ValueError("TASK_IDENTITY_MISMATCH")
        if mutation and (type(payload.get("expectedVersion")) is not int or task["version"] != payload["expectedVersion"]):
            raise ValueError("TASK_VERSION_CONFLICT")
        prior = "GENESIS"
        for version in range(1, task["version"] + 1):
            snapshot = read(directory / "events" / f"{version:08d}.json")
            if snapshot["previousEventHash"] != prior or snapshot["taskHash"] != digest(snapshot["task"]):
                raise ValueError("TASK_EVENT_CHAIN_INVALID")
            prior = digest(snapshot)
        if snapshot["taskHash"] != digest(task):
            raise ValueError("TASK_INTEGRITY_FAILED")
        return directory, task

    def _save(self, directory, task, event):
        previous = task.get("version", 0)
        task["version"] = previous + 1
        task["updatedAt"] = utc_now()
        prior_hash = digest(read(directory / "events" / f"{previous:08d}.json")) if previous else "GENESIS"
        record = {"schemaVersion": "leo.taskEvent/1", "event": event, "at": task["updatedAt"],
                  "previousEventHash": prior_hash, "taskHash": digest(task), "task": task}
        write(directory / "events" / f"{task['version']:08d}.json", record, exclusive=True)
        write(directory / "state.json", task)
        return {"ok": True, "task": task}

    def dispatch(self, operation, payload=None):
        if not isinstance(payload, dict):
            raise ValueError("RESEARCH_REQUEST_INVALID")
        if operation not in {"create", "list", "get", "draft", "update", "approve_model", "prepare",
                              "approve_run", "cancel", "evidence", "export", "review", "fork"}:
            raise ValueError("RESEARCH_OPERATION_INVALID")
        with self.mutex, locked(self.root / "tasks.lock"):
            return getattr(self, "_" + operation)(payload)

    def _create(self, payload):
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 20000:
            raise ValueError("RESEARCH_PROMPT_INVALID")
        for key in ("frameId", "projectId"):
            if not isinstance(payload.get(key), str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", payload[key]):
                raise ValueError("RESEARCH_SESSION_REQUIRED")
        task_id = "research-" + uuid.uuid4().hex
        directory = self._directory(task_id)
        directory.mkdir(parents=True)
        task = {"schemaVersion": "leo.researchTask/1", "taskId": task_id,
            "frameId": payload["frameId"], "projectId": payload["projectId"], "prompt": prompt,
            "state": "DRAFT", "draft": None, "createdAt": utc_now(), "scientificState": "NOT_CHECKED"}
        return self._save(directory, task, "CREATED")

    def _list(self, payload):
        tasks = []
        for path in sorted((self.root / "tasks").glob("research-*/state.json")):
            directory, task = self._load({"taskId": path.parent.name})
            if task["frameId"] == payload.get("frameId"):
                tasks.append({k: task[k] for k in ("taskId", "state", "version", "prompt", "updatedAt")})
        return {"ok": True, "tasks": tasks}

    def _refresh(self, directory, task):
        """Settle a RUNNING/CANCELLING task whose worker finished or died while nobody was looking."""
        if task["state"] in ACTIVE:
            if (directory / "completion.json").exists():
                completion = read(directory / "completion.json")
                task["state"] = completion["state"]
                task["completionHash"] = digest(completion)
                self._save(directory, task, "WORKER_FINISHED")
            elif ((directory / "worker-owner.json").exists() or
                  (datetime.now(timezone.utc) - datetime.fromisoformat(task["updatedAt"].replace("Z", "+00:00"))).total_seconds() > 60):
                try:
                    with locked(directory / "worker.lock"):
                        task["state"] = "INTERRUPTED"
                        self._save(directory, task, "WORKER_INTERRUPTED")
                except ValueError as error:
                    if str(error) != "RESOURCE_BUSY":
                        raise
        return task

    def _get(self, payload):
        directory, task = self._load(payload)
        task = self._refresh(directory, task)
        result = {"ok": True, "task": task}
        if (directory / "execution-plan.json").exists():
            result["plan"] = read(directory / "execution-plan.json")
            # The UI can inspect identity/sets but should not load thousands of file hashes to render.
        if (directory / "progress.json").exists():
            result["progress"] = read(directory / "progress.json")
        if task["state"] == "COMPLETED":
            receipt = read(directory / "completion.json")
            if digest(receipt) != task.get("completionHash") or tree_hashes(directory / "work", exclude=()) != receipt["evidenceHashes"]:
                result["verification"] = {"verified": False, "allowedClaims": [], "reason": "EVIDENCE_HASH_MISMATCH"}
            else:
                try:
                    result["verification"] = verify_attempt(directory / "work/attempts/main")
                except (ValueError, OSError, KeyError):
                    result["verification"] = {"verified": False, "allowedClaims": [], "reason": "EVIDENCE_VALIDATION_FAILED"}
        else:
            result["verification"] = {"verified": False, "allowedClaims": [], "reason": task["state"]}
        return result

    def _draft(self, payload):
        directory, task = self._load(payload, mutation=True)
        if task["state"] != "DRAFT":
            raise ValueError("TASK_NOT_EDITABLE")
        task["draft"] = self.draft_provider(task["frameId"], task["prompt"])
        return self._save(directory, task, "DRAFT_GENERATED")

    def _update(self, payload):
        directory, task = self._load(payload, mutation=True)
        if task["state"] not in {"DRAFT", "MODEL_CONFIRMED"} or (directory / "work").exists():
            raise ValueError("CREATE_NEW_TASK_FOR_REVISION")
        task["draft"] = validate_draft(payload["draft"], task["prompt"])
        task["state"] = "DRAFT"
        task.pop("modelApproval", None)
        return self._save(directory, task, "MODEL_EDITED_APPROVAL_INVALIDATED")

    def _approval(self, task, kind, content):
        content_hash = digest(content)
        text = ("请核对面板中的完整内容。\n任务：" + task["taskId"] + "\n确认类型：" + kind +
                "\n内容 SHA-256：" + content_hash + "\n" +
                ("确认后将运行主实验、Tier-1 和独立复现，最长 60 分钟；失败不会自动调参。" if kind == "RUN" else
                 "该确认不改变任何 Gate 或机器允许的 Claim。"))
        if self.confirm("Leo AI 科研人工确认", text) is not True:
            raise ValueError("HUMAN_CONFIRMATION_DECLINED")
        return {"schemaVersion": "leo.approvalRecord/1", "approvalId": uuid.uuid4().hex,
                "taskId": task["taskId"], "kind": kind, "contentHash": content_hash,
                "at": utc_now(), "actor": "local desktop operator", "channel": "native-dialog"}

    def _approve_model(self, payload):
        directory, task = self._load(payload, mutation=True)
        if task["state"] != "DRAFT" or not (task.get("draft") or {}).get("supported"):
            raise ValueError("MODEL_NOT_SUPPORTED")
        task["modelApproval"] = self._approval(task, "MODEL", task["draft"])
        task["state"] = "MODEL_CONFIRMED"
        return self._save(directory, task, "MODEL_CONFIRMED")

    def _command(self, runtime, command, directory, extra=(), timeout=180):
        args = [runtime["pythonA"], "-u", "-m", "pinn.research.worker", command,
                "--task-root", str(directory), "--code-root", runtime["codeRoot"], *extra]
        return self.command_runner(args, cwd=runtime["codeRoot"], capture_output=True,
            timeout=timeout, creationflags=0x08000000 if os.name == "nt" else 0)

    def _prepare(self, payload):
        directory, task = self._load(payload, mutation=True)
        if task["state"] != "MODEL_CONFIRMED":
            raise ValueError("MODEL_APPROVAL_REQUIRED")
        runtime = self._runtime()
        try:
            result = self._command(runtime, "prepare", directory, ("--python-b", runtime["pythonB"]), timeout=300)
        except subprocess.TimeoutExpired as expired:
            (directory / "preparation.log").write_bytes((expired.stdout or b"") + (expired.stderr or b"")
                                                        + b"\n[timed out after 300 s]\n")
            task["preparationError"] = "PREPARATION_TIMED_OUT"
            self._save(directory, task, "PREPARATION_TIMED_OUT")
            return {"ok": False, "code": "PREPARATION_TIMED_OUT", "task": task}
        (directory / "preparation.log").write_bytes(result.stdout + result.stderr)
        if result.returncode:
            task["preparationError"] = "PREPARATION_FAILED_SEE_EVIDENCE"
            self._save(directory, task, "PREPARATION_FAILED")
            return {"ok": False, "code": "PREPARATION_FAILED_SEE_EVIDENCE", "task": task}
        plan = read(directory / "execution-plan.json")
        task["planHash"] = digest(plan)
        task["state"] = "READY_FOR_RUN_APPROVAL"
        return {**self._save(directory, task, "PLAN_PREPARED"), "plan": plan}

    def _approve_run(self, payload):
        directory, task = self._load(payload)
        # Retrying an admitted request is safe, including after losing its first response.
        if task.get("runApproval"):
            return {"ok": True, "task": task, "alreadyAdmitted": True}
        directory, task = self._load(payload, mutation=True)
        if task["state"] != "READY_FOR_RUN_APPROVAL":
            raise ValueError("RUN_PLAN_REQUIRED")
        for state in (self.root / "tasks").glob("*/state.json"):
            if state.parent.name == directory.name or read(state)["state"] not in ACTIVE:
                continue
            other_directory, other = self._load({"taskId": state.parent.name})
            if self._refresh(other_directory, other)["state"] in ACTIVE:
                raise ValueError("RESEARCH_TASK_ALREADY_RUNNING")
        runtime = self._runtime()
        if self._command(runtime, "check", directory).returncode:
            raise ValueError("RUN_PLAN_IDENTITY_CHANGED")
        plan = read(directory / "execution-plan.json")
        if digest(plan) != task["planHash"] or plan["modelHash"] != digest(task["draft"]):
            raise ValueError("RUN_PLAN_IDENTITY_CHANGED")
        approval = self._approval(task, "RUN", plan)
        write(directory / "run-approval.json", approval, exclusive=True)
        task.update({"runApproval": approval, "state": "RUNNING"})
        self._save(directory, task, "RUN_ADMITTED")
        command = [runtime["pythonA"], "-u", "-m", "pinn.research.worker", "run", "--task-root", str(directory),
                   "--code-root", runtime["codeRoot"]]
        try:
            with (directory / "supervisor.log").open("xb") as log:
                process = subprocess.Popen(command, cwd=runtime["codeRoot"], stdout=log, stderr=subprocess.STDOUT,
                    creationflags=0x08000000 if os.name == "nt" else 0)
            write(directory / "launch.json", {"pid": process.pid, "at": utc_now()})
        except OSError:
            task["state"] = "INTERRUPTED"
            self._save(directory, task, "WORKER_LAUNCH_FAILED")
            raise ValueError("WORKER_LAUNCH_FAILED") from None
        return {"ok": True, "task": task}

    def _fork(self, payload):
        """Start over from a task's draft. Its prepared data and reserved claim set stay as evidence."""
        source_directory, source = self._load(payload)
        if source["state"] in ACTIVE:
            raise ValueError("FORK_REQUIRES_STOPPED_WORKER")
        if not source.get("draft"):
            raise ValueError("FORK_REQUIRES_DRAFT")
        raw = {key: source["draft"][key] for key in ("objective", "equation", "domain", "boundary", "assumptions", "missing", "conflicts")}
        task_id = "research-" + uuid.uuid4().hex
        directory = self._directory(task_id)
        directory.mkdir(parents=True)
        task = {"schemaVersion": "leo.researchTask/1", "taskId": task_id,
            "frameId": source["frameId"], "projectId": source["projectId"], "prompt": source["prompt"],
            "state": "DRAFT", "draft": validate_draft(raw, source["prompt"]), "createdAt": utc_now(),
            "scientificState": "NOT_CHECKED",
            "forkedFrom": {"taskId": source["taskId"], "version": source["version"], "taskHash": digest(source),
                           "state": source["state"], "preparationError": source.get("preparationError")}}
        return self._save(directory, task, "FORKED")

    def _cancel(self, payload):
        directory, task = self._load(payload, mutation=True)
        if task["state"] not in ACTIVE:
            raise ValueError("TASK_NOT_RUNNING")
        write(directory / "cancel-request.json", {"taskId": task["taskId"], "at": utc_now()})
        task["state"] = "CANCELLING"
        return self._save(directory, task, "CANCEL_REQUESTED")

    def _evidence(self, payload):
        directory, task = self._load(payload)
        relative = payload.get("path")
        if relative is None:
            return {"ok": True, "files": sorted(tree_hashes(directory / "work", exclude=())) if (directory / "work").exists() else []}
        if not isinstance(relative, str):
            raise ValueError("EVIDENCE_PATH_INVALID")
        path = contained(directory / "work", relative)
        if path.suffix not in {".json", ".md"} or path.stat().st_size > 2 * 1024 * 1024:
            raise ValueError("EVIDENCE_PREVIEW_UNAVAILABLE")
        return {"ok": True, "path": relative, "text": path.read_text(encoding="utf-8")}

    def _export(self, payload):
        directory, task = self._load(payload, mutation=True)
        if task["state"] in ACTIVE:
            raise ValueError("EXPORT_REQUIRES_STOPPED_WORKER")
        if task["state"] == "COMPLETED" and not self._get(payload)["verification"]["verified"]:
            raise ValueError("EXPORT_EVIDENCE_INVALID")
        destination = self.root / "exports" / (task["taskId"] + "-" + uuid.uuid4().hex[:8])
        plan_path = directory / "execution-plan.json"
        plan = read(plan_path) if plan_path.exists() else None
        export_tree(directory, destination, source_root=plan["context"]["codeRoot"] if plan else None,
                    source_manifest=plan["codeManifest"] if plan else ())
        return {"ok": True, "path": str(destination)}

    def _review(self, payload):
        directory, task = self._load(payload, mutation=True)
        view = self._get(payload)
        if not view["verification"].get("verified"):
            raise ValueError("VERIFIED_REPORT_REQUIRED")
        text = payload.get("interpretation")
        if not isinstance(text, str) or len(text) > 20000:
            raise ValueError("REVIEW_INVALID")
        review = {"interpretation": text, "machineDecision": view["verification"]}
        task["humanReview"] = {**review, "approval": self._approval(task, "CONCLUSION", review)}
        return self._save(directory, task, "CONCLUSION_REVIEWED")
