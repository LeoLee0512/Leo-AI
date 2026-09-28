---
name: local-literature-rag
description: Search the user's own PDF library and answer from it with a filename + page citation for every claim. Use when the question is about what the papers in this library say — "what does my literature say about X", "which of my papers covers Y" — rather than what is published somewhere on the web.
origin: leo
license: MIT
---

# Local literature RAG

`web_search` and Crossref answer "what does the literature say". This skill answers a different question: **what do the papers this user actually keeps say** — the annotated, curated, already-read corpus that is usually more relevant than anything a fresh search returns, and that no web tool can see.

Everything here is local. No network call, no third-party service, no new dependency: text extraction reuses the bundled `pdf-explore` sidecar, retrieval is scikit-learn's TF-IDF plus cosine similarity, and the index is a JSON file in the session workspace.

## Where the library lives

Kernel cells can read the **session workspace** and nothing above it, so the library is a directory inside it — `literature/` by default. Put PDFs there (drag them into the workbench, download them into it, or materialise them from artifacts) and index:

```python
lit_index_build()                      # indexes ./literature
lit_index_build("papers/heat-transfer")  # or any workspace-relative directory
```

`.pdf` files go through `pdf_pages` so every citation carries the page a reader can turn to; `.md`, `.txt` and `.rst` are split on blank lines into pseudo-pages so their citations look the same.

## Searching

```python
hits = lit_search("误差来源 error decomposition", k=6)
# [{"file": "pinn_error.pdf", "page": 7, "score": 0.41, "text": "...", "chunk_id": 88}, ...]
```

For answering a question, `lit_context` is the one to call — it returns the passages already formatted with their citation markers and an instruction not to go beyond them:

```python
ctx = lit_context("What limits PINN accuracy on stiff problems?", k=6)
print(ctx["context"])
```

Then write the answer **from `ctx["context"]` only**, citing each claim as `[filename p.page]`. Quote enough of the passage that the user can check it against the page you named.

`lit_search(..., files="pinn")` restricts retrieval to filenames containing that substring — useful when the user says "in the Wang paper".

## When nothing matches

`lit_search` returns `[]` and `lit_context` returns a context block that says nothing matched. That is the answer: **say the library does not cover it**. Answering from parameter memory and attaching a citation from a file that does not support the claim is the single worst outcome this skill can produce — it is indistinguishable from a real answer and it is wrong. Offer to search the live literature (`literature-review`) instead.

The same rule applies to page numbers. Every `[file p.N]` you emit comes from a hit that `lit_search` returned. Never adjust, guess, or interpolate one.

## Chinese and English

`lit_analyzer` tokenizes Latin words normally and turns CJK runs into character unigrams *plus* bigrams, so `传热反问题` is retrievable without a segmenter and without adding `jieba`. Mixed-language libraries and mixed-language queries both work. The trade-off is honest: character bigrams are coarser than real word segmentation, so Chinese recall is good and Chinese precision is a little below what a segmenter would give.

## Incremental indexing

`lit_index_build()` fingerprints every file (sha256 + size + mtime). A file whose fingerprint is unchanged keeps its stored chunks and is never re-parsed; only new and modified files are extracted, and deleted files drop out. The returned report says exactly what happened:

```python
{"files": 41, "added": ["新论文.pdf"], "updated": [], "removed": [], "unchanged": 40, "chunks": 1187, ...}
```

`lit_index_build(rebuild=True)` forces a full re-parse. `lit_index_stats()` reports what is indexed without touching the library.

## Persistence

The index is written to `literature-index/index.json` in the workspace and registered as the artifact `leo-literature-index.json`. Workspaces are per session, so a later session picks it back up by version:

```python
lit_index_load("<version_id from the workbench artifact list>")
```

Same project only — that is the runtime's artifact isolation rule, not this skill's. Without a version id, `lit_index_load()` reads the workspace copy.

## Upgrading to semantic retrieval

TF-IDF matches terms, not meaning: a query phrased differently from the paper will miss, and that is the main reason to look past v1. `lit_encode` is the only place that has to change. Set `LIT_STATE["encoder"]` to a callable `(texts, fit) -> matrix` returning dense vectors — a sentence-transformer, an embedding endpoint — and `lit_search`, `lit_context` and the cache all become semantic with no other edit. The index format does not change, because chunks are stored as text and vectorized on load.
