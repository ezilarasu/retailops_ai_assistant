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

**Use `CrossEncoderReranker` with `cross-encoder/ms-marco-MiniLM-L-6-v2`** as the default. It's free, runs locally, lightweight, and produces strong ranking improvement. This is the model RetailOps uses (through `sentence_transformers.CrossEncoder` directly, not LangChain's wrapper class).

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
# In LangChain 1.x these built-in retrievers/compressors live in the langchain_classic package
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
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

RetailOps' actual reranking implementation is not LangChain's `CrossEncoderReranker` wrapped in a `ContextualCompressionRetriever` — it's a small standalone `CrossEncoderReranker` **class** in `app/reranker.py`, built directly on `sentence_transformers.CrossEncoder`, with a single `.rerank(query, documents, top_k)` method. (It happens to share its name with LangChain's class, but it is RetailOps' own code.) It's called from inside `HybridRetriever.invoke()` (`app/hybrid_retriever.py`, see doc 14) rather than through LangChain's compression-retriever wrapper. There is no `build_reranking_retriever()` function anywhere in RetailOps.

Real-code details worth knowing:

- **Numbers:** the "top 20 → top 4" figures in this doc are teaching values. In RetailOps the candidate pool is the vector retriever's `RETRIEVAL_K` results plus up to 10 BM25 results (about 12 after merging), and the reranker keeps `RETRIEVAL_K` of them (`.env.example`: 2).
- **On/off switch:** `ENABLE_RERANKING=false` makes `HybridRetriever` skip the cross-encoder and return the first `RETRIEVAL_K` merged candidates. The multi-query path (doc 16) respects the switch too, because it uses the retriever's own reranker, which is `None` when reranking is off.
- **Score:** each surviving chunk gets `metadata["rerank_score"]`, which `format_docs()` shows to the LLM and the logs record. Scores are not probabilities: for this project's model they run from about −11 (unrelated) to +9 (strong match).
- **Relevance cut-off:** the reranker keeps *up to* `RETRIEVAL_K` chunks, but drops any scoring below `RERANK_MIN_SCORE` (default `-9.0`). The best chunk is always kept, so you never get zero results. Without a cut-off, `RETRIEVAL_K=2` meant a clearly unrelated second chunk (for example the returns policy for a vacation question, score about −9) was still sent to the LLM and cost tokens. `RERANK_MIN_SCORE=none` turns the cut-off off.

> **Lesson from this project:** we picked the cut-off by measuring, not guessing. We scored every candidate chunk for 22 questions whose answers are in the documents (plus one whose answer is not) and looked at where relevant and irrelevant chunks fall. On the final chunking, the lowest-scoring *relevant* chunk was −8.4 and the highest irrelevant one was −7.5 across 12 irrelevant candidates, so on a corpus this small the cut-off is a safety net that rarely removes anything. The measurement also showed the danger of a high threshold: a cut-off of 0 would have thrown away 4 of the 22 relevant chunks (for example a paraphrased question whose right chunk scored −1.6). We moved the default from −8.5 to −9.0 because one relevant chunk sat only 0.1 above −8.5. The numbers belong to this model and this tiny corpus, so measure your own scores (`examples/15_hybrid_retrieval.py` plus `rerank_score` in the logs) before reusing them. A cut-off is always a trade-off: a chunk that is only *part* of an answer, like the tail of a list, can score low and be dropped if you set it too high.

- **Model loading:** the cross-encoder model is downloaded from HuggingFace on first use and loaded when a `CrossEncoderReranker()` is created. `HybridRetriever` creates one when it is built (once, at startup), and multi-query retrieval (doc 16) reuses that same instance instead of loading the model again. Loading takes about 2 seconds online (about 0.1 seconds once the model is cached and `HF_HUB_OFFLINE=1` skips the update checks), while scoring a handful of chunks takes milliseconds, so always create the reranker once and reuse it.

```python
import os
from dotenv import load_dotenv
from sentence_transformers import CrossEncoder
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel
from langchain_core.documents import Document

load_dotenv()

llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)

# ══════════════════════════════════════════════════════════════════════════
# app/reranker.py — RetailOps cross-encoder reranking
#
# Full pipeline (see app/hybrid_retriever.py, doc 14):
#   Question
#    ↓
#   HybridRetriever.get_candidates() — vector + BM25, merged and deduplicated
#    ↓
#   CrossEncoderReranker.rerank() — score all candidates against the question
#    ↓ (top_k)
#   LLM
# ══════════════════════════════════════════════════════════════════════════

class CrossEncoderReranker:
    """Scores (query, document) pairs jointly and returns the top_k best matches."""

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        min_score: float | None = None,
    ):
        # ms-marco-MiniLM-L-6-v2: lightweight, fast, trained on MS MARCO QA dataset
        self.model = CrossEncoder(model_name)
        self.min_score = min_score  # None = no cut-off; HybridRetriever passes RERANK_MIN_SCORE

    def rerank(self, query: str, documents: list[Document], top_k: int = 4):
        """Score each document against the query and return up to top_k, highest first."""
        if not documents:
            return []

        # Cross-encoder scores the query and document TOGETHER — one pair at a time
        pairs = [(query, doc.page_content) for doc in documents]
        scores = self.model.predict(pairs)

        scored_docs = list(zip(scores, documents))
        scored_docs.sort(key=lambda item: item[0], reverse=True)

        reranked_docs = []
        for score, doc in scored_docs[:top_k]:
            # Drop clearly irrelevant chunks, but always keep the best one.
            if reranked_docs and self.min_score is not None and score < self.min_score:
                break

            doc.metadata["rerank_score"] = float(score)  # useful for logging/debugging
            reranked_docs.append(doc)

        return reranked_docs


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


def build_full_rag_chain(hybrid_retriever):
    """Build RAG chain: hybrid retrieve (incl. rerank) → generate.

    hybrid_retriever is a HybridRetriever instance (app/hybrid_retriever.py) —
    its invoke() already calls CrossEncoderReranker.rerank() internally, so
    reranking isn't a separate LCEL step here the way ContextualCompressionRetriever
    would make it.

    Input:  {"question": str}
    Output: str answer
    """
    return (
        RunnableParallel({
            "context": RunnableLambda(lambda x: format_docs(hybrid_retriever.invoke(x["question"]))),
            "question": RunnableLambda(lambda x: x["question"]),
        })
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )


# ── Why retrieve many candidates and keep only a few after reranking? ─────
# get_candidates() optimizes for recall: cast a wide net, catch all relevant docs
# rerank() optimizes for precision: from the net, keep only the best fish
#
# Retrieve 5, keep 4 → tiny filtering, minimal benefit
# Retrieve 20, keep 4 → strong filtering, significant benefit
# Retrieve 50, keep 4 → diminishing returns, latency increases
# RetailOps: ~12 candidates (RETRIEVAL_K vector + up to 10 BM25), keep RETRIEVAL_K
#            (2 in .env.example) — tuned for its small, short documents
```

## 🏭 Production Best Practices

1. **Retrieve broadly, rerank aggressively** — The retriever should cast a wide net (k=10–20); the reranker does the precise selection. **How:** Set `candidate_k=10` for the base retriever and `final_k=4` for the cross-encoder. Starting from too few candidates limits how much the reranker can help.

2. **Use `cross-encoder/ms-marco-MiniLM-L-6-v2` as the default** — It's free, runs locally, lightweight, and achieves strong results on question-answering tasks. The -L-12-v2 variant is slightly better but slower. **How:** RetailOps' `CrossEncoderReranker.__init__()` takes `model_name` as a constructor argument (defaulting to `ms-marco-MiniLM-L-6-v2`) — consider sourcing it from an env var so upgrades don't require code changes.

3. **Measure latency impact before deploying** — A cross-encoder adds ~100–300ms per query depending on candidate count and hardware. For a chat interface this is usually acceptable; for sub-100ms requirements, use `EmbeddingsFilter` instead. **How:** Use LangSmith traces to measure `CrossEncoderReranker` step latency.

4. **Control candidate count deliberately** — The number of candidates handed to `rerank()` directly affects both quality and latency. **How:** In RetailOps, `HybridRetriever.get_candidates()` fetches ~10 BM25 results plus the vector retriever's `k`, merges and dedups them, then `rerank(top_k=...)` trims to the final count — expose these as env vars if you want runtime tuning.

5. **Don't use cross-encoders for initial retrieval** — A cross-encoder must receive (query, document) pairs. Scoring 100,000 pairs per query is infeasible. It works only as a reranker over a small candidate set from the retriever. **Why:** Embedding-based ANN search runs in milliseconds; cross-encoder inference is ~10ms per pair.

6. **Log reranker scores for quality monitoring** — Track which documents survive reranking. If the same "wrong" document keeps being promoted, investigate whether a chunking or embedding issue is causing it to look relevant. **How:** Use LangSmith to capture the reranker's input and output lists.

## ⚠️ Common Mistakes to Avoid

⚠️ **Using cross-encoder for full corpus retrieval** — A cross-encoder paired with every chunk in a 100K-chunk corpus would require 100,000 model inferences per query. It only works on small candidate sets (10–30 docs).

⚠️ **Adding reranking before optimizing retrieval** — If the correct document isn't in your top-20 candidates, reranking can't help — it can only reorder what's already there. Fix retrieval recall first (hybrid search, chunking quality), then add reranking.

⚠️ **Reranking too few candidates** — Reranking 4 candidates to get 4 is pointless. The reranker needs filtering room. Retrieve at least 2–3× your desired final count.

⚠️ **Confusing reranking with retrieval** — Retrieval finds candidates (recall). Reranking selects the best from those candidates (precision). They are different stages with different goals.

⚠️ **Skipping evaluation after adding reranking** — "Reranking always helps" is false for some document sets. Measure answer quality before and after to confirm the improvement justifies the latency cost.

## 🔗 How It Connects to Other Concepts

- **Hybrid Search** (doc 14, the previous concept) — Hybrid search produces the candidate set; cross-encoder reranking operates on top of it. The two stages work together.
- **Multi-Query Retrieval** (next: doc 16) — Query expansion widens the candidate pool before reranking; RetailOps reranks the pooled results from all the generated queries.
- **Retrievers** (doc 13) — LangChain's `ContextualCompressionRetriever` is one way to wrap reranking around a base retriever; RetailOps instead calls `CrossEncoderReranker.rerank()` directly inside `HybridRetriever.invoke()` (doc 14)
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

- **Example file:** `app/reranker.py` — RetailOps `CrossEncoderReranker` class and its `.rerank(query, documents, top_k)` method
- **Next doc:** `../16_multi_query_retrieval/README.md` — generating alternative query phrasings to improve retrieval recall
- **Official docs:** https://python.langchain.com/docs/how_to/cross_encoder_reranker/
