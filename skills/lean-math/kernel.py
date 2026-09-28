"""
Lean-math helpers. Auto-loaded into the python kernel by the host when the
skill loads:

  lean_check, lean_check_type, lean_print, lean_find, lean_exact, lean_goal,
  lean_loogle, lean_run, lean_path, lean_env, lean_toolchain_status

Module top level is definition-only (functions, imports, literal constants) so
the sidecar structure gate accepts it; every subprocess call and every network
call happens inside a function body.

Three facts about this toolchain drive the whole design, and all three were
measured rather than assumed:

1. ``lake env lean`` writes its diagnostics to **stderr** and exits **0** even
   when the file has errors. Calling ``lean`` directly with a prepared
   ``LEAN_PATH`` writes JSON diagnostics to **stdout** and exits **1**. This
   file uses the direct route, and still decides pass/fail from the parsed
   diagnostics rather than from the exit code.
2. ``lean --json`` emits one JSON object per diagnostic with exact
   ``pos``/``endPos`` (line, column) — so there is no regex parsing of Lean's
   prose here, and the reported line/column is Lean's own.
3. ``import Mathlib`` costs about 30 s per check on this machine. ``LEAN_PATH``
   is computed once and cached; narrowing the import is the only real speedup
   and :func:`lean_check` takes ``imports`` for exactly that.

The toolchain was installed by unpacking a release tarball, so ``elan default``
is not configured and would try to reach the network. Everything here uses the
absolute toolchain paths instead and never invokes ``elan``.
"""

import glob
import json
import os
import shutil
import subprocess
import time
import urllib.parse

#: Explicit configuration, checked before any discovery. A machine with an
#: unusual layout says where things are instead of hoping the search finds them.
LEAN_ENV_TOOLCHAIN = "LEO_LEAN_TOOLCHAIN"
LEAN_ENV_PROJECT = "LEO_LEAN_PROJECT"
LEAN_ENV_MATHLIB = "LEO_MATHLIB_DIR"

#: Where elan keeps toolchains, relative to the user's home directory.
LEAN_ELAN_TOOLCHAINS = ".elan/toolchains"

#: Directory names searched under the home directory for a built Lake project
#: when none is configured. A project qualifies only if it has a lakefile and a
#: resolved manifest -- an empty directory with the right name is not a project.
LEAN_PROJECT_CANDIDATES = ("lean_test", "lean-test", "mathlib4", "leanproject")

#: Health states. Reported verbatim so a caller can branch on them, and so the
#: difference between "not installed" and "installed but unusable" survives.
LEAN_READY = "READY"
LEAN_NOT_INSTALLED = "NOT_INSTALLED"
LEAN_PROJECT_NOT_READY = "PROJECT_NOT_READY"
LEAN_VERSION_MISMATCH = "VERSION_MISMATCH"

#: Probe files are written here, relative to the session workspace — the only
#: writable place a kernel cell has. The Lean project itself is never written.
LEAN_PROBE_DIR = "lean-probes"

LEAN_DEFAULT_IMPORT = "import Mathlib"
#: A full `import Mathlib` elaboration is ~30 s cold; leave generous headroom.
LEAN_DEFAULT_TIMEOUT = 300
LEAN_PATH_TIMEOUT = 120
#: `#find` builds a discrimination tree over the whole of Mathlib on first
#: use. Measured on this machine: 374 s for `_ + 0 = _`, peaking near 8 GB RSS,
#: so it gets its own ceiling and its own warning in the docs. Prefer
#: `lean_exact` (~13 s) or `lean_loogle` when either can answer the question.
LEAN_FIND_TIMEOUT = 900

#: Lean's own kind for "the tactic block ended with goals left over". Its
#: message body carries the goal state, which is the most useful thing Lean
#: hands back and the reason `goal` is a separate field on every diagnostic.
LEAN_UNSOLVED_KIND = "Tactic.unsolvedGoals"

LEAN_LOOGLE_ENDPOINT = "https://loogle.lean-lang.org/json"

#: Process-lifetime cache: LEAN_PATH, and how it was obtained.
LEAN_STATE = {}


def lean_sdk():
    """Rebind-proof SDK handle — see pdf-explore/kernel.py:pdf_sdk."""
    import host

    return host


# --------------------------------------------------------------- discovery


def lean_home():
    """The user's home directory, however this machine spells it."""
    return os.path.expanduser("~")


def lean_env_path(name):
    """A configured path, or None. Blank and missing are the same answer."""
    value = (os.environ.get(name) or "").strip()
    return value or None


def lean_discover_toolchain():
    """Locate a Lean toolchain: configured, then elan, then PATH.

    Returns ``(toolchain_dir_or_None, lean_bin_or_None, lake_bin_or_None)``.
    A toolchain found on PATH has no directory, which is fine -- only LEAN_PATH
    assembly wants one, and it falls back to globbing the project.
    """
    configured = lean_env_path(LEAN_ENV_TOOLCHAIN)
    if configured:
        lean = os.path.join(configured, "bin", "lean")
        lake = os.path.join(configured, "bin", "lake")
        return configured, (lean if os.path.isfile(lean) else None), (
            lake if os.path.isfile(lake) else None
        )

    root = os.path.join(lean_home(), LEAN_ELAN_TOOLCHAINS)
    if os.path.isdir(root):
        # Newest first, so a machine with several toolchains gets a stable and
        # defensible choice rather than whatever the filesystem returns first.
        for name in sorted(os.listdir(root), reverse=True):
            candidate = os.path.join(root, name)
            lean = os.path.join(candidate, "bin", "lean")
            lake = os.path.join(candidate, "bin", "lake")
            if os.path.isfile(lean) and os.path.isfile(lake):
                return candidate, lean, lake

    lean = shutil.which("lean")
    lake = shutil.which("lake")
    if lean and lake:
        return None, lean, lake
    return None, None, None


def lean_project_ready(path):
    """Whether *path* looks like a Lake project with resolved dependencies."""
    if not path or not os.path.isdir(path):
        return False
    has_lakefile = any(
        os.path.isfile(os.path.join(path, name))
        for name in ("lakefile.lean", "lakefile.toml")
    )
    return has_lakefile and os.path.isfile(os.path.join(path, "lake-manifest.json"))


def lean_discover_project():
    """Locate a built Lake project: configured, then known names under home."""
    configured = lean_env_path(LEAN_ENV_PROJECT)
    if configured:
        return configured
    home = lean_home()
    for name in LEAN_PROJECT_CANDIDATES:
        candidate = os.path.join(home, name)
        if lean_project_ready(candidate):
            return candidate
    return None


def lean_discover_mathlib(project):
    """Locate Mathlib: configured, then inside the project, then under home."""
    configured = lean_env_path(LEAN_ENV_MATHLIB)
    if configured:
        return configured
    if project:
        packaged = os.path.join(project, ".lake", "packages", "mathlib")
        if os.path.isdir(packaged):
            return packaged
    candidate = os.path.join(lean_home(), "mathlib4")
    return candidate if os.path.isdir(candidate) else None


def lean_paths(refresh=False):
    """Resolve every Lean location once and cache it for the process.

    Nothing here installs anything. If Lean is absent the answer is "absent",
    reported through ``lean_toolchain_status``; a skill that silently downloaded
    a multi-gigabyte toolchain would be making a decision that is the user's.
    """
    if not refresh and LEAN_STATE.get("paths"):
        return LEAN_STATE["paths"]
    toolchain, lean, lake = lean_discover_toolchain()
    project = lean_discover_project()
    paths = {
        "toolchain": toolchain,
        "lean": lean,
        "lake": lake,
        "project": project,
        "mathlib": lean_discover_mathlib(project),
    }
    LEAN_STATE["paths"] = paths
    return paths


def lean_require_ready():
    """Return resolved paths, or raise with something the user can act on."""
    status = lean_toolchain_status()
    if status["state"] == LEAN_READY:
        return status["paths"]
    raise RuntimeError(f"{status['state']}: {status['summary']}")


def lean_path(refresh=False):
    """Resolve and cache ``LEAN_PATH`` for the pre-built Mathlib project.

    Asks Lake once (``lake env printenv LEAN_PATH``, ~0.6 s). If Lake cannot
    run — the kernel sandbox mounts the project read-only, and a future Lake
    may want to write there — the package layout is globbed directly, which
    produces the same entries without touching the project.
    """
    if not refresh and LEAN_STATE.get("lean_path"):
        return LEAN_STATE["lean_path"]
    paths = lean_paths()
    if not paths["lake"] or not paths["project"]:
        raise RuntimeError(
            "lean_path: no Lean toolchain or Lake project was found. "
            "Run lean_toolchain_status() to see what is missing, or set "
            f"{LEAN_ENV_TOOLCHAIN} / {LEAN_ENV_PROJECT}."
        )
    resolved, source = "", "none"
    try:
        probe = subprocess.run(
            [paths["lake"], "env", "printenv", "LEAN_PATH"],
            cwd=paths["project"],
            capture_output=True,
            text=True,
            timeout=LEAN_PATH_TIMEOUT,
        )
        candidate = (probe.stdout or "").strip()
        if probe.returncode == 0 and candidate:
            resolved, source = candidate, "lake"
    except (OSError, subprocess.SubprocessError):
        resolved = ""
    if not resolved:
        entries = sorted(
            glob.glob(os.path.join(paths["project"], ".lake/packages/*/.lake/build/lib/lean"))
        )
        if paths["mathlib"]:
            entries.append(os.path.join(paths["mathlib"], ".lake/build/lib/lean"))
        entries.append(os.path.join(paths["project"], ".lake/build/lib/lean"))
        if paths["toolchain"]:
            entries.append(os.path.join(paths["toolchain"], "lib/lean"))
        entries = [entry for entry in entries if os.path.isdir(entry)]
        resolved, source = os.pathsep.join(entries), "glob"
    if not resolved:
        raise RuntimeError(
            "lean_path: could not resolve LEAN_PATH. Check that "
            f"{paths['project']!r} and {paths['mathlib']!r} still hold "
            "their .lake build directories."
        )
    LEAN_STATE["lean_path"] = resolved
    LEAN_STATE["lean_path_source"] = source
    return resolved


def lean_env():
    """Process environment for a Lean run: inherited, plus ``LEAN_PATH``."""
    env = dict(os.environ)
    env["LEAN_PATH"] = lean_path()
    env.setdefault("HOME", os.path.expanduser("~"))
    return env


def lean_toolchain_status():
    """Report what is actually present, without compiling or installing anything.

    ``state`` is one of:

    ``READY``               Lean, Lake, a resolved project and built Mathlib
                            oleans are all present.
    ``NOT_INSTALLED``       No Lean toolchain was configured or discovered.
    ``PROJECT_NOT_READY``   Lean exists but there is no Lake project with a
                            resolved manifest, or Mathlib has not been built.
    ``VERSION_MISMATCH``    The project pins a toolchain that is not the one
                            found, so any elaboration would use the wrong Lean.

    The distinction matters: "not installed" is the user's decision to make,
    while "installed but unusable" is a configuration problem with a fix.
    """
    paths = lean_paths()
    status = {
        "state": LEAN_NOT_INSTALLED,
        "summary": "",
        "paths": paths,
        "lean": paths["lean"],
        "lean_exists": bool(paths["lean"]) and os.path.isfile(paths["lean"]),
        "lake_exists": bool(paths["lake"]) and os.path.isfile(paths["lake"]),
        "project": paths["project"],
        "project_exists": bool(paths["project"]) and os.path.isdir(paths["project"]),
        "project_resolved": lean_project_ready(paths["project"]),
        "mathlib": paths["mathlib"],
        "mathlib_oleans": bool(paths["mathlib"])
        and os.path.isdir(
            os.path.join(paths["mathlib"], ".lake/build/lib/lean/Mathlib")
        ),
        "version": None,
        "expected_toolchain": None,
        "lean_path_source": None,
        "lean_path_entries": 0,
        "configure_with": {
            "toolchain": LEAN_ENV_TOOLCHAIN,
            "project": LEAN_ENV_PROJECT,
            "mathlib": LEAN_ENV_MATHLIB,
        },
    }

    if status["lean_exists"]:
        try:
            probe = subprocess.run(
                [paths["lean"], "--version"], capture_output=True, text=True, timeout=60
            )
            status["version"] = (probe.stdout or probe.stderr or "").strip()
        except (OSError, subprocess.SubprocessError) as error:
            status["version"] = f"{type(error).__name__}: {error}"

    # A project states the toolchain it was built with; using a different one
    # silently produces olean mismatches rather than an honest error.
    if status["project_exists"]:
        pin = os.path.join(paths["project"], "lean-toolchain")
        if os.path.isfile(pin):
            try:
                with open(pin, encoding="utf-8") as handle:
                    status["expected_toolchain"] = handle.read().strip()
            except OSError:
                status["expected_toolchain"] = None

    if not status["lean_exists"] or not status["lake_exists"]:
        status["state"] = LEAN_NOT_INSTALLED
        status["summary"] = (
            "no Lean toolchain found. Install elan (https://github.com/leanprover/elan) "
            f"or set {LEAN_ENV_TOOLCHAIN} to a toolchain directory containing bin/lean "
            "and bin/lake. Nothing is installed automatically: a Lean + Mathlib "
            "toolchain is several gigabytes and that is your call."
        )
        return status

    if not status["project_resolved"]:
        status["state"] = LEAN_PROJECT_NOT_READY
        status["summary"] = (
            "Lean is installed but no built Lake project was found. Expected a "
            "directory with a lakefile and lake-manifest.json; searched "
            f"{list(LEAN_PROJECT_CANDIDATES)} under {lean_home()!r}. "
            f"Set {LEAN_ENV_PROJECT} to point at one."
        )
        return status

    if not status["mathlib_oleans"]:
        status["state"] = LEAN_PROJECT_NOT_READY
        status["summary"] = (
            f"project {paths['project']!r} is resolved but Mathlib oleans were not "
            f"found under {paths['mathlib']!r}. Build them with `lake exe cache get` "
            "in the project, or set " + LEAN_ENV_MATHLIB + "."
        )
        return status

    expected = status["expected_toolchain"]
    if expected and paths["toolchain"]:
        # elan flattens a toolchain name by replacing "/" with a double dash
        # and ":" with a triple dash, which is how the pinned name maps onto
        # the directory name under ~/.elan/toolchains.
        normalised = expected.replace("/", "--").replace(":", "---")
        if normalised not in os.path.basename(paths["toolchain"]):
            status["state"] = LEAN_VERSION_MISMATCH
            status["summary"] = (
                f"project pins {expected!r} but the toolchain found is "
                f"{os.path.basename(paths['toolchain'])!r}. Elaborating against a "
                f"different Lean than the oleans were built with produces confusing "
                f"errors; set {LEAN_ENV_TOOLCHAIN} to the pinned toolchain."
            )
            return status

    try:
        status["lean_path_entries"] = len(lean_path().split(os.pathsep))
        status["lean_path_source"] = LEAN_STATE.get("lean_path_source")
    except RuntimeError as error:
        status["state"] = LEAN_PROJECT_NOT_READY
        status["summary"] = str(error)
        status["lean_path_error"] = str(error)
        return status

    status["state"] = LEAN_READY
    status["summary"] = (
        f"Lean {status['version'] or 'unknown'} with Mathlib at {paths['mathlib']!r}"
    )
    return status


def lean_probe_path(filename="Probe.lean"):
    """Absolute path of a probe file inside the session workspace."""
    name = os.path.basename(str(filename) or "Probe.lean")
    if not name.endswith(".lean"):
        name += ".lean"
    return os.path.abspath(os.path.join(LEAN_PROBE_DIR, name))


def lean_parse_diagnostic(payload, source_lines):
    """Normalize one ``lean --json`` object into a flat diagnostic dict."""
    pos = payload.get("pos") or {}
    end = payload.get("endPos") or {}
    data = str(payload.get("data") or "")
    message, goal = data, None
    if payload.get("kind") == LEAN_UNSOLVED_KIND and "\n" in data:
        message, goal = data.split("\n", 1)
        goal = goal.strip("\n")
    line = pos.get("line")
    text = None
    if isinstance(line, int) and 1 <= line <= len(source_lines):
        text = source_lines[line - 1]
    return {
        "severity": payload.get("severity"),
        "kind": payload.get("kind"),
        "line": line,
        "col": pos.get("column"),
        "end_line": end.get("line"),
        "end_col": end.get("column"),
        "message": message.strip(),
        "goal": goal,
        "source": text,
    }


def lean_run(source, *, filename="Probe.lean", timeout=LEAN_DEFAULT_TIMEOUT):
    """Elaborate ``source`` with the Mathlib LEAN_PATH. Raw, unclassified.

    Returns ``{"returncode", "elapsed", "diagnostics", "path", "unparsed"}``.
    ``lean`` writes one JSON object per line to stdout; stderr is read too and
    anything unparseable is kept in ``unparsed`` rather than dropped, because a
    silently swallowed toolchain error looks exactly like a clean proof.
    """
    text = str(source)
    if not text.endswith("\n"):
        text += "\n"
    path = lean_probe_path(filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)

    started = time.monotonic()
    try:
        completed = subprocess.run(
            [LEAN_BIN, "--json", path],
            cwd=os.path.dirname(path),
            capture_output=True,
            text=True,
            env=lean_env(),
            timeout=float(timeout),
        )
    except subprocess.TimeoutExpired:
        return {
            "returncode": None,
            "elapsed": round(time.monotonic() - started, 2),
            "diagnostics": [],
            "unparsed": [
                f"lean timed out after {timeout}s. A full `import Mathlib` "
                "takes ~30 s here; raise timeout= or narrow the imports."
            ],
            "path": path,
            "timed_out": True,
        }
    elapsed = round(time.monotonic() - started, 2)
    lines = text.splitlines()
    diagnostics, unparsed = [], []
    for stream in (completed.stdout or "", completed.stderr or ""):
        for raw in stream.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except ValueError:
                unparsed.append(raw)
                continue
            if isinstance(payload, dict):
                diagnostics.append(lean_parse_diagnostic(payload, lines))
            else:
                unparsed.append(raw)
    return {
        "returncode": completed.returncode,
        "elapsed": elapsed,
        "diagnostics": diagnostics,
        "unparsed": unparsed,
        "path": path,
        "timed_out": False,
    }


def lean_source(code, imports=None):
    """Assemble the file Lean will see: imports, then the user's code.

    Code that already begins with its own ``import`` lines is used verbatim, so
    the line numbers in every diagnostic are the caller's own line numbers.
    """
    body = str(code or "")
    stripped = [line for line in body.splitlines() if line.strip()]
    has_import = bool(stripped) and stripped[0].lstrip().startswith("import ")
    if has_import:
        return body, 0
    if imports is None:
        requested = [LEAN_DEFAULT_IMPORT]
    elif isinstance(imports, str):
        requested = imports.splitlines()
    else:
        requested = list(imports)
    # Accept both spellings: a bare module name and a full import line.
    # Taking a string verbatim meant imports="Mathlib.Tactic.NormNum" emitted
    # a line with no `import` keyword, and Lean answered "unexpected
    # identifier; expected command" -- a confusing error pointing at the
    # caller's own snippet rather than at the header this function built.
    prepared = []
    for entry in requested:
        spelled = str(entry).strip()
        if not spelled:
            continue
        prepared.append(
            spelled if spelled.startswith("import ") else f"import {spelled}"
        )
    if not prepared:
        prepared = [LEAN_DEFAULT_IMPORT]
    header = "\n".join(prepared) + "\n\n"
    return header + body, len(header.splitlines())


def lean_check(
    code,
    *,
    filename="Probe.lean",
    imports=None,
    timeout=LEAN_DEFAULT_TIMEOUT,
    allow_sorry=False,
):
    """Compile a Lean snippet and report precisely what is wrong with it.

    Returns::

        {"ok": bool, "elapsed": float, "errors": [...], "warnings": [...],
         "infos": [...], "uses_sorry": bool, "header_lines": int,
         "path": str, "returncode": int|None, "unparsed": [...]}

    Each diagnostic carries ``line``, ``col``, ``end_line``, ``end_col``,
    ``message``, the offending ``source`` line, and — for an unsolved-goals
    error — the ``goal`` state Lean printed. ``header_lines`` is how many lines
    of imports were prepended, so ``line - header_lines`` maps back onto the
    caller's own snippet when it did not supply its own imports.

    ``ok`` is computed from the diagnostics, never from the exit code, and a
    proof containing ``sorry`` is **not** ok unless ``allow_sorry=True``: a
    file that compiles because a goal was admitted is not a proof, and
    reporting it as one is the failure mode this whole skill exists to prevent.
    """
    source, header_lines = lean_source(code, imports)
    raw = lean_run(source, filename=filename, timeout=timeout)
    errors, warnings, infos = [], [], []
    for item in raw["diagnostics"]:
        severity = item.get("severity")
        if severity == "error":
            errors.append(item)
        elif severity == "warning":
            warnings.append(item)
        else:
            infos.append(item)
    uses_sorry = any(
        "sorry" in str(item.get("message") or "").lower()
        for item in warnings + errors
    )
    ok = (
        not errors
        and not raw["timed_out"]
        and not raw["unparsed"]
        and (allow_sorry or not uses_sorry)
    )
    return {
        "ok": ok,
        "elapsed": raw["elapsed"],
        "errors": errors,
        "warnings": warnings,
        "infos": infos,
        "uses_sorry": uses_sorry,
        "header_lines": header_lines,
        "path": raw["path"],
        "returncode": raw["returncode"],
        "unparsed": raw["unparsed"],
        "timed_out": raw["timed_out"],
    }


def lean_command(command, *, imports=None, timeout=LEAN_DEFAULT_TIMEOUT, filename=None):
    """Run one Lean `#command` and return its ``information`` messages."""
    result = lean_check(
        str(command),
        filename=filename or "Query.lean",
        imports=imports,
        timeout=timeout,
        allow_sorry=True,
    )
    return result


def lean_check_type(name, *, imports=None, timeout=LEAN_DEFAULT_TIMEOUT):
    """Type signature of ``name`` via ``#check``, or None when it is unknown.

    A None here means Mathlib has no such declaration under that name. Report
    that; do not present a plausible-looking signature you did not get back.
    """
    identifier = str(name or "").strip()
    if not identifier:
        raise ValueError("lean_check_type: name must be a non-empty string")
    spelled = identifier if identifier.startswith("@") else "@" + identifier
    result = lean_command(f"#check {spelled}", imports=imports, timeout=timeout)
    if result["errors"]:
        return None
    for item in result["infos"]:
        if item.get("message"):
            return item["message"]
    return None


def lean_print(name, *, imports=None, timeout=LEAN_DEFAULT_TIMEOUT):
    """Full definition of ``name`` via ``#print``, or None when unknown."""
    identifier = str(name or "").strip()
    if not identifier:
        raise ValueError("lean_print: name must be a non-empty string")
    result = lean_command(f"#print {identifier}", imports=imports, timeout=timeout)
    if result["errors"]:
        return None
    for item in result["infos"]:
        if item.get("message"):
            return item["message"]
    return None


def lean_find(pattern, *, imports=None, timeout=LEAN_FIND_TIMEOUT):
    """Search Mathlib by statement shape with ``#find``. **Expensive.**

    ``lean_find("_ + 0 = _")`` returns matching declarations as
    ``[{"name", "signature"}]``. Results are capped by Lean itself; when it
    says the cap was reached, ``truncated`` is True.

    Cost, measured rather than guessed: the first ``#find`` in a process builds
    a discrimination tree over all of Mathlib: 374 s for ``_ + 0 = _`` here,
    peaking near 8 GB RSS. Reach for :func:`lean_exact` (~13 s) or
    :func:`lean_loogle` first; use this when the question is genuinely about
    statement *shape* and the wait is affordable. A timeout comes back as
    ``timed_out: True`` rather than as an exception.
    """
    query = str(pattern or "").strip()
    if not query:
        raise ValueError("lean_find: pattern must be a non-empty string")
    result = lean_command(f"#find {query}", imports=imports, timeout=timeout)
    matches, truncated = [], False
    for item in result["infos"]:
        message = str(item.get("message") or "")
        if "maximum number of search results" in message:
            truncated = True
            continue
        name, _, signature = message.partition(":")
        if signature.strip():
            matches.append({"name": name.strip(), "signature": signature.strip()})
    return {
        "matches": matches,
        "truncated": truncated,
        "timed_out": result["timed_out"],
        "errors": result["errors"],
        "elapsed": result["elapsed"],
    }


def lean_exact(statement, *, imports=None, timeout=LEAN_DEFAULT_TIMEOUT):
    """Ask ``exact?`` for a term that closes ``statement``.

    ``statement`` is the part of an ``example`` after ``example`` and before
    ``:=``, e.g. ``"(a b : Nat) : a + b = b + a"``. Returns the suggestions
    Lean printed, verbatim — each one still has to be compiled before it is
    claimed to work.
    """
    body = str(statement or "").strip()
    if not body:
        raise ValueError("lean_exact: statement must be a non-empty string")
    result = lean_command(
        f"example {body} := by\n  exact?", imports=imports, timeout=timeout,
        filename="Exact.lean",
    )
    suggestions = []
    for item in result["infos"]:
        message = str(item.get("message") or "")
        if message.startswith("Try this:"):
            for line in message.splitlines()[1:]:
                cleaned = line.strip()
                if cleaned:
                    suggestions.append(cleaned)
    return {
        "suggestions": suggestions,
        "found": bool(suggestions),
        "errors": result["errors"],
        "elapsed": result["elapsed"],
    }


def lean_goal(statement, tactics="", *, imports=None, timeout=LEAN_DEFAULT_TIMEOUT):
    """Show the goal state left after ``tactics``, using Lean's own printer.

    Deliberately leaves the proof unfinished so Lean reports ``unsolved goals``
    and prints the state — the reliable way to read a goal without a language
    server. ``goals`` is None when the tactics actually closed the goal, which
    is itself the answer.
    """
    body = str(statement or "").strip()
    if not body:
        raise ValueError("lean_goal: statement must be a non-empty string")
    steps = str(tactics or "").strip()
    block = "\n".join(f"  {line.strip()}" for line in steps.splitlines() if line.strip())
    program = f"example {body} := by\n{block}\n" if block else f"example {body} := by\n  skip\n"
    result = lean_check(
        program, filename="Goal.lean", imports=imports, timeout=timeout,
        allow_sorry=True,
    )
    for item in result["errors"]:
        if item.get("goal"):
            return {
                "goals": item["goal"],
                "closed": False,
                "line": item.get("line"),
                "col": item.get("col"),
                "elapsed": result["elapsed"],
                "errors": [e for e in result["errors"] if e is not item],
            }
    return {
        "goals": None,
        "closed": not result["errors"],
        "line": None,
        "col": None,
        "elapsed": result["elapsed"],
        "errors": result["errors"],
    }


def lean_loogle(query, *, limit=12, timeout=30):
    """Search Mathlib by name/shape on loogle.lean-lang.org.

    Network goes through ``host.web_fetch`` — the kernel sandbox denies raw
    sockets, and a request made with ``urllib`` would bypass both the egress
    allowlist and the SSRF guard. Use this when ``#find`` comes back empty and
    the question is "what is this theorem called"; a name loogle returns is a
    lead, not a fact, until ``lean_check_type`` confirms it exists locally.
    """
    text = str(query or "").strip()
    if not text:
        raise ValueError("lean_loogle: query must be a non-empty string")
    url = LEAN_LOOGLE_ENDPOINT + "?q=" + urllib.parse.quote(text)
    response = lean_sdk().web_fetch(url, format="json", timeout=timeout)
    payload = response.get("content") if isinstance(response, dict) else response
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except ValueError:
            return {"hits": [], "error": "loogle returned a non-JSON body"}
    if not isinstance(payload, dict):
        return {"hits": [], "error": "unexpected loogle response shape"}
    if payload.get("error"):
        return {"hits": [], "error": str(payload["error"])}
    hits = []
    for item in (payload.get("hits") or [])[: max(1, int(limit))]:
        if isinstance(item, dict):
            hits.append(
                {
                    "name": item.get("name"),
                    "type": item.get("type"),
                    "module": item.get("module"),
                }
            )
    return {"hits": hits, "count": payload.get("count"), "error": None}
