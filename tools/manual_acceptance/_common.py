"""Shared plumbing for the manual acceptance collectors.

What these tools are for
------------------------
``docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md`` has 27 items that cannot be
self-certified from a development environment: a fresh Windows account, a
machine with no WebView2, a WSL user who is not the one here, a real Lean
toolchain, a live five-role run, a clean-machine build. They are all NOT TESTED.

These collectors do not change that. They gather the facts a person needs so
that running those items is a matter of reading output rather than remembering
what to look for, and they save the evidence.

The one rule
------------
**A collector never decides a checklist item.** It reports OBSERVED facts and at
most a ``suggested_verdict``, which is a suggestion to a human and nothing else.
It cannot write to the checklist, and ``tests/test_manual_acceptance.py``
asserts that none of them can. An automated PASS on an item whose whole point is
that a person must be in a different environment would be a fabricated result,
which is worse than having no tool at all.

``UNDETERMINED`` is a first-class answer here. It is what a collector must say
when it is running somewhere that cannot answer the question -- not a guess, and
never a pass by omission.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import platform
import socket
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
EVIDENCE_DIR = REPO / "docs" / "manual-acceptance-evidence"

#: The only verdicts a collector may suggest.
#:
#: There is deliberately no "PASS" that a tool can reach on its own for an item
#: the checklist marks as requiring a person. Where a check *is* fully decidable
#: here (a file exists, a command returns a version), PASS is available -- and
#: the item it answers is a sub-fact, not the checklist row.
PASS = "PASS"
FAIL = "FAIL"
UNDETERMINED = "UNDETERMINED"
NOT_APPLICABLE = "NOT APPLICABLE"
VERDICTS = (PASS, FAIL, UNDETERMINED, NOT_APPLICABLE)

#: Wording that must never appear in a collector's output for a checklist row.
#: Kept here so the test that forbids it has one place to look.
FORBIDDEN_CLAIMS = (
    "simulated pass",
    "assumed pass",
    "probably passes",
    "should pass",
)


class Report:
    """An ordered set of observations plus the checklist rows they inform."""

    def __init__(self, tool: str, block: str, covers: list[str]):
        self.tool = tool
        self.block = block
        self.covers = covers
        self.checks: list[dict] = []
        self.notes: list[str] = []

    def check(self, name: str, verdict: str, detail: str, **evidence) -> dict:
        assert verdict in VERDICTS, f"{verdict!r} is not a permitted verdict"
        entry = {"check": name, "verdict": verdict, "detail": detail, "evidence": evidence}
        self.checks.append(entry)
        return entry

    def note(self, text: str) -> None:
        self.notes.append(text)

    def suggestion(self, item: str, verdict: str, why: str) -> dict:
        """A suggestion about one checklist row. Never a decision about it."""
        assert verdict in VERDICTS, f"{verdict!r} is not a permitted verdict"
        entry = {
            "checklist_item": item,
            "suggested_verdict": verdict,
            "why": why,
            "authority": (
                "suggestion only; the checklist row stays NOT TESTED until a person "
                "runs the item in the required environment and records what they saw"
            ),
        }
        self.checks.append(entry)
        return entry

    def as_dict(self) -> dict:
        return {
            "tool": self.tool,
            "block": self.block,
            "covers": self.covers,
            "collected_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "environment": environment(),
            "checks": self.checks,
            "notes": self.notes,
            "authority": (
                "This file is collected evidence. It does not change any status in "
                "CHANGELOG.md#archive-p0-manual-acceptance-checklist (archived P0_MANUAL_ACCEPTANCE_CHECKLIST). Only a person who ran the item "
                "may do that, and they should attach this file as the record."
            ),
        }

    def failures(self) -> list[dict]:
        return [c for c in self.checks if c.get("verdict") == FAIL]

    def undetermined(self) -> list[dict]:
        return [c for c in self.checks if c.get("verdict") == UNDETERMINED]


def environment() -> dict:
    """Facts about where this ran, because a result without them is not evidence."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "user": _current_user(),
        "cwd": str(pathlib.Path.cwd()),
        "repo": str(REPO),
        "repo_commit": _git_head(),
    }


def _current_user() -> str:
    import getpass

    try:
        return getpass.getuser()
    except Exception:
        return "<unknown>"


def _git_head() -> str | None:
    done = run(["git", "rev-parse", "HEAD"], cwd=REPO)
    return done["stdout"].strip() or None if done["returncode"] == 0 else None


def decode(raw: bytes) -> str:
    """Decode console output without assuming the machine's code page.

    ``text=True`` decodes with the locale encoding, which on a Chinese-locale
    Windows machine is GBK -- and ``wsl.exe`` writes UTF-16LE. That combination
    raises inside subprocess's reader threads and loses the output entirely,
    which is how a collector ends up reporting nothing and looking like a pass.
    Decoding here, in order, and falling back to a replacing decode means output
    is always recorded even when it is not perfectly decodable.
    """
    if not raw:
        return ""
    if b"\x00" in raw[:64]:
        for encoding in ("utf-16-le", "utf-16"):
            try:
                return raw.decode(encoding).lstrip("﻿")
            except (UnicodeDecodeError, ValueError):
                continue
    import locale

    candidates = ["utf-8", locale.getpreferredencoding(False)]
    if os.name == "nt":
        # Windows console tools (whoami, reg) emit the OEM/ANSI code page, which
        # on this machine is GBK. Without these, their output decodes to
        # replacement characters and the evidence records mojibake.
        candidates += ["mbcs", "gbk"]
    for encoding in candidates:
        if not encoding:
            continue
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


def write(text: str = "") -> None:
    """Print without depending on the console code page.

    ``print`` encodes with the console encoding, so a single character outside
    GBK raised UnicodeEncodeError and took the whole collector down -- turning a
    successful collection into a traceback and, through run_all, into an
    unparseable block. Evidence tooling that falls over on a character is not
    evidence tooling.
    """
    stream = getattr(sys.stdout, "buffer", None)
    if stream is None:
        print(text)
        return
    stream.write(text.encode("utf-8", errors="replace") + b"\n")
    stream.flush()


def run(command: list[str], cwd: pathlib.Path | None = None, timeout: int = 120) -> dict:
    """Run a command and record it. Never raises; a missing binary is a fact."""
    try:
        done = subprocess.run(command, cwd=cwd, capture_output=True, timeout=timeout)
        return {
            "command": command,
            "returncode": done.returncode,
            "stdout": decode(done.stdout),
            "stderr": decode(done.stderr),
        }
    except FileNotFoundError:
        return {"command": command, "returncode": None, "stdout": "",
                "stderr": "executable not found"}
    except subprocess.TimeoutExpired:
        return {"command": command, "returncode": None, "stdout": "",
                "stderr": f"timed out after {timeout}s"}
    except OSError as error:
        return {"command": command, "returncode": None, "stdout": "", "stderr": str(error)}


def parser(description: str) -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=description)
    argument_parser.add_argument("--json", action="store_true", help="machine-readable output")
    argument_parser.add_argument(
        "--save",
        nargs="?",
        const="auto",
        default=None,
        help="write the evidence to docs/manual-acceptance-evidence/, or to a named path",
    )
    return argument_parser


def emit(report: Report, args) -> int:
    """Print, optionally save, and return an exit code.

    Exit code is about the *collection*, not about the checklist: 0 when every
    check reached a determination, 1 when something failed, 2 when the
    environment could not answer. A person reads the output; nothing here writes
    a status anywhere.
    """
    payload = report.as_dict()
    if args.json:
        write(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        write(f"{report.tool}  --  checklist block {report.block} ({', '.join(report.covers)})")
        write(f"  host {payload['environment']['hostname']}  user {payload['environment']['user']}")
        write(f"  {payload['environment']['platform']}")
        write()
        for entry in report.checks:
            if "check" in entry:
                write(f"  [{entry['verdict']:^13}] {entry['check']}")
                write(f"                  {entry['detail']}")
            else:
                write(f"  -> {entry['checklist_item']}: suggested {entry['suggested_verdict']}")
                write(f"                  {entry['why']}")
        if report.notes:
            write()
            for note in report.notes:
                write(f"  note: {note}")
        write()
        write("  These are observations. They do not change any row in")
        write("  docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md -- only a person who ran the item can.")

    if args.save:
        destination = (
            EVIDENCE_DIR / f"{report.tool}.json" if args.save == "auto"
            else pathlib.Path(args.save)
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"\n  evidence saved: {destination}", file=sys.stderr)

    if report.failures():
        return 1
    if report.undetermined():
        return 2
    return 0
