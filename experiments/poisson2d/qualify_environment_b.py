"""Qualify the 2D Environment B against Constitution 28.1 and write the record.

Run with the Environment B interpreter so the fingerprint is B's own:

    PYTHONPATH=. <envB python> -B experiments/poisson2d/qualify_environment_b.py <original attempt dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pinn.experiments.common import environment_fingerprint, environment_identity, load_json, utc_now
from pinn.governance.trust_vector import EnvironmentFingerprint, independent_environments

OUT = Path("experiments/poisson2d/environment_b_qualification.json")


def main() -> int:
    attempt = Path(sys.argv[1])
    identity = load_json(attempt / "identity.json")
    a_map = identity["environment"]
    b_map = environment_fingerprint()
    a = EnvironmentFingerprint.from_mapping(a_map)
    b = EnvironmentFingerprint.from_mapping(b_map)
    independent = independent_environments(a, b)
    strong = sorted(a.strong_material())
    differing = sorted(field for field in strong if a_map.get(field) != b_map.get(field))
    document = {
        "purpose": "Constitution 28.1 qualification of the second installation used for the 2D Gate 6 reproduction",
        "qualifiedAt": utc_now(),
        "originalAttempt": attempt.name,
        "environmentA": a_map,
        "environmentIdA": identity["environmentId"],
        "environmentB": b_map,
        "environmentIdB": environment_identity(b_map),
        "strongFields": strong,
        "strongFieldsDiffering": differing,
        "independent": independent,
        "rule": "two environments are independent when at least one strong field differs (machineId, osFamily, "
                "acceleratorClass, frameworkVersion, blasBackend, dependencyLockHash, installationId); a renamed host "
                "or a copied prefix is the same environment",
        "constructionB": ("python -m venv (base: mamba python 3.12.9, no --system-site-packages) at a prefix OUTSIDE the "
                          f"repository whose identity is {b_map['installationId']} (installationId = sha256(prefix)[:16]; the "
                          "absolute path is deliberately not recorded -- Constitution 28.1: paths are not identity); "
                          "pip install --no-cache-dir torch==2.12.1 (CPU index) and numpy==2.4.5 -- only the dependencies the "
                          "reproduction package declares; no copy, no clone, no rename of environment A"),
        "pathRecordingRule": ("prospective rule (Final Closure Audit issue 3C): environment evidence records installationId, "
                              "the prefix hash, dependencyLockHash and the construction method, never an absolute user path"),
        "note": "machineId, osFamily, acceleratorClass, frameworkVersion and blasBackend are necessarily equal on the "
                "same machine; independence rests on installationId and dependencyLockHash, which is what 28.1 requires "
                "and is the same construction the 1D Gate 6 used",
    }
    OUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"independent": independent, "strongFieldsDiffering": differing,
                      "environmentIdB": document["environmentIdB"]}, ensure_ascii=False, indent=2))
    return 0 if independent else 1


if __name__ == "__main__":
    raise SystemExit(main())
