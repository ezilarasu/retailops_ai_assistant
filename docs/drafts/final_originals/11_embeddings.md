# Embeddings
> The bridge between human language and mathematical search — turning meaning into numbers.

## 📌 What Is It?

An **embedding** is a numerical representation of the meaning of a piece of text. An embedding model reads text and outputs a list of floating-point numbers (a vector) that captures the semantic content of that text.

Think of it like a coordinate system for meaning:
```
"vacation policy"   → [0.22, -0.18, 0.93, 0.41, ...]   ← a point in semantic space
"PTO rules"         → [0.24, -0.15, 0.91, 0.38, ...]   ← nearby point (similar meaning)
"inventory report"  → [-0.71, 0.52, -0.33, 0.09, ...]  ← distant point (different meaning)
```

Topics with similar meanings cluster together in this space. Topics with different meanings are far apart. This geometry is what makes semantic search possible.

**Key distinction:** Embeddings represent *meaning*, not facts. A chunk containing "vacation policy" can be found by a query about "PTO" because they have similar embeddings — not because the model memorized the policy.

## ❓ Why Does It Exist?

Traditional search works by exact word matching. Given the query "How much PTO do employees receive?", a keyword search looks for documents containing "PTO". If the document says "18 vacation days", the match fails — even though the answer is right there.

Embeddings solve this by encoding meaning rather than words:
```python
# PTO query finds vacation document — different words, same meaning
query_vector    = embed("How much PTO do employees receive?")   # [0.22, -0.18, ...]
vacation_vector = embed("Employees receive 18 vacation days.")  # [0.24, -0.15, ...]

cosine_similarity(query_vector, vacation_vector)  # → 0.93 (high — retrieved)

incident_vector = embed("P1 means full store outage.")          # [-0.71, 0.52, ...]
cosine_similarity(query_vector, incident_vector)  # → 0.15 (low — skipped)
```

Without embeddings, every user question would need to use the exact vocabulary of every source document. That's not how real users ask questions.

## ⏰ When Should You Use It?

✅ Any RAG system — embeddings are the foundation of semantic retrieval  
✅ When users ask questions using different vocabulary than source documents  
✅ When building semantic chunking — `SemanticChunker` requires embeddings at split time  
✅ In hybrid search — vector search is one half of the hybrid pair  

❌ Don't use embeddings alone for exact ID lookups (`DENIM-4421`, `INC-1001`, `P1`) — use BM25 or hybrid  
❌ Don't confuse embedding models with LLMs — they produce vectors, not text  
❌ Don't switch embedding models without rebuilding the entire vector index  

## 🗂️ Types / Variants

| Type | Class | Model Example | Best For |
|---|---|---|---|
| **HuggingFace (local)** | `HuggingFaceEmbeddings` | `all-MiniLM-L6-v2` | Free, local, fast — dev and learning |
| **OpenAI** | `OpenAIEmbeddings` | `text-embedding-3-small` | High quality, API-based, production SaaS |
| **Ollama (local)** | `OllamaEmbeddings` | `nomic-embed-text` | Fully local, no API key required |
| **Cohere** | `CohereEmbeddings` | `embed-english-v3.0` | Strong multilingual support |

## 🔀 When to Use Which Type

**Start with `HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")`** — free, runs locally, no API key, good enough for learning and structured documents. This is what RetailOps uses.

**Upgrade to `OpenAIEmbeddings`** when you need higher retrieval quality for production and can accept API costs. `text-embedding-3-small` is a good price-quality balance.

**Use `OllamaEmbeddings`** for fully offline or air-gapped systems where API calls are unavailable.

**Critical rule:** Every embedding model produces vectors in its own space. You cannot mix vectors from different models in the same index. If you switch models, rebuild the entire vector store from scratch.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Enables semantic search — finds meaning, not just words | Embeddings represent meaning, not facts — don't "know" answers |
| One query finds documents with different vocabulary | Model switch requires full reindex |
| Foundation for hybrid search and semantic chunking | Weaker than keyword search for exact IDs/codes |
| Works with the whole LangChain ecosystem | Quality varies significantly between models |
| `HuggingFaceEmbeddings` is free and local | Latency at query time for embedding generation |

## 💻 Basic Example

```python
import os
import numpy as np
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings

load_dotenv()

# ── Create the embedding model ────────────────────────────────────────────
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
    # Runs locally — downloads on first use, no API key needed
)

# ── Embed a single query ──────────────────────────────────────────────────
vector = embeddings.embed_query("How much PTO do employees receive?")
print(f"Vector dimensions: {len(vector)}")    # 384 for MiniLM
print(f"First 5 values: {[round(v, 3) for v in vector[:5]]}")

# ── Embed multiple documents at once ─────────────────────────────────────
texts = [
    "Employees receive 18 days of paid vacation annually.",
    "Managers approve all vacation requests.",
    "P1 incidents mean full store outage.",
]
doc_vectors = embeddings.embed_documents(texts)
print(f"Embedded {len(doc_vectors)} documents, {len(doc_vectors[0])} dims each")

# ── Cosine similarity: PTO ≈ vacation ─────────────────────────────────────
def cosine_similarity(a, b):
    """1.0 = identical meaning, 0.0 = unrelated, -1.0 = opposite."""
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

query_vec    = embeddings.embed_query("How much PTO do employees get?")
vacation_vec = embeddings.embed_query("Employees receive 18 vacation days.")
incident_vec = embeddings.embed_query("P1 means full store outage.")

print(f"\nPTO query vs vacation doc: {cosine_similarity(query_vec, vacation_vec):.3f}")
# → ~0.90 — high similarity, retriever finds this

print(f"PTO query vs incident doc: {cosine_similarity(query_vec, incident_vec):.3f}")
# → ~0.15 — low similarity, retriever skips this
```

## 🔧 Real-World Example

RetailOps centralizes the embedding model in one factory function used by ingestion, retrieval, and semantic chunking — ensuring consistency throughout the pipeline.

```python
import os
import numpy as np
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

load_dotenv()

# ══════════════════════════════════════════════════════════════════════════
# app/vectorstore.py — RetailOps embedding model factory
# Single source of truth for the embedding model used everywhere.
# Ingestion, retrieval, and semantic chunking all call get_embedding_model().
# ══════════════════════════════════════════════════════════════════════════

def get_embedding_model() -> HuggingFaceEmbeddings:
    """Return the shared embedding model for RetailOps.

    Reads from EMBEDDING_MODEL env var so upgrades don't require code changes.
    All components (ingestion, retrieval, semantic chunking) must use this
    function — never instantiate the model directly elsewhere.
    """
    model_name = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2",  # free local default
    )
    return HuggingFaceEmbeddings(model_name=model_name)


# ── Ingestion: embed chunks and store in Chroma ───────────────────────────
def build_index(chunks: list[Document]) -> Chroma:
    """Embed all chunks and persist to Chroma.

    Args:
        chunks: Document chunks from build_chunks() in rag.py

    Returns:
        Chroma vectorstore ready for retrieval
    """
    embeddings = get_embedding_model()

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="vectorstore/chroma",  # reuse on restart
    )
    print(f"Indexed {len(chunks)} chunks into Chroma")
    return vectorstore


# ── Retrieval: query embedding must match ingestion model ─────────────────
def get_retriever(vectorstore: Chroma):
    """MMR retriever — diverse results from the same embedding space."""
    # search_type="mmr" selects relevant AND diverse chunks
    # This prevents returning 4 near-identical vacation policy paragraphs
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 4},
    )


# ── Demonstrate semantic similarity ──────────────────────────────────────
def show_semantic_similarity():
    """Illustrate why embeddings work for semantic search."""
    embeddings = get_embedding_model()

    pairs = [
        # Similar meaning — should be close
        ("How much PTO do employees receive?", "Employees receive 18 vacation days."),
        # Exact wording match — should be very close
        ("What does P1 mean?", "P1 means full store outage. Report immediately."),
        # Unrelated — should be distant
        ("How much PTO do employees receive?", "P1 means full store outage."),
    ]

    print("=== Semantic Similarity ===")
    for query, doc in pairs:
        q = np.array(embeddings.embed_query(query))
        d = np.array(embeddings.embed_query(doc))
        score = float(np.dot(q, d) / (np.linalg.norm(q) * np.linalg.norm(d)))
        label = "HIGH" if score > 0.7 else "MED" if score > 0.4 else "LOW"
        print(f"\n[{label}] {score:.3f}")
        print(f"  Q: {query}")
        print(f"  D: {doc}")


# ── Embedding model upgrade path ──────────────────────────────────────────
# Current (learning/dev):
#   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
#   → 384 dims, fast, free, good for structured policy docs
#
# Production upgrade option:
#   EMBEDDING_MODEL=text-embedding-3-small  (requires OpenAI key)
#   → 1536 dims, higher quality, API cost per embedding
#
# IMPORTANT: Changing the model requires rebuilding the entire Chroma index.
# Vectors from different models are in different mathematical spaces
# and cannot be compared. Mixed indexes produce silently wrong retrieval.


if __name__ == "__main__":
    show_semantic_similarity()
```

## 🏭 Production Best Practices

1. **Centralize the embedding model in a factory function** — Every component that generates embeddings (ingestion, retrieval, semantic chunking) must use the same model instance or function. If they diverge, queried vectors won't match indexed ones. **How:** Create `get_embedding_model()` that reads `EMBEDDING_MODEL` from env, import it everywhere. Never instantiate the model inline.

2. **Control the model via env var** — Hard-coding `all-MiniLM-L6-v2` everywhere means a model upgrade requires finding every occurrence. **How:** `model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")`.

3. **Rebuild the entire index when changing models** — Vectors from `all-MiniLM-L6-v2` and `text-embedding-3-small` live in completely different spaces. Mixing them produces nonsense retrieval with no error. **How:** Version your index directory (`vectorstore/chroma_v2/`) and always rebuild from scratch after a model change.

4. **Evaluate retrieval quality before and after upgrades** — A bigger model is not always better on your specific data. Measure source accuracy on your golden dataset before committing to an upgrade. **How:** Run `evals/run_evals.py` with both models; compare source accuracy scores.

5. **Use `embed_documents()` for batch ingestion, `embed_query()` for queries** — Some models apply different normalization to queries vs documents. Using the wrong method produces worse retrieval. **How:** LangChain handles this automatically when you use `Chroma.from_documents()` and `retriever.invoke()`.

6. **Monitor embedding latency** — Local `HuggingFaceEmbeddings` is ~5ms per query; OpenAI adds network round-trip time (~50–200ms). **How:** LangSmith traces show per-step latency including embedding generation. Batch embed at ingestion time; only embed the query at request time.

## ⚠️ Common Mistakes to Avoid

⚠️ **Thinking embeddings store facts** — An embedding is a point in mathematical space, not a knowledge store. The actual text lives in the vector store document metadata. The embedding only helps find similar documents — it doesn't "know" what the document says.

⚠️ **Using embeddings for exact ID lookups** — Queries like "DENIM-4421" or "INC-1001" have little semantic meaning. Embedding-based similarity fails for these. Use BM25 or hybrid search whenever exact identifiers appear in queries.

⚠️ **Changing the embedding model without rebuilding the index** — This produces silently wrong retrieval — cosine similarity scores between a new-model query vector and old-model document vectors are meaningless. Always rebuild.

⚠️ **Using different models in ingestion vs retrieval** — If your ingestion pipeline uses `all-MiniLM-L6-v2` but your retriever accidentally instantiates `text-embedding-3-small`, retrieval collapses with no error. Always use a shared factory function.

⚠️ **Skipping evaluation after any embedding change** — "Better model = better retrieval" is not guaranteed. Measure before assuming.

## 🔗 How It Connects to Other Concepts

- **Text Splitters & Chunking** (doc 10) — Chunks are what gets embedded; chunk quality directly limits embedding quality. `SemanticChunker` also uses embeddings during splitting to detect topic boundaries.
- **Vector Databases** (next: doc 12) — Vector stores hold the embedding vectors; `Chroma.from_documents(documents, embedding=model)` calls `embed_documents()` internally at index time
- **Retrievers** (doc 13) — At query time, the retriever calls `embed_query()` on the user's question and searches the vector store for nearest neighbors
- **Hybrid Search** (doc 14) — Vector search is the semantic half of hybrid search; embeddings find meaning-based matches while BM25 handles exact terms
- **Cross-Encoder Reranking** (doc 15) — Cross encoders improve ranking after embedding-based retrieval; they score query-document pairs together for higher precision

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Numerical vector representation of text meaning produced by a trained embedding model |
| **Why** | Enables semantic search — finds relevant documents even when query vocabulary differs from document vocabulary |
| **When** | At ingestion (embed all chunks) and at query time (embed the user's question) |
| **Types** | `HuggingFaceEmbeddings` (free, local), `OpenAIEmbeddings` (high quality, API), `OllamaEmbeddings` (offline) |
| **Production gotcha** | Centralize in a factory function; rebuild index on model change; don't use for exact ID lookups; always use `embed_query()` for queries and `embed_documents()` for docs |

## ➡️ Next Steps

- **Example file:** `app/vectorstore.py` — RetailOps `get_embedding_model()` and `build_index()`
- **Next doc:** `12_vector_databases.md` — storing and searching embedding vectors at scale with Chroma, FAISS, and Pinecone
- **Official docs:** https://python.langchain.com/docs/concepts/embedding_models/
