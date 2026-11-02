# Vector Databases
> Where embeddings live — the storage and search engine that makes RAG scale.

## 📌 What Is It?

A **vector database** is a database purpose-built to store embedding vectors and search them efficiently by similarity. Instead of finding rows by exact value (like a SQL `WHERE id = 123`), it finds vectors by proximity — the nearest neighbors in embedding space.

Think of it like a smart library card catalogue:
```
Traditional DB:  "Find book titled exactly: 'Vacation Policy v2'"
Vector DB:       "Find books about: vacation time, PTO, leave benefits"
                 → returns everything semantically related, regardless of exact title
```

The key operations:
```
Ingestion:  text → embedding model → vector → store in vector DB
Retrieval:  query → embedding model → vector → search vector DB → top-K similar docs
```

RetailOps uses **Chroma** as its vector database — free, local, and easy to set up.

## ❓ Why Does It Exist?

A regular database can technically store vectors (PostgreSQL supports vector columns), but querying them at scale requires comparing every stored vector against the query vector — one million comparisons for one million chunks.

Vector databases solve this with specialized index structures (HNSW, IVF) that make similarity search run in milliseconds even on large collections, using **Approximate Nearest Neighbor (ANN)** algorithms that find very good matches without exhaustive comparison.

Without a vector database:
```python
# Brute force: O(n) comparisons — too slow for production
for chunk_vector in all_million_vectors:
    score = cosine_similarity(query_vector, chunk_vector)
```

With a vector database:
```python
# ANN index: ~O(log n) effective complexity — milliseconds
results = vectorstore.similarity_search(query, k=4)
```

## ⏰ When Should You Use It?

✅ Any RAG system that stores more than a handful of chunks  
✅ When you need semantic (meaning-based) search at query time  
✅ When you need persistent storage so you don't re-embed on every restart  
✅ When you want metadata filtering (only HR documents, only v2 policies)  

❌ Don't use a vector DB for live operational data (inventory counts, order status) — that belongs in a real-time database queried via Tools  
❌ Don't rebuild the index on every user request — build once at startup, serve from persistence  
❌ Don't use a vector DB for pure exact-match lookups — use a regular database  

## 🗂️ Types / Variants

| Database | Deployment | Best For |
|---|---|---|
| **Chroma** | Local or cloud | Learning, dev, small-to-medium production |
| **FAISS** | Local (in-memory) | Research, fast local search, no persistence built-in |
| **Pinecone** | Managed cloud | Production SaaS, zero infrastructure management |
| **Qdrant** | Self-hosted or cloud | Enterprise RAG, rich metadata filtering |
| **Weaviate** | Self-hosted or cloud | Enterprise with GraphQL query interface |
| **pgvector** | PostgreSQL extension | Teams already on Postgres who want vectors in same DB |

## 🔀 When to Use Which Type

**Use Chroma** for all learning, development, and small-to-medium production deployments. It's free, requires no infrastructure, persists to disk, and integrates seamlessly with LangChain.

**Use FAISS** for research or local batch processing where you need maximum speed and don't need persistence across restarts. Less convenient for production.

**Use Pinecone** when you need a fully managed, infinitely scalable cloud vector database and are willing to pay for it. No infrastructure to manage.

**Use Qdrant** for enterprise deployments where rich metadata filtering and access control are critical. Strong open-source option with good performance.

**Use pgvector** if your team already runs PostgreSQL and wants to keep everything in one database — avoids introducing a new infrastructure component.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Fast similarity search via ANN indexes | Eventual consistency (ANN can miss the true nearest neighbor occasionally) |
| Persistence — don't re-embed on restart | Another infrastructure component to manage (for self-hosted options) |
| Metadata filtering for access control | Not suitable for exact-match queries |
| Native LangChain integration across all options | Must rebuild entire index when embedding model changes |
| Scales from laptop to millions of documents | Different databases have different filtering capabilities |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

load_dotenv()

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# ── Build a vector store from documents ──────────────────────────────────
docs = [
    Document(
        page_content="Employees receive 18 days of paid vacation annually.",
        metadata={"source": "hr_policy.txt", "department": "HR"},
    ),
    Document(
        page_content="P1 incidents mean full store outage. Report immediately to IT.",
        metadata={"source": "it_support_kb.txt", "department": "IT"},
    ),
    Document(
        page_content="Managers approve all vacation requests submitted 2 weeks in advance.",
        metadata={"source": "hr_policy.txt", "department": "HR"},
    ),
]

# Chroma embeds each document and stores vector + text + metadata
vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    persist_directory="vectorstore/chroma",  # persists to disk
)

# ── Similarity search ────────────────────────────────────────────────────
results = vectorstore.similarity_search(
    "How much PTO do employees get?",  # PTO finds vacation docs
    k=2,                               # return top 2
)
for doc in results:
    print(f"Source: {doc.metadata['source']}")
    print(f"Text: {doc.page_content[:80]}")
    print()

# ── Similarity search with scores ────────────────────────────────────────
results_with_scores = vectorstore.similarity_search_with_score(
    "What does P1 mean?",
    k=2,
)
for doc, score in results_with_scores:
    print(f"Score: {score:.3f} | {doc.page_content[:60]}")
# Lower score = more similar (distance metric, not similarity)

# ── Load existing index (no re-embedding on restart) ──────────────────────
existing_store = Chroma(
    persist_directory="vectorstore/chroma",
    embedding_function=embeddings,
)
```

## 🔧 Real-World Example

This is RetailOps' actual vector store setup. `build_vectorstore(chunks)` runs every time the RAG chain is built (at app start); there is no separate "load the existing index" path. For RetailOps' small document set, re-embedding at startup is cheap.

> **Gotcha we hit — duplicate chunks (now fixed).** `Chroma.from_documents()` *adds* documents to a collection that already exists in `persist_directory`; it does not replace them. Without explicit IDs, Chroma gives every chunk a random one, so each restart appended another full copy of the corpus. A long-lived local index of this project grew to 460 stored rows for only 22 distinct chunk texts. Retrieval still worked (the hybrid retriever de-duplicates candidates), but it wasted search slots and disk. `build_vectorstore()` in `app/vectorstore.py` now passes a stable ID per chunk (a SHA-256 of its source and text), and Chroma upserts by ID, so re-adding a chunk replaces it. Lesson for your own projects: **give chunks deterministic IDs** whenever you re-run indexing against a persisted store. If you used an older version, delete the `vectorstore/` folder once to drop the old copies. Doc 31 has the full story.

> **Lesson from this project:** a second trap sits next to the first. To rebuild an index from scratch you might delete the whole folder, but a running app keeps Chroma's database file open, and removing the file underneath it gave `attempt to write a readonly database`. RetailOps rebuilds by deleting the *collection* through Chroma (`Chroma(...).delete_collection()`) and re-adding the chunks, so the folder is never removed while the app runs.

```python
import os
import hashlib
from functools import lru_cache
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

load_dotenv()

# ══════════════════════════════════════════════════════════════════════════
# app/vectorstore.py — RetailOps Chroma vector store
# build_vectorstore(chunks) runs each time the RAG chain is built (app start) —
# there is no separate "load existing index" path.
# ══════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)  # build the model once; each new instance reloads it from disk
def get_embeddings() -> HuggingFaceEmbeddings:
    """Shared embedding model — must be the same model used at index time."""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def _chunk_id(chunk: Document) -> str:
    key = f"{chunk.metadata.get('source', '')}\n{chunk.page_content}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def build_vectorstore(chunks: list[Document]) -> Chroma:
    """Embed chunks and load them into a Chroma vectorstore.

    Called each time the RAG chain is built. Every chunk gets a stable id and Chroma
    upserts by id, so chunks that are already stored are replaced, not duplicated
    (see the note above).
    """
    embeddings = get_embeddings()
    unique_chunks = {_chunk_id(chunk): chunk for chunk in chunks}

    # Chroma.from_documents calls embed_documents() internally.
    # The real code uses persist_directory=settings.vectorstore_dir
    # (VECTORSTORE_DIR in .env, default vectorstore/chroma).
    vectorstore = Chroma.from_documents(
        documents=list(unique_chunks.values()),
        ids=list(unique_chunks.keys()),
        embedding=embeddings,
        persist_directory=os.getenv("VECTORSTORE_DIR", "vectorstore/chroma"),
    )
    return vectorstore


def get_retriever(vectorstore: Chroma):
    """MMR retriever — returns relevant AND diverse chunks."""
    # RetailOps uses k = settings.retrieval_k (RETRIEVAL_K=2 in .env.example);
    # k=4 here is a common teaching value.
    return vectorstore.as_retriever(
        search_type="mmr",       # avoid returning near-duplicate chunks
        search_kwargs={"k": 4},  # 4 chunks as context for the LLM
    )


# ── Metadata filtering: enterprise access control ─────────────────────────
# NOT in RetailOps — a teaching example of how you would add access control.
def get_department_retriever(vectorstore: Chroma, department: str):
    """Retriever filtered to a specific department's documents.

    Example: HR documents only for HR users.
    Requires metadata["department"] set at ingestion time (RetailOps chunks
    only carry metadata["source"], so this would need an ingestion change).
    """
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 4,
            "filter": {"department": department},  # only search matching docs
        },
    )


# ── Demo ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample_chunks = [
        Document(
            page_content="Employees receive 18 days of paid vacation annually.",
            metadata={"source": "hr_policy.txt", "department": "HR"},
        ),
        Document(
            page_content="P1 incidents mean full store outage. Report immediately.",
            metadata={"source": "it_support_kb.txt", "department": "IT"},
        ),
        Document(
            page_content="Returns must be processed within 30 days of purchase.",
            metadata={"source": "returns_policy.txt", "department": "Operations"},
        ),
    ]

    # build_vectorstore() is called fresh here — there is no load_index() step
    store = build_vectorstore(sample_chunks)
    retriever = get_retriever(store)

    results = retriever.invoke("How much vacation time do employees get?")
    for doc in results:
        print(f"[{doc.metadata['department']}] {doc.page_content[:80]}")
```

> **Note:** RetailOps also has `get_hybrid_retriever(db, chunks)` in `app/vectorstore.py`, which wraps `get_retriever(db)` together with BM25 keyword search (see doc 14).

## 🏭 Production Best Practices

1. **Persist the index when your document set is large — rebuild when it's small** — Rebuilding means re-embedding every chunk on every app start, which costs time and (for API-based embedding models) money. For large corpora, save to disk and load without re-embedding. **How:** RetailOps' document set is small enough that it takes the simpler path — `build_vectorstore(chunks)` re-embeds every chunk on every run instead of maintaining a separate load-from-disk path (stable chunk IDs make that safe: the same chunk replaces itself instead of piling up, as the note in the Real-World Example explains). At larger scale, switch to loading a persisted `Chroma(persist_directory=..., embedding_function=...)` and only call `build_vectorstore()` when documents change.

2. **Store rich metadata at index time** — The default `{"source": "file.txt"}` is not enough for production. Add `department`, `doc_type`, `version`, and `access_level`. **Why:** Metadata enables filtering (restrict to HR docs), source attribution in answers, and audit trails. It cannot be added later without reindexing.

3. **Version your index directory** — When the document set or embedding model changes, use a new directory (`vectorstore/chroma_v2/`) rather than overwriting. **Why:** Keeps the old index as a rollback option while you validate the new one. (RetailOps keeps one folder instead and records a fingerprint of the document version, chunking settings and embedding model in `vectorstore/manifest.json`; the app rebuilds automatically when the fingerprint changes. See doc 31.)

4. **Use `MMR` as the default retrieval type** — `search_type="mmr"` prevents returning four near-duplicate paragraphs from the same section. **How:** `vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 4})`.

5. **Keep `k` small (3–6 chunks)** — More chunks means more tokens sent to the LLM, higher cost, and potential context dilution. Start with k=4 and increase only if evaluation shows incomplete answers. **How:** If answers are incomplete, consider parent-child retrieval (doc 10) instead of increasing k blindly.

6. **Monitor index size and search latency** — Chroma works well up to ~100K chunks on a laptop. Beyond that, consider Qdrant or Pinecone. **How:** Log the chunk count at build time; use LangSmith to monitor retrieval latency per query.

## ⚠️ Common Mistakes to Avoid

⚠️ **Rebuilding the index on every user request** — Loading and embedding all documents per query is catastrophically slow. Build once; serve from persistence.

⚠️ **No metadata** — Loading documents without rich metadata means no filtering, no source attribution, and no access control. Add metadata at ingestion time — it cannot be added retroactively without a full reindex.

⚠️ **Confusing the vector database with the retriever** — The vector database is the *storage layer* (holds vectors + text). The retriever is the *access layer* (takes a question, returns documents). `vectorstore.as_retriever()` creates a retriever on top of the vector store.

⚠️ **Using a vector DB for exact ID lookups** — "Find inventory for SKU DENIM-4421" is not a similarity search problem. Exact identifiers should be queried via Tools that hit the actual inventory system.

⚠️ **Mixing vectors from different embedding models** — If you change the embedding model and don't rebuild, old vectors and new query vectors are in different spaces. The cosine similarity scores will be meaningless and retrieval quality will silently collapse.

## 🔗 How It Connects to Other Concepts

- **Embeddings** (doc 11) — Embeddings are what gets stored in the vector DB; `Chroma.from_documents()` calls the embedding model internally
- **Retrievers** (next: doc 13) — Retrievers wrap the vector DB; `vectorstore.as_retriever()` is the bridge between storage and search
- **Document Loaders** (doc 09) — Loaders produce Documents → Chunking → Embeddings → Vector DB is the full ingestion pipeline
- **Hybrid Search** (doc 14) — Combines vector DB search with BM25 keyword search for better retrieval coverage
- **RAG Evaluation** (doc 19) — Source accuracy metrics directly reflect vector DB retrieval quality

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Purpose-built database for storing embedding vectors and searching them by similarity using ANN algorithms |
| **Why** | Makes similarity search fast at scale; brute-force comparison against millions of vectors is too slow |
| **When** | At ingestion (store chunks + embeddings) and at query time (search for nearest neighbors) |
| **Types** | Chroma (local/free), FAISS (local/research), Pinecone (managed cloud), Qdrant/Weaviate (enterprise) |
| **Production gotcha** | Persist the index; add rich metadata at ingestion time; use MMR retrieval; never mix embedding models in the same index |

## ➡️ Next Steps

- **Example file:** `app/vectorstore.py` — RetailOps `build_vectorstore(chunks)`, `get_retriever(db)`, and `get_hybrid_retriever(db, chunks)`
- **Runnable demo:** `examples/04_vectorstore_retriever.py` also builds and queries the vectorstore — see `13_retrievers_and_similarity_search/RUN.md` for how to run it
- **Next doc:** `../13_retrievers_and_similarity_search/README.md` — how LangChain retrieves documents from the vector store at query time
- **Official docs:** https://python.langchain.com/docs/concepts/vectorstores/
