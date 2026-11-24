"""Block E — run the five-role chain against a real model, and classify what fails.

Why this is not just "run it and see"
-------------------------------------
Two live attempts on 2026-09-03 failed, and the failures were blamed on the
models: ``deepseek-v4-pro`` degenerated into repetition, ``deepseek-v4-flash``
self-corrected in a loop without ever emitting a usable fenced Python cell.
"The model went wrong" is not a finding anyone can act on, and it is one bad
guess away from being fixed in the wrong place -- research-sop's orchestration
logic, which 81 automated tests already cover and which was never implicated.

So this tool does two separable things:

1. **``--transcript``** classifies a captured model reply against the *shipped*
   upstream parser, so a failure is named rather than described. This runs
   anywhere, needs no model, and no credentials.
2. **``--live``** checks every precondition a real five-role run would need and
   reports which of them hold. It does not run one: there is no headless
   entrypoint in this repository that drives ``orchestrate_research`` against a
   chosen provider from the command line. ``headless_verify.py`` exercises the
   daemon lifecycle, not skill orchestration. Inventing flags for it would have
   produced a tool that looked like it ran an acceptance item and did not, so it
   says what is missing instead. E1-E3 stay NOT TESTED.

Provider neutrality is deliberate. Nothing here names a vendor: the provider and
model are arguments. A fix that hardcoded a workaround for one model's output
would move the failure rather than remove it, and would rot the moment that model
changed.

What is already known about the parsing boundary
------------------------------------------------
Measured against the pinned upstream (``a792c38d``) rather than assumed:

- a second labelled ```` ```python ```` fence before the first one closes leaves
  the outer block **unclosed**, so no cell is extracted and the harness replies
  with the incomplete-cell nudge. A model that answers that nudge the same way
  loops. This matches the flash symptom exactly;
- closing a cell with ```` ```python ```` rather than a bare ```` ``` ```` has
  the same effect;
- an info string of ``python3`` is not in the executable set (``""``/``python``/
  ``py``), so such a reply is treated as containing no code at all.

Those are upstream behaviours, and deliberate ones -- the nesting rule exists so a
quoted ```` ```tool ```` example inside a cell cannot truncate it. **Upstream is
not modified here.** ``manifests/upstream-pin.json`` requires the checkout to stay
byte-clean and ``tools/verify_release.py`` fails if it drifts, so changing the
parser is a decision about the product's relationship with upstream, not a bug
fix. It is written up in the closure report instead of guessed at.

    python tools/manual_acceptance/verify_research_sop_live.py --transcript reply.txt
    python tools/manual_acceptance/verify_research_sop_live.py --live \\
        --provider <name> --model <id> --task "..." --save
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    FAIL,
    NOT_APPLICABLE,
    PASS,
    REPO,
    UNDETERMINED,
    Report,
    emit,
    parser,
    run,
)

COVERS = ["E1", "E2", "E3"]

UPSTREAM_DEFAULT = pathlib.Path(
    os.environ.get("LEO_UPSTREAM_ROOT")
    or REPO / "LeoAIStudio" / "upstream" / "OpenAI4S"
)

#: Failure classes, so a live run ends with a name rather than a narrative.
#: The first four are harness/model interface problems; the last two would be
#: research-sop's own, and are listed so that "not one of these" is a statement
#: someone can check rather than an assumption.
FAILURE_CLASSES = {
    "no-action-in-reply": "the reply contained neither a fenced cell nor a native tool call",
    "unclosed-cell": "a fence opened and never closed at top level, usually a nested labelled fence",
    "unexecutable-info-string": "a fenced block whose language label is outside the executable set",
    "repetition": "the reply repeats itself without progressing",
    "schema-rejected": "a stage submitted output that failed ROLE_OUTPUT_SCHEMA",
    "orchestration": "a stage completed but the run was assembled wrongly -- this one WOULD be research-sop's",
}


def _load_upstream_parser(report: Report, upstream: pathlib.Path):
    """Import the shipped parser read-only. Never modify the upstream checkout."""
    if not upstream.is_dir():
        report.check("upstream checkout", UNDETERMINED,
                     f"not found at {upstream}; pass --upstream", path=str(upstream))
        return None
    dirty = run(["git", "status", "--porcelain"], cwd=upstream)
    if dirty["returncode"] == 0 and dirty["stdout"].strip():
        report.check(
            "upstream is byte-clean", FAIL,
            "the upstream checkout has local modifications. manifests/upstream-pin.json "
            "requires it to stay clean so it remains pullable, and verify_release.py "
            "fails on drift. Classifying against a modified parser would also describe "
            "a harness nobody else has",
            changes=dirty["stdout"].strip()[:2000],
        )
        return None
    head = run(["git", "rev-parse", "HEAD"], cwd=upstream)
    report.check(
        "upstream checkout", PASS,
        f"clean at {head['stdout'].strip()[:12]}",
        path=str(upstream), commit=head["stdout"].strip(),
    )
    sys.path.insert(0, str(upstream))
    try:
        from openai4s.agent.actions import (  # noqa: PLC0415
            count_code_blocks,
            extract_action,
            has_incomplete_code_block,
        )
        from openai4s.agent.actions import PYTHON_INFOS, R_INFOS  # noqa: PLC0415
        from openai4s.tools import scan_fenced_blocks  # noqa: PLC0415
    except Exception as error:
        report.check("upstream parser importable", UNDETERMINED,
                     f"could not import the shipped parser: {error!r}")
        return None
    return {
        "extract_action": extract_action,
        "count_code_blocks": count_code_blocks,
        "has_incomplete_code_block": has_incomplete_code_block,
        "scan_fenced_blocks": scan_fenced_blocks,
        "executable_infos": tuple(PYTHON_INFOS) + tuple(R_INFOS),
    }


def classify_reply(text: str, parser_api: dict) -> dict:
    """Name why a model reply produced no executable action, using the real parser."""
    cell = parser_api["extract_action"](text)
    blocks = parser_api["scan_fenced_blocks"](text)
    if cell is not None:
        return {
            "classification": "ok",
            "detail": f"a {cell.language} cell was extracted",
            "cells": parser_api["count_code_blocks"](text),
        }
    if parser_api["has_incomplete_code_block"](text):
        labelled_inside = sum(
            1 for block in blocks if block.info in parser_api["executable_infos"]
        )
        return {
            "classification": "unclosed-cell",
            "detail": (
                "a top-level executable fence never closed. The usual cause is a second "
                "labelled ```python fence appearing before the first one closes: the "
                "scanner treats a labelled fence inside a block as a nested example and "
                "only a bare ``` closes it"
            ),
            "labelled_blocks": labelled_inside,
        }
    infos = sorted({block.info for block in blocks if block.closed})
    unexecutable = [info for info in infos if info and info not in parser_api["executable_infos"]]
    if unexecutable:
        return {
            "classification": "unexecutable-info-string",
            "detail": (
                f"fenced block(s) labelled {unexecutable}, which are outside the "
                f"executable set {list(parser_api['executable_infos'])}. 'python3' is the "
                "common near-miss"
            ),
            "info_strings": infos,
        }
    if _looks_repetitive(text):
        return {
            "classification": "repetition",
            "detail": "the reply repeats a line or paragraph without progressing",
        }
    return {
        "classification": "no-action-in-reply",
        "detail": "no fenced block at all; the harness would send the no-code nudge",
        "info_strings": infos,
    }


def _looks_repetitive(text: str, threshold: int = 5) -> bool:
    """A crude but honest repetition signal: the same non-trivial line, many times."""
    counts: dict[str, int] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if len(stripped) < 20:
            continue
        counts[stripped] = counts.get(stripped, 0) + 1
    return any(count >= threshold for count in counts.values())


# ------------------------------------------------------------------ live run


def _live_preconditions(report: Report, args) -> bool:
    """Everything that must be true before a real run is even attempted."""
    ready = True

    provider = args.provider or os.environ.get("LEO_LIVE_PROVIDER")
    model = args.model or os.environ.get("LEO_LIVE_MODEL")
    report.check(
        "provider and model named",
        PASS if provider and model else UNDETERMINED,
        f"provider={provider!r} model={model!r}" if provider and model
        else "pass --provider and --model (or LEO_LIVE_PROVIDER / LEO_LIVE_MODEL). "
             "Nothing here defaults to a vendor",
        provider=provider, model=model,
    )
    ready &= bool(provider and model)

    key_variable = args.key_env
    has_key = bool(os.environ.get(key_variable))
    report.check(
        "credentials present",
        PASS if has_key else UNDETERMINED,
        f"{key_variable} is set" if has_key
        else f"{key_variable} is not set in this environment. A live run costs money "
             "and calls an external service, so this tool never goes looking for a key "
             "elsewhere and never falls back to one it finds",
        key_env=key_variable,
    )
    ready &= has_key

    # headless_verify.py takes an optional package root and no flags. Passing it
    # an invented switch would make it fail for the wrong reason and report a
    # missing daemon that is actually running -- which is what happened the first
    # time this was written.
    app_root = os.environ.get("LEO_APP_ROOT") or str(REPO / "LeoAIStudio")
    daemon = run([sys.executable, str(REPO / "tools" / "headless_verify.py"), app_root],
                 cwd=REPO, timeout=900)
    daemon_ok = daemon["returncode"] == 0 and "[stage] status: ok" in daemon["stdout"]
    report.check(
        "daemon reachable",
        PASS if daemon_ok else UNDETERMINED,
        "the WSL bridge answers preflight and status" if daemon_ok
        else "the bridge did not report a running daemon; start the application first",
        app_root=app_root,
        returncode=daemon["returncode"],
        stdout=daemon["stdout"].strip()[-4000:],
    )
    ready &= daemon_ok

    # And the part that does not exist yet, stated rather than worked around.
    report.check(
        "headless five-role entrypoint", UNDETERMINED,
        "there is no tool in this repository that drives orchestrate_research end to "
        "end from the command line against a chosen provider. headless_verify.py "
        "verifies the daemon lifecycle (preflight/status/start/url/http/stop), not "
        "skill orchestration. E1-E3 therefore need the application driven by hand; "
        "see the note below",
        candidate="tools/headless_verify.py",
    )
    report.note(
        "Manual E procedure until a headless entrypoint exists: start the app with the "
        "provider configured, load research-sop, call orchestrate_research(task) from "
        "the agent, then save the run report and the model replies. Feed a reply that "
        "produced no action back through --transcript to get it classified. Building "
        "that entrypoint is a design decision about the product's public surface, not "
        "something to improvise inside an acceptance tool."
    )
    # Even with a provider, a key and a live daemon, there is nothing to invoke.
    # `ready` is still computed and reported above so that the other
    # preconditions are visible: someone building the entrypoint needs to know
    # which of them already hold.
    del ready
    return False


def main() -> int:
    argument_parser = parser(__doc__.splitlines()[0])
    argument_parser.add_argument("--transcript", type=pathlib.Path,
                                 help="classify a captured model reply and exit")
    argument_parser.add_argument("--live", action="store_true",
                                 help="attempt a real five-role run")
    argument_parser.add_argument("--provider", help="provider name; no default")
    argument_parser.add_argument("--model", help="model id; no default")
    argument_parser.add_argument("--key-env", default="OPENAI_API_KEY",
                                 help="environment variable holding the credential")
    argument_parser.add_argument("--task", help="the research question to run")
    argument_parser.add_argument("--upstream", type=pathlib.Path, default=UPSTREAM_DEFAULT)
    args = argument_parser.parse_args()

    report = Report("verify_research_sop_live", "E", COVERS)
    report.note(
        "Failure classes: " + "; ".join(f"{k} = {v}" for k, v in FAILURE_CLASSES.items())
    )

    parser_api = _load_upstream_parser(report, args.upstream)

    if args.transcript:
        if parser_api is None:
            report.check("transcript classification", UNDETERMINED,
                         "the shipped parser could not be loaded, so nothing was classified")
            return emit(report, args)
        text = args.transcript.read_text(encoding="utf-8", errors="replace")
        verdict = classify_reply(text, parser_api)
        report.check(
            "transcript classification",
            PASS if verdict["classification"] == "ok" else FAIL,
            f"{verdict['classification']}: {verdict['detail']}",
            transcript=str(args.transcript),
            **{k: v for k, v in verdict.items() if k not in ("classification", "detail")},
        )
        report.note(
            "A classification of unclosed-cell / unexecutable-info-string is a "
            "model-harness interface problem. It is NOT evidence of a research-sop "
            "defect, and must not be 'fixed' there."
        )
        return emit(report, args)

    if not args.live:
        report.check(
            "mode", UNDETERMINED,
            "neither --transcript nor --live was given, so nothing was run",
        )
        for item in COVERS:
            report.suggestion(item, UNDETERMINED, "no live run was attempted")
        return emit(report, args)

    if not _live_preconditions(report, args):
        for item in COVERS:
            report.suggestion(
                item, UNDETERMINED,
                "preconditions for a live run were not met; the item stays NOT TESTED. "
                "Not attempting a run is the honest outcome -- a partial run recorded as "
                "a pass would be worse than no run",
            )
        return emit(report, args)

    # Unreachable while the entrypoint is missing: _live_preconditions returns
    # False unconditionally and says why. Kept as a single explicit line rather
    # than a stub that pretends to run something.
    raise AssertionError("unreachable: no headless five-role entrypoint exists")


if __name__ == "__main__":
    raise SystemExit(main())
