"""Poisson product adapter. Preparation never trains; execution requires a bound approval."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from pinn.research.context import RunContext, using
from pinn.research.storage import read, write, digest, locked
from pinn.research.evidence import tree_hashes, verify_attempt
from pinn.research.quota import claim_grid_candidates
from pinn.experiments.common import (code_manifest, code_hash_from_manifest, sha256_file,
    environment_fingerprint, environment_identity, assert_code_identity_complete, workspace_dirty_paths, utc_now)

CONFIG = "pinn/research/poisson1d-config.json"
CONFIG_2D = "pinn/research/poisson2d-config.json"
IDENTITY_EXTRAS = (CONFIG, CONFIG_2D, "leo_shell/research.py", "leo_shell/research_draft.py", "leo_shell/api.py",
                   "stage/research-panel.js")

# The problem families the product runs, keyed by the draft's templateId. Each names its frozen
# configuration, its runner and where its claim sets live; everything else is the same pipeline.
FAMILIES = {
    "poisson1d": {"templateId": "poisson1d-v1", "config": CONFIG, "runner": "pinn.experiments.runner",
                  "experiments": "experiments/poisson1d", "claimGlob": "*-claim-GL*.json",
                  # A full 1D chain measured ~8 minutes; one hour is the hard cap.
                  "budgetSeconds": 3600, "workers": 1},
    "poisson2d": {"templateId": "poisson2d-v1", "config": CONFIG_2D, "runner": "pinn.experiments2d.runner2d",
                  "experiments": "experiments/poisson2d", "claimGlob": "*-claim-D2C-*.json",
                  # Serially ~90 minutes (calibration 2026-09-16); seeds and Tier-1 retrains run side by
                  # side (owner, 2026-09-29), with a 90-minute cap.
                  "budgetSeconds": 5400, "workers": 10},
}
TEMPLATE_FAMILIES = {spec["templateId"]: name for name, spec in FAMILIES.items()}


def family_of(draft):
    """The family a confirmed draft belongs to; only a supported template has one."""
    family = TEMPLATE_FAMILIES.get((draft or {}).get("templateId"))
    if family is None:
        raise ValueError("RESEARCH_FAMILY_INVALID")
    return family


def parallel_workers(family):
    """How many trainings run side by side: an execution parameter, never part of the method."""
    return max(1, min(FAMILIES[family]["workers"], (os.cpu_count() or 2) - 2))


def _runner(family):
    import importlib
    return importlib.import_module(FAMILIES[family]["runner"])


def scientific_identity(root):
    extras = (*IDENTITY_EXTRAS, ".gitattributes", *sorted(p.relative_to(root).as_posix() for p in (root / "governance/AMENDMENTS").glob("*.md")))
    manifest = code_manifest(root, extras)
    assert_code_identity_complete(manifest, root, extras)
    if workspace_dirty_paths(root):
        raise ValueError("CODE_IDENTITY_DIRTY")
    # Extra decision surfaces outside pinn/ must also be clean.
    status = subprocess.check_output(["git", "status", "--porcelain", "--", *extras], cwd=root)
    if status.strip():
        raise ValueError("CODE_IDENTITY_DIRTY")
    return manifest


def _environment(python, root):
    done = subprocess.run([str(python), "-m", "pinn.research.worker", "environment"], cwd=root,
                          check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)
    return json.loads(done.stdout)


def historical_claims(root, research_root, family="poisson1d"):
    """Include reserved as well as opened historical sets, and every product reservation."""
    from pinn.governance.evaluation_sets import load_evaluation_set
    identities = set()
    history = {}
    experiments, pattern = FAMILIES[family]["experiments"], FAMILIES[family]["claimGlob"]
    candidates = list((root / experiments).glob("runs/*/sets/claim.json"))
    candidates += list((root / experiments / "problems").glob(pattern))
    candidates += list((research_root / "tasks").glob(f"*/work/{experiments}/problems/{pattern}"))
    for path in sorted(candidates):
        doc = read(path)
        identities.update(load_evaluation_set(doc).identities)
        history[str(path)] = sha256_file(path)
    if not history:
        raise ValueError("HISTORICAL_CLAIM_REGISTRY_MISSING")
    return identities, history


def _base_sets(family, config, root, label):
    """The train / dev / phys sets a candidate claim grid must stay apart from."""
    if family == "poisson1d":
        from pinn.experiments import runner, datasets
        protocol = runner.load_candidate_protocol(root)
        return datasets.build_sets(config, claim_nodes=protocol.quadrature_nodes,
                                   claim_pointwise=protocol.pointwise_nodes, claim_label=label)
    from pinn.experiments2d import datasets2d
    # The claim entry is replaced by each candidate below; any valid placeholder builds the others.
    placeholder = datasets2d.claim_member_points(4, 5)
    return datasets2d.build_sets(config, claim_points=placeholder, claim_artifact_id="set-claim-placeholder",
                                 claim_generator={"generatorId": "placeholder", "generatorVersion": "-"}, label=label)


def _datasets(family):
    if family == "poisson1d":
        from pinn.experiments import datasets
        return datasets
    from pinn.experiments2d import datasets2d
    return datasets2d


def _attempt(family, root, data, problem_id, *, attempt_id, claim_member, seed_offset=0, reproduction_of=None,
             workers=None):
    runner = _runner(family)
    config = root / FAMILIES[family]["config"]
    kwargs = {"config_path": config, "attempt_id": attempt_id, "problem_id": problem_id, "revision": 1,
              "out_root": data / "attempts", "ledger_path": data / runner.LEDGER_DIR / f"{problem_id}.json",
              "reenter_from": None, "claim_pool_member": claim_member, "seed_offset": seed_offset,
              "reproduction_of": reproduction_of}
    if family == "poisson1d":
        return runner.Attempt(**kwargs)
    return runner.Attempt2D(**kwargs, workers=parallel_workers(family) if workers is None else workers)


def prepare(task_root, root, python_b):
    from pinn.governance.canonical import canonical_bytes, canonical_sha256
    from pinn.governance.evaluation_sets import load_evaluation_set, sample_set_hash
    from pinn.governance.trust_vector import EnvironmentFingerprint, independent_environments
    manifest = scientific_identity(root)
    environment_a = environment_fingerprint()
    environment_b = _environment(python_b, root)
    if not independent_environments(EnvironmentFingerprint.from_mapping(environment_a),
                                    EnvironmentFingerprint.from_mapping(environment_b)):
        raise ValueError("REPRODUCTION_ENVIRONMENT_NOT_INDEPENDENT")
    task = read(task_root / "state.json")
    # The desktop moves the task to PREPARING before it launches this command.
    if task["state"] != "PREPARING" or not task.get("modelApproval"):
        raise ValueError("MODEL_APPROVAL_REQUIRED")
    if task["modelApproval"]["contentHash"] != digest(task["draft"]):
        raise ValueError("MODEL_APPROVAL_STALE")
    family = family_of(task["draft"])
    spec = FAMILIES[family]
    data = task_root / "work"
    if data.exists():
        raise ValueError("PREPARATION_ALREADY_EXISTS")
    context = RunContext(root, data)
    task_id = task_root.name
    problem_id = "pdef-" + task_id
    runner, datasets = _runner(family), _datasets(family)
    with locked(task_root.parent.parent / "claim-reservations.lock"), using(context):
        used, history = historical_claims(root, task_root.parent.parent, family)
        config = read(root / spec["config"])
        base = _base_sets(family, config, root, task_id + "-r1")
        chosen = None
        # A predetermined search over grid sizes, using only geometry and separation, never errors.
        for name, gl, cgl in claim_grid_candidates(family):
            claim = datasets.claim_pool_manifests({name: (gl, cgl)}, label=problem_id)[name]
            if set(load_evaluation_set(claim).identities) & used:
                continue
            # 2D: the attempt refuses a grid whose coordinates sit on a small rational (preregistered rule).
            if family == "poisson2d" and not datasets.component_anti_collision(datasets.points_of(claim))["ok"]:
                continue
            base["claim"] = claim
            isolation = datasets.isolation_report(base, min_separation=config["sets"]["minSeparation"])
            if isolation["disjoint"]:
                chosen = (name, gl, cgl, claim)
                break
        if chosen is None:
            raise ValueError("NO_FRESH_DISJOINT_CLAIM_SET")
        name, gl, cgl, claim = chosen
        problems = data / runner.PROBLEMS_DIR
        problems.mkdir(parents=True)
        (problems / f"{problem_id}-claim-{name}.json").write_bytes(canonical_bytes(claim))
        write(problems / f"{problem_id}-claim-pool.json", {"members": {name: {
            "glOrder": gl, "cglCount": cgl, "artifactHash": canonical_sha256(claim),
            "sampleSetHash": sample_set_hash(claim), "designatedRevision": 1, "status": "SEALED"}}})
        attempt = _attempt(family, root, data, problem_id, attempt_id="main", claim_member=name)
        attempt.phase_identity()
        attempt.phase_problem()
        write(data / "historical-claims.json", history)
        # 1D keeps its historical tolerance; 2D's is the reproduction block of its frozen configuration.
        tolerance = ({"devRelL2MedianAbsDiff": 1e-4, "seedProtocolVerdictMustAgree": True} if family == "poisson1d" else
                     {k: config["reproduction"][k] for k in ("devRelL2MedianAbsDiff", "devRelL2MedianRelDiff",
                                                             "seedProtocolVerdictMustAgree")})
        plan = {"schemaVersion": "leo.executionPlan/1", "taskId": task_id, "problemId": problem_id, "createdAt": utc_now(),
            "family": family, "context": context.document(), "configPath": spec["config"], "codeManifest": manifest,
            "codeHash": code_hash_from_manifest(manifest), "specHash": attempt.pdef["specHash"],
            "problemDefinition": attempt.pdef, "solverConfiguration": config,
            "claimMember": name, "claimSampleSetHash": sample_set_hash(claim),
            "pythonA": sys.executable, "pythonB": str(python_b),
            "environmentA": environment_a, "environmentB": environment_b,
            "modelHash": digest(task["draft"]), "seedProtocol": config["seedProtocol"],
            "reproductionSeedOffset": 10000, "budgetSeconds": spec["budgetSeconds"],
            "parallelWorkers": parallel_workers(family),
            "phases": ["main", "tier1", "reproduction", "g6"],
            "expectedTolerance": tolerance,
            "dataFiles": tree_hashes(data, exclude=())}
        write(task_root / "execution-plan.json", plan, exclusive=True)
    return plan


def check_plan(task_root, root, *, prepared=True):
    plan = read(task_root / "execution-plan.json")
    if plan["taskId"] != task_root.name or Path(plan["context"]["codeRoot"]).resolve() != root.resolve():
        raise ValueError("PLAN_LOCATION_MISMATCH")
    if Path(plan["context"]["dataRoot"]).resolve() != (task_root / "work").resolve():
        raise ValueError("PLAN_DATA_ROOT_MISMATCH")
    if scientific_identity(root) != plan["codeManifest"]:
        raise ValueError("PLAN_CODE_CHANGED")
    if prepared and tree_hashes(task_root / "work", exclude=()) != plan["dataFiles"]:
        raise ValueError("PREPARED_EVIDENCE_CHANGED")
    for key in ("A", "B"):
        if _environment(plan["python" + key], root) != plan["environment" + key]:
            raise ValueError("PLAN_ENVIRONMENT_CHANGED")
    return plan


def phase(task_root, root, name):
    plan = read(task_root / "execution-plan.json")
    # Plans written before 2.2.11 carry no family: they are 1D.
    family = plan.get("family", "poisson1d")
    if family not in FAMILIES:
        raise ValueError("RESEARCH_FAMILY_INVALID")
    runner = _runner(family)
    context = RunContext.from_document(plan["context"])
    data = context.data_root
    original = data / "attempts/main"
    reproduction = data / "attempts/reproduction"
    with using(context):
        if name in ("main", "reproduction"):
            attempt = _attempt(family, root, data, plan["problemId"], attempt_id=name, claim_member=plan["claimMember"],
                               seed_offset=0 if name == "main" else 10000,
                               reproduction_of=None if name == "main" else original,
                               workers=plan.get("parallelWorkers", 1))
            result = attempt.run()
            if name == "main" and result["finalState"] != "REPRODUCIBILITY_CHECK":
                return False
        elif name == "tier1":
            runner.run_redteam(original, label="tier1")
            result = read(original / "tier1_redteam.json")
            if not result["passed"]:
                return False
        elif name == "g6":
            if family == "poisson1d":
                from pinn.experiments import report
            else:
                from pinn.experiments2d import report2d as report
            verify_attempt(original)
            verify_attempt(reproduction)
            runner.run_apply_g6(original, reproduction)
            report.write_trust_report(original, root)
        else:
            raise ValueError("PHASE_INVALID")
    return True


def execute(task_root, root):
    """Run the approved plan; a supervisor failure is recorded, never left for the UI to guess."""
    try:
        _execute(task_root, root)
    except Exception as error:
        text = str(error)
        reason = text if re.fullmatch(r"[A-Z][A-Z0-9_]{2,80}", text) else type(error).__name__
        if not (task_root / "completion.json").exists():
            write(task_root / "completion.json", {"state": "STOPPED", "phase": "supervisor", "reason": reason,
                                                  "allowedClaims": [], "at": utc_now()})
        raise


def _stop(child):
    """End a phase and everything it started: parallel trainings are the phase's own children, and
    terminating only the phase would leave them computing after a cancel or a time-out."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(child.pid)], capture_output=True,
                       creationflags=0x08000000, timeout=30)
    else:
        child.terminate()
    try:
        child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        child.kill()
        child.wait()


def _execute(task_root, root):
    """Supervisor owns a lock across child phases; cancellation survives app restarts."""
    with locked(task_root.parent.parent / "execution.lock"), locked(task_root / "worker.lock"):
        started = time.monotonic()
        write(task_root / "worker-owner.json", {"pid": os.getpid(), "at": utc_now()})
        plan = check_plan(task_root, root)
        approval = read(task_root / "run-approval.json")
        if approval["contentHash"] != digest(plan) or approval["taskId"] != task_root.name:
            raise ValueError("RUN_APPROVAL_STALE")
        if read(task_root / "state.json")["state"] not in ("RUNNING", "CANCELLING"):
            raise ValueError("RUN_NOT_ADMITTED")
        write(task_root / "worker-owner.json", {"pid": os.getpid(), "approvalHash": digest(approval), "at": utc_now()})
        for name in plan["phases"]:
            if (task_root / "cancel-request.json").exists():
                write(task_root / "completion.json", {"state": "CANCELLED", "allowedClaims": [], "at": utc_now()})
                return
            if scientific_identity(root) != plan["codeManifest"]:
                raise ValueError("RUN_CODE_CHANGED")
            write(task_root / "progress.json", {"phase": name, "at": utc_now()})
            python = plan["pythonB" if name == "reproduction" else "pythonA"]
            command = [python, "-u", "-m", "pinn.research.worker", "phase", "--task-root", str(task_root),
                       "--code-root", str(root), "--phase", name]
            with (task_root / (name + ".log")).open("xb") as log:
                child = subprocess.Popen(command, cwd=root, stdout=log, stderr=subprocess.STDOUT,
                    creationflags=0x08000000 if os.name == "nt" else 0)
                while child.poll() is None:
                    cancelled = (task_root / "cancel-request.json").exists()
                    expired = time.monotonic() - started >= plan["budgetSeconds"]
                    if cancelled or expired:
                        _stop(child)
                        write(task_root / "completion.json", {"state": "CANCELLED" if cancelled else "TIMED_OUT",
                                                              "allowedClaims": [], "at": utc_now()})
                        return
                    time.sleep(0.25)
            if child.returncode:
                write(task_root / "completion.json", {"state": "STOPPED", "phase": name,
                    "exitCode": child.returncode, "allowedClaims": [], "at": utc_now()})
                return
        original = task_root / "work/attempts/main"
        result = verify_attempt(original)
        # Snapshot binds the completed records; UI re-verifies on every view/export.
        write(task_root / "completion.json", {"state": "COMPLETED", "at": utc_now(), "result": result,
            "evidenceHashes": tree_hashes(task_root / "work", exclude=())})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("environment", "prepare", "check", "run", "phase", "verify"))
    parser.add_argument("--task-root", type=Path)
    parser.add_argument("--code-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--python-b", type=Path)
    parser.add_argument("--phase")
    args = parser.parse_args()
    root = args.code_root.resolve()
    if args.command == "environment":
        import torch, numpy  # qualification must fail when the actual frameworks are absent
        print(json.dumps(environment_fingerprint()))
    elif args.command == "prepare":
        prepare(args.task_root.resolve(), root, args.python_b.resolve())
    elif args.command == "check":
        check_plan(args.task_root.resolve(), root)
    elif args.command == "run":
        execute(args.task_root.resolve(), root)
    elif args.command == "phase":
        return 0 if phase(args.task_root.resolve(), root, args.phase) else 3
    else:
        print(json.dumps(verify_attempt(args.task_root / "work/attempts/main"), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
