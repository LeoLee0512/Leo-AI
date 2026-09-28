"""Prove that a build manifest actually describes what is deployed.

The first round generated a manifest and stopped there. It was written before
the final commit, so it named commit 8a65838 while the tree had moved on to
86786cd, and its recorded source hashes no longer matched the files on disk.
A manifest nobody checks is provenance theatre.

This is the check. Every claim in the manifest is re-measured against the
repository, the deployed tree and the WSL daemon, and any mismatch exits
non-zero. In ``--strict`` (release) mode a check that could not be performed is
a failure too: NOT TESTED is never folded into PASS.

    python tools/verify_release.py --manifest manifests/build-current.json
    python tools/verify_release.py --manifest manifests/build-current.json --strict

Correct release order, which this enforces after the fact:

    edit -> test -> commit -> clean build -> deploy -> generate manifest -> verify
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
#: Must equal tools/build_manifest.py FRONTEND_FILES (a test keeps them together).
FRONTEND_FILES = ("shell.html", "workbench.html", "workbench.css", "workbench.js", "research-panel.js")
#: Theme payload no release ships since 2026-09-26 (injection layer, then the unused
#: web fonts); deploy_release.ps1 moves it into the rollback directory, so finding it
#: installed means a stale deployment.
RETIRED_THEME_PATHS = ("leo-inject.js", "leo.css", "i18n", "fonts")
DEFAULT_APP_ROOT = pathlib.Path(os.environ.get("LEO_APP_ROOT") or REPO / "LeoAIStudio")
PIN_PATH = REPO / "manifests" / "upstream-pin.json"

PASS, FAIL, NOT_TESTED = "PASS", "FAIL", "NOT TESTED"


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []

    def add(self, name: str, status: str, detail: str = "") -> None:
        self.rows.append((name, status, detail))

    def render(self) -> None:
        width = max(len(name) for name, _, _ in self.rows)
        for name, status, detail in self.rows:
            print(f"  {name:<{width}}  {status:<10} {detail}")

    def counts(self) -> dict[str, int]:
        out = {PASS: 0, FAIL: 0, NOT_TESTED: 0}
        for _, status, _ in self.rows:
            out[status] = out.get(status, 0) + 1
        return out


def run(args, cwd=None) -> tuple[int, str]:
    try:
        done = subprocess.run(args, cwd=cwd, capture_output=True, timeout=180)
    except Exception as error:  # noqa: BLE001
        return 1, f"{type(error).__name__}: {error}"
    return done.returncode, done.stdout.decode("utf-8", errors="replace").strip()


def sha256(path: pathlib.Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(manifest: dict, app_root: pathlib.Path, strict: bool) -> Report:
    report = Report()
    from release_identity import product_identity, executable_identity
    expected = product_identity()
    try:
        matches = manifest.get("product") == expected and executable_identity(app_root / "LeoAIStudio.exe") == expected
        report.add("product version", PASS if matches else FAIL, str(expected))
    except (OSError, ValueError) as exc:
        report.add("product version", FAIL, str(exc))

    # 1. The manifest must name the commit that is checked out.
    code, head = run(["git", "rev-parse", "HEAD"], cwd=REPO)
    claimed = (manifest.get("leo_repo") or {}).get("commit")
    if code != 0:
        report.add("leo commit", NOT_TESTED, "not a git repository")
    elif claimed == head:
        report.add("leo commit", PASS, head[:12])
    else:
        report.add("leo commit", FAIL, f"manifest {str(claimed)[:12]} != HEAD {head[:12]}")

    # 2. A dirty tree cannot be described by a commit.
    code, dirty = run(["git", "status", "--porcelain"], cwd=REPO)
    if code != 0:
        report.add("repo clean", NOT_TESTED, "git unavailable")
    elif dirty:
        report.add("repo clean", FAIL, f"{len(dirty.splitlines())} uncommitted file(s)")
    else:
        report.add("repo clean", PASS)

    # Build-time evidence must predate deployment and bind every packaged byte.
    from build_receipt import verify as verify_receipt
    receipt_path = app_root / "build-receipt.json"
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        problems = verify_receipt(receipt, REPO, app_root)
        if sha256(receipt_path) != manifest.get("build_receipt_sha256"):
            problems.append("receipt hash mismatch")
        report.add("build receipt", FAIL if problems else PASS, "; ".join(problems))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        report.add("build receipt", FAIL, f"missing/invalid build evidence: {type(exc).__name__}")

    # 3. Recorded source hashes must still match the files.
    frontend = manifest.get("frontend") or {}
    recorded_sources = frontend.get("sources") or {}
    drifted = []
    if set(recorded_sources) != {f"stage/{name}" for name in FRONTEND_FILES}:
        drifted.append("manifest does not record exactly the documents the shell loads")
    for name in FRONTEND_FILES:
        key = f"stage/{name}"
        recorded = recorded_sources.get(key)
        actual = sha256(REPO / "stage" / name)
        if recorded != actual:
            drifted.append(f"{key} {str(recorded)[:12]}!={str(actual)[:12]}")
    report.add("source hashes", FAIL if drifted else PASS, "; ".join(drifted))

    # 3b. Every theme asset the runtime reads must have a committed source, and
    # the installed copy must be that source. Recording the hashes in the
    # manifest proves nothing on its own; this is the check that makes the
    # record load-bearing. A manifest with no theme section is NOT TESTED, which
    # --strict treats as a failure rather than folding into PASS.
    themes = (frontend.get("themes") or {})
    asset_rows = {k: v for k, v in themes.items() if isinstance(v, dict) and "source_sha256" in v}
    if not asset_rows:
        report.add("theme assets versioned", NOT_TESTED, "manifest records no theme assets")
    else:
        problems = []
        for relative, recorded in sorted(asset_rows.items()):
            source = REPO / "stage" / relative
            installed = app_root / "theme" / relative
            source_hash = sha256(source)
            if source_hash is None:
                problems.append(f"{relative}: no committed source")
                continue
            if recorded.get("source_sha256") != source_hash:
                problems.append(f"{relative}: source drifted since the manifest")
                continue
            installed_hash = sha256(installed)
            if installed_hash is None:
                problems.append(f"{relative}: not deployed")
            elif installed_hash != source_hash:
                problems.append(f"{relative}: deployed copy is not the committed source")
        report.add(
            "theme assets versioned",
            FAIL if problems else PASS,
            "; ".join(problems) or f"{len(asset_rows)} asset(s) trace to stage/",
        )

    # 3c. The WebP artwork is derived, so its masters must be committed too and
    # must still be the ones the shipped files were rendered from.
    masters = themes.get("masters") if isinstance(themes.get("masters"), dict) else None
    if not masters:
        report.add("artwork masters", NOT_TESTED, "manifest records no masters")
    else:
        problems = [
            f"{name}: {'missing' if sha256(REPO / 'assets' / 'backgrounds' / name) is None else 'changed'}"
            for name, recorded in sorted(masters.items())
            if sha256(REPO / "assets" / "backgrounds" / name) != recorded
        ]
        report.add(
            "artwork masters",
            FAIL if problems else PASS,
            "; ".join(problems) or f"{len(masters)} master(s) committed",
        )

    # Bridge sidecars run outside the frozen EXE and require their own hashes.
    resources = (manifest.get("runtime") or {}).get("bridge_resources")
    expected_resources = {"bridge/leo_local_relay.py", "bridge/leo_model_selection.py",
                          "bridge/leo_identity.py", "bridge/leo_runtime_compat.py",
                          "bridge/leo_example_persistence.py",
                          "bridge/leo_runtime_features.py", "bridge/leo_reasoning.py", "bridge/leo_turn_binding.py", "bridge/leo_turn_binding_runtime.py", "bridge/leo_thought_runtime.py"}
    problems = []
    if not isinstance(resources, dict) or set(resources) != expected_resources:
        report.add("bridge resources", FAIL, "manifest must record every runtime sidecar")
    else:
        for relative in sorted(expected_resources):
            recorded = resources[relative]
            source_hash = sha256(REPO / relative)
            deployed_hash = sha256(app_root / relative)
            if (not isinstance(recorded, dict) or source_hash is None
                    or source_hash != deployed_hash
                    or recorded.get("source_sha256") != source_hash
                    or recorded.get("deployed_sha256") != deployed_hash):
                problems.append(relative)
        report.add("bridge resources", FAIL if problems else PASS,
                   "; ".join(problems) or f"{len(expected_resources)} deployed sidecars match source")

    # 4. Each deployed document must be its committed source, as the manifest recorded.
    recorded_deployed = frontend.get("deployed") or {}
    problems = []
    missing = []
    for name in FRONTEND_FILES:
        installed = sha256(app_root / "theme" / name)
        if installed is None:
            missing.append(name)
        elif installed != sha256(REPO / "stage" / name) or recorded_deployed.get(f"theme/{name}") != installed:
            problems.append(name)
    retired = [name for name in RETIRED_THEME_PATHS if (app_root / "theme" / name).exists()]
    if missing:
        report.add("deployed frontend", NOT_TESTED, "missing " + ", ".join(missing))
    elif problems or retired:
        report.add("deployed frontend", FAIL, "; ".join(
            [f"{name} is not the committed source" for name in problems] +
            [f"retired {name} is still installed" for name in retired]))
    else:
        report.add("deployed frontend", PASS, f"{len(FRONTEND_FILES)} document(s) match source")

    # 5. The deployed executable.
    exe = app_root / "LeoAIStudio.exe"
    actual = sha256(exe)
    if actual is None:
        report.add("deployed exe", NOT_TESTED, f"missing {exe}")
    elif manifest.get("deployed_exe_sha256") == actual:
        report.add("deployed exe", PASS, actual[:12])
    else:
        report.add("deployed exe", FAIL, "manifest does not match the deployed exe")

    # 6. Skill hashes recorded vs canonical on disk.
    recorded_skills = manifest.get("skills")
    if not isinstance(recorded_skills, dict):
        report.add("skill hashes", NOT_TESTED, "manifest records no skills")
    else:
        problems = []
        for name, files in recorded_skills.items():
            skill_dir = REPO / "skills" / name
            for filename, digest in (files or {}).items():
                if sha256(skill_dir / filename) != digest:
                    problems.append(f"{name}/{filename}")
        report.add("skill hashes", FAIL if problems else PASS, ", ".join(problems))

    # 7-8. Deployed and daemon skill copies, delegated to the tool that owns it.
    code, out = run(
        [sys.executable, str(REPO / "tools" / "sync_skills.py"), "--check", "--require-wsl",
         "--app-root", str(app_root.resolve())],
        cwd=REPO,
    )
    tail = out.splitlines()[-1] if out else ""
    if code == 0:
        report.add("skills deployed+daemon", PASS, tail)
    elif "NOT TESTED" in out:
        report.add("skills deployed+daemon", NOT_TESTED, tail)
    else:
        report.add("skills deployed+daemon", FAIL, tail)

    # 9. Upstream must sit on the pinned revision.
    upstream = app_root / "upstream" / "OpenAI4S"
    code, actual_rev = run(["git", "rev-parse", "HEAD"], cwd=upstream)
    if code != 0:
        report.add("upstream revision", NOT_TESTED, f"cannot read {upstream}")
    elif not PIN_PATH.is_file():
        report.add("upstream revision", NOT_TESTED, f"no pin file at {PIN_PATH}")
    else:
        pin = json.loads(PIN_PATH.read_text(encoding="utf-8"))
        expected = pin.get("revision")
        if expected == actual_rev:
            report.add("upstream revision", PASS, actual_rev[:12])
        else:
            report.add(
                "upstream revision", FAIL,
                f"pinned {str(expected)[:12]} != checked out {actual_rev[:12]}",
            )
        code, dirty = run(["git", "status", "--porcelain"], cwd=upstream)
        if code != 0:
            report.add("upstream clean", NOT_TESTED, "git unavailable")
        elif dirty:
            report.add("upstream clean", FAIL,
                       f"{len(dirty.splitlines())} modified file(s) -- upstream must stay pullable")
        else:
            report.add("upstream clean", PASS)

    # A 2.1 software release includes offline dependencies and the scientific
    # runtime. Readiness does not certify any experiment or scientific claim.
    from science_environment import verify_runtime, verify_wheelhouse
    for label, check in (("science wheelhouse", verify_wheelhouse),
                         ("science runtime", lambda: verify_runtime(app_root))):
        try:
            problems = check()
            report.add(label, FAIL if problems else PASS, "; ".join(problems))
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
            report.add(label, FAIL, f"{type(exc).__name__}: {exc}")
    code, out = run([sys.executable, str(REPO / "tools/build_wheelhouse.py"), "verify"], cwd=REPO)
    report.add("build wheelhouse", PASS if code == 0 else FAIL,
               "locked wheels verified" if code == 0 else out)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=pathlib.Path,
                        default=REPO / "manifests" / "build-current.json")
    parser.add_argument("--app-root", type=pathlib.Path, default=DEFAULT_APP_ROOT)
    parser.add_argument("--strict", action="store_true",
                        help="release mode: NOT TESTED is a failure")
    args = parser.parse_args()

    if not args.manifest.is_file():
        print(f"[FAIL] no manifest at {args.manifest}")
        return 1
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))

    print(f"[verify] {args.manifest}")
    report = verify(manifest, args.app_root, args.strict)
    report.render()
    counts = report.counts()
    print(f"\n  {counts[PASS]} PASS   {counts[FAIL]} FAIL   {counts[NOT_TESTED]} NOT TESTED")

    if counts[FAIL]:
        print("[FAIL] the manifest does not describe what is deployed")
        return 1
    if counts[NOT_TESTED]:
        if args.strict:
            print("[FAIL] --strict: a check could not be performed, so this is not a release")
            return 1
        print("[PARTIAL] no mismatches, but some checks could not be performed")
        return 0
    print("[OK] the manifest describes exactly what is deployed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
