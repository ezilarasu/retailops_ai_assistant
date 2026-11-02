# Cross-Encoder Reranking
> The final filter that turns a good candidate set into a precise, high-quality context.

## 📌 What Is It?

**Reranking** is the process of taking a set of candidate documents retrieved by the retriever and reordering them by how well they actually answer the specific question — before sending them to the LLM.

A **cross-encoder** is the model used for this reranking. Unlike embedding models (which produce a vector for a document *independently* of any query), a cross-encoder takes the query and a document *together* as a single input and outputs a relevance score:

```
Embedding similarity:
  embed("What does P1 mean?")     → vector Q
  embed("P1 means full store outage.") → vector D
  cosine_similarity(Q, D)         → 0.88  (approximate — independent encoding)

Cross-encoder:
  model("What does P1 mean? [SEP] P1 means full store outage.") → 0.99  (precise — joint encoding)
  model("What does P1 mean? [SEP] P1 incidents require approval.") → 0.42
```

The cross-encoder is more accurate because it sees the relationship between question and document directly, rather than comparing two independently-encoded vectors.

## ❓ Why Does It Exist?

Retrievers are optimized for **speed** — they must search millions of vectors in milliseconds using ANN indexes. This speed comes at the cost of ranking precision.

A cross-encoder is too slow for full-corpus retrieval (it would need to score every chunk paired with the query — millions of slow inference calls). But it's fast enough to rerank 10–20 candidates into a precise top-4.

The two-stage architecture gets both speed and precision:
```
Stage 1 — Retrieval (speed):
  Hybrid search → Top 20 candidates in <100ms

Stage 2 — Reranking (precision):
  Cross-encoder scores 20 candidate pairs → True top 4 in ~200ms

Result: 4 high-quality chunks sent to LLM
```

Without reranking, the retriever's approximation errors propagate to the LLM — it receives a mix of relevant and marginally-relevant chunks.

## ⏰ When Should You Use It?

✅ After any retrieval step, especially hybrid search which returns a larger candidate set  
✅ When evaluation shows the right document is retrieved but ranked too low to be in top-K  
✅ When LLM answers are often "I don't know" despite correct documents existing in the corpus  
✅ Production systems where answer quality justifies the ~200ms extra latency  

❌ Don't add reranking before measuring whether basic retrieval quality is already sufficient  
❌ Don't use a cross-encoder for initial retrieval — it doesn't scale to large document sets  
❌ Don't rerank too many candidates (> 30) — latency grows linearly with candidate count  

## 🗂️ Types / Variants

| Type | Class | Model Example | Best For |
|---|---|---|---|
| **Cross-encoder (local)** | `CrossEncoderReranker` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Production standard — fast, free, local |
| **Embedding filter** | `EmbeddingsFilter` | Same model as retrieval | Simple score threshold — low latency |
| **LLM-based reranker** | Custom chain | Any LLM | Highest flexibility, highest cost |
| **Cohere Rerank API** | `CohereRerank` | `rerank-english-v3.0` | Managed cloud reranking, easy setup |

## 🔀 When to Use Which Type

**Use `CrossEncoderReranker` with `cross-encoder/ms-marco-MiniLM-L-6-v2`** as the default. It's free, runs locally, lightweight, and produces strong ranking improvement. This is what RetailOps uses.

**Use `EmbeddingsFilter`** as a lightweight fallback when cross-encoder latency is a concern. It filters chunks by embedding similarity to the query — less accurate than a cross-encoder but faster.

**Use Cohere Rerank** when you want a managed API with no model hosting overhead and can accept API costs.

**Use LLM reranking** only for research or when you need highly customized ranking logic. It's the slowest and most expensive option.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Dramatically improves precision of top-K results | Adds ~100–300ms latency per query |
| Catches cases where retriever ranking was wrong | Cannot be used for initial retrieval (doesn't scale) |
| Free local model (`ms-marco-MiniLM-L-6-v2`) | One more component to maintain |
| Reduces noise sent to LLM — better answers for same token cost | Candidate set size must be tuned (too few = misses; too many = slow) |
| Works with any retrieval strategy | |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain.retrievers import ContextualCompressionRetriever
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

load_dotenv()

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Build a small vector store
docs = [
    Document(page_content="P1 means full store outage. Report immediately to IT.", metadata={"source": "it_kb.txt"}),
    Document(page_content="P1 incidents require manager notification.", metadata={"source": "it_kb.txt"}),
    Document(page_content="P2 incidents mean partial outage. Report within 1 hour.", metadata={"source": "it_kb.txt"}),
    Document(page_content="Employees receive 18 vacation days annually.", metadata={"source": "hr_policy.txt"}),
    Document(page_content="P1 tickets must have resolution plan within 2 hours.", metadata={"source": "it_kb.txt"}),
]
vectorstore = Chroma.from_documents(docs, embedding=embeddings)

# ── Step 1: Base retriever fetches candidates ─────────────────────────────
base_retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5},   # retrieve more candidates for reranker to choose from
)

# ── Step 2: Cross-encoder reranker reorders candidates ────────────────────
cross_encoder = HuggingFaceCrossEncoder(
    model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"
    # Free model — downloads on first use, runs locally
)

reranker = CrossEncoderReranker(
    model=cross_encoder,
    top_n=2,    # return only the top 2 after reranking the 5 candidates
)

# ── Step 3: Wrap with ContextualCompressionRetriever ─────────────────────
# This chains: base_retriever → reranker
reranking_retriever = ContextualCompressionRetriever(
    base_compressor=reranker,
    base_retriever=base_retriever,
)

# ── Test: cross-encoder finds the best answer ─────────────────────────────
question = "What does P1 mean?"

# Without reranking: returns top-K by embedding similarity
base_results = base_retriever.invoke(question)
print("=== Base retriever ===")
for doc in base_results:
    print(f"  {doc.page_content[:80]}")

# With reranking: cross-encoder selects most relevant from candidates
reranked_results = reranking_retriever.invoke(question)
print("\n=== After cross-encoder reranking ===")
for doc in reranked_results:
    print(f"  {doc.page_content[:80]}")
# The doc that directly defines P1 should rank highest after reranking
```

## 🔧 Real-World Example

RetailOps' full retrieval pipeline: multi-query expansion → hybrid search → cross-encoder reranking. Each stage feeds the next.

```python
import os
from dotenv import load_dotenv
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain.retrievers import ContextualCompressionRetriever, EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
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
# app/reranker.py — RetailOps cross-encoder reranking
#
# Full pipeline:
#   Question
#    ↓ (multi-query: generate 3 alternate queries)
#   Hybrid Search (vector + BM25, k=10 candidates per query)
#    ↓ (merge, deduplicate)
#   Cross-Encoder (score all candidates against original question)
#    ↓ (top 4)
#   LLM
# ══════════════════════════════════════════════════════════════════════════

def build_reranking_retriever(
    vectorstore: Chroma,
    all_docs: list[Document],
    candidate_k: int = 10,
    final_k: int = 4,
) -> ContextualCompressionRetriever:
    """Build a hybrid retriever with cross-encoder reranking.

    Args:
        vectorstore: Chroma instance (must be built with same embedding model)
        all_docs: Document list for BM25 index
        candidate_k: How many candidates to fetch before reranking
        final_k: How many to return after reranking

    Returns:
        Retriever that internally: hybrid search → rerank → return top final_k
    """
    # Stage 1: Hybrid search — broad candidate retrieval
    vector_retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": candidate_k},
    )
    bm25_retriever = BM25Retriever.from_documents(all_docs)
    bm25_retriever.k = candidate_k

    hybrid_retriever = EnsembleRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        weights=[0.5, 0.5],
    )

    # Stage 2: Cross-encoder reranker — precise candidate selection
    # ms-marco-MiniLM-L-6-v2: lightweight, fast, trained on MS MARCO QA dataset
    cross_encoder = HuggingFaceCrossEncoder(
        model_name=os.getenv(
            "RERANKER_MODEL",
            "cross-encoder/ms-marco-MiniLM-L-6-v2",  # free local default
        )
    )

    reranker = CrossEncoderReranker(
        model=cross_encoder,
        top_n=final_k,  # return the top final_k after scoring all candidates
    )

    # Wrap hybrid retriever with reranker
    return ContextualCompressionRetriever(
        base_compressor=reranker,
        base_retriever=hybrid_retriever,
    )


def format_docs(docs: list[Document]) -> str:
    """Format docs for LLM context — include source for attribution."""
    return "\n\n".join(
        f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    )


# ── Full RAG chain with reranking ─────────────────────────────────────────
RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are RetailOps AI Assistant.
Answer ONLY using the provided context. Cite sources.
If not in context, say "I don't know based on available documents." """),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])


def build_full_rag_chain(reranking_retriever):
    """Build RAG chain: hybrid retrieve → rerank → generate.

    Input:  {"question": str}
    Output: str answer
    """
    return (
        RunnableParallel({
            "context": reranking_retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough() | RunnableLambda(lambda x: x["question"]),
        })
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )


# ── Why retrieve 10 and keep 4? ───────────────────────────────────────────
# Retriever optimizes for recall: cast a wide net, catch all relevant docs
# Reranker optimizes for precision: from the net, keep only the best fish
#
# Retrieve 5, keep 4 → tiny filtering, minimal benefit
# Retrieve 20, keep 4 → strong filtering, significant benefit
# Retrieve 50, keep 4 → diminishing returns, latency increases
# Retrieve 10, keep 4 → good trade-off (RetailOps default)
```

## 🏭 Production Best Practices

1. **Retrieve broadly, rerank aggressively** — The retriever should cast a wide net (k=10–20); the reranker does the precise selection. **How:** Set `candidate_k=10` for the base retriever and `final_k=4` for the cross-encoder. Starting from too few candidates limits how much the reranker can help.

2. **Use `cross-encoder/ms-marco-MiniLM-L-6-v2` as the default** — It's free, runs locally, lightweight, and achieves strong results on question-answering tasks. The -L-12-v2 variant is slightly better but slower. **How:** Set via `RERANKER_MODEL` env var so upgrades don't require code changes.

3. **Measure latency impact before deploying** — A cross-encoder adds ~100–300ms per query depending on candidate count and hardware. For a chat interface this is usually acceptable; for sub-100ms requirements, use `EmbeddingsFilter` instead. **How:** Use LangSmith traces to measure `CrossEncoderReranker` step latency.

4. **Control candidate count with an env var** — The number of candidates to rerank directly affects both quality and latency. **How:** `candidate_k = int(os.getenv("RERANKER_CANDIDATES", "10"))`.

5. **Don't use cross-encoders for initial retrieval** — A cross-encoder must receive (query, document) pairs. Scoring 100,000 pairs per query is infeasible. It works only as a reranker over a small candidate set from the retriever. **Why:** Embedding-based ANN search runs in milliseconds; cross-encoder inference is ~10ms per pair.

6. **Log reranker scores for quality monitoring** — Track which documents survive reranking. If the same "wrong" document keeps being promoted, investigate whether a chunking or embedding issue is causing it to look relevant. **How:** Use LangSmith to capture the reranker's input and output lists.

## ⚠️ Common Mistakes to Avoid

⚠️ **Using cross-encoder for full corpus retrieval** — A cross-encoder paired with every chunk in a 100K-chunk corpus would require 100,000 model inferences per query. It only works on small candidate sets (10–30 docs).

⚠️ **Adding reranking before optimizing retrieval** — If the correct document isn't in your top-20 candidates, reranking can't help — it can only reorder what's already there. Fix retrieval recall first (hybrid search, chunking quality), then add reranking.

⚠️ **Reranking too few candidates** — Reranking 4 candidates to get 4 is pointless. The reranker needs filtering room. Retrieve at least 2–3× your desired final count.

⚠️ **Confusing reranking with retrieval** — Retrieval finds candidates (recall). Reranking selects the best from those candidates (precision). They are different stages with different goals.

⚠️ **Skipping evaluation after adding reranking** — "Reranking always helps" is false for some document sets. Measure answer quality before and after to confirm the improvement justifies the latency cost.

## 🔗 How It Connects to Other Concepts

- **Hybrid Search** (doc 14) — Hybrid search produces the candidate set; cross-encoder reranking operates on top of it. The two stages work together.
- **Retrievers** (doc 13) — `ContextualCompressionRetriever` wraps any base retriever and applies reranking transparently
- **Embeddings** (doc 11) — Embedding similarity (cosine distance) is the fast approximate ranking that reranking corrects and improves
- **RAG Chains** (doc 18) — The reranking retriever drops in as a replacement for the basic retriever in any LCEL RAG chain
- **RAG Evaluation** (doc 19) — Answer quality metrics measure whether reranking improved the final output; source accuracy measures whether it changed what was retrieved

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | A two-stage process where the retriever finds candidates and a cross-encoder reranks them by true relevance to the query |
| **Why** | Retrievers optimize for speed (approximate), cross-encoders optimize for precision (exact joint encoding of query + doc) |
| **When** | After hybrid retrieval, before sending context to the LLM; adds ~100–300ms per query |
| **Types** | `CrossEncoderReranker` (local, default), `EmbeddingsFilter` (simpler), `CohereRerank` (managed API) |
| **Production gotcha** | Retrieve broadly (k=10), rerank aggressively (top_n=4); don't use cross-encoder for initial retrieval; measure latency before deploying |

## ➡️ Next Steps

- **Example file:** `app/reranker.py` — RetailOps `build_reranking_retriever()` combining hybrid search and cross-encoder
- **Next doc:** `16_conversation_memory.md` — maintaining context across multi-turn conversations
- **Official docs:** https://python.langchain.com/docs/how_to/cross_encoder_reranker/
