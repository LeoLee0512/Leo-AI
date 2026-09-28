# P0 runtime remediation and current evidence — 2026-09-08

This report describes the isolated remediation worktree derived from inherited snapshot `7c7a6b1`, not the deployed application. Historical P0 reports/checklist and rollback files were restored byte-for-byte from `a4455cc32dccbcf26bdc9c65b0e5df94b6cbf4b4`; their old verdicts are historical evidence, not current results. No historical report, scientific specification, Constitution, installed application, user credential, or upstream checkout was rewritten.

## Current P0 assessment

| Gate | Current status | Evidence and limit |
|---|---|---|
| P0-1 single trusted source / deployment provenance | FAIL | `python tools/verify_release.py --strict` exits 1: no `manifests/build-current.json` in this worktree. No current build/deployment manifest binds this source to an installed release. No release was built or deployed here. |
| P0-2 research-sop evidence integrity | PASS for automated current behavior | Restored research-sop tests pass within the 584-pass regression; all registered reconstructed cases remain. Reviewer-original independent suite remains ABSENT/NOT PROVIDED in restored `manifests/test-suites.json`. Real-model five-role acceptance E1–E3 was NOT-RUN, so this is not a live-model acceptance claim. |
| P0-3 visible UI / ShellApi consistency | PARTIAL | Source contract tests and all 4 real Chromium theme-picker cases pass, including both locales, save, new SettingsStore reconstruction, reload, and credential-write exclusion. Installed EXE/WebView2 visible-window acceptance was NOT-RUN. |
| P0-4 portability | PARTIAL | Scanner exits 0: 0 hard bindings, 1 configurable default, 3 explicitly visible exact-hash historical findings. A fresh Windows account, alternate/non-leo WSL, missing WSL and missing WebView2 scenarios are NOT-RUN. |
| P0-5 dependency/build reproducibility | PARTIAL | All 21 source wheel files matched the existing declared manifest before copy into ignored worktree `wheelhouse/`; destination hashes match, verifier reports 0 problems. Parent provisions isolated environment offline. Clean-machine/fresh-clone/two-build F1–F3 acceptance remains NOT-RUN. |
| P0-6 downstream development gate | FAIL | Existing P0 definitions require P0-4/P0-5 full acceptance; neither is PASS. Dependent product PINN/release work remains blocked. Independent diagnostics, oracle checks, and fail-closed repairs do not imply product acceptance. |

The unchanged checklist's 27 rows remain `NOT TESTED` (report vocabulary equivalent: NOT-RUN). Collector exit 0 and `suggested_verdict: PASS` never sign a checklist row. In particular the WebView2 collector suggests B1 and WSL collector suggests C5 only from observed prerequisites; this report does not adopt those suggestions as acceptance.

## Baseline and regression

All commands below used the original environment interpreter as an explicitly recorded test dependency: `../LeoAIStudio-build/.venv/Scripts/python.exe` (Python 3.12.9), with `cwd` at this isolated worktree. Parent separately provisions and validates the worktree's `.venv`.

| Command | Result | Raw evidence |
|---|---|---|
| `python -m pytest tests -q --tb=short --disable-warnings` after restoration and before repairs | 554 passed, 11 failed, 2 skipped, 34.07 s | `p0/restored-baseline-full.txt` |
| `python -m pytest tests -q -rs --tb=short --disable-warnings` after repairs | 584 passed, 0 failed, 1 skipped, 29.73 s | `p0/after-fixture-restoration-full.txt` |
| `python tools/build_wheelhouse.py verify` | exit 0; 21 wheels, 0 problems | `p0/wheelhouse-verify.txt` |
| `python tools/portability_check.py --json` | exit 0; hard 0, configurable 1, historical 3 | `p0/portability-scan.json` |
| `python tools/verify_release.py --strict` | exit 1; missing current build manifest | `p0/strict-deployment-verifier.txt` |
| `python tools/theme_asset_provenance.py --strict` | exit 1; 12/20 tracked assets, 8 gaps, 0 drift | `p0/theme-asset-provenance-strict.txt` |

The remaining skip is inherited `tests/test_ui_api_contract.py:163`: `entityLifecycle` is enabled, so the obsolete “data pane is hidden while backend absent” branch does not apply. Existing tests still require every enabled feature API to be implemented and correctly gated. Added EntityStore persistence, corrupt-byte preservation and revision-conflict cases verify current supported behavior. No skip/xfail, acceptance threshold change, test deletion, or failure-log replacement was introduced.

One initial `git apply --check` for the historical portability patch failed because current comment context differed; the check made no mutation. The known fix's classifier functions were then integrated precisely. One theme audit invocation incorrectly supplied unsupported `--json` and exited 2; its original output is retained as `p0/theme-asset-provenance.json`; the documented `--strict` invocation above is the actual audit result.

## Root causes addressed and exact ownership

1. **Deleted verification/evidence assets.** Restored 46 original files: all deleted tests and the renamed-away package-contract test, manual acceptance collectors, headless/theme utilities, P0/theme/migration documents and the suite registry. Restored 10 deleted `docs/rollback/` snapshots separately. Every exact source blob hash is recorded in restoration manifests; restored scientific failure evidence stays immutable.
2. **Lost historical-evidence classification.** `tools/portability_check.py` regains the prior `df5e4b2cc7aef7dd92eb609dad712fbdb2b34b7e` implementation; `manifests/portability-historical-evidence.json` and `tests/test_portability.py` restore that accepted revision exactly. The protected audit SHA-256 is `018ff149d95df09eafded81e0274ded0e4ba39fd3023039b9bb1b67883acf8cf`; exact path/hash/type/count matching is mandatory. No general governance/Markdown exclusion was added. Negative fixtures exercise changed bytes, changed path, forbidden runtime/build/deploy/config targets and wrong finding type.
3. **Personal machine path in current design.** `leo_shell/DESIGN.md` replaces one current LeoTree source location with `<LEOTREE_ROOT>`; implementation and locked scientific documents are unchanged.
4. **Dangling manual-acceptance references.** `tools/build_wheelhouse.py` and scanner documentation point back to restored `docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md`; verifier results remain explicitly distinct from clean-machine acceptance.
5. **Obsolete fixture protocol.** `tests/leo_shell/test_bridge_client.py` now scripts all five existing startup phases (stop, identity, compatibility, model selection, start), keeps the original secret-only-in-env assertions, applies argv secret exclusion across every phase, and adds three preparation-failure tests proving no daemon start occurs after failure.
6. **Obsolete unsupported-feature contract.** `tests/leo_shell/test_api.py` retains all 11 extension parameter cases; the four already implemented EntityStore APIs must return typed unavailable-store failure without paths. Six additional cases validate fresh API persistence, restore/forget revision guards, and preservation of corrupt bytes for all entity operations.
7. **Local preset schema evolution.** `tests/leo_shell/test_settings_store.py` retains exact cloud field sets; the one existing local preset must expose exactly one additional typed `requires_key: false` field and its fixed model/address/noneditable endpoint contract.
8. **Incomplete real DOM harness.** `tests/test_theme_settings_integration.py` extracts the actual production `setLocalModelAccess` dependency newly called by existing `loadPanelState`; no theme cards/state/persistence results are mocked and original three-theme/locale/reload assertions remain unchanged.

No application runtime production behavior was altered by this P0 subtask. Scientific governance implementation repairs are owned and reported separately in the main MVP report. The only production tooling behavior repair is the narrow hash-bound portability classifier restoration.

## Current environment observations and F-008

Read-only collectors observed the existing Windows account; system Evergreen WebView2 `152.0.4191.66`, fixed runtime `152.0.4191.53`; one installed WSL distribution `Ubuntu-24.04`; existing installed LeoAIStudio executable; and available local external build prerequisites. These facts do not simulate missing/fresh scenarios. A/B/C/F JSON files and their exact commands/exit codes are retained in `p0/collector-commands.json`.

F-008 remains OPEN: missing canonical tracked sources include font manifest, two i18n tables, four font files and one legacy hash-named icon (8/20 runtime-read assets). Twelve current source/deployed asset mappings match, including the three-layer injection bundle. No asset was imported or invented to hide this gap.

## Evidence manifests

External evidence root is the sibling `LeoAIStudio-pinn-evidence-20260908T120017Z` directory; paths below are relative to that root:

- `p0/restoration-manifest.json` — 46 exact-source blobs and SHA-256 values.
- `p0/rollback-restoration-manifest.json` — 10 immutable historical rollback files.
- `p0/historical-policy-restoration.json` — prior reviewed policy and unchanged protected-document identity.
- `p0/wheelhouse-copy-manifest.json` — exact 21-wheel source/destination identity.
- `p0/restored-baseline-command.json`, `p0/after-fixture-restoration-command.json` — actual interpreter, command, cwd and exit.
- `p0/audit-commands.json`, `p0/collector-commands.json` — audit/collector commands and exits; the corrected theme command is recorded above.

This report intentionally does not claim PINN MVP COMPLETE or P0 closure. Current-source automated integrity is much better evidenced; human/environment/deployment acceptance is still unresolved.
