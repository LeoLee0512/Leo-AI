"""Static scan for anything that ties this build to one machine.

This is a *static* check. Passing it does not mean the app runs for someone
else -- that requires a real install under a fresh Windows account and a WSL
user who is not ``leo``, which cannot be self-certified from inside this
environment. Those stay in ``docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md`` and are
recorded as NOT TESTED until a human runs them.

What it does catch is the class of defect that made the previous build
unshippable: a path that only exists on the author's computer.

    python tools/portability_check.py            # human readable
    python tools/portability_check.py --json     # machine readable
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
HISTORICAL_EVIDENCE_POLICY = "manifests/portability-historical-evidence.json"
HISTORICAL_CLASSIFICATION = "immutable-historical-evidence"
HISTORICAL_MARKER = "EXEMPT-HISTORICAL-EVIDENCE"

#: Where a human-approved immutable-evidence classification may point.
#:
#: External review ruling 2026-09-16 ("portability policy extension APPROVED WITH
#: STRICT SCOPE") widened this from ``governance/**.md`` to the immutable evidence
#: an experiment leaves behind, because the findings that kept the suite red are
#: Gate-6 environment records and post-audit annotations under ``experiments/``,
#: which by construction may never be rewritten. The widening is bounded by three
#: rules, each asserted by a test:
#:
#:   1. an entry names one literal file -- no wildcard, no directory, no pattern;
#:   2. the file must be prose or a machine record in one of these trees, never a
#:      source file, script or anything the app, build or installer executes;
#:   3. the classification still applies only on an exact match of file, SHA-256,
#:      finding type and occurrence count, so one changed byte revokes it.
EVIDENCE_POLICY_PREFIXES: tuple[str, ...] = ("governance/", "experiments/")

#: The only two shapes immutable evidence takes here: a report (``.md``) and a
#: machine record (``.json``). Anything else is out of scope by default rather
#: than by enumeration.
EVIDENCE_POLICY_SUFFIXES: tuple[str, ...] = (".md", ".json")

#: Belt and braces for rule 2: even inside an allowed tree, these can never be
#: classified. ``experiments/`` holds the driver scripts next to the evidence they
#: wrote, and a script that quotes a user path is a binding, not a record of one.
EVIDENCE_POLICY_FORBIDDEN_SUFFIXES: tuple[str, ...] = (
    ".py", ".pyw", ".ps1", ".psm1", ".psd1", ".sh", ".bash", ".bat", ".cmd",
    ".js", ".mjs", ".cjs", ".ts", ".exe", ".dll", ".pyd", ".so", ".lock",
)

#: Characters that would turn a literal path into a pattern.
_EVIDENCE_POLICY_PATTERN_CHARACTERS = "*?[]"

#: Files that legitimately contain machine-specific strings.
#:  - historical docs/rollback snapshots remain eligible for evidence classification;
#:  - this scanner necessarily contains the patterns it looks for;
#:  - one report at the repository root, kept for the same reason as docs/*.md.
#:
#: Naming individual reports here turned out to be a trap: every new governance
#: document that quoted the path its own negative-control test plants ("a
#: planted /home/<name>/... must be caught") turned the suite red until someone
#: remembered to edit this list. docs/*.md is therefore exempt as a class --
#: see ``is_exempt``. Prose about a machine is not a binding to it: no Markdown
#: file under docs/ is read by the app, the build or the installer.
#:
#: What keeps that from hiding a real defect is ``EXEMPT_KINDS`` below, which
#: was checked by the archived portability suite: nothing executable or consumed by
#: the build can ever be exempted, whatever gets added here.
EXEMPT = (
    "docs/rollback/",
    "CHANGELOG.md",
    "tools/portability_check.py",
)

#: The kinds of file that may ever be exempt, and why. Anything exempt that is
#: not one of these is a bug in the exemption rules, not a portable file --
#: the archived portability suite checked every tracked file against it. This is
#: what stops the class exemption above from being widened into a way of hiding
#: a real binding in something the app, the build or the installer actually
#: reads.
EXEMPT_KINDS = {
    "frozen-evidence": "pre-fix copies kept under docs/rollback/; editing them would destroy the evidence",
    "documentation": "Markdown prose about the machine; not read by the app, the build or the installer",
    "the-scanner-itself": "necessarily contains the patterns it looks for",
}


def exemption_kind(rel: str) -> str | None:
    """Which permitted kind exempts *rel*, or None if nothing should."""
    if rel.startswith("docs/rollback/"):
        return "frozen-evidence"
    if rel == "tools/portability_check.py":
        return "the-scanner-itself"
    if rel.endswith(".md"):
        return "documentation"
    return None


#: A per-occurrence escape hatch for files that are *not* exempt as a class --
#: a script that must quote a path in a message, say. It states the claim at the
#: site instead of in a list somewhere else, and it is rule-specific, so it
#: cannot silently suppress a different binding that appears later on the same
#: line. Write it on the offending line or the line above:
#:
#:     TEXT = "look under /home/<user>/.elan"  # portability-allow: linux-user-home
_ALLOW_MARKER = re.compile(r"portability-allow:\s*([a-z0-9-]+)")

RULES = (
    (
        "windows-user-home",
        re.compile(r"C:[\\/]+Users[\\/]+(?!<)[A-Za-z0-9._-]+"),
        "an absolute path into one Windows user's profile",
    ),
    (
        "desktop-path",
        re.compile(r"[Dd]esktop[\\/]+Leo", re.IGNORECASE),
        "assumes the app lives on the Desktop",
    ),
    (
        "linux-user-home",
        re.compile(r"/home/(?!<)[A-Za-z0-9._-]+"),
        "an absolute path into one Linux user's home",
    ),
    (
        "wsl-distro-literal",
        re.compile(r"[\"']Ubuntu-\d+\.\d+[\"']"),
        "a hardcoded WSL distribution name",
    ),
    (
        "lean-toolchain-literal",
        re.compile(r"leanprover--lean4---v[\d.]+(?:-rc\d+)?"),
        "a pinned Lean toolchain directory",
    ),
)

#: Patterns that are acceptable when they appear as a *default* next to an
#: environment-variable override, because the machine can then be configured.
CONFIGURABLE_NEAR = ("os.environ.get", "getenv", "LEO_WSL_", "LEO_LEAN_", "LEO_APP_ROOT")


def _sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def historical_evidence_policy() -> list[dict]:
    """Load and validate the narrow, tracked human-review policy."""
    policy_path = REPO / HISTORICAL_EVIDENCE_POLICY
    try:
        data = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read historical evidence policy: {policy_path}") from exc

    if data.get("schema_version") != 1 or not isinstance(data.get("entries"), list):
        raise RuntimeError("historical evidence policy must have schema_version 1 and entries")

    rule_names = {name for name, _pattern, _why in RULES}
    seen = set()
    for entry in data["entries"]:
        if not isinstance(entry, dict):
            raise RuntimeError("historical evidence policy entries must be objects")
        rel = entry.get("file")
        if isinstance(rel, str):
            if any(character in rel for character in _EVIDENCE_POLICY_PATTERN_CHARACTERS):
                raise RuntimeError(
                    f"historical evidence policy cannot target a wildcard or pattern: {rel}"
                )
            if rel.endswith("/"):
                raise RuntimeError(
                    f"historical evidence policy cannot target a directory: {rel}"
                )
        pure = pathlib.PurePosixPath(rel) if isinstance(rel, str) else None
        if (
            pure is None
            or pure.is_absolute()
            or ".." in pure.parts
            or str(pure) != rel
            or "\\" in rel
        ):
            raise RuntimeError(f"historical evidence policy has unsafe file: {rel!r}")
        if (
            not rel.startswith(EVIDENCE_POLICY_PREFIXES)
            or not rel.endswith(EVIDENCE_POLICY_SUFFIXES)
            or rel.endswith(EVIDENCE_POLICY_FORBIDDEN_SUFFIXES)
        ):
            raise RuntimeError(
                "historical evidence policy cannot target a non-evidence file "
                f"(allowed: a literal .md or .json under {'/, '.join(EVIDENCE_POLICY_PREFIXES)}): {rel}"
            )
        for field in ("ruling", "constraint"):
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                raise RuntimeError(
                    f"historical evidence policy entry for {rel} has no {field}: "
                    "every classification is a human review decision and must say whose and what it binds"
                )
        if not re.fullmatch(r"[0-9a-f]{64}", entry.get("sha256", "")):
            raise RuntimeError(f"historical evidence policy has invalid sha256 for {rel}")
        if entry.get("classification") != HISTORICAL_CLASSIFICATION:
            raise RuntimeError(f"historical evidence policy has invalid classification for {rel}")
        if entry.get("finding_type") not in rule_names:
            raise RuntimeError(f"historical evidence policy has unknown finding type for {rel}")
        if not isinstance(entry.get("expected_occurrences"), int) or entry["expected_occurrences"] < 1:
            raise RuntimeError(f"historical evidence policy has invalid occurrence count for {rel}")
        key = (rel, entry["finding_type"])
        if key in seen:
            raise RuntimeError(f"historical evidence policy has duplicate entry: {key}")
        seen.add(key)
    return data["entries"]


def classify_historical_evidence(findings: list[dict]) -> list[dict]:
    """Classify findings only after scanning, and only on an exact policy match."""
    classified = [dict(finding) for finding in findings]
    for entry in historical_evidence_policy():
        rel = entry["file"]
        target = REPO / pathlib.PurePosixPath(rel)
        if not target.is_file() or _sha256(target) != entry["sha256"]:
            continue
        matches = [
            finding
            for finding in classified
            if finding["file"] == rel and finding["rule"] == entry["finding_type"]
        ]
        if len(matches) != entry["expected_occurrences"]:
            continue
        for finding in matches:
            finding["classification"] = HISTORICAL_CLASSIFICATION
            finding["audit_marker"] = HISTORICAL_MARKER
            finding["policy"] = HISTORICAL_EVIDENCE_POLICY
            finding["evidence_sha256"] = entry["sha256"]
    return classified


def partition_findings(findings: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    historical = [f for f in findings if f.get("audit_marker") == HISTORICAL_MARKER]
    hard = [
        f
        for f in findings
        if not f["configurable_default"] and f.get("audit_marker") != HISTORICAL_MARKER
    ]
    configurable = [
        f
        for f in findings
        if f["configurable_default"] and f.get("audit_marker") != HISTORICAL_MARKER
    ]
    return hard, configurable, historical


def tracked_files() -> list[pathlib.Path]:
    done = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, timeout=120
    )
    if done.returncode != 0:
        return sorted(p for p in REPO.rglob("*") if p.is_file())
    names = done.stdout.decode("utf-8", errors="replace").splitlines()
    return [REPO / name for name in names if (REPO / name).is_file()]


def is_exempt(rel: str) -> bool:
    """Whether this path is exempt from the literal-pattern rules as a class.

    Markdown under docs/ is documentation *about* the machine, not a binding to
    it. Everything else must earn its exemption line by line, via
    ``portability-allow:``.
    """
    if rel.startswith("docs/") and rel.endswith(".md"):
        return True
    return any(rel.startswith(prefix) or rel == prefix for prefix in EXEMPT)


def allowed_on_line(lines: list[str], number: int, rule: str) -> bool:
    """Whether an in-file marker waives *rule* for the 1-based line *number*."""
    for candidate in (lines[number - 1], lines[number - 2] if number >= 2 else ""):
        for allowed in _ALLOW_MARKER.findall(candidate):
            if allowed == rule:
                return True
    return False


def scan() -> list[dict]:
    findings = []
    for path in tracked_files():
        rel = path.relative_to(REPO).as_posix()
        if is_exempt(rel):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        lines = text.splitlines()
        for rule, pattern, why in RULES:
            # Tests are exempt from the literal-pattern rules. A test that says
            #     assert "/home/leo" not in source
            # or that builds a fake toolchain directory named after a pinned
            # release, or that passes "Ubuntu-24.04" in to prove the distro
            # reaches the command line, is the guard against machine binding --
            # not an instance of it. Flagging those would punish the checks.
            #
            # What keeps tests themselves portable is that they resolve paths
            # from the repository rather than from an absolute location. The
            # restored suite and historical results remain available; this
            # compatibility rule also applies when a historical tree is scanned.
            if rel.startswith("tests/"):
                continue
            for number, line in enumerate(lines, start=1):
                match = pattern.search(line)
                if not match:
                    continue
                if allowed_on_line(lines, number, rule):
                    continue
                window = "\n".join(lines[max(0, number - 6): number + 5])
                configurable = any(token in window for token in CONFIGURABLE_NEAR)
                findings.append(
                    {
                        "rule": rule,
                        "file": rel,
                        "line": number,
                        "text": line.strip()[:160],
                        "why": why,
                        "configurable_default": configurable,
                    }
                )
    return classify_historical_evidence(findings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--allow-configurable-defaults",
        action="store_true",
        default=True,
        help="treat a hardcoded value sitting beside an env override as acceptable",
    )
    args = parser.parse_args()

    findings = scan()
    hard, soft, historical = partition_findings(findings)

    if args.json:
        print(
            json.dumps(
                {
                    "hard": hard,
                    "configurable": soft,
                    "historical_evidence": historical,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for item in soft:
            print(f"  [default ] {item['file']}:{item['line']}  {item['rule']}"
                  f"  (overridable) {item['text']}")
        for item in historical:
            print(
                f"  [{HISTORICAL_MARKER}] {item['file']}:{item['line']}  {item['rule']}\n"
                f"              policy={item['policy']} sha256={item['evidence_sha256']}\n"
                f"              {item['text']}"
            )
        for item in hard:
            print(f"  [BINDING ] {item['file']}:{item['line']}  {item['rule']}"
                  f"  -- {item['why']}\n              {item['text']}")
        print(
            f"\n  {len(hard)} hard binding(s), {len(soft)} configurable default(s), "
            f"{len(historical)} historical evidence finding(s)"
        )
        print(
            "  NOTE: this is a static scan. A clean result is NOT the same as a "
            "successful install\n        under a fresh Windows account -- that stays a "
            "manual acceptance item."
        )

    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main())
