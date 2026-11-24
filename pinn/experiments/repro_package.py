"""G6 reproduction package: everything a second, independent installation needs to reproduce a formal attempt.

Written when no independent environment is available here (C_repro BLOCKED,
Constitution 54 A-0001).  The package is self-describing: frozen spec and
config, code identity, dependency lock of the original installation, seed
manifest, dataset generation rules, the preregistered reproduction tolerance,
the artifact schemas and step-by-step instructions.  The reproducing party
runs the same commit with *its own* environment fingerprint and a *different*
seed set; ``reproduction_status`` then judges C_repro.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .common import load_json, sha256_file, utc_now
from pinn.research.evidence import tree_hashes, verify_package

TOLERANCE = {"devRelL2MedianAbsDiff": 1e-4, "seedProtocolVerdictMustAgree": True,
             "note": "compare the dev relative-L2 median and the k/N verdict of the reproduction run with the original; the claim set is not reopened"}


def write_package(attempt_dir: Path, repo_root: Path, out_dir: Path) -> Path:
    if out_dir.exists():
        raise FileExistsError("reproduction packages are immutable; choose a new destination")
    out_dir.mkdir(parents=True)
    identity = load_json(attempt_dir / "identity.json")
    pdef = load_json(attempt_dir / "problem_definition.json")
    run_record = load_json(attempt_dir / "run_record.json")
    training = load_json(attempt_dir / "training_report.json")
    config_path = repo_root / identity["configPath"]
    for src, name in ((attempt_dir / "problem_definition.json", "problem_definition.json"), (config_path, "config.json"),
                      (attempt_dir / "run_record.json", "original_run_record.json"), (attempt_dir / "seed_ledger.json", "original_seed_ledger.json"),
                      (attempt_dir / "sets/isolation.json", "dataset_isolation.json"), (attempt_dir / "training_report.json", "original_training_report.json")):
        (out_dir / name).write_bytes(src.read_bytes())
    if sha256_file(config_path) != identity["configSha256"]:
        raise ValueError("configuration changed since the original attempt")
    for entry in identity["codeManifest"]:
        source = repo_root / entry["path"]
        if sha256_file(source) != entry["sha256"]:
            raise ValueError("source identity changed: " + entry["path"])
    schemas = sorted((repo_root / "pinn/governance/schemas").glob("*.json"))
    (out_dir / "schemas").mkdir(exist_ok=True)
    for s in schemas:
        (out_dir / "schemas" / s.name).write_bytes(s.read_bytes())
    sp = load_json(config_path)["seedProtocol"]
    manifest = {
        "packageType": "PINN_G6_REPRODUCTION_PACKAGE", "createdAt": utc_now(), "attemptId": attempt_dir.name,
        "problemId": pdef["problemId"], "revision": pdef["revision"], "specHash": pdef["specHash"], "codeHash": identity["codeHash"],
        "gitHead": identity["gitHead"], "constitutionVersion": identity["constitutionVersion"],
        "originalEnvironment": identity["environment"], "originalEnvironmentId": identity["environmentId"],
        "originalDependencyLockHash": identity["environment"]["dependencyLockHash"],
        "originalSeedSetId": run_record["seedSetId"], "originalSeeds": run_record["seeds"],
        "originalResult": training["seedStatistics"],
        "reproductionSeedRule": f"use a DIFFERENT seed set, e.g. init={sp['initBase']}+10000+i, sample={sp['sampleBase']}+10000+i, batch={sp['batchBase']}+10000+i (i in 0..{sp['runs'] - 1}); register it before training",
        "datasetGenerationRules": load_json(attempt_dir / "sets/isolation.json").get("generation"),
        "expectedTolerance": TOLERANCE,
        "independenceRequirement": "at least one strong environment field must differ (machineId, osFamily, acceleratorClass, frameworkVersion, blasBackend, dependencyLockHash, installationId); a renamed host or a copied prefix is the same environment",
        "instructions": [
            f"git checkout {identity['gitHead']} in a clean tree (codeHash must recompute to {identity['codeHash'][:12]}... for the tracked code identity files plus config.json at {identity['configPath']})",
            "install torch (CPU float64 sufficient), numpy, matplotlib in a NEW installation (different prefix / lock)",
            "python -m pinn.experiments.runner attempt --config <configPath> --attempt-id repro-<label> --problem-id <problemId> --revision <revision> --seed-offset 10000 --reproduction-of <original-attempt-directory>",
            "compare RUN_SUMMARY.training.median and successRate with original_training_report.json under expectedTolerance",
            "hand the new RunRecord (environment fingerprint, seeds) to the original party; C_repro is judged with pinn.governance.trust_vector.reproduction_status",
        ],
        "schemas": [s.name for s in schemas],
        "fileHashes": tree_hashes(out_dir),
    }
    (out_dir / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    verify_package(out_dir)
    return out_dir
