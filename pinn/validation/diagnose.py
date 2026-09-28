"""Write append-only component evidence without formal Gate or training APIs.

Run as ``python -m pinn.validation.diagnose --output NEW_DIRECTORY``. The output
directory must not already exist. No claim is emitted, even for good controls.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import uuid

from scientific_reference.poisson_fdm import refinement_diagnostic
from .fixtures import FIXTURES
from .poisson import evaluate_samples, load_candidate_protocol, sample_callable_fixture


def _json_write(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    protocol = load_candidate_protocol(root)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    created_at = datetime.now(timezone.utc).isoformat()
    dependency_versions = {}
    for name in ("numpy", "torch", "pytest"):
        try:
            dependency_versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            dependency_versions[name] = "NOT_INSTALLED"
    git = lambda *command: subprocess.check_output(["git", *command], cwd=root, text=True).strip()
    sources = ("pinn/validation/poisson.py", "pinn/validation/fixtures.py",
               "pinn/validation/diagnose.py", "scientific_reference/poisson_fdm.py",
               "pinn/reference/analytic_poisson.py", "pinn/governance/poisson_contract.py")
    fixture_source_hash = hashlib.sha256((root / "pinn/validation/fixtures.py").read_bytes()).hexdigest()
    metadata = {
        "diagnosticId": "validator-component-" + uuid.uuid4().hex,
        "evaluationScope": "VALIDATOR_COMPONENT", "createdAt": created_at,
        "workflowStatus": "NOT_APPLICABLE", "claimStatus": "NOT_APPLICABLE",
        "trainingApplicable": False, "formalGatesExecuted": [], "hashLockExecuted": False,
        "gitCommit": git("rev-parse", "HEAD"), "gitStatus": git("status", "--porcelain=v1"),
        "pythonExecutable": sys.executable, "pythonVersion": sys.version,
        "platform": platform.platform(), "machine": platform.machine(),
        "device": "cpu", "dtype": "float64", "logicalCpuCount": os.cpu_count(),
        "dependencies": dependency_versions, "evaluationSeed": "NOT_APPLICABLE",
        "sourceHashes": {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in sources},
        "candidateHashes": {"spec": protocol.spec_sha256, "protocol": protocol.protocol_sha256},
        "command": [sys.executable, "-m", "pinn.validation.diagnose", "--output", str(output)],
    }
    _json_write(output / "metadata.json", metadata)
    results = []
    for fixture in FIXTURES:
        samples = sample_callable_fixture(protocol, fixture.solution, fixture.first_derivative,
                                          fixture.second_derivative)
        _json_write(output / (fixture.fixture_id + "-raw.json"), {
            "evaluationScope": "VALIDATOR_COMPONENT", "trainingApplicable": False,
            "fixtureSourceSha256": fixture_source_hash,
            "fixtureParameters": asdict(fixture), "samples": asdict(samples),
        })
        result = evaluate_samples(protocol, samples)
        result["fixtureParameters"] = asdict(fixture)
        result["fixtureSourceSha256"] = fixture_source_hash
        repeated = evaluate_samples(protocol, samples)
        result["identicalInProcessEvaluation"] = repeated["metrics"] == result["metrics"]
        results.append(result)
    _json_write(output / "fixture-metrics.json", results)
    _json_write(output / "fdm-refinement.json", refinement_diagnostic())
    _json_write(output / "fdm-B11-single-grid.json", refinement_diagnostic((4,)))
    _json_write(output / "files.sha256.json", {
        "evaluationScope": "VALIDATOR_COMPONENT", "createdAt": created_at,
        "files": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in sorted(output.iterdir()) if path.is_file()},
    })
    print(json.dumps({"evidence": str(output), "evaluationScope": "VALIDATOR_COMPONENT",
                      "fixtures": len(results), "formalGatesExecuted": [],
                      "claimStatus": "NOT_APPLICABLE"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
