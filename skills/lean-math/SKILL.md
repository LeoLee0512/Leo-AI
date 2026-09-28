---
name: lean-math
description: Compile Lean 4 proofs against Mathlib, locate every error by line and column with the goal state Lean printed, and look up whether a theorem actually exists. Use whenever a proof, a formalisation, or a "what is this lemma called" question needs a machine-checked answer instead of a plausible one.
origin: leo
license: MIT
---

# Lean 4 + Mathlib

A proof either compiles or it does not, and the compiler is right. That makes this the rare place where an agent can be *certain* — and the rare place where sounding right and being right diverge completely. Every claim this skill makes about Lean has to come from a run that happened.

Lean 4 and a built Mathlib are located at run time, never assumed. `kernel.py` wraps them and is auto-loaded; if `lean_check` is not in `dir()`, read this skill's `kernel.py` and exec it.

Call `lean_toolchain_status()` before anything else. It reports one of `READY` / `NOT_INSTALLED` / `PROJECT_NOT_READY` / `VERSION_MISMATCH` together with a summary saying how to fix it, and it never installs anything: a Lean plus Mathlib toolchain is several gigabytes and that is the user's decision. Resolution order is configuration first (`LEO_LEAN_TOOLCHAIN`, `LEO_LEAN_PROJECT`, `LEO_MATHLIB_DIR`), then an elan install under the home directory, then `lean`/`lake` on PATH.

## Compiling a proof

```python
result = lean_check("""
example (a b : Nat) : a + b = b + a := by
  exact Nat.add_comm a b
""")
result["ok"]        # True only if Lean reported no error and no `sorry`
result["elapsed"]   # ~30 s with the full Mathlib import
```

`import Mathlib` is prepended when the snippet has no import of its own, so a snippet's own line numbers stay meaningful; `header_lines` tells you the offset when they were added. Pass `imports="Mathlib.Tactic.NormNum"` (or a list) to import less and finish faster — the import, not the proof, is what costs the 30 seconds; that one narrowing measured 9.3 s against 28.1 s for full Mathlib.

**`ok` is computed from the diagnostics, never from the exit code.** This matters: `lake env lean` exits 0 on a file full of errors and writes them to stderr. `kernel.py` therefore calls `lean` directly with a prepared `LEAN_PATH`, reads its JSON diagnostics, and decides from those.

**A proof containing `sorry` is not ok.** `uses_sorry` is reported and `ok` is False unless you pass `allow_sorry=True` deliberately. Never tell the user a proof went through when a goal was admitted.

## Reading the error

Every diagnostic carries Lean's own position and message:

```python
for e in result["errors"]:
    print(e["line"], e["col"], e["message"])
    print(e["source"])   # the offending line, verbatim
    print(e["goal"])     # goal state, when Lean printed one
```

So the answer to "what's wrong" is "line 4, column 2: `No goals to be solved`, and here is the goal that was open" — not a guess about which tactic probably failed. `end_line`/`end_col` bound the span. `kind` is Lean's internal classification (`Tactic.unsolvedGoals` and friends), which is the reliable way to tell "the tactic block ended early" from every other error.

To inspect a goal without an error, use `lean_goal`:

```python
lean_goal("(a b : Nat) : a + b = b + a")                     # the initial goal
lean_goal("(a b : Nat) : a + b = b + a", "rw [Nat.add_comm]") # what is left after a step
```

It leaves the proof open on purpose so Lean prints the state. `closed=True` with `goals=None` means the tactics finished the proof — which is a useful answer too.

## Finding the theorem

Five tools, in increasing cost:

```python
lean_check_type("Nat.add_comm")   # "Nat.add_comm : ∀ (n m : ℕ), n + m = m + n", or None   ~5 s
lean_print("Nat.succ_le_of_lt")   # the full declaration                                    ~5 s
lean_exact("(a b : Nat) : a + b = b + a")     # ask exact? for a closing term              ~13 s
lean_loogle("Continuous ?f → Continuous ?g")  # online, via host.web_fetch                  ~1 s
lean_find("_ + 0 = _")            # search by statement shape — ~374 s, ~8 GB RSS
```

Those costs are measured on this machine, and the ordering matters. `#find` builds a discrimination tree over all of Mathlib on first use: `_ + 0 = _` took 374 s at roughly 8 GB RSS and returned 20 matches (capped). `lean_find` therefore carries its own 900 s timeout and returns `timed_out: True` rather than raising. Try `lean_exact` or `lean_loogle` first; spend `lean_find` only when the question is genuinely about statement *shape*.

`lean_check_type` returning `None` means **Mathlib has no declaration by that name**. Say so. A name that sounds like a Mathlib lemma, spelled in Mathlib's naming convention, is the single easiest thing to fabricate here and the hardest for the user to catch — the whole point of having a compiler in the loop is that you never have to.

`lean_exact` returns suggestions, not facts: compile the suggested term with `lean_check` before telling the user it works. `lean_loogle` goes over the network through `host.web_fetch` (raw sockets are denied in the kernel sandbox, and a `urllib` request would bypass the egress allowlist); treat a loogle hit as a lead and confirm it locally with `lean_check_type`.

## Coaching a proof

The pattern this skill is built for is a loop, not a single shot:

1. `lean_goal` on the statement — what actually has to be shown.
2. Propose one step. Explain why that step, in terms of the goal.
3. `lean_check` the partial proof. Report the exact line and column of whatever broke, plus the remaining goal.
4. When stuck on a lemma, try `lean_exact`/`lean_loogle` first (seconds) and `lean_find` only if the search is genuinely shape-based (minutes); confirm any name with `lean_check_type`.
5. Repeat until `ok` is True with `uses_sorry` False.

Report the compile result plainly each round. "This compiles" and "this fails at line 4" are both good answers; "this should work" is not one, because checking took thirty seconds and you had the option.

## Cost and mechanics

- ~30 s per check with the full Mathlib import; a narrowed import is substantially faster. `timeout` defaults to 300 s and returns `timed_out: True` rather than raising. `imports=` accepts either spelling — `"Mathlib.Tactic.NormNum"` and `"import Mathlib.Tactic.NormNum"` both produce a valid header, and so does a list of either.
- `LEAN_PATH` is resolved once (`lake env printenv LEAN_PATH`) and cached for the process; if Lake cannot run, the package layout is globbed instead, so a read-only project still works.
- Probe files are written to `lean-probes/` in the session workspace — the only writable location a kernel cell has. The discovered Lake project and Mathlib directory are read, never modified.
- `elan default` is never called: the toolchain was unpacked from a tarball rather than installed through elan, so `elan` would try to reach the network and fail. Absolute toolchain paths are used throughout.
- `lean_toolchain_status()` reports what is present without compiling anything — run it first when something looks wrong.
