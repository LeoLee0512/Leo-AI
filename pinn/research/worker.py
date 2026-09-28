"""Poisson product adapter. Preparation never trains; execution requires a bound approval."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from pinn.research.context import RunContext, using
from pinn.research.storage import read, write, digest, locked
from pinn.research.evidence import tree_hashes, verify_attempt
from pinn.experiments.common import (code_manifest, code_hash_from_manifest, sha256_file,
    environment_fingerprint, environment_identity, assert_code_identity_complete, workspace_dirty_paths, utc_now)

CONFIG = "pinn/research/poisson1d-config.json"
IDENTITY_EXTRAS = (CONFIG, "leo_shell/research.py", "leo_shell/research_draft.py", "leo_shell/api.py",
                   "stage/research-panel.js")


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


def historical_claims(root, research_root):
    """Include reserved as well as opened historical sets, and every product reservation."""
    from pinn.governance.evaluation_sets import load_evaluation_set
    identities = set()
    history = {}
    candidates = list((root / "experiments/poisson1d").glob("runs/*/sets/claim.json"))
    candidates += list((root / "experiments/poisson1d/problems").glob("*-claim-GL*.json"))
    candidates += list((research_root / "tasks").glob("*/work/experiments/poisson1d/problems/*-claim-GL*.json"))
    for path in sorted(candidates):
        doc = read(path)
        identities.update(load_evaluation_set(doc).identities)
        history[str(path)] = sha256_file(path)
    if not history:
        raise ValueError("HISTORICAL_CLAIM_REGISTRY_MISSING")
    return identities, history


def prepare(task_root, root, python_b):
    from pinn.experiments import runner, datasets
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
    if task["state"] != "MODEL_CONFIRMED" or not task.get("modelApproval"):
        raise ValueError("MODEL_APPROVAL_REQUIRED")
    if task["modelApproval"]["contentHash"] != digest(task["draft"]):
        raise ValueError("MODEL_APPROVAL_STALE")
    data = task_root / "work"
    if data.exists():
        raise ValueError("PREPARATION_ALREADY_EXISTS")
    context = RunContext(root, data)
    task_id = task_root.name
    problem_id = "pdef-" + task_id
    with locked(task_root.parent.parent / "claim-reservations.lock"), using(context):
        used, history = historical_claims(root, task_root.parent.parent)
        config = read(root / CONFIG)
        protocol = runner.load_candidate_protocol(root)
        base = datasets.build_sets(config, claim_nodes=protocol.quadrature_nodes,
                                   claim_pointwise=protocol.pointwise_nodes, claim_label=task_id + "-r1")
        chosen = None
        # A predetermined search over grid sizes, using only geometry and separation, never errors.
        for index in range(32):
            gl, cgl = 1024 + 32 * index, 4002 + 2 * index
            name = f"GL{gl}-CGL{cgl}"
            claim = datasets.claim_pool_manifests({name: (gl, cgl)}, label=problem_id)[name]
            if set(load_evaluation_set(claim).identities) & used:
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
        attempt = runner.Attempt(config_path=root / CONFIG, attempt_id="main", problem_id=problem_id, revision=1,
            out_root=data / "attempts", ledger_path=data / runner.LEDGER_DIR / f"{problem_id}.json",
            reenter_from=None, claim_pool_member=name)
        attempt.phase_identity()
        attempt.phase_problem()
        write(data / "historical-claims.json", history)
        plan = {"schemaVersion": "leo.executionPlan/1", "taskId": task_id, "problemId": problem_id, "createdAt": utc_now(),
            "context": context.document(), "configPath": CONFIG, "codeManifest": manifest,
            "codeHash": code_hash_from_manifest(manifest), "specHash": attempt.pdef["specHash"],
            "problemDefinition": attempt.pdef, "solverConfiguration": config,
            "claimMember": name, "claimSampleSetHash": sample_set_hash(claim),
            "pythonA": sys.executable, "pythonB": str(python_b),
            "environmentA": environment_a, "environmentB": environment_b,
            "modelHash": digest(task["draft"]), "seedProtocol": config["seedProtocol"],
            "reproductionSeedOffset": 10000, "budgetSeconds": 3600,
            "phases": ["main", "tier1", "reproduction", "g6"],
            "expectedTolerance": {"devRelL2MedianAbsDiff": 1e-4, "seedProtocolVerdictMustAgree": True},
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
    from pinn.experiments import runner
    from pinn.experiments import report
    plan = read(task_root / "execution-plan.json")
    context = RunContext.from_document(plan["context"])
    data = context.data_root
    original = data / "attempts/main"
    reproduction = data / "attempts/reproduction"
    with using(context):
        if name in ("main", "reproduction"):
            attempt = runner.Attempt(config_path=root / CONFIG, attempt_id=name,
                problem_id=plan["problemId"], revision=1, out_root=data / "attempts",
                ledger_path=data / runner.LEDGER_DIR / f"{plan['problemId']}.json", reenter_from=None,
                claim_pool_member=plan["claimMember"], seed_offset=0 if name == "main" else 10000,
                reproduction_of=None if name == "main" else original)
            result = attempt.run()
            if name == "main" and result["finalState"] != "REPRODUCIBILITY_CHECK":
                return False
        elif name == "tier1":
            runner.run_redteam(original, label="tier1")
            result = read(original / "tier1_redteam.json")
            if not result["passed"]:
                return False
        elif name == "g6":
            verify_attempt(original)
            verify_attempt(reproduction)
            runner.run_apply_g6(original, reproduction)
            report.write_trust_report(original, root)
        else:
            raise ValueError("PHASE_INVALID")
    return True


def execute(task_root, root):
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
                        child.terminate()
                        try:
                            child.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            child.kill()
                            child.wait()
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
