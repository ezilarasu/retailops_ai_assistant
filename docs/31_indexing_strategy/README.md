# Indexing Strategy
> How to build, version, and maintain the vector store that powers your RAG system.

## 📌 What Is It?

**Indexing** is the process of converting your documents into searchable vector representations that live in a vector store. Think of it like building a library's card catalogue — before anyone can search, someone has to read every book, decide how to describe it, and file it in the right drawer. Indexing is that offline preparation step.

```
Indexing pipeline (runs before retrieval):

  Source Documents
       ↓
  Document Loaders   ← read files, APIs, databases
       ↓
  Chunking           ← split into searchable pieces
       ↓
  Embeddings         ← convert chunks to vectors
       ↓
  Vector Store       ← Chroma, Pinecone, Qdrant

  ─────────────────────────────────────────────
  Retrieval happens later, querying this index.
```

**Indexing strategy** refers to the decisions around:
- **When** to rebuild the index (full rebuild vs incremental updates)
- **How** to track which version of documents created an index
- **What** to do when source documents change

## ❓ Why Does It Exist?

Without an index, answering "What does P1 mean?" requires scanning every document in real time — too slow for any interactive application.

The index is built once (or periodically) offline, so queries can be answered in milliseconds. But this creates a maintenance problem: **the index can go stale**. When the vacation policy document is updated, the vector store still contains the old version, leading to confidently wrong answers.

Indexing strategy addresses this: how do you know the index is current? How do you rebuild it when something changes? How do you track what state it's in when a bug is reported?

## ⏰ When Should You Use It?

✅ When first setting up a RAG system — you need an index before retrieval works  
✅ After changing any source document — stale content produces wrong answers  
✅ After changing chunk size, embedding model, or chunking strategy — index must be rebuilt  
✅ When debugging wrong answers — check which document version the index reflects  
✅ In production — monitor index health and version  

❌ Don't rebuild the full index on every request — that's extremely expensive  
❌ Don't skip version tracking — you'll lose the ability to reproduce bugs  
❌ Don't assume index quality is constant after a rebuild — run evaluations  
❌ Don't log full document content during indexing — it may contain sensitive data  

## 🗂️ Types / Variants

| Strategy | Description | Best For |
|---|---|---|
| **Full Rebuild** | Delete entire index, reprocess all documents from scratch | Small document sets (<1k docs), simple deployments |
| **Incremental Update** | Detect changed documents, reindex only those | Large document sets, frequent updates |
| **Versioned Rebuild** | Full rebuild, but stamp the index with a version identifier | Any production system needing traceability |
| **Scheduled Sync** | Run full or incremental rebuild on a cron schedule | Documents that change regularly (daily/weekly) |
| **Event-Driven** | Trigger reindex when a source system emits a change event | Enterprise connectors (SharePoint, Confluence) |

## 🔀 When to Use Which Type

**Start with versioned full rebuilds** — they're simple, reliable, and the version stamp gives you traceability. RetailOps uses this approach: you change the `DOCUMENT_VERSION` string in `.env` after editing documents, and the next startup sees that the version no longer matches the manifest and rebuilds. (There is no automatic detection of changed files — bumping the version is a manual step.)

**Move to incremental updates** when your document set grows beyond a few hundred files. A 1-million-document index that rebuilds every time one file changes wastes enormous compute. Incremental indexing detects changes via file hash or timestamp and reindexes only affected documents.

**Use event-driven ingestion** in enterprise systems where documents live in external systems (Confluence, SharePoint, Google Drive). These platforms emit webhooks or provide change APIs; subscribe to those events rather than polling.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Full rebuild is simple and reliable | Full rebuild is expensive for large document sets |
| Version tracking makes bugs reproducible | Incremental indexing requires change detection logic |
| Manifest files enable health checks | Skipping version tracking makes debugging very hard |
| Scheduled rebuilds automate freshness | Staleness window depends on rebuild frequency |
| Incremental updates scale to millions of docs | Incremental state can drift if change detection misses events |

## 💻 Basic Example

A self-contained teaching version (RetailOps' real module is in the Real-World Example below). Run from the repository root so the relative paths resolve.

```python
import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()

DATA_DIR = Path("data/")
CHROMA_PATH = "vectorstore/chroma"                   # same location RetailOps uses (VECTORSTORE_DIR)
MANIFEST_PATH = "vectorstore/manifest.json"          # kept OUTSIDE the Chroma folder so a rebuild can delete that folder

# ── Version tracking ─────────────────────────────────────────────────────
# DOCUMENT_VERSION tells you which document set created this index.
# Set it in .env or derive from a timestamp.
DOCUMENT_VERSION = os.getenv("DOCUMENT_VERSION", datetime.now().strftime("%Y-%m-%d-v1"))


def build_index(force_rebuild: bool = False) -> Chroma:
    """Build (or load existing) vector index with version tracking."""

    # Check if a current index already exists
    if not force_rebuild and Path(MANIFEST_PATH).exists():
        manifest = json.loads(Path(MANIFEST_PATH).read_text())
        if manifest.get("document_version") == DOCUMENT_VERSION:
            print(f"Index is current (version: {DOCUMENT_VERSION}). Loading.")
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            return Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

    # Full rebuild: load, chunk, embed, store
    print(f"Building index version: {DOCUMENT_VERSION}")

    # Chroma.from_documents() ADDS to whatever is already in the folder, it does
    # not replace it. So a true "full rebuild" must delete the old index first.
    # (Deleting the folder is fine in a one-shot script like this one. In a running
    # app another part of the process may still have the folder open, so RetailOps
    # deletes the Chroma *collection* instead; see the Real-World Example below.)
    shutil.rmtree(CHROMA_PATH, ignore_errors=True)

    docs = []
    for filepath in DATA_DIR.glob("*.txt"):
        loader = TextLoader(str(filepath))
        docs.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)  # RetailOps' .env.example values
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory=CHROMA_PATH,
    )

    # Write manifest — records what version created this index
    manifest = {
        "document_version": DOCUMENT_VERSION,
        "chunk_count": len(chunks),
        "built_at": datetime.now().isoformat(),
        "source_files": [f.name for f in DATA_DIR.glob("*.txt")],
    }
    Path(MANIFEST_PATH).write_text(json.dumps(manifest, indent=2))
    print(f"Index built: {len(chunks)} chunks. Manifest saved.")

    return vectorstore
```

## 🔧 Real-World Example

RetailOps' actual indexing module (`app/indexing.py`) — six functions: `manifest_path()`, `index_fingerprint()`, `get_manifest()`, `write_manifest()`, `rebuild_index()`, and `ensure_index_current()`. The vector store itself is built by `build_vectorstore(chunks)` in `app/vectorstore.py`, and the chunking strategy is chosen by `chunk_documents()` in `app/rag.py`; `app/indexing.py` calls into them rather than duplicating them. There is no `get_index_status()` function anywhere in the codebase.

```python
import json
from pathlib import Path

from langchain_chroma import Chroma

from app.config import settings
from app.rag import chunk_documents, load_documents
from app.vectorstore import EMBEDDING_MODEL_NAME, build_vectorstore, get_embeddings


# ══════════════════════════════════════════════════════════════════════════
# app/indexing.py — RetailOps indexing module (actual implementation)
#
# Strategy: versioned full rebuilds, with a manifest that records what the
# index was built from (its "fingerprint"). If anything in the fingerprint
# changes, the index is out of date and is rebuilt.
# ══════════════════════════════════════════════════════════════════════════

def manifest_path() -> Path:
    # Next to the index folder, not inside it, so rebuilding the index never touches it.
    return Path(settings.vectorstore_dir).parent / "manifest.json"


def index_fingerprint() -> dict:
    """Everything that, if changed, makes an existing index out of date."""
    fingerprint = {
        "document_version": settings.document_version,
        "semantic_chunking": settings.enable_semantic_chunking,
        "embedding_model": EMBEDDING_MODEL_NAME,
    }

    # Chunk size and overlap only matter for the recursive splitter.
    if not settings.enable_semantic_chunking:
        fingerprint["chunk_size"] = settings.chunk_size
        fingerprint["chunk_overlap"] = settings.chunk_overlap

    return fingerprint


def get_manifest() -> dict | None:
    path = manifest_path()

    if not path.exists():
        return None

    with open(path, "r") as file:
        return json.load(file)


def write_manifest(chunk_count: int) -> None:
    path = manifest_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {**index_fingerprint(), "chunk_count": chunk_count}

    with open(path, "w") as file:
        json.dump(manifest, file, indent=2)


def rebuild_index() -> dict:
    store_path = Path(settings.vectorstore_dir)

    if store_path.exists():
        # Delete the collection through Chroma rather than deleting the folder: code that is
        # already running keeps the folder's database file open, and removing the file under
        # it causes "attempt to write a readonly database" errors.
        Chroma(
            persist_directory=str(store_path),
            embedding_function=get_embeddings(),
        ).delete_collection()

    chunks = chunk_documents(load_documents())

    build_vectorstore(chunks)

    write_manifest(chunk_count=len(chunks))

    return {
        "status": "rebuilt",
        "document_version": settings.document_version,
        "chunk_count": len(chunks),
    }


def ensure_index_current() -> dict:
    manifest = get_manifest()

    if (
        manifest is None
        or not Path(settings.vectorstore_dir).exists()
        or any(manifest.get(key) != value for key, value in index_fingerprint().items())
    ):
        return rebuild_index()

    return {
        "status": "current",
        "document_version": settings.document_version,
        "chunk_count": manifest.get("chunk_count"),
    }
```

### How the pieces fit together

When `get_container()` in `app/container.py` builds the app for the first time (the CLI does it at start-up, the API on its first request):

1. **`ensure_index_current()`** runs first. It rebuilds the index when the manifest is missing, the index folder is missing, or **any** fingerprint field differs from the current settings. So changing `DOCUMENT_VERSION`, `ENABLE_SEMANTIC_CHUNKING`, the embedding model, or (for recursive chunking) `CHUNK_SIZE`/`CHUNK_OVERLAP` triggers a rebuild automatically. Otherwise it reports `"current"`.
2. **`build_retriever()`** (`app/chains.py`) then loads the documents, splits them with the **same** `chunk_documents()` function, calls `build_vectorstore(chunks)`, and hands the same chunk list to the in-memory BM25 index, so vector search and keyword search see identical chunks.
3. `build_vectorstore()` gives every chunk a stable ID (a SHA-256 of its source and text) and Chroma upserts by ID, so adding a chunk that is already stored replaces it instead of duplicating it. After a clean start the number of stored entries equals the manifest's `chunk_count` (checked live: 8 and 8).
4. **`/debug/retrieval`** reuses the retriever the container already built; it no longer re-chunks or writes to the index.
5. **`POST /index/rebuild`** calls `rebuild_index()`, then `get_container.cache_clear()`, clears the response cache (doc 29), and builds a fresh container on the new index. The running app switches over with no restart.

### What was wrong before (found while writing this doc, now fixed)

- **Duplicate vectors.** `from_documents()` used to be called without IDs, so Chroma gave every chunk a random ID and **appended a full duplicate copy of the corpus on every startup, test run, and `/debug/retrieval` call**. On the development machine the store had grown to 460 entries holding only 22 distinct texts, while `manifest.json` said `chunk_count: 14`. Stable chunk IDs fixed it. You can check yours: compare `chromadb.PersistentClient(path="vectorstore/chroma").get_collection("langchain").count()` with `chunk_count` in `vectorstore/manifest.json`.
- **Two chunking strategies in one index.** `rebuild_index()` used recursive chunking while the RAG chain used semantic chunking, so a rebuilt store held chunks from both. Both now call `chunk_documents()`.
- **A version-only check.** `ensure_index_current()` compared only `DOCUMENT_VERSION`, so changing chunk settings or the embedding model silently kept a stale index. The manifest now stores a fingerprint and every field is compared. (An index built by an older version has a manifest without those fields, so the first start rebuilds it, which also clears any old duplicates.)
- **Deleting the folder under a running process.** `rebuild_index()` used to `shutil.rmtree` the index folder while the app held it open, which caused `attempt to write a readonly database` errors (it broke the router tests when they ran after the retrieval test). It now deletes the Chroma collection in place.
- **A rebuild that did not reach the running app.** `/index/rebuild` rebuilt the files, but the cached chains kept the old index until a restart. The endpoint now reloads the container.

### What is still true

- Start-up still re-chunks and re-embeds the documents every time, even when the index is "current": `build_retriever()` needs the chunks in memory for BM25, and `Chroma.from_documents()` embeds each chunk before upserting it. With the small RetailOps corpus that is a few seconds; with a large one you would open the existing index and rebuild only BM25 (that is the exercise below).
- The manifest is minimal: a fingerprint plus `chunk_count`, with no build timestamp or file list.
- Changing the *content* of a file in `data/` is not detected; bump `DOCUMENT_VERSION` (or call `/index/rebuild`) yourself.

This is a good, realistic exercise: make `build_retriever()` open the persisted store when `ensure_index_current()` reports `"current"` and keep the chunk list only for BM25, so a normal start skips the embedding work.

## 🏭 Production Best Practices

1. **Always track a document version** — When a user reports a wrong answer, the first question is: which version of the documents was the index built from? Without a version, you can't reproduce the bug. Set `DOCUMENT_VERSION` in your `.env` and increment it when documents change. **How:** `DOCUMENT_VERSION = os.getenv("DOCUMENT_VERSION", "2026-06-08-v1")` — change the value whenever source docs are updated.

2. **Write a manifest file after every index build** — The manifest records chunk count, build timestamp, and source files. This enables health checks, debugging, and regression analysis. **How:** After `Chroma.from_documents()` completes, write `manifest.json` with version, chunk count, and file list — and keep it outside the folder you delete on rebuild. RetailOps' manifest (`vectorstore/manifest.json`, next to the index folder) records a fingerprint (document version, semantic-chunking flag, embedding model, and chunk size/overlap when recursive chunking is used) plus `chunk_count`, with no build timestamp or file list yet.

3. **Check the manifest at startup — skip rebuilds when nothing changed** — Rebuilding the vector store on every server startup is slow and wasteful. Read the manifest, compare it with the current settings, and only rebuild when needed. **How:** `if all(manifest.get(k) == v for k, v in index_fingerprint().items()): load existing`. RetailOps does this in `ensure_index_current()`, called from `AppContainer.__init__`, and compares every fingerprint field, not just the version. The skip is still only half-effective: `build_retriever()` re-chunks and re-embeds the documents at start-up anyway (see "What is still true" above).

4. **Run evaluations after every index rebuild** — Changing chunk size, embedding model, or document content can silently degrade retrieval quality. Never assume quality is preserved across rebuilds. **How:** After `build_vectorstore()` completes, run `python -m evals.run_rag_eval` and compare source accuracy and correctness scores.

5. **Store metadata on every chunk** — `source`, `document_version`, and `department` metadata enable filtering, debugging, and eventual RBAC. Metadata added at indexing time is available for free at retrieval time. **How:** `doc.metadata["source"] = filepath.name` before calling `vectorstore.add_documents()`. RetailOps keeps only what `TextLoader` provides — `source` set to the file path (such as `data/hr_policy.txt`); there is no `document_version` or `department` metadata on chunks yet.

6. **Design for incremental indexing from day one** — Even if you start with full rebuilds, structure your code so the load/chunk/embed steps are separate functions. This makes incremental indexing a drop-in upgrade later — you replace the outer loop, not the entire pipeline. **How:** Separate `_load_documents()`, `_chunk_documents()`, and vectorstore write into distinct functions.

## ⚠️ Common Mistakes to Avoid

⚠️ **No version tracking** — When evaluation scores change unexpectedly or a user reports wrong answers, you have no way to know which documents built the current index. Always stamp the index with a version that matches your document set state.

⚠️ **Rebuilding the index on every startup** — Many tutorial setups call `Chroma.from_documents()` in `__init__` unconditionally. In production, this adds 30–120 seconds to startup time every deploy and thrashes your embeddings API. Check the manifest version first. (RetailOps' own `build_retriever()` still re-embeds the documents on every startup even when the index is current — a realistic, small-scale example of this mistake; see "What is still true" above.)

⚠️ **No post-rebuild evaluation** — After changing chunk size from 500 to 1000, source accuracy may drop 15%. You won't know unless you run evaluations. Rebuilds don't automatically preserve quality.

⚠️ **Missing metadata on chunks** — If chunks don't have `source` metadata, retrieval responses can't cite their sources, source-accuracy tests (like the ones sketched in doc 28) can't pass, and RBAC filtering becomes impossible. Add metadata at load time, before chunking.

⚠️ **Full rebuilds at enterprise scale** — A full rebuild of a 100,000-document corpus takes hours and costs significantly in embedding API calls. Plan the incremental indexing path before you hit this scale, not after.

## 🔗 How It Connects to Other Concepts

- **Vector Databases** (doc 12) — The index lives in the vector store; indexing strategy determines when and how that store is populated
- **Document Loaders** (doc 09) — Loading is the first step of indexing; `TextLoader` records each file's path (for example `data/hr_policy.txt`) as the chunk's `source` metadata
- **Chunking** (doc 10) — Chunking is a step inside indexing; chunk strategy decisions (size, overlap, semantic vs recursive) are made during index design
- **Embeddings** (doc 11) — Embedding model choice is locked in at index time; changing models requires a full rebuild
- **RAG Chains** (doc 18) — The retriever uses the index built here; stale indexes cause retrieval failures that manifest as wrong answers
- **Testing** (doc 28) — Retrieval source accuracy tests verify index quality; run them after every rebuild (RetailOps has one basic retrieval test, `test_retriever_finds_hr_policy` in `tests/test_rag.py`, which builds its own temporary index so it never touches the app's folder; the rebuild rules above are covered by `tests/test_retrieval_components.py`)
- **Caching** (doc 29) — `POST /index/rebuild` clears the response cache so answers built from the old documents are dropped immediately. RetailOps' cache keys do *not* include the document version, which only matters once the cache is shared between processes (a gap noted in doc 29)

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Converting documents into a versioned, searchable vector index |
| **Why** | Retrieval needs a pre-built index; stale indexes cause wrong answers; version tracking enables debugging |
| **When** | At startup (load or rebuild); after any document, chunk, or embedding change |
| **Types** | Full rebuild (simple), incremental (scalable), versioned rebuild (traceable), event-driven (enterprise) |
| **Production gotcha** | Always track version; write a manifest; run evaluations after rebuilds; don't rebuild on every startup |

## ➡️ Next Steps

- **Example file:** `app/indexing.py` — `manifest_path()`, `index_fingerprint()`, `get_manifest()`, `write_manifest()`, `rebuild_index()`, `ensure_index_current()` (vector store construction itself is in `app/vectorstore.py`'s `build_vectorstore(chunks)`, and the chunking choice in `app/rag.py`'s `chunk_documents()`). To trigger a rebuild from the API: `POST /index/rebuild` with the `x-api-key` header; the running app picks up the new index without a restart. There is no `examples/` script for this doc.
- **Previous doc:** `../30_security/README.md`
- **Next doc:** `../32_production_rag_patterns/README.md` — the complete production RAG architecture and enterprise readiness assessment
- **Official docs:** https://python.langchain.com/docs/how_to/#text-splitters
