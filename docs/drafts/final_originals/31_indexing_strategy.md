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

**Start with versioned full rebuilds** — they're simple, reliable, and the version stamp gives you traceability. RetailOps uses this approach: rebuild when documents change, tag the index with a version string.

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

```python
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()

DATA_DIR = Path("data/")
CHROMA_PATH = "chroma_db"
MANIFEST_PATH = "chroma_db/manifest.json"

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
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            return Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

    # Full rebuild: load, chunk, embed, store
    print(f"Building index version: {DOCUMENT_VERSION}")

    docs = []
    for filepath in DATA_DIR.glob("*.txt"):
        loader = TextLoader(str(filepath))
        docs.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
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

RetailOps' indexing module — versioned full rebuilds with a manifest file, hash-based change detection, and a health check endpoint.

```python
import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════
# app/indexing.py — RetailOps indexing module
#
# Strategy: versioned full rebuilds with manifest tracking
#
# DOCUMENT_VERSION is set in .env and incremented when documents change.
# The manifest.json records chunk count and build timestamp for debugging.
#
# Enterprise upgrade: move to incremental indexing with SHA256 change
# detection when document set exceeds ~1,000 files.
# ══════════════════════════════════════════════════════════════════════════

DATA_DIR = Path(os.getenv("DATA_DIR", "data/"))
CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma_db")
MANIFEST_PATH = Path(CHROMA_PATH) / "manifest.json"
DOCUMENT_VERSION = os.getenv("DOCUMENT_VERSION", "2026-06-08-v1")


def _compute_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash of a file for change detection."""
    sha = hashlib.sha256()
    sha.update(filepath.read_bytes())
    return sha.hexdigest()[:16]  # short prefix for logging


def _load_documents() -> list:
    """Load all source documents with metadata."""
    docs = []
    for filepath in sorted(DATA_DIR.glob("*.txt")):
        try:
            loader = TextLoader(str(filepath), encoding="utf-8")
            file_docs = loader.load()
            # Attach metadata for retrieval and access control
            for doc in file_docs:
                doc.metadata["source"] = filepath.name
                doc.metadata["document_version"] = DOCUMENT_VERSION
                doc.metadata["file_hash"] = _compute_file_hash(filepath)
            docs.extend(file_docs)
        except Exception as e:
            logger.error("Failed to load document", extra={"extra_fields": {
                "file": filepath.name,
                "error": str(e)[:200],
            }})
    logger.info("documents_loaded", extra={"extra_fields": {
        "count": len(docs),
        "version": DOCUMENT_VERSION,
    }})
    return docs


def _chunk_documents(docs: list) -> list:
    """Split documents into chunks for indexing.

    Uses RecursiveCharacterTextSplitter for consistent chunk boundaries.
    Enterprise upgrade: use SemanticChunker for higher-quality chunks.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_documents(docs)
    logger.info("chunking_complete", extra={"extra_fields": {
        "input_docs": len(docs),
        "output_chunks": len(chunks),
    }})
    return chunks


def build_vectorstore(force_rebuild: bool = False) -> Chroma:
    """Build the vector store, or load existing if version matches.

    force_rebuild=True skips version check and always rebuilds.
    """
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )

    # Check existing manifest — skip rebuild if version matches
    if not force_rebuild and MANIFEST_PATH.exists():
        try:
            manifest = json.loads(MANIFEST_PATH.read_text())
            if manifest.get("document_version") == DOCUMENT_VERSION:
                logger.info("index_current", extra={"extra_fields": {
                    "version": DOCUMENT_VERSION,
                    "chunk_count": manifest.get("chunk_count"),
                }})
                return Chroma(
                    persist_directory=CHROMA_PATH,
                    embedding_function=embeddings,
                )
        except Exception as e:
            logger.warning("manifest_read_failed", extra={"extra_fields": {"error": str(e)}})

    # Full rebuild
    logger.info("index_rebuild_started", extra={"extra_fields": {"version": DOCUMENT_VERSION}})
    docs = _load_documents()
    chunks = _chunk_documents(docs)

    vectorstore = Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory=CHROMA_PATH,
    )

    # Write manifest
    manifest = {
        "document_version": DOCUMENT_VERSION,
        "chunk_count": len(chunks),
        "source_count": len(docs),
        "built_at": datetime.now().isoformat(),
        "source_files": [d.metadata["source"] for d in docs],
    }
    Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))

    logger.info("index_rebuild_complete", extra={"extra_fields": {
        "version": DOCUMENT_VERSION,
        "chunks": len(chunks),
    }})
    return vectorstore


def get_index_status() -> dict:
    """Return index health status for the /health endpoint."""
    if not MANIFEST_PATH.exists():
        return {"status": "not_built", "document_version": None}
    try:
        manifest = json.loads(MANIFEST_PATH.read_text())
        return {
            "status": "ok",
            "document_version": manifest.get("document_version"),
            "chunk_count": manifest.get("chunk_count"),
            "built_at": manifest.get("built_at"),
            "version_match": manifest.get("document_version") == DOCUMENT_VERSION,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Enterprise path: incremental indexing ────────────────────────────────
#
# When document set grows to 1,000+ files, full rebuilds become expensive.
# Incremental strategy:
#
# 1. Store a hash manifest: {filename: sha256_hash}
# 2. On each sync, compare current hashes to stored hashes
# 3. Reindex only files where hash changed (or new/deleted files)
# 4. Update the hash manifest
#
# def detect_changed_files(data_dir: Path, hash_manifest_path: Path) -> list[Path]:
#     """Return list of files that have changed since last index."""
#     try:
#         stored = json.loads(hash_manifest_path.read_text())
#     except FileNotFoundError:
#         stored = {}
#
#     changed = []
#     for filepath in data_dir.glob("*.txt"):
#         current_hash = _compute_file_hash(filepath)
#         if stored.get(filepath.name) != current_hash:
#             changed.append(filepath)
#     return changed
#
# def update_changed_documents(changed_files: list[Path], vectorstore: Chroma):
#     """Remove stale chunks and re-add updated documents."""
#     for filepath in changed_files:
#         # Delete existing chunks from this source
#         vectorstore.delete(where={"source": filepath.name})
#         # Reload and rechunk the updated file
#         loader = TextLoader(str(filepath))
#         docs = loader.load()
#         chunks = _chunk_documents(docs)
#         vectorstore.add_documents(chunks)
#         logger.info("incremental_update", extra={"extra_fields": {"file": filepath.name}})
```

## 🏭 Production Best Practices

1. **Always track a document version** — When a user reports a wrong answer, the first question is: which version of the documents was the index built from? Without a version, you can't reproduce the bug. Set `DOCUMENT_VERSION` in your `.env` and increment it when documents change. **How:** `DOCUMENT_VERSION = os.getenv("DOCUMENT_VERSION", "2026-06-08-v1")` — change the value whenever source docs are updated.

2. **Write a manifest file after every index build** — The manifest records chunk count, build timestamp, and source files. This enables health checks, debugging, and regression analysis. **How:** After `Chroma.from_documents()` completes, write `manifest.json` to the persist directory with version, chunk count, and file list.

3. **Check the manifest at startup — skip rebuilds when version matches** — Rebuilding the vector store on every server startup is slow and wasteful. Read the manifest, compare versions, and only rebuild when needed. **How:** `if manifest["document_version"] == DOCUMENT_VERSION: load existing`.

4. **Run evaluations after every index rebuild** — Changing chunk size, embedding model, or document content can silently degrade retrieval quality. Never assume quality is preserved across rebuilds. **How:** After `build_vectorstore()` completes, run `python -m evals.run_rag_eval` and compare source accuracy and correctness scores.

5. **Store metadata on every chunk** — `source`, `document_version`, and `department` metadata enable filtering, debugging, and eventual RBAC. Metadata added at indexing time is available for free at retrieval time. **How:** `doc.metadata["source"] = filepath.name` before calling `vectorstore.add_documents()`.

6. **Design for incremental indexing from day one** — Even if you start with full rebuilds, structure your code so the load/chunk/embed steps are separate functions. This makes incremental indexing a drop-in upgrade later — you replace the outer loop, not the entire pipeline. **How:** Separate `_load_documents()`, `_chunk_documents()`, and vectorstore write into distinct functions.

## ⚠️ Common Mistakes to Avoid

⚠️ **No version tracking** — When evaluation scores change unexpectedly or a user reports wrong answers, you have no way to know which documents built the current index. Always stamp the index with a version that matches your document set state.

⚠️ **Rebuilding the index on every startup** — Many tutorial setups call `Chroma.from_documents()` in `__init__` unconditionally. In production, this adds 30–120 seconds to startup time every deploy and thrashes your embeddings API. Check the manifest version first.

⚠️ **No post-rebuild evaluation** — After changing chunk size from 500 to 1000, source accuracy may drop 15%. You won't know unless you run evaluations. Rebuilds don't automatically preserve quality.

⚠️ **Missing metadata on chunks** — If chunks don't have `source` metadata, retrieval responses can't cite their sources, `test_retrieval_source_accuracy` tests can't pass, and RBAC filtering becomes impossible. Add metadata at load time, before chunking.

⚠️ **Full rebuilds at enterprise scale** — A full rebuild of a 100,000-document corpus takes hours and costs significantly in embedding API calls. Plan the incremental indexing path before you hit this scale, not after.

## 🔗 How It Connects to Other Concepts

- **Vector Databases** (doc 12) — The index lives in the vector store; indexing strategy determines when and how that store is populated
- **Chunking** (doc 07) — Chunking is a step inside indexing; chunk strategy decisions (size, overlap, semantic vs recursive) are made during index design
- **Embeddings** (doc 10) — Embedding model choice is locked in at index time; changing models requires a full rebuild
- **RAG Chains** (doc 18) — The retriever uses the index built here; stale indexes cause retrieval failures that manifest as wrong answers
- **Testing** (doc 28) — Retrieval source accuracy tests verify index quality; run them after every rebuild
- **Caching** (doc 29) — Cache keys include `DOCUMENT_VERSION`; when the index version changes, old cache entries are automatically invalidated

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Converting documents into a versioned, searchable vector index |
| **Why** | Retrieval needs a pre-built index; stale indexes cause wrong answers; version tracking enables debugging |
| **When** | At startup (load or rebuild); after any document, chunk, or embedding change |
| **Types** | Full rebuild (simple), incremental (scalable), versioned rebuild (traceable), event-driven (enterprise) |
| **Production gotcha** | Always track version; write a manifest; run evaluations after rebuilds; don't rebuild on every startup |

## ➡️ Next Steps

- **Example file:** `app/indexing.py` — `build_vectorstore()`, `get_index_status()`, incremental path in comments
- **Next doc:** `32_production_rag_patterns.md` — the complete production RAG architecture and enterprise readiness assessment
- **Official docs:** https://python.langchain.com/docs/how_to/#text-splitters
