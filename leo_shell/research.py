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
# 3.2.0 · The panel's plain words live outside the identity too; they only explain, never decide.
from . import research_words

ID = re.compile(r"^research-[0-9a-f]{32}$")
ACTIVE = {"RUNNING", "CANCELLING"}
# A task in any of these states owns work in progress: it cannot be forked, edited or exported.
BUSY = ACTIVE | {"PREPARING"}
COMPLETION_FIELDS = ("state", "phase", "exitCode", "reason", "at")
# Preparation scans each candidate claim grid against the training and dev points (pure Python);
# 2D grids are larger and grow along the list, so a 2D preparation may take several minutes.
# 3.2.2 · An annulus grid holds up to ~15 000 samples and is scanned against ~8 200 others.
PREPARE_TIMEOUT_SECONDS = {"poisson1d": 300, "poisson2d": 900, "annulus": 1800}
GUIDE_ERRORS = (ValueError, OSError, KeyError, TypeError)
_STILL_ACTIVE = 259
_QUERY_PROCESS = 0x1000


def process_alive(pid):
    """Whether *pid* is still running. A dead or unusable id is not alive."""
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.GetExitCodeProcess.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        handle = kernel.OpenProcess(_QUERY_PROCESS, False, pid)
        if not handle:
            return False
        try:
            code = wintypes.DWORD()
            if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
                return False
            return code.value == _STILL_ACTIVE
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _kill_pid(pid):
    """Stop *pid* and the children it started. A process that is already gone is success."""
    if not process_alive(pid):
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True,
                       creationflags=0x08000000, timeout=30)
        return
    try:
        os.kill(pid, 15)
    except OSError:
        return
    for _ in range(50):
        if not process_alive(pid):
            return
        time.sleep(0.1)
    try:
        os.kill(pid, 9)
    except OSError:
        pass


def _plain(value, limit):
    text = value if isinstance(value, str) else str(value)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "…"


def _approval_body(kind, content):
    """The lines the confirmation shows, so the hash is not the only thing on screen."""
    if not isinstance(content, dict):
        return ""
    lines = []
    if kind == "RUN":
        family = content.get("family")
        code = content.get("codeHash")
        config = (content.get("solverConfiguration") or {}).get("configId") if isinstance(content.get("solverConfiguration"), dict) else None
        if isinstance(family, str) and family:
            lines.append("问题族：" + _plain(family, 40))
        if isinstance(config, str) and config:
            lines.append("求解配置：" + _plain(config, 80))
        if isinstance(code, str) and code:
            lines.append("代码指纹：" + code[:12])
    else:
        template = content.get("templateId")
        equation = content.get("equation")
        if isinstance(template, str) and template:
            lines.append("模板：" + _plain(template, 80))
        if isinstance(equation, str) and equation:
            lines.append("方程：" + _plain(equation, 300))
        if content.get("domain") is not None:
            lines.append("区域：" + _plain(content.get("domain"), 120))
        if content.get("boundary") is not None:
            lines.append("边界：" + _plain(content.get("boundary"), 160))
    return ("\n" + "\n".join(lines)) if lines else ""


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

    def _roll_forward(self, directory, task):
        """Adopt an event that was committed when the following state write did not finish.

        ``_save`` writes the event file first. A crash in between leaves ``state.json`` on the
        previous version and the next exclusive event create can never succeed. A readable event
        that chains from the state on disk is the task; an unreadable fragment is not, and is
        removed so the same version can be written again.
        """
        for _ in range(8):
            nxt = directory / "events" / f"{task['version'] + 1:08d}.json"
            if not nxt.is_file():
                return task
            try:
                snapshot = read(nxt)
            except (ValueError, OSError):
                nxt.unlink(missing_ok=True)
                return task
            prior = digest(read(directory / "events" / f"{task['version']:08d}.json")) if task.get("version") else "GENESIS"
            recovered = snapshot.get("task") if isinstance(snapshot, dict) else None
            if (not isinstance(recovered, dict) or snapshot.get("previousEventHash") != prior
                    or snapshot.get("taskHash") != digest(recovered)
                    or recovered.get("version") != task["version"] + 1 or recovered.get("taskId") != task.get("taskId")):
                return task
            write(directory / "state.json", recovered)
            task = recovered
        return task

    def _load(self, payload, *, mutation=False):
        directory = self._directory(payload.get("taskId"))
        task = self._roll_forward(directory, read(directory / "state.json"))
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
                tasks.append({**{k: task[k] for k in ("taskId", "state", "version", "prompt", "updatedAt", "frameId")},
                              "family": TEMPLATE_FAMILIES.get((task.get("draft") or {}).get("templateId")),
                              "hasDraft": bool(task.get("draft"))})
        if every:
            tasks.sort(key=lambda t: t["updatedAt"], reverse=True)
        return {"ok": True, "tasks": tasks}

    def _owner_pid(self, directory, name):
        path = directory / name
        if not path.is_file():
            return None
        try:
            pid = read(path).get("pid")
        except (ValueError, OSError, AttributeError):
            return None
        return pid if isinstance(pid, int) and not isinstance(pid, bool) else None

    def _supervisor_alive(self, directory):
        return process_alive(self._owner_pid(directory, "launch.json"))

    def _seconds_since_update(self, task):
        try:
            updated = datetime.fromisoformat(str(task.get("updatedAt", "")).replace("Z", "+00:00"))
        except ValueError:
            return 0
        return (datetime.now(timezone.utc) - updated).total_seconds()

    def _stop_preparation(self, directory):
        """End a preparation whose parent app is gone, so it cannot keep writing afterwards."""
        pid = self._owner_pid(directory, "preparation-owner.json")
        if process_alive(pid):
            _kill_pid(pid)

    def _adopt_completion(self, directory, task):
        completion = read(directory / "completion.json")
        task["state"] = completion["state"]
        task["completionHash"] = digest(completion)
        task["completion"] = {k: completion[k] for k in COMPLETION_FIELDS if k in completion}
        self._save(directory, task, "WORKER_FINISHED")
        return task

    def _lose_worker(self, directory, task):
        task["state"] = "INTERRUPTED"
        task["completion"] = {"state": "INTERRUPTED", "reason": "WORKER_LOST", "at": utc_now()}
        self._save(directory, task, "WORKER_INTERRUPTED")
        return task

    def _refresh(self, directory, task):
        """Settle a RUNNING/CANCELLING task whose worker finished or died while nobody was looking."""
        if task["state"] == "PREPARING" and task["taskId"] not in self._preparing:
            # The preparation thread belonged to an earlier session. Stop it before recording
            # the outcome, or it can still create work/ after the task has left PREPARING.
            self._stop_preparation(directory)
            plan_path = directory / "execution-plan.json"
            if plan_path.is_file():
                try:
                    task["planHash"] = digest(read(plan_path))
                except (ValueError, OSError):
                    plan_path = None
            if plan_path is not None and plan_path.is_file():
                task.pop("preparationError", None)
                task["state"] = "READY_FOR_RUN_APPROVAL"
                self._save(directory, task, "PLAN_PREPARED")
            else:
                task["state"] = "MODEL_CONFIRMED"
                task["preparationError"] = "PREPARATION_INTERRUPTED"
                self._save(directory, task, "PREPARATION_INTERRUPTED")
        if task["state"] in ACTIVE:
            if (directory / "completion.json").exists():
                return self._adopt_completion(directory, task)
            # The worker writes its owner file only after it takes worker.lock, and it holds that
            # lock until completion. A live pid with no owner file is still importing: do not
            # declare it lost. Once the owner file exists, a free lock means that process has
            # left the run, even if the recorded pid was later reused.
            if self._supervisor_alive(directory) and not (directory / "worker-owner.json").exists():
                return task
            abandoned = ((directory / "launch.json").exists() or (directory / "worker-owner.json").exists()
                         or self._seconds_since_update(task) > 60)
            if abandoned:
                try:
                    with locked(directory / "worker.lock"):
                        if (directory / "completion.json").exists():
                            return self._adopt_completion(directory, task)
                        if self._supervisor_alive(directory) and not (directory / "worker-owner.json").exists():
                            return task
                        return self._lose_worker(directory, task)
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
        if task["state"] == "PREPARING" and (directory / "preparation-progress.json").exists():
            result["preparationProgress"] = read(directory / "preparation-progress.json")
        result["words"] = research_words.panel_words(family)
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
            if task["state"] in ("STOPPED", "INTERRUPTED", "CANCELLED", "TIMED_OUT"):
                try:
                    result["verification"]["story"] = research_words.failure_story(directory, task, failure)
                except GUIDE_ERRORS:
                    pass
        research_words.annotate_verification(result["verification"])
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
        text = ("请核对接下来列出的内容。确认记录保存的是同一份内容的 SHA-256。\n任务：" + task["taskId"]
                + "\n确认类型：" + kind + _approval_body(kind, content) +
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

    def _command(self, runtime, command, directory, extra=(), timeout=180, *, owned=False):
        args = [runtime["pythonA"], "-u", "-m", "pinn.research.worker", command,
                "--task-root", str(directory), "--code-root", runtime["codeRoot"], *extra]
        if owned and self.command_runner is subprocess.run:
            return self._run_owned(args, runtime["codeRoot"], directory, timeout)
        return self.command_runner(args, cwd=runtime["codeRoot"], capture_output=True,
            timeout=timeout, creationflags=0x08000000 if os.name == "nt" else 0)

    def _run_owned(self, args, cwd, directory, timeout):
        """Run preparation as a process this service can stop when the app closes."""
        proc = subprocess.Popen(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                creationflags=0x08000000 if os.name == "nt" else 0)
        write(directory / "preparation-owner.json", {"pid": proc.pid, "at": utc_now()})
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as expired:
            _kill_pid(proc.pid)
            try:
                out, err = proc.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                out, err = b"", b""
            raise subprocess.TimeoutExpired(args, timeout, output=out, stderr=err) from expired
        return SimpleNamespace(returncode=proc.returncode, stdout=out or b"", stderr=err or b"")

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
        task["preparationStartedAt"] = utc_now()
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
                result = self._command(runtime, "prepare", directory, ("--python-b", runtime["pythonB"]),
                                       timeout=timeout, owned=True)
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
            owner = directory / "preparation-owner.json"
            pid = self._owner_pid(directory, "preparation-owner.json")
            if owner.exists() and not process_alive(pid):
                owner.unlink(missing_ok=True)

    def _can_relaunch(self, directory, task):
        """A launch that never entered the worker can be started again. One that did cannot:
        it may already have opened the blind set."""
        if task.get("state") != "INTERRUPTED" or not task.get("runApproval"):
            return False
        if (directory / "worker-owner.json").exists() or (directory / "completion.json").exists():
            return False
        return not self._supervisor_alive(directory)

    def _mark_launch_failed(self, directory):
        _, task = self._load({"taskId": directory.name})
        if task["state"] != "RUNNING":
            return
        task["state"] = "INTERRUPTED"
        task["completion"] = {"state": "INTERRUPTED", "reason": "WORKER_LAUNCH_FAILED", "at": utc_now()}
        self._save(directory, task, "WORKER_LAUNCH_FAILED")

    def _spawn_supervisor(self, directory, runtime):
        command = [runtime["pythonA"], "-u", "-m", "pinn.research.worker", "run", "--task-root", str(directory),
                   "--code-root", runtime["codeRoot"]]
        log_path = directory / "supervisor.log"
        process = None
        try:
            log = log_path.open("ab" if log_path.exists() else "xb")
        except OSError:
            self._mark_launch_failed(directory)
            raise ValueError("WORKER_LAUNCH_FAILED") from None
        try:
            process = subprocess.Popen(command, cwd=runtime["codeRoot"], stdout=log, stderr=subprocess.STDOUT,
                                       creationflags=0x08000000 if os.name == "nt" else 0)
            write(directory / "launch.json", {"pid": process.pid, "at": utc_now()})
        except OSError:
            if process is not None and process.poll() is None:
                _kill_pid(process.pid)
            self._mark_launch_failed(directory)
            raise ValueError("WORKER_LAUNCH_FAILED") from None
        finally:
            log.close()

    def _relaunch(self, directory, task):
        runtime = self._runtime()
        plan = read(directory / "execution-plan.json")
        approval = read(directory / "run-approval.json")
        if (approval.get("contentHash") != digest(plan) or approval.get("taskId") != directory.name
                or digest(plan) != task.get("planHash")):
            raise ValueError("RUN_PLAN_IDENTITY_CHANGED")
        if self._command(runtime, "check", directory).returncode:
            raise ValueError("RUN_PLAN_IDENTITY_CHANGED")
        task["state"] = "RUNNING"
        task.pop("completion", None)
        self._save(directory, task, "RUN_ADMITTED")
        self._spawn_supervisor(directory, runtime)
        return {"ok": True, "task": self._load({"taskId": directory.name})[1]}

    def _approve_run(self, payload):
        directory, task = self._load(payload)
        # Retrying an admitted request is safe, including after losing its first response.
        # A launch that failed before the worker existed is the exception: it has an approval
        # and no computation, and used to answer alreadyAdmitted without ever starting.
        if task.get("runApproval"):
            if self._can_relaunch(directory, task):
                return self._relaunch(directory, task)
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
        self._spawn_supervisor(directory, runtime)
        return {"ok": True, "task": self._load({"taskId": directory.name})[1]}

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
                state = read(path)["state"]
                directory = path.parent
                if state == "PREPARING":
                    # Leave the state for the next session to record. Stop the process now, or it
                    # keeps writing after that record says the preparation ended.
                    self._stop_preparation(directory)
                    continue
                if state != "RUNNING":
                    continue
                directory, task = self._load({"taskId": path.parent.name})
                write(directory / "cancel-request.json", {"taskId": task["taskId"], "at": utc_now(), "reason": "APP_CLOSED"})
                task["state"] = "CANCELLING"
                self._save(directory, task, "CANCEL_REQUESTED_ON_CLOSE")
