# Hybrid Search & BM25
> Neither semantic nor keyword search alone is enough — production systems use both.

## 📌 What Is It?

**Hybrid search** combines two retrieval strategies:
- **Vector search** — finds documents by meaning (embeddings + cosine similarity)
- **BM25** — finds documents by exact keyword relevance (term frequency ranking)

Each strategy has a blind spot the other covers:

```
Query: "How much PTO do employees receive?"
  → Vector search finds vacation docs (PTO ≈ vacation, different words)
  → BM25 struggles (term "PTO" not in document)

Query: "What does P1 mean?"
  → Vector search struggles (P1 has no rich semantic meaning)
  → BM25 finds docs containing exactly "P1"

Query: "DENIM-4421 reorder quantity"
  → Vector search: weak (SKU has no semantic content)
  → BM25: strong (exact term match)
```

**BM25** (Best Match 25) is the industry-standard keyword retrieval algorithm used by Elasticsearch, OpenSearch, and Lucene. It improves on naive keyword matching by weighting rare words higher, penalizing term repetition, and normalizing for document length.

## ❓ Why Does It Exist?

Semantic search alone fails for:
- Product SKUs: `DENIM-4421`, `JACKET-001`
- Incident IDs: `INC-1001`, `P1`, `P2`
- Dates and version numbers: `October 31`, `v3.2`
- Any exact code or identifier where meaning ≠ surface form

BM25 alone fails for:
- Synonym queries: "PTO" vs "vacation days"
- Paraphrase queries: "how do I return items" vs "refund process"
- Intent-based queries where the user's words differ from the document's words

Hybrid search handles both. RetailOps needs to answer questions about policies (semantic) AND look up specific incident priorities and SKUs (exact term), so hybrid search is the right architecture.

## ⏰ When Should You Use It?

✅ Any production RAG system — hybrid search almost always outperforms either strategy alone  
✅ When your documents contain identifiers, product codes, or incident IDs  
✅ When user queries might use different vocabulary than source documents  
✅ When you've baseline-tested similarity search and want to improve recall  

❌ Don't add hybrid search before measuring whether pure semantic search is insufficient  
❌ Don't use hybrid search as a substitute for fixing bad chunking  
❌ Don't expect hybrid search alone to fix poor answer quality — always pair with reranking  

## 🗂️ Types / Variants

| Approach | Description | Best For |
|---|---|---|
| **Vector + BM25 merge** | Run both retrievers, deduplicate results | Standard hybrid search — covers meaning + exact terms |
| **EnsembleRetriever** | LangChain built-in for weighted combination | Easy setup, configurable weights per retriever |
| **Reciprocal Rank Fusion (RRF)** | Merge by rank position rather than score | Avoids score normalization problems across retriever types |
| **BM25 only** | Keyword retrieval without vector search | Legacy systems, exact-match-heavy domains |

## 🔀 When to Use Which Type

**Use `EnsembleRetriever`** as the easiest way to combine a Chroma retriever with `BM25Retriever`. It handles merging and deduplication automatically.

**Use custom merge with RRF** when you need more control over how results are combined — especially when the score ranges from your two retrievers are very different.

**Use BM25 alone** only as a fallback for systems where no embedding model is available. It handles exact terms well but misses semantic queries.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Covers both meaning-based and exact-match queries | More complex pipeline than single retriever |
| BM25 handles identifiers, SKUs, and codes well | BM25 index must be rebuilt when documents change |
| Higher recall than either strategy alone | Merged result set can be noisy without reranking |
| `EnsembleRetriever` makes implementation straightforward | BM25 doesn't understand meaning — won't find PTO when document says vacation |
| Industry-standard production pattern | Slight latency increase (two parallel searches) |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

load_dotenv()

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Sample documents
docs = [
    Document(page_content="Employees receive 18 days of paid vacation annually.",
             metadata={"source": "hr_policy.txt"}),
    Document(page_content="P1 incidents mean full store outage. Report immediately.",
             metadata={"source": "it_support_kb.txt"}),
    Document(page_content="P2 incidents mean partial outage. Report within 1 hour.",
             metadata={"source": "it_support_kb.txt"}),
    Document(page_content="DENIM-4421 reorder threshold is 50 units.",
             metadata={"source": "inventory.txt"}),
    Document(page_content="Vacation requests must be submitted 2 weeks in advance.",
             metadata={"source": "hr_policy.txt"}),
]

# ── Vector retriever (semantic search) ───────────────────────────────────
vectorstore = Chroma.from_documents(docs, embedding=embeddings)
vector_retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 3},
)

# ── BM25 retriever (keyword search) ──────────────────────────────────────
# BM25 index is built in-memory from the document list
bm25_retriever = BM25Retriever.from_documents(docs)
bm25_retriever.k = 3   # number of results to return

# ── EnsembleRetriever: combine both ──────────────────────────────────────
hybrid_retriever = EnsembleRetriever(
    retrievers=[vector_retriever, bm25_retriever],
    weights=[0.5, 0.5],  # equal weight to both strategies
)

# ── Test: semantic query ─────────────────────────────────────────────────
print("=== 'How much PTO?' (semantic) ===")
results = hybrid_retriever.invoke("How much PTO do employees receive?")
for doc in results:
    print(f"  {doc.page_content[:80]}")
# Vector search finds vacation doc (PTO ≈ vacation)

# ── Test: exact term query ───────────────────────────────────────────────
print("\n=== 'DENIM-4421' (exact) ===")
results = hybrid_retriever.invoke("What is the reorder quantity for DENIM-4421?")
for doc in results:
    print(f"  {doc.page_content[:80]}")
# BM25 finds exact SKU match

# ── Test: incident code ──────────────────────────────────────────────────
print("\n=== 'What does P1 mean?' (exact) ===")
results = hybrid_retriever.invoke("What does P1 mean?")
for doc in results:
    print(f"  {doc.page_content[:80]}")
# BM25 reliably finds P1 docs regardless of semantic similarity
```

## 🔧 Real-World Example

RetailOps' hybrid retriever — used as the retrieval component in the full RAG chain. Notice the custom merge logic that includes deduplication and prepares the candidate set for cross-encoder reranking.

```python
import os
from dotenv import load_dotenv
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_core.documents import Document

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)


def get_embedding_model():
    return HuggingFaceEmbeddings(
        model_name=os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
    )


# ══════════════════════════════════════════════════════════════════════════
# app/hybrid_retriever.py — RetailOps hybrid retrieval
# Combines vector search (meaning) + BM25 (exact terms)
# Results feed into the cross-encoder reranker (app/reranker.py)
# ══════════════════════════════════════════════════════════════════════════

def build_hybrid_retriever(
    vectorstore: Chroma,
    all_docs: list[Document],
    vector_weight: float = 0.5,
    k: int = 4,
) -> EnsembleRetriever:
    """Build a hybrid retriever combining vector search and BM25.

    Args:
        vectorstore: Chroma instance with indexed documents
        all_docs: Full list of documents for BM25 index (must match vectorstore docs)
        vector_weight: Weight given to vector search (0.0–1.0). BM25 gets (1 - vector_weight).
        k: Number of results from each retriever

    Returns:
        EnsembleRetriever — invoke(question) → list[Document]
    """
    # Vector retriever: semantic meaning search
    vector_retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": k},
    )

    # BM25 retriever: exact keyword search
    # BM25 excels at: P1, P2, INC-1001, DENIM-4421, Store 102, etc.
    bm25_retriever = BM25Retriever.from_documents(all_docs)
    bm25_retriever.k = k

    bm25_weight = 1.0 - vector_weight

    # EnsembleRetriever merges results, deduplicates, and applies weights
    return EnsembleRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        weights=[vector_weight, bm25_weight],
    )


def format_docs(docs: list[Document]) -> str:
    """Format documents into context string with source attribution."""
    return "\n\n".join(
        f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    )


# ── Full RAG chain using hybrid retrieval ────────────────────────────────
RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are RetailOps AI Assistant.
Answer ONLY from the provided context. Cite your sources.
If the answer is not in context, say "I don't know based on available documents." """),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])


def build_rag_chain_with_hybrid(hybrid_retriever):
    """Build RAG chain with hybrid retrieval.

    Input:  {"question": str}
    Output: str answer with source citations
    """
    return (
        RunnableParallel({
            "context": hybrid_retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough() | RunnableLambda(lambda x: x["question"]),
        })
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )


# ── BM25 Advantages: why exact-term queries need it ───────────────────────
def demonstrate_bm25_advantage(hybrid_retriever, vector_retriever):
    """Compare hybrid vs vector-only on exact-term queries."""
    test_queries = [
        "What does P1 mean?",           # exact code — BM25 wins
        "What is DENIM-4421?",          # exact SKU — BM25 wins
        "How much PTO do employees get?",  # semantic — vector wins
    ]

    print("=== Hybrid vs Vector-Only Retrieval ===")
    for q in test_queries:
        hybrid_results = hybrid_retriever.invoke(q)
        vector_results = vector_retriever.invoke(q)

        hybrid_sources = [d.metadata.get("source", "?") for d in hybrid_results]
        vector_sources = [d.metadata.get("source", "?") for d in vector_results]

        print(f"\nQ: {q}")
        print(f"  Hybrid:  {hybrid_sources}")
        print(f"  Vector:  {vector_sources}")
        # For P1/SKU queries, hybrid includes the exact-match doc; vector may not


# ── Tuning BM25 weight ────────────────────────────────────────────────────
# vector_weight=0.7 → favor semantic (good for policy/FAQ documents)
# vector_weight=0.3 → favor BM25 (good for inventory/incident ID-heavy documents)
# vector_weight=0.5 → balanced (RetailOps default — handles both types)
```

## 🏭 Production Best Practices

1. **Add BM25 before any other retrieval optimization** — The biggest retrieval improvement in enterprise RAG is almost always adding BM25, because real business queries contain product IDs, incident codes, and employee IDs. **How:** `EnsembleRetriever([vector_retriever, bm25_retriever], weights=[0.5, 0.5])`.

2. **Start with equal weights (0.5 / 0.5) and tune based on evaluation** — The right weight ratio depends on how many exact-term queries your users actually ask. Measure source accuracy with your golden dataset at different weight ratios. **How:** Run evals at 0.3/0.7, 0.5/0.5, 0.7/0.3 and pick the best.

3. **Always follow hybrid search with reranking** — The merged candidate set from hybrid search contains a mix of good, average, and noise results. A cross-encoder reranker (doc 15) selects the best 4 from the merged 10–20. **Why:** Hybrid search improves recall; reranking improves precision.

4. **Rebuild the BM25 index when documents change** — The BM25 index is built from the document list in memory. If you add or update documents, rebuild both the Chroma index and the BM25 index. **How:** Call `BM25Retriever.from_documents(all_docs)` as part of your ingestion pipeline.

5. **Log which retriever found each result** — When debugging retrieval quality, you need to know whether BM25 or vector search found the relevant chunk. **How:** Use separate retrievers first, log their results, then combine via `EnsembleRetriever`.

6. **Use higher BM25 weight for domains heavy in codes and IDs** — Retail inventory, incident management, and order systems have many identifiers. Policy and HR documents are more semantic. Tune accordingly. **How:** Expose `VECTOR_WEIGHT` as an env var.

## ⚠️ Common Mistakes to Avoid

⚠️ **Treating hybrid search as a replacement for reranking** — Hybrid search and cross-encoder reranking are different stages. Hybrid search improves recall (finds more relevant candidates). Reranking improves precision (selects the best candidates). You need both.

⚠️ **Thinking hybrid search fixes chunking problems** — If your chunks mix multiple topics, neither BM25 nor vector search will retrieve them cleanly. Fix chunking first, then add hybrid search.

⚠️ **Ignoring BM25 because "embeddings understand meaning"** — Embeddings do not understand identifiers. "P1" embedded next to "P2" might produce very similar vectors even though they mean completely different things in context. BM25 is the reliable fallback for exact terms.

⚠️ **Not evaluating whether hybrid actually helps your data** — On some well-structured document sets, pure semantic search already achieves 90%+ source accuracy. Adding BM25 adds complexity for marginal gain. Measure before committing.

⚠️ **Equal k for both retrievers when documents are skewed** — If your corpus is 80% policy docs (better for semantic) and 20% incident/SKU data (better for BM25), weight accordingly rather than defaulting to equal k.

## 🔗 How It Connects to Other Concepts

- **Embeddings** (doc 11) — Vector search uses embedding similarity; same model must be used at ingestion and query time
- **Vector Databases** (doc 12) — The vector retriever wraps Chroma; hybrid search adds BM25 on top of it
- **Retrievers** (doc 13) — `EnsembleRetriever` combines multiple retrievers; all are Runnables with the same interface
- **Cross-Encoder Reranking** (next: doc 15) — Hybrid search produces candidates; reranking selects the best from those candidates
- **RAG Chains** (doc 18) — Hybrid retriever replaces the single vector retriever in the RAG chain

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Combining semantic vector search and BM25 keyword search to cover both meaning-based and exact-term queries |
| **Why** | Neither strategy alone is sufficient — semantic search misses exact IDs; BM25 misses paraphrases |
| **When** | Any production RAG system, especially with enterprise data containing codes, IDs, and SKUs |
| **Types** | `EnsembleRetriever` (built-in LangChain), custom RRF merge, BM25-only fallback |
| **Production gotcha** | Always follow with cross-encoder reranking; tune weights via evaluation; rebuild BM25 index when docs change |

## ➡️ Next Steps

- **Example file:** `app/hybrid_retriever.py` — RetailOps `build_hybrid_retriever()` combining vector search and BM25
- **Next doc:** `15_cross_encoder_reranking.md` — ranking the hybrid candidate set for maximum precision
- **Official docs:** https://python.langchain.com/docs/how_to/ensemble_retriever/
