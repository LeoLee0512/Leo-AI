"""
Research-SOP helpers. Auto-loaded into the python kernel by the host when the
skill loads:

  orchestrate_research, sop_status, sop_list_runs, sop_role_prompt,
  sop_read_stage, sop_write_stage, sop_stage_path, sop_resolve_run

Module top level is definition-only (functions, imports, literal constants) so
the sidecar structure gate accepts it; everything that touches the host runtime
happens inside a function body.

Sub-agents are spawned through ``host.delegate`` with the role persona carried
in the request text, not through ``openai4s/specialists.py``. That keeps this
skill entirely inside ``<data_dir>/user-skills`` and leaves the upstream tree
untouched and updatable.

Stage handoffs are files in the session workspace, written through
``host.write_file``. Files, not conversation state, are what make a run
resumable and a claim auditable: the JSON record says what each role returned,
and the markdown next to it is the document that role produced.

Every run lives in its own directory and is bound to its research question::

    research-runs/<run_id>/
        manifest.json          run_id, task_text, task_sha256, pipeline_version,
                               role_prompt_hashes, model_fingerprint,
                               created_at, parent_run_id, rollbacks
        01-literature-surveyor.json / .md
        ... one pair per role ...

``run_id`` is derived from the task hash, so resuming is only ever possible
within the same research question. The previous layout wrote every run to a
single fixed ``research-sop/`` folder with no task binding, which meant a second
study silently resumed the first study's stages and reported them as its own
findings. That is evidence contamination, not a convenience bug, which is why
there is no compatibility fallback to the old path.
"""

import hashlib
import json
import posixpath
import re
import uuid

#: Pipeline order. Every helper derives its numbering from this tuple, so
#: reordering or trimming roles needs no other edit.
ROLE_ORDER = (
    "literature-surveyor",
    "modeler",
    "numerical-experimenter",
    "validator",
    "paper-writer",
)

#: One directory per research run. The previous layout was a single fixed
#: ``research-sop/`` folder with no task binding, which let one study resume
#: another study's stages. ``LEGACY_SOP_DIR`` is kept only so old material can
#: be recognised as legacy and never read as evidence for a new run.
RUNS_DIR = "research-runs"
LEGACY_SOP_DIR = "research-sop"

#: Bump when the run-directory layout or manifest shape changes.
SCHEMA_VERSION = 2

#: Bump when role order or personas change; recorded in every manifest so two
#: runs of the same task are only comparable when this matches.
PIPELINE_VERSION = "2.0.0"

#: Per-role turn ceiling. The experimenter gets the largest budget because it
#: is the only role that runs code in a loop; the writer needs the fewest.
ROLE_MAX_TURNS = {
    "literature-surveyor": 40,
    "modeler": 24,
    "numerical-experimenter": 60,
    "validator": 32,
    "paper-writer": 28,
}

#: What each child must put in ``host.submit_output(output=...)``. The runtime
#: only enforces type + required keys, which is exactly the part worth
#: enforcing: it makes a missing verdict a refused submission rather than a
#: field the orchestrator has to guess at.
ROLE_OUTPUT_SCHEMA = {
    "literature-surveyor": {
        "type": "object",
        "required": ["summary", "citations", "gaps"],
    },
    "modeler": {
        "type": "object",
        "required": ["summary", "equations", "assumptions"],
    },
    "numerical-experimenter": {
        "type": "object",
        "required": ["summary", "method", "results", "convergence"],
    },
    "validator": {
        "type": "object",
        "required": ["summary", "verdict", "findings"],
    },
    "paper-writer": {
        "type": "object",
        "required": ["summary", "sections"],
    },
}

ROLE_MISSIONS = {
    "literature-surveyor": (
        "You are the LITERATURE SURVEYOR of a five-role research pipeline.\n"
        "Establish what is already known about the question, with citations a "
        "reader can resolve.\n\n"
        "How to work:\n"
        "- Retrieve first, write second. Load the `literature-review` skill and use "
        "its kernel helpers (`search_openalex`, `crossref_lookup`, "
        "`expand_citations`, `verify_dois`). If a `local-literature-rag` index "
        "exists, query it first with `lit_search` — the user's own library is the "
        "most relevant corpus available — then go to the live sources for what it "
        "does not cover.\n"
        "- After the first sweep, walk one step backward (reference lists) and one "
        "step forward (cited-by) from the two or three most relevant hits.\n"
        "- Organise by question or theme, never paper by paper. Say what is "
        "established, what is contested, and where the gap this task sits in "
        "actually is.\n"
        "- Cite inline as [Author Year](https://doi.org/10.xxxx/xxxxxx). A DOI you "
        "did not resolve is not a citation — leave it out and say the evidence is "
        "missing.\n\n"
        "Deliverable: a synthesis in prose (not a bulleted bibliography) that the "
        "modeler can build on."
    ),
    "modeler": (
        "You are the MODELER of a five-role research pipeline.\n"
        "Turn the research question into something a numericist can solve without "
        "asking you follow-up questions.\n\n"
        "Your specification must state:\n"
        "- the governing equations, in full, with every symbol defined;\n"
        "- every assumption, and what each one buys you;\n"
        "- the domain, boundary conditions and initial conditions;\n"
        "- the non-dimensional groups and the regimes they select;\n"
        "- the quantities of interest and how they will be measured;\n"
        "- an explicit list, ordered by risk, of the assumptions most likely to "
        "break. The validator will come looking for exactly this list, so writing "
        "it honestly is the point.\n\n"
        "Write no solver code here. Ground modelling choices in the survey and say "
        "when you are departing from what the literature does, and why."
    ),
    "numerical-experimenter": (
        "You are the NUMERICAL EXPERIMENTER of a five-role research pipeline.\n"
        "Implement the model specification, run it, and report what actually "
        "happened.\n\n"
        "Requirements:\n"
        "- Justify the discretisation and the solver; a choice without a reason is "
        "an untested assumption.\n"
        "- Run a convergence study (grid / timestep / iteration count, as "
        "applicable) and report the observed order.\n"
        "- Quantify error against an analytical solution or an accepted benchmark "
        "wherever one exists; say so plainly when none does.\n"
        "- Fix and record the seed for anything stochastic.\n"
        "- Save the solver code and the result data with `host.save_artifact` so "
        "they are versioned and re-runnable.\n"
        "- Report the runs that failed or diverged as well as the ones that "
        "worked. A clean results table with the failures deleted is a fabricated "
        "result.\n"
        "- Use the preinstalled scientific stack: numpy, scipy, pandas, "
        "matplotlib, sklearn, sympy, statsmodels, networkx, numba and h5py are "
        "already there. torch and jax are NOT, and the kernel runs sandboxed, so "
        "anything pip installs lands in a throwaway site-packages and is gone when "
        "the task ends.\n"
        "- Never run a bare `pip install torch`: the default index serves the CUDA "
        "build and pulls several GB of nvidia-cudnn and CUDA toolkit for an "
        "experiment that does not need a GPU. If a deep-learning framework is "
        "genuinely unavoidable, install the CPU wheel explicitly with "
        "`pip install torch --index-url https://download.pytorch.org/whl/cpu`.\n"
        "- Prefer the smallest reproducible experiment that confirms or falsifies "
        "the modeller's hypothesis over a full training run. If an experiment would "
        "need gigabytes of dependencies, downgrade it: compare against an analytical "
        "or manufactured solution, do a truncation-error and convergence-order "
        "study, or take residual distribution statistics. Record the downgrade and "
        "its reason in the stage file rather than stopping to install.\n\n"
        "Every number you report must come from a run that happened in this "
        "session."
    ),
    "validator": (
        "You are the VALIDATOR of a five-role research pipeline. Your job is to "
        "try to break the work, not to approve it.\n\n"
        "Check, in this order:\n"
        "1. Model against survey — are the assumptions defensible given what is "
        "known?\n"
        "2. Implementation against model — does the code solve the equations that "
        "were specified, with the stated boundary conditions?\n"
        "3. Numbers against claims — does every reported figure trace to a run, "
        "and does the convergence evidence support the accuracy claimed?\n"
        "4. Independent re-derivation — reproduce at least one result another way: "
        "a limiting case, a conservation or symmetry check, an order-of-magnitude "
        "estimate.\n"
        "5. Reproducibility — re-run the saved code and confirm it produces the "
        "reported numbers.\n\n"
        "Your `output` must carry:\n"
        "  verdict: \"pass\" | \"revise\" | \"fail\"\n"
        "  send_back_to: the role name that must redo its stage, or null on pass\n"
        "  findings: a list of concrete problems, each naming what is wrong, where, "
        "and what would settle it\n\n"
        "`send_back_to` must be one of: literature-surveyor, modeler, "
        "numerical-experimenter. Passing something through to keep the pipeline "
        "moving is the one failure this role cannot have."
    ),
    "paper-writer": (
        "You are the PAPER WRITER of a five-role research pipeline.\n"
        "Turn everything upstream into the document a reader actually gets.\n\n"
        "Structure: abstract, introduction (with the literature framing), model and "
        "assumptions, numerical method, results, discussion, limitations, "
        "conclusion, references.\n\n"
        "Standards:\n"
        "- Paragraphs of connected argument. Each opens on your claim and spends "
        "citations backing it. If consecutive lines start with an author name, that "
        "paragraph has not been written yet.\n"
        "- Methods precise enough that someone else could reproduce the runs.\n"
        "- Every result carries its uncertainty and the convergence evidence "
        "behind it.\n"
        "- The limitations section names the assumptions the validator flagged, "
        "including the ones that were not resolved.\n"
        "- Cite as [Author Year](https://doi.org/10.xxxx/xxxxxx), carrying through "
        "only DOIs the surveyor actually resolved. Invent nothing: no citation, no "
        "number, and no result that is not upstream of you in this pipeline.\n\n"
        "Write in the language the original research question is written in."
    ),
}

#: Which upstream stages each role is given. Handing a role less than the whole
#: history is deliberate: the modeler that never sees the raw solver logs cannot
#: quietly rewrite its assumptions to match them.
ROLE_INPUTS = {
    "literature-surveyor": (),
    "modeler": ("literature-surveyor",),
    "numerical-experimenter": ("modeler",),
    "validator": ("modeler", "numerical-experimenter", "literature-surveyor"),
    "paper-writer": (
        "literature-surveyor",
        "modeler",
        "numerical-experimenter",
        "validator",
    ),
}

#: Roles the validator may send work back to, in pipeline order.
REWORKABLE_ROLES = (
    "literature-surveyor",
    "modeler",
    "numerical-experimenter",
)

VALID_VERDICTS = ("pass", "revise", "fail")

_SLUG_UNSAFE = re.compile(r"[^a-z0-9-]+")


def sop_sdk():
    """Rebind-proof SDK handle — see pdf-explore/kernel.py:pdf_sdk."""
    import host

    return host


def sop_stage_index(role):
    """1-based position of ``role`` in the pipeline."""
    return ROLE_ORDER.index(role) + 1


#: Manifest read outcomes. "missing" and "corrupt" used to collapse into a single
#: None, which meant a damaged manifest was treated as absent, rebuilt in place,
#: and the old stages underneath it were then reported as this run's evidence.
MANIFEST_MISSING = "missing"
MANIFEST_VALID = "valid"
MANIFEST_CORRUPT = "corrupt"
MANIFEST_INCOMPATIBLE = "incompatible"

#: A run id is either the 16-hex task prefix or that prefix with a rework
#: suffix. Anchored fullmatch: the previous check only asked whether *any*
#: character survived slug scrubbing, so "../evil" passed it.
_RUN_ID_RE = re.compile(r"\A[0-9a-f]{16}(?:-r[1-9][0-9]*)?\Z")

#: Stage files are records and documents. Nothing else may be addressed.
STAGE_SUFFIXES = ("json", "md")

#: Roles whose stage cannot be complete unless the markdown document they are
#: contracted to produce actually exists. The paper writer is the one whose
#: absence previously produced a report pointing at a file that was never written.
ROLE_REQUIRES_DOCUMENT = ("paper-writer",)

#: Outcomes of checking a stage document against the digest its record claims.
DOCUMENT_OK = "ok"
DOCUMENT_MISSING = "missing"
DOCUMENT_EMPTY = "empty"
DOCUMENT_HASH_MISMATCH = "hash-mismatch"
DOCUMENT_UNHASHED = "unhashed"

#: Outcomes of re-hashing an archived history file against its manifest entry.
ARCHIVE_OK = "ok"
ARCHIVE_MISSING = "missing"
ARCHIVE_HASH_MISMATCH = "hash-mismatch"
ARCHIVE_SIZE_MISMATCH = "size-mismatch"
ARCHIVE_UNHASHED = "unhashed"

#: Whole-run history audit outcomes.
HISTORY_OK = "ok"
HISTORY_EMPTY = "empty"
HISTORY_CORRUPT = "corrupt"

#: task_status values that mean the child finished its work. Anything else --
#: including "failed", "cancelled" and "timeout" -- is not a completed stage,
#: however much output came back with it.
DELEGATE_SUCCESS_STATUS = ("completed", "complete", "success", "succeeded", "ok", "done")

#: stop_reason values that mean the child was cut off rather than finished.
DELEGATE_FAILURE_STOP = ("error", "failed", "failure", "timeout", "timed_out",
                         "cancelled", "canceled", "max_turns", "budget_exhausted")


def sop_task_sha256(task):
    """Stable identity of a research task: SHA-256 over its normalised text.

    Whitespace is collapsed so re-wrapping the same question still resumes, but
    any change to the actual words produces a different id and a different run.
    """
    normalised = " ".join(str(task or "").split())
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def sop_role_prompt_hashes():
    """SHA-256 of each role persona, so a prompt edit is visible in the record."""
    return {
        role: hashlib.sha256(ROLE_MISSIONS[role].encode("utf-8")).hexdigest()[:16]
        for role in ROLE_ORDER
        if role in ROLE_MISSIONS
    }


def sop_model_fingerprint():
    """Best-effort record of which model produced a run.

    The host exposes no documented model-identity call, so this reports what it
    can and says so plainly otherwise. An honest "unknown" is worth more here
    than a fabricated identifier: the manifest is evidence.
    """
    host = sop_sdk()
    for name in ("model_info", "get_model", "model"):
        probe = getattr(host, name, None)
        if probe is None:
            continue
        try:
            value = probe() if callable(probe) else probe
        except Exception:
            continue
        if isinstance(value, dict):
            return dict(value)
        if value:
            return {"model": str(value), "source": name}
    return {"model": "unknown", "source": "host exposes no model identity call"}


# ------------------------------------------------------------------ paths


def sop_validate_run_id(run_id):
    """Return *run_id* if it is well formed, else raise. No path may skip this."""
    text = str(run_id or "")
    if not _RUN_ID_RE.match(text):
        raise ValueError(
            f"invalid run_id {run_id!r}: expected 16 hex characters, "
            "optionally followed by -r<N>"
        )
    return text


def sop_run_dir(run_id):
    """Workspace directory holding one run's manifest, stages and history."""
    return f"{RUNS_DIR}/{sop_validate_run_id(run_id)}"


def sop_manifest_path(run_id):
    """Path of a run's manifest."""
    return f"{sop_run_dir(run_id)}/manifest.json"


def sop_contained_path(run_id, *parts):
    """Join *parts* under the run directory, refusing anything that escapes it.

    Belt and braces on top of the run-id and suffix checks: the joined path is
    normalised and then required to still start with this run's directory, so a
    traversal segment introduced anywhere cannot reach the rest of the
    workspace.
    """
    root = sop_run_dir(run_id)
    for part in parts:
        text = str(part)
        if not text or "\\" in text or text.startswith("/"):
            raise ValueError(f"unsafe path segment {part!r}")
        if text == "." or text == ".." or text.startswith("../") or "/../" in text:
            raise ValueError(f"unsafe path segment {part!r}")
    joined = "/".join((root,) + tuple(str(p) for p in parts))
    normalised = posixpath.normpath(joined)
    if normalised != joined or not normalised.startswith(root + "/"):
        raise ValueError(f"path escapes the run directory: {joined!r}")
    return normalised


def sop_stage_path(run_id, role, suffix="json"):
    """Path of one stage's record (json) or document (md) inside a run."""
    if role not in ROLE_ORDER:
        raise ValueError(f"unknown role {role!r}; expected one of {ROLE_ORDER}")
    if suffix not in STAGE_SUFFIXES:
        raise ValueError(f"invalid stage suffix {suffix!r}; expected one of {STAGE_SUFFIXES}")
    slug = _SLUG_UNSAFE.sub("-", role.lower())
    return sop_contained_path(run_id, f"{sop_stage_index(role):02d}-{slug}.{suffix}")


# ------------------------------------------------------------- file access


def sop_read_text(path):
    """Read a workspace file, returning None only when it is genuinely absent."""
    try:
        result = sop_sdk().read_file(path)
    except Exception:
        return None
    content = result.get("content") if isinstance(result, dict) else result
    return content if isinstance(content, str) else None


def sop_run_dir_exists(run_id):
    """Whether anything has been written for this run yet."""
    try:
        listing = sop_sdk().list_dir(sop_run_dir(run_id))
    except Exception:
        return False
    entries = listing.get("entries") if isinstance(listing, dict) else listing
    return bool(entries)


# ---------------------------------------------------------------- manifest


def sop_manifest_compatibility(manifest):
    """Reasons this manifest describes a different pipeline than the one loaded.

    A run recorded under different role prompts or a different pipeline version
    is not the same experiment, even when the question is identical. Reusing its
    stages would silently mix results from two different methods.
    """
    problems = []
    if manifest.get("schema_version") != SCHEMA_VERSION:
        problems.append(
            f"schema_version {manifest.get('schema_version')!r} != {SCHEMA_VERSION!r}"
        )
    if manifest.get("pipeline_version") != PIPELINE_VERSION:
        problems.append(
            f"pipeline_version {manifest.get('pipeline_version')!r} != {PIPELINE_VERSION!r}"
        )
    if list(manifest.get("role_order") or ()) != list(ROLE_ORDER):
        problems.append("role_order changed")
    current = sop_role_prompt_hashes()
    stored = manifest.get("role_prompt_hashes")
    if not isinstance(stored, dict):
        problems.append("role_prompt_hashes missing")
    else:
        changed = sorted(
            role for role, digest in current.items() if stored.get(role) != digest
        )
        if changed:
            problems.append(f"role prompt(s) changed: {', '.join(changed)}")
    return problems


def sop_inspect_manifest(run_id):
    """Classify a run's manifest as missing / valid / corrupt / incompatible.

    Never collapses "damaged" into "absent". A manifest whose bytes are present
    but unreadable is CORRUPT and the caller must fail closed: rebuilding it in
    place would re-adopt whatever stage files sit beside it as this run's
    evidence, which is exactly the contamination this module exists to prevent.
    """
    path = sop_manifest_path(run_id)
    content = sop_read_text(path)
    if content is None:
        if sop_run_dir_exists(run_id):
            return {
                "state": MANIFEST_CORRUPT,
                "manifest": None,
                "reason": "run directory exists but its manifest could not be read",
                "path": path,
            }
        return {"state": MANIFEST_MISSING, "manifest": None, "reason": None, "path": path}
    if not content.strip():
        return {
            "state": MANIFEST_CORRUPT,
            "manifest": None,
            "reason": "manifest is empty",
            "path": path,
        }
    try:
        manifest = json.loads(content)
    except (TypeError, ValueError) as error:
        return {
            "state": MANIFEST_CORRUPT,
            "manifest": None,
            "reason": f"manifest is not valid JSON: {error}",
            "path": path,
        }
    if not isinstance(manifest, dict):
        return {
            "state": MANIFEST_CORRUPT,
            "manifest": None,
            "reason": "manifest is not a JSON object",
            "path": path,
        }
    required = (
        "run_id",
        "task_text",
        "task_sha256",
        "schema_version",
        "pipeline_version",
    )
    missing = [key for key in required if not manifest.get(key)]
    if missing:
        return {
            "state": MANIFEST_CORRUPT,
            "manifest": manifest,
            "reason": f"manifest is missing required field(s): {', '.join(missing)}",
            "path": path,
        }
    if manifest.get("run_id") != run_id:
        return {
            "state": MANIFEST_CORRUPT,
            "manifest": manifest,
            "reason": (
                f"manifest claims run_id {manifest.get('run_id')!r} but is stored "
                f"as run {run_id!r}"
            ),
            "path": path,
        }
    task_text = manifest.get("task_text")
    if not isinstance(task_text, str) or not task_text.strip():
        return {
            "state": MANIFEST_CORRUPT,
            "manifest": manifest,
            "reason": "manifest task_text is not text",
            "path": path,
        }
    recomputed = sop_task_sha256(task_text)
    if manifest.get("task_sha256") != recomputed:
        return {
            "state": MANIFEST_CORRUPT,
            "manifest": manifest,
            "reason": (
                f"manifest task_sha256 {manifest.get('task_sha256')!r} does not "
                f"match this task: its own task_text hashes to {recomputed}"
            ),
            "path": path,
        }
    for field in ("role_order", "lineage", "rollbacks"):
        value = manifest.get(field)
        if value is not None and not isinstance(value, list):
            return {
                "state": MANIFEST_CORRUPT,
                "manifest": manifest,
                "reason": f"manifest {field} is not a list",
                "path": path,
            }
    problems = sop_manifest_compatibility(manifest)
    if problems:
        return {
            "state": MANIFEST_INCOMPATIBLE,
            "manifest": manifest,
            "reason": "; ".join(problems),
            "path": path,
        }
    return {"state": MANIFEST_VALID, "manifest": manifest, "reason": None, "path": path}


def sop_read_manifest(run_id):
    """Return a run's manifest only when it is valid for *this* pipeline.

    "Valid" is relative to the loaded role prompts and pipeline version, so after
    an edit to ROLE_MISSIONS this returns None for runs recorded under the old
    prompts. That is the intended answer, and it is not a claim that the run is
    missing or damaged:

    - its bytes are untouched -- nothing here or in sop_resolve_run deletes or
      rewrites a superseded run;
    - it stays auditable -- sop_inspect_manifest and sop_list_runs return its
      contents, labelled MANIFEST_INCOMPATIBLE with the reason;
    - it is simply not evidence produced under the prompts now in force, so its
      stages must not be adopted by the new run.

    An earlier description had this backwards, saying an old run should still
    read back as a valid run after a prompt change. Treating it as valid is what
    would mix two methods' results under one conclusion. Use sop_inspect_manifest
    when you want to read a run rather than to build on it.
    """
    report = sop_inspect_manifest(run_id)
    return report["manifest"] if report["state"] == MANIFEST_VALID else None


def sop_write_manifest(run_id, manifest):
    """Persist a run manifest, then read it back to prove it landed."""
    payload = dict(manifest)
    payload["run_id"] = sop_validate_run_id(run_id)
    path = sop_manifest_path(run_id)
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    sop_sdk().write_file(path, body)
    written = sop_read_text(path)
    if written is None or json.loads(written).get("run_id") != payload["run_id"]:
        raise RuntimeError(f"manifest write to {path} could not be verified")
    return payload


def sop_new_manifest(task, run_id, parent_run_id=None, lineage=None):
    """Build the manifest that binds a run to its task and its pipeline."""
    import datetime

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "task_text": str(task),
        "task_sha256": sop_task_sha256(task),
        "pipeline_version": PIPELINE_VERSION,
        "role_order": list(ROLE_ORDER),
        "role_prompt_hashes": sop_role_prompt_hashes(),
        "model_fingerprint": sop_model_fingerprint(),
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "parent_run_id": parent_run_id,
        "lineage": list(lineage or ()),
        "rollbacks": [],
    }


# --------------------------------------------------------------- run choice


def sop_run_branches(task):
    """Every run id for *task* that has been started, base branch first."""
    base = sop_task_sha256(task)[:16]
    found = []
    attempt = 1
    misses = 0
    while misses < 3:
        run_id = base if attempt == 1 else f"{base}-r{attempt}"
        if sop_run_dir_exists(run_id):
            found.append(run_id)
            misses = 0
        else:
            misses += 1
        attempt += 1
    return found


def sop_run_lineage(run_id):
    """Walk a run back to its origin through parent_run_id."""
    chain = []
    seen = set()
    current = sop_validate_run_id(run_id)
    while current and current not in seen:
        seen.add(current)
        report = sop_inspect_manifest(current)
        chain.append({"run_id": current, "state": report["state"], "reason": report["reason"]})
        manifest = report["manifest"] or {}
        current = manifest.get("parent_run_id")
    return chain


def sop_resolve_run(task, resume=True, run_id=None, on_incompatible="fork"):
    """Decide which run this task belongs to. Returns ``(manifest, resumed)``.

    Rules, in order:

    - an explicit ``run_id`` resumes exactly that run, and only if its manifest
      is valid and carries this task's hash;
    - otherwise ``resume=True`` continues the **latest** branch of this task, so
      a rework is not silently abandoned in favour of the original attempt;
    - a different question always gets a new run;
    - ``resume=False`` is a deliberate rework: a new branch recording
      ``parent_run_id``, leaving the earlier attempt intact as evidence;
    - a corrupt manifest fails closed. It is never rebuilt in place, because the
      stage files beside it would then be adopted as this task's evidence.
    """
    digest = sop_task_sha256(task)
    base = digest[:16]

    if run_id is not None:
        report = sop_inspect_manifest(run_id)
        if report["state"] != MANIFEST_VALID:
            raise ValueError(
                f"cannot resume run {run_id}: manifest is {report['state']}"
                + (f" ({report['reason']})" if report["reason"] else "")
            )
        if report["manifest"].get("task_sha256") != digest:
            raise ValueError(
                f"run {run_id} belongs to a different research question; refusing to reuse it"
            )
        return report["manifest"], True

    branches = sop_run_branches(task)
    if resume and branches:
        latest = branches[-1]
        report = sop_inspect_manifest(latest)
        state = report["state"]
        if state == MANIFEST_CORRUPT:
            raise ValueError(
                f"run {latest} has a corrupt manifest ({report['reason']}). "
                "Refusing to rebuild it: the stage files beside it would be adopted as "
                "evidence for this task. Inspect or move "
                f"{report['path']} by hand, or start a new run with resume=False."
            )
        if state == MANIFEST_VALID:
            if report["manifest"].get("task_sha256") != digest:
                raise ValueError(
                    f"run {latest} manifest task_sha256 does not match this task; "
                    "refusing to reuse it"
                )
            return report["manifest"], True
        if state == MANIFEST_INCOMPATIBLE:
            if on_incompatible == "fail":
                raise ValueError(
                    f"run {latest} was produced by a different pipeline "
                    f"({report['reason']}); refusing to resume it"
                )
            # Fork rather than reuse: the stored stages came from a different
            # method, so they are not this pipeline's evidence.
            return sop_fork_run(task, parent_run_id=latest, reason=report["reason"]), False

    if not branches:
        created = sop_new_manifest(task, base)
        return sop_write_manifest(base, created), False

    return sop_fork_run(task, parent_run_id=branches[-1], reason="explicit rework"), False


def sop_fork_run(task, parent_run_id=None, reason=None):
    """Open a new branch for *task*, recording where it came from."""
    base = sop_task_sha256(task)[:16]
    attempt = 2
    while sop_run_dir_exists(f"{base}-r{attempt}"):
        attempt += 1
    run_id = f"{base}-r{attempt}"
    lineage = []
    if parent_run_id:
        lineage.append({"from": parent_run_id, "reason": reason or "rework"})
    created = sop_new_manifest(task, run_id, parent_run_id=parent_run_id, lineage=lineage)
    return sop_write_manifest(run_id, created)


def sop_list_runs():
    """Every run directory with a readable manifest, plus damaged ones."""
    host = sop_sdk()
    try:
        listing = host.list_dir(RUNS_DIR)
    except Exception:
        return []
    entries = listing.get("entries") if isinstance(listing, dict) else listing
    runs = []
    for entry in entries or ():
        name = entry.get("name") if isinstance(entry, dict) else str(entry)
        if not name:
            continue
        name = str(name).rstrip("/").split("/")[-1]
        try:
            report = sop_inspect_manifest(name)
        except ValueError:
            continue
        runs.append(
            {
                "run_id": name,
                "state": report["state"],
                "reason": report["reason"],
                "manifest": report["manifest"],
            }
        )
    return runs


# ------------------------------------------------------------------ stages


def sop_validate_output(role, output):
    """Local schema check. Returns a list of problems; empty means acceptable.

    ``host.delegate`` is given the same schema, but trusting the runtime to have
    enforced it is a single point of failure for the evidence chain. This is the
    second check, done where the record is written.
    """
    schema = ROLE_OUTPUT_SCHEMA.get(role) or {}
    problems = []
    if not isinstance(output, dict):
        return [f"output is {type(output).__name__}, expected an object"]
    for key in schema.get("required", ()):
        if key not in output:
            problems.append(f"missing required key {key!r}")
            continue
        value = output[key]
        if value is None:
            problems.append(f"required key {key!r} is null")
        elif isinstance(value, str) and not value.strip():
            problems.append(f"required key {key!r} is empty")
        elif isinstance(value, (list, dict)) and len(value) == 0 and key != "findings":
            problems.append(f"required key {key!r} is empty")
    if role == "validator" and isinstance(output.get("verdict"), str):
        if output["verdict"].strip().lower() not in VALID_VERDICTS:
            problems.append(f"verdict {output['verdict']!r} is not one of {sorted(VALID_VERDICTS)}")
    return problems


def sop_delegate_problems(role, result):
    """Reasons this delegate response is not a completed stage."""
    problems = []
    status = result.get("task_status")
    if status is not None and str(status).strip().lower() not in DELEGATE_SUCCESS_STATUS:
        problems.append(f"task_status={status!r}")
    error = result.get("error")
    if error:
        problems.append(f"error={error!r}")
    stop = result.get("stop_reason")
    if stop is not None and str(stop).strip().lower() in DELEGATE_FAILURE_STOP:
        problems.append(f"stop_reason={stop!r}")
    output = result.get("output")
    if output is None and not result.get("final_message"):
        problems.append("no output and no final message")
    else:
        problems.extend(sop_validate_output(role, output))
    return problems


def sop_read_stage(run_id, role, task_sha256):
    """Return a completed stage record from *run_id*, or None.

    Binding is exact. A record without a ``run_id`` or ``task_sha256`` field, or
    with the wrong one, is not evidence for this run: the previous version
    accepted a missing field as a match, which meant an unbound or hand-placed
    stage could be read as a completed result.
    """
    content = sop_read_text(sop_stage_path(run_id, role))
    if not content:
        return None
    try:
        record = json.loads(content)
    except (TypeError, ValueError):
        return None
    if not isinstance(record, dict) or record.get("state") != "complete":
        return None
    if record.get("run_id") != run_id:
        return None
    if record.get("task_sha256") != task_sha256:
        return None
    if record.get("role") != role:
        return None
    if not sop_document_ok(run_id, role, record):
        # The record claims completion but the document it is contracted to
        # produce is gone; that is not a stage anyone should build on.
        #
        # Returning None here means "this stage is no longer complete", which the
        # orchestrator answers by *running the stage again* and producing a real
        # new document. It does not mean the run has no paper: an earlier
        # description of this behaviour said a vanished document must make
        # orchestrate_research return paper=None, and that is wrong. Refusing to
        # redo recoverable work is not integrity. What integrity requires is only
        # that a paper path is never returned for a file that is not there.
        return None
    return record


def sop_document_digest(body):
    """Return the digest recorded for a stage document."""
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def sop_document_state(run_id, role, record=None):
    """Classify a role document against the digest claimed by its stage record."""
    claimed = (record or {}).get("document_sha256")
    contracted = role in ROLE_REQUIRES_DOCUMENT
    path = sop_stage_path(run_id, role, "md")
    body = sop_read_text(path)
    if body is None:
        if contracted or claimed:
            return DOCUMENT_MISSING, f"no document at {path}"
        return DOCUMENT_OK, None
    if not body.strip():
        if contracted or claimed:
            return DOCUMENT_EMPTY, f"document at {path} is empty"
        return DOCUMENT_OK, None
    if not claimed:
        if contracted:
            return DOCUMENT_UNHASHED, (
                f"{role} claims a complete stage but its record carries no "
                f"document_sha256 for {path}"
            )
        return DOCUMENT_OK, None
    actual = sop_document_digest(body)
    if actual != claimed:
        return DOCUMENT_HASH_MISMATCH, (
            f"document at {path} hashes to {actual} but its record claims {claimed}"
        )
    return DOCUMENT_OK, None


def sop_stored_stage(run_id, role):
    """Return the stored stage record without treating its claims as evidence."""
    content = sop_read_text(sop_stage_path(run_id, role))
    if not content:
        return None
    try:
        record = json.loads(content)
    except (TypeError, ValueError):
        return None
    return record if isinstance(record, dict) else None


def sop_document_verified(run_id, role):
    """Whether a role's document still matches the stored record beside it."""
    return sop_document_ok(run_id, role, sop_stored_stage(run_id, role))


def sop_document_ok(run_id, role, record=None):
    """Whether a role's document is still the document its record describes."""
    return sop_document_state(run_id, role, record)[0] == DOCUMENT_OK


def sop_write_stage(run_id, role, record, document=None, task_sha256=None):
    """Persist one stage inside a run: the JSON record plus its markdown."""
    host = sop_sdk()
    payload = dict(record)
    payload["role"] = role
    payload["run_id"] = sop_validate_run_id(run_id)
    payload["task_sha256"] = task_sha256
    payload.setdefault("state", "complete")
    if document:
        doc_path = sop_stage_path(run_id, role, "md")
        host.write_file(doc_path, str(document))
        body = sop_read_text(doc_path)
        if not body or not body.strip():
            raise RuntimeError(f"stage document write to {doc_path} could not be verified")
        payload["document_sha256"] = sop_document_digest(body)
        payload["document_path"] = doc_path
    host.write_file(
        sop_stage_path(run_id, role),
        json.dumps(payload, ensure_ascii=False, indent=2),
    )
    return payload


def sop_stage_digest(run_id, role, record, max_chars=6000):
    """Render one upstream stage as the block a downstream role is handed."""
    output = record.get("output")
    if isinstance(output, (dict, list)):
        body = json.dumps(output, ensure_ascii=False, indent=2)
    else:
        body = str(output or record.get("final_message") or "")
    if len(body) > max_chars:
        body = body[:max_chars] + "\n…(truncated; read the full record at "
        body += f"{sop_stage_path(run_id, role)})"
    return (
        f"### Upstream stage {sop_stage_index(role)} — {role}\n"
        f"Full record: {sop_stage_path(run_id, role)}\n"
        f"Document: {sop_stage_path(run_id, role, 'md')}\n\n"
        f"{body}\n"
    )


def sop_role_prompt(run_id, role, task, upstream=None, findings=None):
    """Assemble one child's request: persona, task, upstream, rework notes."""
    if role not in ROLE_MISSIONS:
        raise ValueError(f"unknown role {role!r}")
    parts = [ROLE_MISSIONS[role], "", "## Research question", str(task).strip()]
    if upstream:
        parts += ["", "## What the pipeline has established so far", ""]
        parts += list(upstream)
    if findings:
        parts += [
            "",
            "## The validator sent this stage back. Fix these before anything else",
            "",
        ]
        for item in findings:
            parts.append(f"- {item}")
        parts.append(
            "\nRedo your stage addressing every point above. Say explicitly which "
            "findings you resolved and which you could not, and why."
        )
    parts += [
        "",
        "## How to finish",
        "Write your document to "
        f"`{sop_stage_path(run_id, role, 'md')}` with `host.write_file`, then call "
        "`host.submit_output(output=..., completion_bullets=[...])` with an "
        "`output` object carrying the required keys: "
        f"{', '.join(ROLE_OUTPUT_SCHEMA[role]['required'])}. "
        "Add `document` holding the full markdown when it is short enough to "
        "carry. Report an incomplete stage as incomplete; never fill a gap with "
        "something you did not retrieve, derive, or run.",
    ]
    return "\n".join(parts)


def sop_collect_upstream(run_id, role, task_sha256):
    """Digests of the completed stages this role is allowed to see."""
    blocks = []
    for source in ROLE_INPUTS.get(role, ()):
        record = sop_read_stage(run_id, source, task_sha256)
        if record is not None:
            blocks.append(sop_stage_digest(run_id, source, record))
    return blocks


def sop_run_role(run_id, task, role, findings=None, retries=1, task_sha256=None):
    """Delegate one role and persist its stage. Returns the stage record."""
    host = sop_sdk()
    digest = task_sha256 or sop_task_sha256(task)
    request = sop_role_prompt(
        run_id,
        role,
        task,
        upstream=sop_collect_upstream(run_id, role, digest),
        findings=findings,
    )
    result = host.delegate(
        request,
        name=role,
        task=f"research-sop stage {sop_stage_index(role)}: {role}",
        output_schema=ROLE_OUTPUT_SCHEMA[role],
        max_turns=ROLE_MAX_TURNS.get(role, 32),
        retries=retries,
        wait=True,
    )
    if isinstance(result, list):
        result = result[0] if result else {}
    if not isinstance(result, dict):
        result = {"output": result}
    output = result.get("output")
    document = output.get("document") if isinstance(output, dict) else None

    problems = sop_delegate_problems(role, result)
    record = {
        "role": role,
        "stage": sop_stage_index(role),
        # Execution identity and artifact identity are intentionally separate.
        # Deterministic work may reproduce identical bytes on a later attempt;
        # changing the scientific document just to force a new digest would
        # manufacture evidence rather than distinguish the executions.
        "attempt_id": uuid.uuid4().hex,
        "state": "complete" if not problems else "incomplete",
        "task_status": result.get("task_status"),
        "stop_reason": result.get("stop_reason"),
        "turns": result.get("turns"),
        "child_id": result.get("child_id"),
        "output": output,
        "completion_bullets": result.get("completion_bullets", []),
        "limitations": result.get("limitations", []),
        "artifacts": result.get("artifacts", []),
        "error": result.get("error"),
        "reworked_for": list(findings or ()),
        "problems": problems,
        # The raw response is kept whatever the verdict: a rejected stage is
        # evidence about the run, not something to discard.
        "raw_final_message": result.get("final_message"),
    }
    written = sop_write_stage(run_id, role, record, document=document, task_sha256=digest)
    if written["state"] == "complete" and role in ROLE_REQUIRES_DOCUMENT:
        if not sop_document_ok(run_id, role, written):
            written["state"] = "incomplete"
            written["problems"] = list(written.get("problems") or ()) + [
                f"{role} produced no document at {sop_stage_path(run_id, role, 'md')}"
            ]
            sop_write_stage(run_id, role, written, task_sha256=digest)
    return written


def sop_verdict(record):
    """Read the validator's verdict as (verdict, send_back_to, findings).

    A validator that returns something unparseable is treated as a failure to
    validate, not as a pass: the pipeline stops rather than shipping unchecked.
    """
    output = record.get("output") if isinstance(record, dict) else None
    if not isinstance(output, dict):
        return "fail", None, ["validator returned no structured output"]
    verdict = str(output.get("verdict") or "").strip().lower()
    if verdict not in VALID_VERDICTS:
        return "fail", None, [f"validator returned an unknown verdict {verdict!r}"]
    findings = output.get("findings")
    if isinstance(findings, str):
        findings = [findings]
    elif not isinstance(findings, list):
        findings = []
    findings = [str(item) for item in findings if str(item).strip()]
    target = output.get("send_back_to")
    target = str(target).strip() if target else None
    if verdict == "pass":
        return "pass", None, findings
    if target not in REWORKABLE_ROLES:
        target = "modeler"
    return verdict, target, findings or ["validator reported no specific finding"]


# --------------------------------------------------------------- rollbacks


def sop_archive_stage(run_id, role, event_id):
    """Copy one stage's files into history/ and prove the copy landed.

    Returns the archived entries. Raises on any failure: losing the superseded
    version while claiming to have archived it is worse than refusing the
    rollback, because the audit trail would then be silently wrong.
    """
    host = sop_sdk()
    archived = []
    for suffix in STAGE_SUFFIXES:
        source = sop_stage_path(run_id, role, suffix)
        body = sop_read_text(source)
        if body is None or not body.strip():
            continue
        slug = _SLUG_UNSAFE.sub("-", role.lower())
        target = sop_contained_path(
            run_id, "history", event_id, f"{sop_stage_index(role):02d}-{slug}.{suffix}"
        )
        host.write_file(target, body)
        readback = sop_read_text(target)
        if readback != body:
            raise RuntimeError(
                f"archiving {source} to {target} could not be verified; rollback aborted"
            )
        archived.append(
            {
                "role": role,
                "from": source,
                "archived_to": target,
                "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest()[:16],
                "bytes": len(body.encode("utf-8")),
            }
        )
    return archived


def sop_verify_archive(entry):
    """Re-hash one archived history file against its recorded digest and size."""
    if not isinstance(entry, dict):
        return ARCHIVE_MISSING, "rollback archive entry is not an object"
    target = entry.get("archived_to")
    if not target:
        return ARCHIVE_MISSING, "rollback archive entry names no file"
    body = sop_read_text(target)
    if body is None:
        return ARCHIVE_MISSING, f"archived file {target} is gone"
    claimed = entry.get("sha256")
    if not claimed:
        return ARCHIVE_UNHASHED, f"archive entry for {target} carries no sha256"
    actual = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    if actual != claimed:
        return ARCHIVE_HASH_MISMATCH, (
            f"archived file {target} hashes to {actual} but the manifest claims "
            f"{claimed}"
        )
    claimed_bytes = entry.get("bytes")
    actual_bytes = len(body.encode("utf-8"))
    if isinstance(claimed_bytes, int) and claimed_bytes != actual_bytes:
        return ARCHIVE_SIZE_MISMATCH, (
            f"archived file {target} is {actual_bytes} bytes but the manifest "
            f"claims {claimed_bytes}"
        )
    return ARCHIVE_OK, None


def sop_inspect_history(run_id, report=None):
    """Audit every rollback archive claimed by a run manifest without repair."""
    if report is None:
        report = sop_inspect_manifest(run_id)
    manifest = report.get("manifest") or {}
    events = manifest.get("rollbacks")
    if not isinstance(events, list):
        events = []
    archives = []
    problems = []
    for event in events:
        if not isinstance(event, dict):
            problems.append("rollback event is not an object")
            continue
        entries = event.get("archived")
        if not isinstance(entries, list):
            problems.append(
                f"rollback event {event.get('event_id')!r} has no archive list"
            )
            continue
        for entry in entries:
            state, detail = sop_verify_archive(entry)
            archives.append(
                {
                    "event_id": event.get("event_id"),
                    "role": entry.get("role") if isinstance(entry, dict) else None,
                    "archived_to": (
                        entry.get("archived_to") if isinstance(entry, dict) else None
                    ),
                    "state": state,
                    "detail": detail,
                }
            )
            if state != ARCHIVE_OK:
                problems.append(detail or state)
    if problems:
        state = HISTORY_CORRUPT
    elif archives:
        state = HISTORY_OK
    else:
        state = HISTORY_EMPTY
    return {
        "run_id": run_id,
        "state": state,
        "events": len(events),
        "archives": archives,
        "problems": problems,
    }


def sop_clear_from(run_id, role, findings=None):
    """Archive *role* and everything downstream, then clear them for a redo.

    The previous implementation wrote an empty string over each file and
    recorded only the path, which destroyed the superseded model assumptions,
    experiment results and the pre-rejection version of the work. Recording a
    path is not preserving evidence. Everything is archived under
    ``history/<event id>/`` and verified before anything is cleared, and any
    failure aborts the rollback instead of being swallowed.
    """
    import datetime

    host = sop_sdk()
    inspection = sop_inspect_manifest(run_id)
    if inspection["state"] != MANIFEST_VALID:
        raise ValueError(
            f"cannot roll back run {run_id}: manifest is {inspection['state']}"
        )
    manifest = inspection["manifest"]
    events = manifest.get("rollbacks")
    if not isinstance(events, list):
        events = []
    event_id = f"rollback-{len(events) + 1:03d}"

    downstream = ROLE_ORDER[ROLE_ORDER.index(role):]
    archived = []
    for target_role in downstream:
        archived.extend(sop_archive_stage(run_id, target_role, event_id))

    cleared = []
    for target_role in downstream:
        for suffix in STAGE_SUFFIXES:
            path = sop_stage_path(run_id, target_role, suffix)
            if sop_read_text(path) is None:
                continue
            host.write_file(path, "")
            cleared.append(path)

    events.append(
        {
            "event_id": event_id,
            "from_role": role,
            "archived": archived,
            "cleared": cleared,
            "findings": list(findings or ()),
            "model_fingerprint": manifest.get("model_fingerprint"),
            "at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
    )
    manifest["rollbacks"] = events
    sop_write_manifest(run_id, manifest)
    return {"event_id": event_id, "archived": archived, "cleared": cleared}


# ------------------------------------------------------------------ status


def sop_status(run_id):
    """What is on disk for one run. Runs nothing."""
    report = sop_inspect_manifest(run_id)
    manifest = report["manifest"] or {}
    digest = manifest.get("task_sha256")
    history = sop_inspect_history(run_id, report=report)
    stages = []
    for role in ROLE_ORDER:
        record = sop_read_stage(run_id, role, digest) if digest else None
        document_state, document_detail = sop_document_state(
            run_id, role, sop_stored_stage(run_id, role)
        )
        stages.append(
            {
                "role": role,
                "stage": sop_stage_index(role),
                "complete": record is not None,
                "task_status": (record or {}).get("task_status"),
                "document": sop_stage_path(run_id, role, "md"),
                "document_state": document_state,
                "document_problem": document_detail,
            }
        )
    done = [stage for stage in stages if stage["complete"]]
    return {
        "run_id": run_id,
        "manifest_state": report["state"],
        "manifest_reason": report["reason"],
        "manifest": manifest or None,
        "history_state": history["state"],
        "history_problems": history["problems"],
        "history": history,
        "stages": stages,
        "completed": len(done),
        "next_role": next(
            (stage["role"] for stage in stages if not stage["complete"]), None
        ),
    }


def sop_normalise_roles(roles):
    """Validate ``roles`` as a unique, order-preserving subsequence of ROLE_ORDER.

    An arbitrary list is not a pipeline. ``["paper-writer", "literature-surveyor"]``
    would have run the writer before anything existed for it to write about, and
    a repeated role would have overwritten its own stage mid-run.
    """
    if roles is None:
        return ROLE_ORDER
    pipeline = tuple(roles)
    if not pipeline:
        raise ValueError("roles must not be empty")
    unknown = [role for role in pipeline if role not in ROLE_ORDER]
    if unknown:
        raise ValueError(f"unknown role(s): {unknown}")
    if len(set(pipeline)) != len(pipeline):
        raise ValueError(f"roles must not repeat: {list(pipeline)}")
    positions = [ROLE_ORDER.index(role) for role in pipeline]
    if positions != sorted(positions):
        raise ValueError(
            f"roles must follow pipeline order {list(ROLE_ORDER)}; got {list(pipeline)}"
        )
    return pipeline


def orchestrate_research(
    task,
    *,
    resume=True,
    max_rollbacks=2,
    retries=1,
    roles=None,
    run_id=None,
    on_incompatible="fork",
):
    """Run the five-role pipeline over ``task`` and return a run report.

    Every run is bound to its research question, its pipeline version and its
    role prompts. Resuming continues the latest branch of the same question, or
    an explicit ``run_id``; a different question, a different pipeline or a
    damaged manifest never silently reuses stored stages.

    ``status`` is honest about what actually ran:

    - ``complete`` — every role in ``ROLE_ORDER`` ran, the validator passed, and
      the paper document exists;
    - ``partial``  — only some roles ran;
    - ``unresolved`` — the validator did not pass within ``max_rollbacks``;
    - ``blocked``  — a stage failed to complete.

    ``validator`` is None unless the validator actually ran, and ``paper`` is
    None unless the document exists and is non-empty.
    """
    if not str(task or "").strip():
        raise ValueError("orchestrate_research: task must be a non-empty string")
    pipeline = sop_normalise_roles(roles)

    manifest, resumed = sop_resolve_run(
        task, resume=resume, run_id=run_id, on_incompatible=on_incompatible
    )
    active_run = manifest["run_id"]
    digest = manifest["task_sha256"]

    def report(status, stages, rollbacks, validator, findings):
        completed = {s["role"] for s in stages if s.get("state") == "complete"}
        paper_ready = "paper-writer" in completed and sop_document_verified(
            active_run, "paper-writer"
        )
        return {
            "status": status,
            "run_id": active_run,
            "manifest": sop_manifest_path(active_run),
            "task": task,
            "task_sha256": digest,
            "resumed": resumed,
            "parent_run_id": manifest.get("parent_run_id"),
            "lineage": manifest.get("lineage") or [],
            "pipeline": list(pipeline),
            "stages": stages,
            "rollbacks": rollbacks,
            "validator": validator,
            "paper": sop_stage_path(active_run, "paper-writer", "md") if paper_ready else None,
            "findings": findings,
        }

    rollbacks = 0
    findings = []
    pending = {}
    stages = []
    validator_verdict = None
    index = 0
    while index < len(pipeline):
        role = pipeline[index]
        record = sop_read_stage(active_run, role, digest) if resume else None
        if record is None:
            record = sop_run_role(
                active_run, task, role,
                findings=pending.pop(role, None), retries=retries, task_sha256=digest,
            )
        stages.append(
            {
                "role": role,
                "stage": sop_stage_index(role),
                "state": record.get("state"),
                "task_status": record.get("task_status"),
                "problems": record.get("problems") or [],
                "document": sop_stage_path(active_run, role, "md"),
            }
        )
        if record.get("state") != "complete":
            return report(
                "blocked", stages, rollbacks, validator_verdict,
                [f"stage {role} did not complete"] + list(record.get("problems") or ()),
            )
        if role == "validator":
            verdict, target, reported = sop_verdict(record)
            validator_verdict = verdict
            findings = reported
            if verdict != "pass":
                if rollbacks >= max_rollbacks or target not in pipeline:
                    return report("unresolved", stages, rollbacks, verdict, reported)
                rollbacks += 1
                sop_clear_from(active_run, target, findings=reported)
                pending[target] = reported
                index = pipeline.index(target)
                stages = [s for s in stages if s["stage"] < sop_stage_index(target)]
                validator_verdict = None
                continue
        index += 1

    completed = {s["role"] for s in stages if s.get("state") == "complete"}
    if not set(ROLE_ORDER) <= completed:
        return report("partial", stages, rollbacks, validator_verdict, findings)
    if validator_verdict != "pass":
        return report("unresolved", stages, rollbacks, validator_verdict, findings)
    paper_state, paper_problem = sop_document_state(
        active_run, "paper-writer", sop_stored_stage(active_run, "paper-writer")
    )
    if paper_state != DOCUMENT_OK:
        return report(
            "blocked", stages, rollbacks, validator_verdict,
            findings + [
                f"paper-writer stage document is {paper_state}"
                + (f": {paper_problem}" if paper_problem else "")
            ],
        )
    return report("complete", stages, rollbacks, validator_verdict, findings)
