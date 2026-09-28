"""
Local-literature-RAG helpers. Auto-loaded into the python kernel by the host
when the skill loads:

  lit_index_build, lit_index_load, lit_index_save, lit_index_stats,
  lit_search, lit_context, lit_analyzer, lit_encode, lit_extract, lit_chunk

Module top level is definition-only (functions, imports, literal constants) so
the sidecar structure gate accepts it.

This skill is purely local: it reads files from the session workspace and does
its own retrieval. It makes no network request, so there is no ``host.web_fetch``
here and no third-party service to declare. Text extraction reuses the bundled
``pdf-explore`` sidecar's ``pdf_pages`` rather than reimplementing PDF parsing;
retrieval is TF-IDF + cosine similarity from scikit-learn, which is already in
the runtime, so the skill adds no dependency.

Retrieval quality note: TF-IDF matches terms, not meaning. A query using
different words than the paper does will miss. ``lit_encode`` is the single
seam where that changes — set ``LIT_STATE["encoder"]`` to a callable returning
dense vectors and every search in this file becomes semantic with no other
edit.
"""

import hashlib
import json
import os
import re
import time

#: Where PDFs are expected, relative to the session workspace.
LIT_LIBRARY_DIR = "literature"
#: Where the index is written, relative to the session workspace.
LIT_INDEX_DIR = "literature-index"
LIT_INDEX_FILE = "literature-index/index.json"
#: Stable artifact filename, so a later session can materialise it by version.
LIT_ARTIFACT_NAME = "leo-literature-index.json"

LIT_INDEX_SCHEMA = 1

#: Target chunk size in characters, with an overlap so a sentence split across
#: a boundary is still retrievable from one side of it.
LIT_CHUNK_CHARS = 900
LIT_CHUNK_OVERLAP = 150
#: Chunks shorter than this are page furniture (headers, page numbers) and only
#: add noise to the term statistics.
LIT_MIN_CHUNK_CHARS = 80

LIT_TEXT_SUFFIXES = (".md", ".markdown", ".txt", ".rst")
LIT_PDF_SUFFIXES = (".pdf",)

#: Latin/number runs, CJK runs, and Japanese kana runs, tokenized separately.
LIT_TOKEN_PATTERN = re.compile(
    r"[A-Za-z][A-Za-z0-9_+\-.]*|\d+(?:\.\d+)?|[一-鿿㐀-䶿]+"
    r"|[぀-ヿ]+"
)
LIT_CJK_PATTERN = re.compile(r"[一-鿿㐀-䶿぀-ヿ]")

#: Process-lifetime cache: the loaded index, the fitted vectorizer, and the
#: document matrix. Keyed by index revision so a rebuild invalidates it.
LIT_STATE = {}


def lit_sdk():
    """Rebind-proof SDK handle — see pdf-explore/kernel.py:pdf_sdk."""
    import host

    return host


def lit_analyzer(text):
    """Tokenize mixed Chinese/English scientific text.

    Latin words and numbers become lowercased word tokens. CJK runs become
    character unigrams *and* bigrams, which is what makes Chinese retrievable
    without a segmenter: 「传热」 is matched as a bigram even though no
    whitespace ever separated it, and the unigrams keep single-character terms
    reachable. The cost is a larger vocabulary, which at library scale (a few
    thousand chunks) is irrelevant.

    Adding ``jieba`` would give cleaner Chinese tokens, but it is not in the
    runtime and the whole point of this skill is that it adds no dependency.
    """
    tokens = []
    for match in LIT_TOKEN_PATTERN.finditer(str(text or "")):
        token = match.group(0)
        if LIT_CJK_PATTERN.match(token):
            tokens.extend(token)
            tokens.extend(token[i : i + 2] for i in range(len(token) - 1))
        else:
            token = token.lower().strip("-._+")
            if len(token) >= 2:
                tokens.append(token)
    return tokens


def lit_encode(texts, *, fit=False):
    """Vectorize ``texts``. The seam a semantic encoder would replace.

    Default backend is TF-IDF over :func:`lit_analyzer`. Set
    ``LIT_STATE["encoder"]`` to a callable ``(texts, fit) -> matrix`` — a
    sentence-transformer, an embedding API through ``host.llm`` — and search
    becomes semantic with no other change. ``fit=True`` builds the corpus
    representation; ``fit=False`` encodes a query against the fitted one.
    """
    encoder = LIT_STATE.get("encoder")
    if callable(encoder):
        return encoder(texts, fit)
    from sklearn.feature_extraction.text import TfidfVectorizer

    if fit:
        vectorizer = TfidfVectorizer(
            analyzer=lit_analyzer, sublinear_tf=True, min_df=1
        )
        matrix = vectorizer.fit_transform(texts)
        LIT_STATE["vectorizer"] = vectorizer
        return matrix
    vectorizer = LIT_STATE.get("vectorizer")
    if vectorizer is None:
        raise RuntimeError("lit_encode: nothing fitted yet — call lit_search/lit_fit")
    return vectorizer.transform(texts)


def lit_fingerprint(path):
    """Content fingerprint of one library file, for incremental indexing."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    stat = os.stat(path)
    return {
        "sha256": digest.hexdigest(),
        "size": stat.st_size,
        "mtime": int(stat.st_mtime),
    }


def lit_library_files(source_dir=LIT_LIBRARY_DIR):
    """Every indexable file under ``source_dir``, as workspace-relative paths."""
    root = os.path.abspath(os.path.expanduser(source_dir))
    if not os.path.isdir(root):
        return []
    suffixes = LIT_PDF_SUFFIXES + LIT_TEXT_SUFFIXES
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if not name.startswith(".")]
        for name in sorted(filenames):
            if name.startswith("."):
                continue
            if not name.lower().endswith(suffixes):
                continue
            absolute = os.path.join(dirpath, name)
            found.append(os.path.relpath(absolute, root).replace(os.sep, "/"))
    return sorted(found)


def lit_extract(path):
    """Extract one document as ``[{"page": int, "text": str}, ...]``.

    PDFs go through the bundled ``pdf-explore`` sidecar (``pdf_pages``) so page
    numbers are the real ones a reader can turn to; plain-text files are split
    on blank lines into pseudo-pages so their citations stay uniform.
    """
    lower = path.lower()
    if lower.endswith(LIT_PDF_SUFFIXES):
        pages = None
        pdf_pages = globals().get("pdf_pages")
        if not callable(pdf_pages):
            import importlib

            pdf_pages = getattr(
                importlib.import_module("pdf-explore.kernel"), "pdf_pages"
            )
        pages = pdf_pages(path, mode="text")
        return [
            {"page": int(page.get("page", 0)), "text": str(page.get("text") or "")}
            for page in pages or []
        ]
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        body = handle.read()
    blocks = [block for block in re.split(r"\n{2,}", body) if block.strip()]
    return [{"page": index + 1, "text": block} for index, block in enumerate(blocks)]


def lit_chunk(text, page, *, size=LIT_CHUNK_CHARS, overlap=LIT_CHUNK_OVERLAP):
    """Split one page into overlapping chunks, each keeping its page number."""
    body = re.sub(r"[ \t]+", " ", str(text or "")).strip()
    if len(body) < LIT_MIN_CHUNK_CHARS:
        return []
    if len(body) <= size:
        return [{"page": page, "text": body}]
    step = max(1, size - overlap)
    chunks = []
    for start in range(0, len(body), step):
        piece = body[start : start + size].strip()
        if len(piece) >= LIT_MIN_CHUNK_CHARS:
            chunks.append({"page": page, "text": piece})
        if start + size >= len(body):
            break
    return chunks


def lit_index_path(source_dir=LIT_LIBRARY_DIR):
    """Absolute path of the library root for ``source_dir``."""
    return os.path.abspath(os.path.expanduser(source_dir))


def lit_index_build(source_dir=LIT_LIBRARY_DIR, *, rebuild=False, save=True):
    """Build or refresh the index over ``source_dir``. Incremental by default.

    A file whose sha256, size and mtime all match the stored fingerprint keeps
    its existing chunks and is never re-extracted; everything else is parsed
    again. ``rebuild=True`` discards the stored index first.

    Returns ``{"files", "added", "updated", "removed", "unchanged", "chunks",
    "index_path", "artifact"}``.
    """
    root = lit_index_path(source_dir)
    if not os.path.isdir(root):
        raise FileNotFoundError(
            f"lit_index_build: no library directory at {root!r}. Put the PDFs in "
            f"'{LIT_LIBRARY_DIR}/' inside this session's workspace, or pass "
            "source_dir=..."
        )
    previous = {} if rebuild else (lit_index_read() or {}).get("files", {})
    present = lit_library_files(source_dir)

    files = {}
    chunks = []
    added, updated, unchanged = [], [], []
    for relative in present:
        absolute = os.path.join(root, relative)
        try:
            fingerprint = lit_fingerprint(absolute)
        except OSError:
            continue
        record = previous.get(relative)
        reusable = (
            isinstance(record, dict)
            and record.get("sha256") == fingerprint["sha256"]
            and record.get("size") == fingerprint["size"]
            and isinstance(record.get("chunks"), list)
        )
        if reusable:
            file_chunks = record["chunks"]
            unchanged.append(relative)
        else:
            file_chunks = []
            for page in lit_extract(absolute):
                file_chunks.extend(lit_chunk(page["text"], page["page"]))
            (updated if relative in previous else added).append(relative)
        files[relative] = dict(fingerprint, pages=0, chunks=file_chunks)
        files[relative]["pages"] = len({item["page"] for item in file_chunks})
        for item in file_chunks:
            chunks.append(
                {
                    "id": len(chunks),
                    "file": relative,
                    "page": item["page"],
                    "text": item["text"],
                }
            )
    removed = sorted(set(previous) - set(files))

    index = {
        "schema": LIT_INDEX_SCHEMA,
        "revision": f"{int(time.time())}-{len(chunks)}",
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source_dir": source_dir,
        "files": files,
        "chunks": chunks,
    }
    LIT_STATE["index"] = index
    LIT_STATE.pop("matrix", None)
    LIT_STATE.pop("vectorizer", None)
    LIT_STATE.pop("fitted_revision", None)

    artifact = lit_index_save() if save else None
    return {
        "files": len(files),
        "added": added,
        "updated": updated,
        "removed": removed,
        "unchanged": len(unchanged),
        "chunks": len(chunks),
        "index_path": LIT_INDEX_FILE,
        "artifact": artifact,
    }


def lit_index_read():
    """Read the index from the workspace copy, or None when there is none."""
    if isinstance(LIT_STATE.get("index"), dict):
        return LIT_STATE["index"]
    try:
        with open(LIT_INDEX_FILE, "r", encoding="utf-8") as handle:
            index = json.load(handle)
    except (OSError, ValueError):
        return None
    if not isinstance(index, dict) or index.get("schema") != LIT_INDEX_SCHEMA:
        return None
    LIT_STATE["index"] = index
    return index


def lit_index_save():
    """Write the index to the workspace and register it as an artifact.

    The artifact is what survives the session: a later session can pull it back
    with ``lit_index_load(version_id)`` using the id shown in the workbench.
    Registration failing is not fatal — the workspace copy is still usable.
    """
    index = LIT_STATE.get("index")
    if not isinstance(index, dict):
        raise RuntimeError("lit_index_save: no index in memory — build or load first")
    os.makedirs(LIT_INDEX_DIR, exist_ok=True)
    with open(LIT_INDEX_FILE, "w", encoding="utf-8") as handle:
        json.dump(index, handle, ensure_ascii=False)
    try:
        return lit_sdk().save_artifact(LIT_INDEX_FILE, filename=LIT_ARTIFACT_NAME)
    except Exception as error:  # noqa: BLE001 - registration is best-effort
        return {"error": f"{type(error).__name__}: {error}"}


def lit_index_load(version_id=None):
    """Load the index: from the workspace, or from an artifact version.

    ``version_id`` materialises a previously saved index into this session
    (same project only, which is the runtime's rule, not this skill's).
    """
    if version_id:
        result = lit_sdk().materialise_artifact(version_id, filename=LIT_ARTIFACT_NAME)
        path = (result or {}).get("path") if isinstance(result, dict) else None
        source = path or LIT_ARTIFACT_NAME
        with open(source, "r", encoding="utf-8") as handle:
            index = json.load(handle)
        if not isinstance(index, dict) or index.get("schema") != LIT_INDEX_SCHEMA:
            raise ValueError(f"artifact {version_id!r} is not a v{LIT_INDEX_SCHEMA} index")
        LIT_STATE["index"] = index
        LIT_STATE.pop("matrix", None)
        LIT_STATE.pop("vectorizer", None)
        LIT_STATE.pop("fitted_revision", None)
        os.makedirs(LIT_INDEX_DIR, exist_ok=True)
        with open(LIT_INDEX_FILE, "w", encoding="utf-8") as handle:
            json.dump(index, handle, ensure_ascii=False)
        return lit_index_stats()
    if lit_index_read() is None:
        raise FileNotFoundError(
            f"lit_index_load: no index at {LIT_INDEX_FILE}. Run lit_index_build()."
        )
    return lit_index_stats()


def lit_fit():
    """Fit the retrieval representation over the loaded index. Cached."""
    index = lit_index_read()
    if index is None:
        raise FileNotFoundError("lit_fit: no index — run lit_index_build() first")
    chunks = index.get("chunks") or []
    if not chunks:
        raise ValueError("lit_fit: the index has no chunks; is the library empty?")
    if (
        LIT_STATE.get("fitted_revision") == index.get("revision")
        and LIT_STATE.get("matrix") is not None
    ):
        return LIT_STATE["matrix"]
    matrix = lit_encode([chunk["text"] for chunk in chunks], fit=True)
    LIT_STATE["matrix"] = matrix
    LIT_STATE["fitted_revision"] = index.get("revision")
    return matrix


def lit_search(query, k=6, *, files=None, min_score=0.02):
    """Top-``k`` chunks for ``query``, each with the file and page to cite.

    Returns ``[{"file", "page", "score", "text", "chunk_id"}, ...]`` ordered by
    score. ``files`` restricts the search to matching filenames (substring
    match). An empty list means nothing in the library scored above
    ``min_score`` — report that, do not answer from memory instead.
    """
    if not str(query or "").strip():
        raise ValueError("lit_search: query must be a non-empty string")
    from sklearn.metrics.pairwise import cosine_similarity

    index = lit_index_read()
    matrix = lit_fit()
    chunks = index["chunks"]
    scores = cosine_similarity(lit_encode([query], fit=False), matrix)[0]

    wanted = None
    if files:
        needles = [files] if isinstance(files, str) else list(files)
        wanted = {
            chunk["id"]
            for chunk in chunks
            if any(str(needle).lower() in chunk["file"].lower() for needle in needles)
        }
    ranked = sorted(
        (
            {
                "chunk_id": chunk["id"],
                "file": chunk["file"],
                "page": chunk["page"],
                "score": round(float(scores[chunk["id"]]), 4),
                "text": chunk["text"],
            }
            for chunk in chunks
            if (wanted is None or chunk["id"] in wanted)
            and float(scores[chunk["id"]]) >= min_score
        ),
        key=lambda hit: hit["score"],
        reverse=True,
    )
    return ranked[: max(1, int(k))]


def lit_context(query, k=6, *, files=None, min_score=0.02, max_chars=8000):
    """Retrieved passages formatted for quoting, with `[file p.N]` citations.

    Feed the returned ``context`` to the model and answer only from it. The
    header is deliberately blunt about the empty case: a retrieval skill whose
    failure mode is a confident answer from parameter memory is worse than no
    retrieval skill.
    """
    hits = lit_search(query, k=k, files=files, min_score=min_score)
    if not hits:
        return {
            "query": query,
            "hits": [],
            "context": (
                "No passage in the local library matched this query. Say so; do "
                "not answer from memory and do not cite anything."
            ),
        }
    blocks, used = [], 0
    for hit in hits:
        citation = f"[{os.path.basename(hit['file'])} p.{hit['page']}]"
        block = f"{citation} (score {hit['score']})\n{hit['text']}"
        if used + len(block) > max_chars:
            break
        blocks.append(block)
        used += len(block)
    return {
        "query": query,
        "hits": hits[: len(blocks)],
        "context": (
            "Answer only from the passages below. Cite each claim with the "
            "[filename p.page] marker that precedes the passage it came from. "
            "If they do not answer the question, say so.\n\n"
            + "\n\n---\n\n".join(blocks)
        ),
    }


def lit_index_stats():
    """What is indexed right now. Reads nothing from the library itself."""
    index = lit_index_read()
    if index is None:
        return {"indexed": False, "index_path": LIT_INDEX_FILE}
    files = index.get("files") or {}
    return {
        "indexed": True,
        "index_path": LIT_INDEX_FILE,
        "revision": index.get("revision"),
        "built_at": index.get("built_at"),
        "source_dir": index.get("source_dir"),
        "files": len(files),
        "pages": sum(int(entry.get("pages") or 0) for entry in files.values()),
        "chunks": len(index.get("chunks") or []),
        "documents": sorted(files),
    }
