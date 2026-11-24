"""Block D — whether a real Lean toolchain is here, and what the skill says about it.

``tests/skills/test_lean_math_discovery.py`` has eight tests, and every one of
them builds a fake toolchain in a temporary directory. Not one has ever seen Lean
evaluate anything. That gap is exactly what D1-D6 are for.

This runs the shipped ``lean_toolchain_status()`` against whatever is really on
this machine, and -- when the toolchain is genuinely READY -- goes one step
further and asks Lean to check a trivial theorem. That last step is the only part
of block D that can be discharged without a person, and only on a machine that
has Lean.

D6 is informed by a filesystem inventory taken before any version/status probe
and again afterwards. Unchanged paths, sizes and mtimes are a scoped observation,
not proof that no network download occurred in every possible environment.

    python tools/manual_acceptance/verify_lean_real_toolchain.py --save
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    FAIL,
    PASS,
    REPO,
    UNDETERMINED,
    Report,
    emit,
    parser,
    run,
)

COVERS = ["D1", "D2", "D3", "D4", "D5", "D6"]

TRIVIAL_THEOREM = "theorem leo_acceptance_probe (n : Nat) : n + 0 = n := by simp\n"


class _CollectorHost:
    """The minimum host surface the lean-math kernel touches.

    Deliberately not a stub that pretends to succeed: file reads and writes go to
    the real filesystem, because the point of this tool is to observe the real
    machine. Anything the kernel asks for that is not implemented raises, which
    is preferable to a fake answer.
    """

    def __init__(self):
        self.written: list[str] = []

    def read_file(self, path):
        return {"content": pathlib.Path(path).read_text(encoding="utf-8")}

    def write_file(self, path, content):
        target = pathlib.Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self.written.append(str(target))
        return {"path": str(target), "bytes": len(content)}

    def list_dir(self, path):
        directory = pathlib.Path(path)
        if not directory.is_dir():
            return {"entries": []}
        return {"entries": [{"name": p.name} for p in sorted(directory.iterdir())]}


def _load_kernel(host):
    path = REPO / "skills" / "lean-math" / "kernel.py"
    sys.modules["host"] = host
    spec = importlib.util.spec_from_file_location("leo_lean_math_kernel_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    args = parser(__doc__.splitlines()[0]).parse_args()
    report = Report("verify_lean_real_toolchain", "D", COVERS)
    toolchain_before = _toolchain_snapshot()

    overrides = {
        name: os.environ.get(name)
        for name in ("LEO_LEAN_TOOLCHAIN", "LEO_LEAN_PROJECT", "LEO_MATHLIB_DIR")
    }
    report.check(
        "override variables",
        PASS,
        "the three D5 overrides as currently set",
        **{k: v for k, v in overrides.items()},
    )

    for binary in ("lean", "lake", "elan"):
        found = run([binary, "--version"])
        report.check(
            f"{binary} on PATH",
            PASS if found["returncode"] == 0 else UNDETERMINED,
            found["stdout"].strip().splitlines()[0] if found["returncode"] == 0
            else f"{binary} is not runnable here",
            returncode=found["returncode"],
            stdout=found["stdout"].strip()[:400],
        )

    host = _CollectorHost()
    try:
        kernel = _load_kernel(host)
    except Exception as error:
        report.check("lean-math kernel loads", FAIL,
                     f"the shipped kernel could not be imported: {error}")
        return emit(report, args)

    try:
        status = kernel.lean_toolchain_status()
    except Exception as error:
        report.check("lean_toolchain_status()", FAIL,
                     f"raised instead of reporting a state: {error!r}")
        return emit(report, args)
    finally:
        sys.modules.pop("host", None)

    state = status.get("state")
    report.check(
        "lean_toolchain_status()",
        PASS,
        f"reported {state!r}",
        status=status,
    )

    expected = {
        "NOT_INSTALLED": "D1",
        "PROJECT_NOT_READY": "D2",
        "VERSION_MISMATCH": "D3",
        "READY": "D4",
    }
    matched = expected.get(state)
    if matched:
        report.check(
            f"this machine is the {matched} scenario",
            PASS,
            f"state {state!r} is the one {matched} describes; the remaining question "
            "is whether the accompanying guidance is actionable, which a person reads",
            checklist_item=matched,
        )

    if state == "READY":
        _really_evaluate(report, kernel, host)
    else:
        report.check(
            "real Lean evaluation", UNDETERMINED,
            f"state is {state!r}, so there is nothing to evaluate. D4 stays untested "
            "until this runs on a machine with a working toolchain",
        )

    _check_no_autoinstall(report, status, toolchain_before)

    for item in COVERS:
        if item == matched:
            report.suggestion(
                item, PASS,
                f"observed directly: lean_toolchain_status() returned {state!r} on a "
                "machine in this state. A person should still confirm the message text "
                "is actionable",
            )
        else:
            report.suggestion(
                item, UNDETERMINED,
                f"needs a machine in that state; this one reports {state!r}",
            )

    report.note(
        "The eight unit tests in tests/skills/test_lean_math_discovery.py use fake "
        "toolchains in temporary directories. None of them evaluates Lean. That is the "
        "gap block D exists to close, and only a machine with Lean can close it."
    )
    return emit(report, args)


def _really_evaluate(report: Report, kernel, host) -> None:
    """Ask Lean to check a trivial theorem. This is the D4 evidence."""
    sys.modules["host"] = host
    try:
        result = kernel.lean_check(TRIVIAL_THEOREM)
    except Exception as error:
        report.check("real Lean evaluation", FAIL,
                     f"lean_check raised on a trivial theorem: {error!r}",
                     source=TRIVIAL_THEOREM)
        return
    finally:
        sys.modules.pop("host", None)

    ok = bool(result) and not result.get("errors")
    report.check(
        "real Lean evaluation",
        PASS if ok else FAIL,
        "Lean accepted `n + 0 = n` by simp -- the toolchain genuinely evaluates"
        if ok else "Lean did not accept a trivial theorem; the toolchain reports READY "
                   "but does not work",
        source=TRIVIAL_THEOREM,
        result=result,
    )


def _toolchain_snapshot() -> dict:
    """Read-only metadata inventory; does not execute toolchain commands."""
    roots = {pathlib.Path.home() / ".elan"}
    if os.environ.get("LEO_LEAN_TOOLCHAIN"):
        roots.add(pathlib.Path(os.environ["LEO_LEAN_TOOLCHAIN"]))
    inventory = {}
    for root in sorted(roots, key=str):
        files = {}
        errors = []
        try:
            exists = root.exists()
            if exists and root.is_dir():
                for directory, names, filenames in os.walk(root, followlinks=False):
                    # Never traverse junctions/symlinks into unrelated directories.
                    names[:] = [name for name in names if not pathlib.Path(directory, name).is_symlink()
                                and not getattr(pathlib.Path(directory, name), "is_junction", lambda: False)()]
                    for name in filenames:
                        path = pathlib.Path(directory, name)
                        if path.is_symlink():
                            continue
                        stat = path.stat()
                        files[path.relative_to(root).as_posix()] = {"bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}
        except OSError as error:
            exists = None
            errors.append(type(error).__name__)
        inventory[str(root)] = {"exists": exists, "files": files, "errors": errors}
    return inventory


def _check_no_autoinstall(report: Report, status: dict, before: dict) -> None:
    """Compare the real pre-probe snapshot, preserving unavailable evidence."""
    after = _toolchain_snapshot()
    complete = not any(item["errors"] for inventory in (before, after) for item in inventory.values())
    unchanged = before == after
    report.check(
        "toolchain filesystem inventory before/after probing",
        (PASS if unchanged else FAIL) if complete else UNDETERMINED,
        "recorded toolchain paths, sizes and modification times are unchanged"
        if complete and unchanged else "toolchain inventory changed or could not be fully read",
        before=before, after=after, status=status.get("state"),
        scope="directory metadata only; network activity and all other D1-D5 environments are not established",
    )


if __name__ == "__main__":
    raise SystemExit(main())
