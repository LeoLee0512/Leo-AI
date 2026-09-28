---
name: research-sop
description: Run a research question through a five-role pipeline — literature surveyor, modeler, numerical experimenter, validator, paper writer — where each role is a sub-agent that hands a checked artifact to the next and the validator can send work back. Use for open-ended research tasks that need modelling, numerical experiments and a written result, not for one-shot questions.
origin: leo
license: MIT
---

# Research SOP — a five-role research pipeline

A research question that needs a model, numbers, and a write-up is not one task. It is five, and they fail in different ways: a survey that cites papers nobody checked, a model whose assumptions were never stated, an experiment whose convergence was never tested, a draft that quietly promotes a preliminary number into a claim. Running them as one long conversation lets each failure hide inside the next stage's output.

This skill runs them as five sub-agents. Each one gets only what it needs, produces one file with a fixed shape, and hands that file forward. Because every handoff is a file on disk, a reviewer — or the next run — can read exactly what stage 3 believed when stage 4 started.

## The pipeline

```
literature-surveyor → modeler → numerical-experimenter → validator → paper-writer
                          ↑                    │
                          └──── send back ─────┘
```

| Role | Owns | Reads | Writes |
|---|---|---|---|
| `literature-surveyor` | What is already known, with resolvable citations | the research question | `01-literature-surveyor.md` + `.json` |
| `modeler` | Governing equations, assumptions, boundary/initial conditions, dimensional analysis | survey + question | `02-modeler.md` + `.json` |
| `numerical-experimenter` | A runnable solver, the runs, the raw results | model spec | `03-numerical-experimenter.md` + `.json` + code + data |
| `validator` | Whether any of it holds up | model + code + results | `04-validator.md` + `.json` |
| `paper-writer` | The document a reader actually gets | everything upstream | `05-paper-writer.md` + `.json` |

All five live in one run directory, `research-runs/<run_id>/`, next to the
`manifest.json` that binds them to the research question.

`kernel.py` provides `orchestrate_research(task)`, which runs this whole chain through `host.delegate`, plus `sop_status(run_id)` and `sop_list_runs()`. It is auto-loaded; if `orchestrate_research` is not in `dir()`, read this skill's `kernel.py` and exec it.

## Running it

```python
result = orchestrate_research(
    "Where does the error in a PINN solution of the 2-D heat equation actually come from?",
    max_rollbacks=2,
)
print(result["status"], [s["role"] for s in result["stages"]])
```

### Runs are bound to their research question

Every call resolves to a run directory whose id is derived from a hash of the
task text, and writes a `manifest.json` recording `task_text`, `task_sha256`,
`pipeline_version`, `role_prompt_hashes`, `model_fingerprint`, `created_at` and
`parent_run_id`. Resuming is therefore only ever possible **within the same
question**:

- same task → stages already marked `complete` are reused, nothing is re-run;
- different task → a new run, always. One study can never be handed another
  study's evidence;
- `resume=False` → a deliberate rework: a **new** run whose manifest records
  `parent_run_id`. The earlier attempt is left intact, because deleting a
  previous run destroys the audit trail.

`sop_status(run_id)` reports what is on disk without running anything, and
`sop_list_runs()` lists every run with a readable manifest.

The status this returns is about what actually ran, not about how far the
function got:

| `status` | means |
|---|---|
| `complete` | every role in `ROLE_ORDER` ran **and** the validator passed |
| `partial` | only some roles ran (for example a `roles=` subset) |
| `unresolved` | the validator did not pass within `max_rollbacks` |
| `blocked` | a stage failed to complete |

`validator` is `None` unless the validator actually ran, and `paper` is `None`
unless the paper-writer actually produced its document. A subset run does not
report a validated paper it never wrote.

### What makes a stored stage trustworthy

Path separation alone is not an evidence chain. A stage is only read back as
evidence when all of the following hold, and each of these was a real hole:

| check | what it stops |
|---|---|
| manifest is `valid`, not `corrupt` | a damaged manifest being treated as absent, rebuilt in place, and the stages beside it adopted as this task's results |
| `record.run_id` and `record.task_sha256` match **exactly** | an unbound or hand-placed stage counting as a completed result |
| `task_status` / `error` / `stop_reason` all indicate success | a delegate that failed being recorded as `complete` because it returned some output |
| output revalidated locally against `ROLE_OUTPUT_SCHEMA` | trusting the runtime to have enforced the schema; a modeler with no equations passing through |
| the contracted document exists and is non-empty | a `paper` path pointing at a file that was never written |
| `pipeline_version`, `role_order` and `role_prompt_hashes` match | mixing results produced by two different methods under one run |

A manifest is classified `missing` / `valid` / `corrupt` / `incompatible`.
`corrupt` fails closed and the original bytes are left untouched; `incompatible`
forks a new run recording `parent_run_id` (or refuses, with
`on_incompatible="fail"`).

### A missing artifact means re-run that stage

If a stage's record or its contracted document is gone, that stage is no longer
complete — and the correct response is to **run it again and produce a real new
artifact**, not to report the run as having no paper. Upstream stages that are
still valid are not re-run; recovery is scoped to what actually broke.

`paper=None` is the honest answer only when the writer genuinely produced no
document. It is not the definition of successful recovery, and a run that
answered `None` where it could have re-run would be a run that lost the ability
to finish the work. What must never happen is the other direction: a `paper`
path pointing at a file that is not there.

If the re-run cannot write its document, `sop_write_stage` reads it back, fails
to verify it and raises. The run stops rather than returning a claim.

### A changed prompt makes an old run incompatible, not invalid-and-gone

Editing `ROLE_MISSIONS` changes `role_prompt_hashes`, and every run recorded
under the old prompts is then a run of a different method. Three things hold at
once, and they are easy to confuse:

- **its bytes survive** — nothing is deleted, overwritten or rewritten;
- **it stays auditable** — `sop_inspect_manifest` and `sop_list_runs` still
  return its manifest, labelled `incompatible` with the reason;
- **it is not evidence for the new pipeline** — `sop_read_manifest` returns
  `None`, and its stages are never adopted by the new run.

`sop_read_manifest` is the "is this valid for the pipeline I am running now"
door, so `None` there is correct and is not a claim that the run is missing or
damaged. `incompatible` and `corrupt` are deliberately different states: one is a
run of another method, the other is damage.

### Rollback preserves what it supersedes

When the validator sends work back, every affected stage is copied to
`history/rollback-NNN/` and the copy is read back and hashed **before** anything
is cleared. If archiving fails the rollback aborts. The manifest records the
archived path, its SHA-256, the validator's findings, the timestamp and the model
fingerprint. Writing an empty file over a stage and noting its path is not
preserving evidence, which is what the previous version did.

### Choosing a run

```python
orchestrate_research(task)                      # continue the latest branch
orchestrate_research(task, run_id="a1b2…")      # continue exactly this run
orchestrate_research(task, resume=False)        # rework: new branch, old kept
sop_run_lineage(run_id)                         # walk back through parents
sop_list_runs()                                 # every run, including damaged ones
```

`roles=` must be a unique, order-preserving subsequence of `ROLE_ORDER`; an
arbitrary list is not a pipeline.

Nothing here pins the domain. Fluid mechanics, PINNs, heat transfer, materials — the roles are the same; the domain knowledge arrives through the task text, through whatever domain skill is loaded alongside, and through the surveyor's retrieval.

## Role contracts

Each role's request is assembled by `sop_role_prompt` from the definitions in `kernel.py`. The contract each sub-agent is held to:

**literature-surveyor.** Retrieve before writing. The `literature-review` skill is the tool for this — `search_openalex`, `crossref_lookup`, `expand_citations`, `verify_dois`. If a `local-literature-rag` index exists, search it first (the user's own library is the most relevant corpus and costs nothing), then go to the live sources for anything it does not cover. Output is a synthesis with inline DOI links, a list of what is established, what is contested, and where the gap this task sits in actually is. A DOI that was not resolved is not a citation.

**modeler.** Turn the question into something solvable. State the governing equations, every assumption and what it buys, the domain and boundary/initial conditions, the non-dimensional groups, and the expected regimes. Name the assumptions most likely to break first — the validator will come looking for exactly this list. No code here; the deliverable is a specification a competent numericist could implement without asking follow-up questions.

**numerical-experimenter.** Implement and run. Discretisation and solver choice with a reason attached, a convergence study (grid/timestep/iteration as applicable), error metrics against an analytical solution or a benchmark where one exists, and a seed for anything stochastic. Save the code and the result data as artifacts (`host.save_artifact`) so they are versioned. Report what actually ran, including the runs that failed.

**validator.** Try to break it. Check the model against the survey, the implementation against the model, the numbers against the claims. Re-derive at least one result independently — a limiting case, a conservation check, an order-of-magnitude estimate. Confirm the code reruns and reproduces its reported numbers. The output carries `verdict` ∈ `pass` | `revise` | `fail`, and when it is not `pass`, `send_back_to` naming the role that must redo its stage, plus what specifically was wrong. Passing something through to keep the pipeline moving is the one failure mode this role cannot have.

**paper-writer.** Write the document. Prose paragraphs that each open on a claim and spend citations backing it, not an annotated bibliography. Methods precise enough to reproduce. Results with the uncertainty attached. A limitations section that names the assumptions the validator flagged, whether or not they were resolved. Cite as `[Author Year](https://doi.org/10.xxxx/xxxxxx)` and carry through only DOIs the surveyor actually resolved.

## The experiment environment

This section is for the `numerical-experimenter`, and it is the one place where a role has repeatedly wasted an entire run.

The runtime already ships a scientific stack: `numpy`, `scipy`, `pandas`, `matplotlib`, `sklearn`, `sympy`, `statsmodels`, `networkx`, `numba`, `h5py`, `plotly`, `seaborn`. Finite differences, finite volumes, a small FEM assembly, spectral methods, a small PINN trained with an explicit optimiser, least-squares and regression fits, symbolic derivation of an exact solution to compare against — all of that is reachable with what is already installed. Start there. Do not install a heavy framework on the fly.

`torch` and `jax` are **not** installed. If a deep-learning framework is genuinely required — not "would be convenient", required — install the CPU build explicitly:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

Never `pip install torch` on its own: the default index serves the CUDA wheel, which drags in `nvidia-cudnn` and the CUDA toolkit, runs to several gigabytes, and has taken longer than ten minutes without finishing on a task whose experiment fit comfortably on a CPU.

And note where the install lands. The kernel runs inside a sandbox, so anything `pip` writes goes to a throwaway `site-packages` that disappears when the task ends. A run-time install of a large framework is not merely slow — it buys nothing that survives the run, and the next run pays for it again.

The experimenter's first objective is the smallest reproducible experiment that confirms or falsifies the modeler's hypothesis, not a full training run. So when an experiment as conceived would need gigabytes of dependencies, **downgrade the experiment** rather than stopping to install: compare against an analytical or manufactured solution, do a truncation-error and convergence-order analysis, look at residual distribution statistics, shrink the network to something an explicit `numpy`/`scipy` optimiser can train. A lighter experiment that actually ran and reported an order of convergence is worth more to the validator than a heavier one that never started. Report the downgrade and its reason in the stage file; that is a result about the experiment's design, not a failure to hide.

## The send-back loop

When the validator returns `verdict != "pass"` with a `send_back_to`, `orchestrate_research` deletes that stage and everything downstream of it, then re-runs from there with the validator's findings appended to the role's request. This repeats up to `max_rollbacks` (default 2). After that the run finishes with `status="unresolved"` and the outstanding findings recorded — an honest unresolved result, not a silently downgraded pass.

The rollback is what makes the pipeline worth its overhead. A validator that can only comment is a reviewer nobody has to listen to.

## Budget and depth

Each child runs with a `max_turns` ceiling (`ROLE_MAX_TURNS`, per role) so a stuck sub-agent cannot burn the session, and with `retries=1` so one transient failure re-runs with its own limitations appended rather than collapsing the chain. Delegation depth is capped at 4 by the runtime and `orchestrate_research` itself occupies one level, so a role that wants its own fan-out has three levels left — plenty for a parameter sweep, not enough for a role to re-enter this whole pipeline. Do not call `orchestrate_research` from inside one of its own children.

## What must not happen

The pipeline produces a document with citations and numbers in it, which is exactly the shape of output that is most damaging when it is invented. Every DOI resolves or it does not appear. Every number in the paper traces to a run that happened, in a file that exists. A stage that could not be completed is reported as incomplete — `status="unresolved"` with the reason — and never papered over by the next stage writing around the hole.
