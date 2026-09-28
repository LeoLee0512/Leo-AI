"""Verify the scientific wheelhouse and both installed research interpreters.

This checks software readiness, not scientific acceptance or experiment identity.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
LOCK = REPO / "pinn/research/requirements-science.lock"
MANIFEST = REPO / "manifests/science-wheelhouse.json"
WHEELS = REPO / "wheelhouse-science"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pins():
    return {name.lower().replace("_", "-"): version for name, version in
            (line.split("==", 1) for line in LOCK.read_text().splitlines() if "==" in line)}


def record_wheelhouse():
    from packaging.utils import parse_wheel_filename
    rows = []
    for path in sorted(WHEELS.glob("*.whl")):
        name, version, _, _ = parse_wheel_filename(path.name)
        rows.append({"filename": path.name, "package": name, "version": str(version),
                     "size": path.stat().st_size, "sha256": sha(path)})
    if {row["package"]: row["version"] for row in rows} != pins() or len(rows) != len(pins()):
        raise ValueError("Scientific wheels do not exactly match the lock")
    MANIFEST.write_text(json.dumps({"schema_version": 1, "requirements_sha256": sha(LOCK),
        "platform": "Windows x64 / CPython 3.12", "indexes": ["https://pypi.org/simple", "https://download.pytorch.org/whl/cpu"],
        "wheels": rows}, indent=2) + "\n", encoding="utf-8", newline="\n")


def verify_wheelhouse():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    problems = []
    rows = data["wheels"]
    if data.get("requirements_sha256") != sha(LOCK):
        problems.append("science lock hash mismatch")
    if {row["package"]: row["version"] for row in rows} != pins() or len(rows) != len(pins()):
        problems.append("science wheel inventory does not match lock")
    if {p.name for p in WHEELS.glob("*.whl")} != {row["filename"] for row in rows}:
        problems.append("science wheel files differ from manifest")
    for row in rows:
        path = (WHEELS / row["filename"]).resolve()
        if not path.is_relative_to(WHEELS.resolve()) or not path.is_file():
            problems.append("missing/unsafe wheel: " + row["filename"])
        elif path.stat().st_size != row["size"] or sha(path) != row["sha256"]:
            problems.append("wheel hash/size mismatch: " + row["filename"])
    return problems


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, timeout=60).decode("utf-8").strip()


def verify_runtime(app_root):
    data = json.loads((app_root / "runtime/research-runtime.json").read_text(encoding="utf-8-sig"))
    paths = {k: (app_root / data[k]).resolve() for k in ("codeRoot", "pythonA", "pythonB")}
    errors = []
    if git(paths["codeRoot"], "rev-parse", "HEAD") != git(REPO, "rev-parse", "HEAD"):
        errors.append("science source commit differs from release")
    if git(paths["codeRoot"], "status", "--porcelain"):
        errors.append("science source checkout is dirty")
    if sha(paths["codeRoot"] / "pinn/research/requirements-science.lock") != sha(LOCK):
        errors.append("science runtime lock differs from release")
    prefixes = []
    probe = "import sys,json,importlib.metadata as m;print(json.dumps({'prefix':sys.prefix,'python':list(sys.version_info[:3]),'packages':{d.metadata['Name'].lower().replace('_','-'):d.version for d in m.distributions()}}))"
    for key in ("pythonA", "pythonB"):
        raw = subprocess.check_output([str(paths[key]), "-I", "-B", "-c", probe], timeout=60)
        actual = json.loads(raw)
        prefixes.append(Path(actual["prefix"]).resolve())
        if actual["python"] != [3, 12, 9]:
            errors.append(key + ": unexpected Python version")
        if actual["packages"] != pins():
            errors.append(key + ": installed packages differ from science lock")
        check = subprocess.run([str(paths[key]), "-B", "-m", "pip", "check"], capture_output=True, timeout=60)
        if check.returncode:
            errors.append(key + ": pip check failed")
    if prefixes[0] == prefixes[1] or paths["pythonA"] == paths["pythonB"]:
        errors.append("science interpreters are not separate installations")
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record-wheelhouse", action="store_true")
    parser.add_argument("--app-root", type=Path)
    args = parser.parse_args()
    if args.record_wheelhouse:
        record_wheelhouse()
    problems = verify_wheelhouse()
    if args.app_root:
        problems += verify_runtime(args.app_root)
    print(json.dumps({"problems": problems}, ensure_ascii=False, indent=2))
    raise SystemExit(bool(problems))
