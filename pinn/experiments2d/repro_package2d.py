"""G6 reproduction package for the 2D calibration.

Same contract as the 1D package (``pinn.experiments.repro_package``): frozen
spec and config, code identity, dependency lock of the original installation,
seed manifest, dataset generation rules, the preregistered tolerance, the
artifact schemas and step-by-step instructions.  Two 2D-specific differences:
the tolerance is read from the frozen configuration (it carries the tightened
relative limit as well as the 1D-inherited absolute one), and the instructions
name the 2D runner and the frozen-checkout requirement that the 1D round
learned the hard way.
"""

from __future__ import annotations

import json
from pathlib import Path

from pinn.experiments.common import load_json, sha256_file, utc_now


def write_package(attempt_dir: Path, repo_root: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    identity = load_json(attempt_dir / "identity.json")
    pdef = load_json(attempt_dir / "problem_definition.json")
    run_record = load_json(attempt_dir / "run_record.json")
    training = load_json(attempt_dir / "training_report.json")
    config_path = repo_root / identity["configPath"]
    config = load_json(config_path)
    for src, name in ((attempt_dir / "problem_definition.json", "problem_definition.json"),
                      (config_path, "config.json"),
                      (repo_root / "specs/poisson-2d/v1.0/POISSON_2D_V1.0_spec.json", "POISSON_2D_V1.0_spec.json"),
                      (attempt_dir / "run_record.json", "original_run_record.json"),
                      (attempt_dir / "seed_ledger.json", "original_seed_ledger.json"),
                      (attempt_dir / "sets/isolation.json", "dataset_isolation.json"),
                      (attempt_dir / "training_report.json", "original_training_report.json")):
        (out_dir / name).write_bytes(src.read_bytes())
    schemas = sorted((repo_root / "pinn/governance/schemas").glob("*.json"))
    (out_dir / "schemas").mkdir(exist_ok=True)
    for schema in schemas:
        (out_dir / "schemas" / schema.name).write_bytes(schema.read_bytes())
    sp = config["seedProtocol"]
    offset = int(config["reproduction"].get("seedOffset", 10000))
    tolerance = dict(config["reproduction"])
    tolerance["note"] = ("compare the dev relative-L2 median and the k/N verdict of the reproduction run with the original; "
                         "BOTH the absolute and the relative limit must hold; the claim set is not reopened")
    manifest = {
        "packageType": "PINN_G6_REPRODUCTION_PACKAGE_2D", "createdAt": utc_now(), "attemptId": attempt_dir.name,
        "spatialDimension": 2, "problemId": pdef["problemId"], "revision": pdef["revision"], "specHash": pdef["specHash"],
        "codeHash": identity["codeHash"], "gitHead": identity["gitHead"], "constitutionVersion": identity["constitutionVersion"],
        "originalEnvironment": identity["environment"], "originalEnvironmentId": identity["environmentId"],
        "originalDependencyLockHash": identity["environment"]["dependencyLockHash"],
        "originalSeedSetId": run_record["seedSetId"], "originalSeeds": run_record["seeds"],
        "originalResult": training["seedStatistics"],
        "reproductionSeedRule": (f"use a DIFFERENT seed set: init={sp['initBase']}+{offset}+i, sample={sp['sampleBase']}+{offset}+i, "
                                 f"batch={sp['batchBase']}+{offset}+i (i in 0..{sp['runs'] - 1}); register it before training"),
        "datasetGenerationRules": load_json(attempt_dir / "sets/isolation.json").get("generation"),
        "expectedTolerance": tolerance,
        "independenceRequirement": ("at least one strong environment field must differ (machineId, osFamily, acceleratorClass, "
                                    "frameworkVersion, blasBackend, dependencyLockHash, installationId); a renamed host or a copied "
                                    "prefix is the same environment"),
        "instructions": [
            f"git worktree add --detach <frozen dir> {identity['gitHead']}  -- the reproduction MUST run the runner of that commit; "
            f"running a newer runner changes codeHash and reproduction_status will (correctly) return BLOCKED (1D lesson, log 5.24)",
            f"in the frozen checkout the tracked code identity files plus {identity['configPath']} must recompute codeHash "
            f"{identity['codeHash'][:12]}...",
            "install torch and numpy of the versions in this manifest into a NEW installation (different prefix / dependency lock); "
            "do not copy or clone the original environment",
            "drive the runner from a script OUTSIDE the code identity manifest (e.g. a scratch directory), or call "
            "pinn.experiments2d.runner2d attempt --config <configPath> --attempt-id repro-<label> --problem-id <problemId> "
            f"--revision <revision> --claim-pool-member <member> --seed-offset {offset} --reproduction-of <original attempt dir>",
            "the reproduction stops after Gate 4 and never opens a claim set",
            "hand the new RunRecord (environment fingerprint, seeds) back; C_repro is judged by "
            "pinn.experiments2d.runner2d.judge_reproduction -> pinn.governance.trust_vector.reproduction_status",
        ],
        "schemas": [schema.name for schema in schemas],
        "fileHashes": {p.name: sha256_file(p) for p in sorted(out_dir.iterdir()) if p.is_file()},
    }
    (out_dir / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                                   encoding="utf-8", newline="\n")
    return out_dir
