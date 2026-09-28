"""Human-invoked, portable reproduction of an exported task (never reopens D_claim)."""
import argparse
from pathlib import Path
import shutil
import subprocess
import json

from pinn.research.storage import read
from pinn.research.evidence import verify_package, verify_attempt
from pinn.research.context import RunContext, using
from pinn.experiments.common import environment_fingerprint, sha256_file
from pinn.governance.trust_vector import EnvironmentFingerprint, independent_environments


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    package, output = args.package.resolve(), args.out.resolve()
    verify_package(package)
    original = package / "work/attempts/main"
    verify_attempt(original)
    plan = read(package / "execution-plan.json")
    identity = read(original / "identity.json")
    if output.exists() or output.is_relative_to(package):
        raise ValueError("REPRODUCTION_OUTPUT_MUST_BE_NEW_AND_OUTSIDE_PACKAGE")
    env = environment_fingerprint()
    if not independent_environments(EnvironmentFingerprint.from_mapping(env),
                                    EnvironmentFingerprint.from_mapping(identity["environment"])):
        raise ValueError("REPRODUCTION_ENVIRONMENT_NOT_INDEPENDENT")
    print(json.dumps({"codeHash": identity["codeHash"], "specHash": plan["specHash"], "environment": env,
        "seedOffset": 10000, "claimSetWillBeOpened": False, "output": str(output), "execute": args.execute}, indent=2))
    if not args.execute:
        return 0
    # Work on a copy so Git metadata and new evidence never change the delivered package.
    source = output / "source"
    shutil.copytree(package / "source", source)
    for entry in identity["codeManifest"]:
        if sha256_file(source / entry["path"]) != entry["sha256"]:
            raise ValueError("REPRODUCTION_CODE_MISMATCH")
    subprocess.run(["git", "init", str(source)], check=True, capture_output=True)
    paths = [p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file() and ".git" not in p.parts]
    subprocess.run(["git", "add", "--", *paths], cwd=source, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.name=Leo evidence reconstruction", "-c", "user.email=local@invalid",
                    "commit", "-m", "Reconstruct exported method bytes"], cwd=source, check=True, capture_output=True)
    data = output / "work"
    for name in ("ledger", "problems"):
        shutil.copytree(package / "work/experiments/poisson1d" / name, data / "experiments/poisson1d" / name)
    # Execute the copied, verified method, not a newer installed pinn module.
    import sys
    from pinn.research.storage import write
    context_file = output / "context.json"
    write(context_file, RunContext(source, data).document())
    command = [sys.executable, "-m", "pinn.experiments.runner", "--context", str(context_file), "attempt",
        "--config", str(source / plan["configPath"]), "--attempt-id", "independent-reproduction",
        "--problem-id", plan["problemId"], "--revision", "1", "--out-root", str(data / "attempts"),
        "--ledger", str(data / "experiments/poisson1d/ledger" / (plan["problemId"] + ".json")),
        "--claim-pool-member", plan["claimMember"], "--seed-offset", "10000", "--reproduction-of", str(original)]
    subprocess.run(command, cwd=source, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
