# Research-SOP migration audit for `24f3fd7`

Date: 2026-09-05

## Scope and method

The source commit `24f3fd7` was audited against mainline HEAD `d58dffe` from
their merge base `58aeb19`. It was not merged or cherry-picked. The mixed
commit was decomposed so each production guarantee and its tests can be
reviewed independently.

| Contract | Disposition | Mainline commit |
|---|---|---|
| F-007 manifest self-consistency | migrated with focused and mutation tests | `e92fa81` |
| F-001 document digest verification on read | migrated with focused and mutation tests | `3e809f2` |
| F-002 rollback archive verification on audit | migrated with focused and mutation tests | `8084078` |
| B08 attempt identity | implemented as a separate contract and test | `ad11801` |
| F-008 `theme-src` architecture | not migrated | deferred |

## B07 external-test disposition

The frozen external `test_B07_modify_history_file` is structurally invalid and
is retained unchanged as an external-test record. Its final branch raises when
the archived manifest digest equals the digest of the saved pre-tamper bytes:

```python
if claimed == sha256(original):
    raise AssertionError(...)
```

That equality is true by construction for a correct archive: `claimed` was
recorded from `original` before the test appends `FORGED`. It is independent of
whether production detects the later tamper, so no production implementation
can satisfy the final assertion without corrupting the archive contract.

Production was not changed to accommodate that assertion. F-002 instead tests
the valid property directly: after a length-preserving rewrite, append,
deletion, or digest removal, `sop_inspect_history` and `sop_status` report the
archive as corrupt; intact and restored bytes report clean.

## B08 contract correction

Attempt identity and artifact identity are distinct:

- every execution of a stage receives a new opaque `attempt_id`;
- deterministic reruns may produce byte-identical artifacts and therefore the
  same `document_sha256`;
- scientific documents must never be edited merely to manufacture different
  evidence bytes.

The focused B08 test forces a real paper-writer rerun, proves that the two
`attempt_id` values differ, and simultaneously proves that identical document
bytes and digests remain valid.

## F-008 overlap and conflict audit

The current Ink Autumn hierarchy is the accepted canonical source for its own
theme assets:

- `stage/themes.json`;
- `stage/backgrounds/manifest.json` and the three rendered WebP files;
- untouched masters under `assets/backgrounds/`;
- `tools/build_backgrounds.py` and `tools/bundle_theme.py` as the recorded
  build chain.

The proposed `theme-src` tree in `24f3fd7` re-declares `themes.json` and the
background manifest with byte-identical Git blobs, references the same three
rendered backgrounds through a separate asset house, adds a second assembler
(`tools/build_theme.py`), and rewires `tools/build_launcher.ps1` around that
assembler. Migrating it now would create overlapping canonical sources and two
competing assembly paths.

The existing provenance measurement currently reports 8 of 18 runtime-read
theme assets with tracked canonical sources, 10 pre-existing gaps, and one
deployed `shell.html` drift. F-008 therefore remains open. Its brand-asset gaps
may be addressed later, but only after choosing an architecture compatible with
the frozen Ink Autumn hierarchy.

No Ink Autumn image, stylesheet, registry, manifest, master, or build recipe was
modified during this research-sop migration. Its status remains ACCEPTED &
FROZEN.
