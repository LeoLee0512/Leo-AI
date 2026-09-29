"""Desktop research tasks. Native confirmations are the only admission authority."""
from contextlib import nullcontext
import os
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
import threading
import time
import uuid

from pinn.research.storage import read, write, digest, locked
from pinn.research.evidence import contained, tree_hashes, verify_attempt, export_tree
from pinn.research.quota import quota
from pinn.research.worker import TEMPLATE_FAMILIES
from pinn.experiments.common import utc_now
from pinn.governance.trust_loop import code_hash_from_manifest
from . import __version__
from .entitlements import COSTLY, check as entitlement_check
from .evidence_guide import build_guide, write_guide
from .research_draft import validate_draft
# Display-only wall times live outside the research code identity; the plan's budget is the limit.
from .research_estimates import ESTIMATE_MINUTES

ID = re.compile(r"^research-[0-9a-f]{32}$")
ACTIVE = {"RUNNING", "CANCELLING"}
# A task in any of these states owns work in progress: it cannot be forked, edited or exported.
BUSY = ACTIVE | {"PREPARING"}
COMPLETION_FIELDS = ("state", "phase", "exitCode", "reason", "at")
# Preparation scans each candidate claim grid against the training and dev points (pure Python);
# 2D grids are larger and grow along the list, so a 2D preparation may take several minutes.
PREPARE_TIMEOUT_SECONDS = {"poisson1d": 300, "poisson2d": 900}
GUIDE_ERRORS = (ValueError, OSError, KeyError, TypeError)


def task_family(task):
    """The problem family of a task's draft; a draft without a verified template counts as 1D."""
    return TEMPLATE_FAMILIES.get((task.get("draft") or {}).get("templateId"), "poisson1d")


class ResearchService:
    def __init__(self, paths, *, confirm, draft_provider, runtime=None, command_runner=subprocess.run,
                 entitlement=entitlement_check, background=True):
        self.paths = paths
        self.root = paths.user / "research"
        self.confirm = confirm
        self.draft_provider = draft_provider
        self.runtime_override = runtime
        self.command_runner = command_runner
        self.entitlement = entitlement
        self.background = background
        self.mutex = threading.RLock()
        self._preparing = set()

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
                              "approve_run", "cancel", "evidence", "export", "review", "fork", "recheck"}:
            raise ValueError("RESEARCH_OPERATION_INVALID")
        if operation in COSTLY:
            # Paid-feature checkpoint; the decision lives outside the research code identity.
            self.entitlement(operation, {"taskId": payload.get("taskId"), "frameId": payload.get("frameId")})
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
        """Tasks of one conversation, or of every conversation with ``scope: "all"``."""
        every = payload.get("scope") == "all"
        tasks = []
        for path in sorted((self.root / "tasks").glob("research-*/state.json")):
            directory, task = self._load({"taskId": path.parent.name})
            if every or task["frameId"] == payload.get("frameId"):
                tasks.append({k: task[k] for k in ("taskId", "state", "version", "prompt", "updatedAt", "frameId")})
        if every:
            tasks.sort(key=lambda t: t["updatedAt"], reverse=True)
        return {"ok": True, "tasks": tasks}

    def _refresh(self, directory, task):
        """Settle a RUNNING/CANCELLING task whose worker finished or died while nobody was looking."""
        if task["state"] == "PREPARING" and task["taskId"] not in self._preparing:
            # The preparation thread belonged to an earlier session of the app.
            task["state"] = "MODEL_CONFIRMED"
            task["preparationError"] = "PREPARATION_INTERRUPTED"
            self._save(directory, task, "PREPARATION_INTERRUPTED")
        if task["state"] in ACTIVE:
            if (directory / "completion.json").exists():
                completion = read(directory / "completion.json")
                task["state"] = completion["state"]
                task["completionHash"] = digest(completion)
                # Why and where the run ended travels with the task, not only in a log.
                task["completion"] = {k: completion[k] for k in COMPLETION_FIELDS if k in completion}
                self._save(directory, task, "WORKER_FINISHED")
            elif ((directory / "worker-owner.json").exists() or
                  (datetime.now(timezone.utc) - datetime.fromisoformat(task["updatedAt"].replace("Z", "+00:00"))).total_seconds() > 60):
                try:
                    with locked(directory / "worker.lock"):
                        task["state"] = "INTERRUPTED"
                        task["completion"] = {"state": "INTERRUPTED", "reason": "WORKER_LOST", "at": utc_now()}
                        self._save(directory, task, "WORKER_INTERRUPTED")
                except ValueError as error:
                    if str(error) != "RESOURCE_BUSY":
                        raise
        return task

    def _failure(self, directory, task):
        """What a run that ended without a verified decision recorded: shown, never hidden."""
        summary_path = directory / "work/attempts/main/RUN_SUMMARY.json"
        if not summary_path.exists():
            return None
        summary = read(summary_path)
        failure = {"finalState": summary.get("finalState"), "trustVector": summary.get("trustVector"),
                   "highestAllowedClaim": summary.get("highestAllowedClaim")}
        detail = summary.get("failure") or {}
        if isinstance(detail, dict):
            failure.update({k: detail[k] for k in ("gate", "observedSignatures") if k in detail})
        tier1 = directory / "work/attempts/main/tier1_redteam.json"
        if tier1.exists():
            failure["tier1Passed"] = read(tier1).get("passed")
        if task.get("completion"):
            failure["completion"] = task["completion"]
        return failure

    def _get(self, payload):
        directory, task = self._load(payload)
        task = self._refresh(directory, task)
        code_root = None
        try:
            code_root = self._runtime()["codeRoot"]
        except (ValueError, KeyError, OSError):
            pass
        family = task_family(task)
        result = {"ok": True, "task": task, "quota": quota(self.root, code_root, family), "family": family,
                  "prepareLimitMinutes": round(PREPARE_TIMEOUT_SECONDS[family] / 60),
                  "canPrepare": task["state"] == "MODEL_CONFIRMED" and not (directory / "work").exists()}
        if (directory / "execution-plan.json").exists():
            result["plan"] = read(directory / "execution-plan.json")
            # The UI can inspect identity/sets but should not load thousands of file hashes to render.
            result["estimateMinutes"] = ESTIMATE_MINUTES.get((result["plan"].get("solverConfiguration") or {}).get("configId"))
        if (directory / "progress.json").exists():
            result["progress"] = read(directory / "progress.json")
        if task["state"] == "COMPLETED":
            result["verification"] = self._verified(directory, task)
            if result["verification"].get("verified"):
                try:
                    result["guide"] = build_guide(directory, task, result["verification"])
                except GUIDE_ERRORS:
                    # The guide only explains; the verification above stands without it.
                    result["guide"] = None
        else:
            result["verification"] = {"verified": False, "allowedClaims": [], "reason": task["state"]}
            failure = self._failure(directory, task) if task["state"] not in BUSY else None
            if failure:
                result["verification"]["failure"] = failure
        return result

    def _verified(self, directory, task, *, fresh=False):
        """Full evidence verification, run once per evidence state instead of on every view.

        Viewing a finished task re-hashes its evidence (tens of milliseconds) every time. The full
        check (seconds: it includes the pairwise set-separation proof) is cached under a key bound
        to the completion receipt, the evidence hashes and this desktop's version, so any change to
        the evidence or an upgrade forces it again. Export and the explicit re-check always run it.
        """
        receipt = read(directory / "completion.json")
        evidence = tree_hashes(directory / "work", exclude=())
        if digest(receipt) != task.get("completionHash") or evidence != receipt["evidenceHashes"]:
            return {"verified": False, "allowedClaims": [], "reason": "EVIDENCE_HASH_MISMATCH"}
        key = digest({"completion": task["completionHash"], "evidence": digest(evidence), "verifier": __version__})
        cache = self.root / "cache" / (task["taskId"] + ".json")
        if not fresh and cache.exists():
            try:
                cached = read(cache)
                if cached.get("key") == key:
                    return cached["verification"]
            except (ValueError, OSError, KeyError):
                pass
        try:
            verification = verify_attempt(directory / "work/attempts/main")
        except (ValueError, OSError, KeyError):
            return {"verified": False, "allowedClaims": [], "reason": "EVIDENCE_VALIDATION_FAILED"}
        write(cache, {"key": key, "verification": verification})
        return verification

    def _recheck(self, payload):
        """Re-verify a finished run step by step, for a reader who will not open the files."""
        directory, task = self._load(payload)
        if task["state"] != "COMPLETED":
            raise ValueError("RECHECK_REQUIRES_COMPLETED")
        main = directory / "work/attempts/main"
        steps = []

        def step(label, check):
            started = time.perf_counter()
            try:
                passed, detail = check()
            except (ValueError, OSError, KeyError, TypeError, IndexError) as error:
                passed, detail = False, str(error) if re.fullmatch(r"[A-Z][A-Z0-9_]{2,80}", str(error)) else type(error).__name__
            steps.append({"label": label, "passed": bool(passed), "detail": detail,
                          "seconds": round(time.perf_counter() - started, 1)})

        def files():
            receipt = read(directory / "completion.json")
            evidence = tree_hashes(directory / "work", exclude=())
            passed = digest(receipt) == task.get("completionHash") and evidence == receipt["evidenceHashes"]
            return passed, f"{len(evidence)} 个文件的指纹" + ("与完成回执全部一致" if passed else "与完成回执不一致")

        def code():
            plan, identity = read(directory / "execution-plan.json"), read(main / "identity.json")
            computed = code_hash_from_manifest(identity["codeManifest"])
            passed = identity["codeManifest"] == plan["codeManifest"] and identity["codeHash"] == plan["codeHash"] == computed
            return passed, "指纹 " + computed[:12]

        def sealed():
            ledger, summary = read(main / "claim_set_ledger.json"), read(main / "RUN_SUMMARY.json")
            seals = [e for e in ledger if e["event"] == "SEALED"]
            opens = [e for e in ledger if e["event"] == "OPENED"]
            passed = len(seals) == 1 and len(opens) == 1 and seals[0]["at"] <= summary["startedAt"] <= opens[0]["at"]
            return passed, f"训练前封存，打开 {len(opens)} 次"

        def decision():
            verification = self._verified(directory, task, fresh=True)
            passed = bool(verification.get("verified"))
            return passed, ("允许 " + "、".join(verification["allowedClaims"])) if passed else verification.get("reason", "")

        step("证据文件完整，没有被改动", files)
        step("运行记录的代码指纹与运行确认包一致", code)
        step("盲测检验点在训练前封存，且只打开过一次", sealed)
        step("重新复核六项判定与结论等级（含四组计算点互不重叠的完整检查）", decision)
        return {"ok": True, "passed": all(s["passed"] for s in steps), "steps": steps}

    def _draft(self, payload):
        directory, task = self._load(payload, mutation=True)
        if task["state"] != "DRAFT":
            raise ValueError("TASK_NOT_EDITABLE")
        started = time.monotonic()
        try:
            draft = self.draft_provider(task["frameId"], task["prompt"])
        except ValueError as error:
            # Why the model call failed stays with the task, so the panel can say it and offer a retry.
            code = str(error) if re.fullmatch(r"[A-Z][A-Z0-9_]{2,80}", str(error)) else "RESEARCH_DRAFT_FAILED"
            task["draftError"] = {"code": code, "seconds": round(time.monotonic() - started), "at": utc_now()}
            self._save(directory, task, "DRAFT_FAILED")
            raise
        task.pop("draftError", None)
        task["draft"] = draft
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
        if kind == "RUN":
            estimate = ESTIMATE_MINUTES.get((content.get("solverConfiguration") or {}).get("configId"))
            limit = round(content.get("budgetSeconds", 3600) / 60)
            duration = (f"预计约 {estimate} 分钟，上限 {limit} 分钟" if estimate else f"上限 {limit} 分钟")
            tail = "确认后将运行主实验、Tier-1 和独立复现，" + duration + "；失败不会自动调参。"
        else:
            tail = "该确认不改变任何 Gate 或机器允许的 Claim。"
        text = ("请核对面板中的完整内容。\n任务：" + task["taskId"] + "\n确认类型：" + kind +
                "\n内容 SHA-256：" + content_hash + "\n" + tail)
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
        """Start preparation; the panel polls while it runs, so nothing waits on this call."""
        directory, task = self._load(payload, mutation=True)
        if task["state"] != "MODEL_CONFIRMED":
            raise ValueError("MODEL_APPROVAL_REQUIRED")
        if (directory / "work").exists():
            # A reserved claim grid is evidence; the way on is a new task from this draft.
            raise ValueError("PREPARATION_ALREADY_EXISTS")
        runtime = self._runtime()
        task.pop("preparationError", None)
        task["state"] = "PREPARING"
        saved = self._save(directory, task, "PREPARATION_STARTED")
        self._preparing.add(task["taskId"])
        timeout = PREPARE_TIMEOUT_SECONDS[task_family(task)]
        if not self.background:
            self._finish_preparation(directory, runtime, relock=False, timeout=timeout)
            return {"ok": True, "task": self._load({"taskId": directory.name})[1]}
        threading.Thread(target=self._finish_preparation, args=(directory, runtime), kwargs={"timeout": timeout},
                         name="leo-research-prepare", daemon=True).start()
        return saved

    def _finish_preparation(self, directory, runtime, *, relock=True, timeout=300):
        try:
            try:
                result = self._command(runtime, "prepare", directory, ("--python-b", runtime["pythonB"]), timeout=timeout)
                output = result.stdout + result.stderr
                code = "PREPARATION_FAILED_SEE_EVIDENCE" if result.returncode else None
            except subprocess.TimeoutExpired as expired:
                output = (expired.stdout or b"") + (expired.stderr or b"") + f"\n[timed out after {timeout} s]\n".encode()
                code = "PREPARATION_TIMED_OUT"
            except OSError as error:
                output = ("[could not start preparation: " + type(error).__name__ + "]\n").encode()
                code = "PREPARATION_FAILED_SEE_EVIDENCE"
            (directory / "preparation.log").write_bytes(output)
            # The thread takes the process mutex first, like every other caller, so the file lock is free.
            with self.mutex, (locked(self.root / "tasks.lock") if relock else nullcontext()):
                _, task = self._load({"taskId": directory.name})
                if task["state"] != "PREPARING":
                    return
                if code:
                    task["state"] = "MODEL_CONFIRMED"
                    task["preparationError"] = code
                    self._save(directory, task, "PREPARATION_TIMED_OUT" if code == "PREPARATION_TIMED_OUT" else "PREPARATION_FAILED")
                else:
                    task["planHash"] = digest(read(directory / "execution-plan.json"))
                    task["state"] = "READY_FOR_RUN_APPROVAL"
                    self._save(directory, task, "PLAN_PREPARED")
        finally:
            self._preparing.discard(directory.name)

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
        checked = not self._command(runtime, "check", directory).returncode
        plan = read(directory / "execution-plan.json") if checked else None
        if not checked or digest(plan) != task["planHash"] or plan["modelHash"] != digest(task["draft"]):
            # Code, environment or prepared data moved since the plan was made (an upgrade does
            # this). The plan can never be admitted; record it so the panel offers a new task.
            task["runBlocked"] = {"reason": "RUN_PLAN_IDENTITY_CHANGED", "at": utc_now()}
            self._save(directory, task, "RUN_PLAN_BLOCKED")
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
        if source["state"] in BUSY:
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
        if task["state"] in BUSY:
            raise ValueError("EXPORT_REQUIRES_STOPPED_WORKER")
        if task["state"] == "COMPLETED":
            # Export re-proves the evidence in full; a cached result is never what gets shipped.
            verification = self._verified(directory, task, fresh=True)
            if not verification["verified"]:
                raise ValueError("EXPORT_EVIDENCE_INVALID")
            # The reader's guide travels inside the package, under its hash manifest. It only explains,
            # so a failure to write it never blocks the evidence, and a stale copy is never shipped.
            (directory / "证据说明书.html").unlink(missing_ok=True)
            try:
                write_guide(directory, build_guide(directory, task, verification))
            except GUIDE_ERRORS:
                pass
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

    # -- desktop lifecycle: called by the shell window, never by the page ---------------

    def busy_tasks(self):
        """Tasks that closing the app would affect."""
        with self.mutex, locked(self.root / "tasks.lock"):
            busy = []
            for path in sorted((self.root / "tasks").glob("research-*/state.json")):
                if read(path)["state"] not in BUSY:
                    continue
                directory, task = self._load({"taskId": path.parent.name})
                if self._refresh(directory, task)["state"] in BUSY:
                    busy.append(task["taskId"])
            return busy

    def stop_for_close(self):
        """Closing the app stops its runs: each supervisor ends its phase and records CANCELLED."""
        with self.mutex, locked(self.root / "tasks.lock"):
            for path in sorted((self.root / "tasks").glob("research-*/state.json")):
                if read(path)["state"] != "RUNNING":
                    continue
                directory, task = self._load({"taskId": path.parent.name})
                write(directory / "cancel-request.json", {"taskId": task["taskId"], "at": utc_now(), "reason": "APP_CLOSED"})
                task["state"] = "CANCELLING"
                self._save(directory, task, "CANCEL_REQUESTED_ON_CLOSE")
