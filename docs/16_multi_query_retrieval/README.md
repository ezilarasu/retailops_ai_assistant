# Multi-Query Retrieval
> Generate multiple search queries from one question to dramatically improve retrieval recall.

## 📌 What Is It?

**Multi-query retrieval** generates several alternative phrasings of a user's question, runs retrieval for each one, merges the results, and deduplicates. The LLM sees a richer candidate set than a single query would produce.

```
Single query:
  "How much PTO do employees get?"
  → retrieves 4 chunks with "vacation"

Multi-query:
  "How much PTO do employees get?"
  "What is the paid time off policy?"
  "How many vacation days do employees receive?"
  "What employee leave benefits are available?"
  → retrieves 4+4+4+4 chunks, deduplicated → richer candidate set
```

The core insight: a single question represents one perspective and one vocabulary. Documents may use completely different wording to express the same information. Generating multiple queries increases the chance of matching each phrasing.

## ❓ Why Does It Exist?

Users ask questions in their own words. Documents are written by someone else in different words. Even good embedding models can miss relevant chunks when the vocabulary gap is large.

```
User asks:    "How much PTO do employees get?"     → embeds to vector Q1
Document has: "Employees receive 18 vacation days" → embeds to vector D

cosine(Q1, D) = 0.82  ← decent, but might not rank in top-4 behind more literal matches

Alternate query: "What is the vacation days policy?" → vector Q2
cosine(Q2, D) = 0.94  ← much stronger — this phrasing finds the doc
```

By generating both queries, the relevant chunk is retrieved even when the user's exact vocabulary doesn't match well.

## ⏰ When Should You Use It?

✅ When users ask vague or short questions ("What about benefits?", "How many days?")  
✅ When retrieval evaluation shows low recall — right document missing from top-K  
✅ For knowledge-base and policy document retrieval where vocabulary is unpredictable  
✅ Combined with hybrid search and reranking for maximum quality  

❌ Don't use for exact identifier lookups (SKU, incident ID) — BM25 handles those better  
❌ Don't generate too many queries (>5) — latency grows linearly with query count  
❌ Don't use without reranking — the merged set contains noise that needs filtering  

## 🗂️ Types / Variants

| Approach | How Queries Are Generated | Best For |
|---|---|---|
| **LLM-generated variants** *(what RetailOps uses)* | Chain: `question → LLM → 3 alternate phrasings` | General questions, policy docs |
| **`MultiQueryRetriever`** *(built-in, not used by RetailOps)* | LangChain built-in that handles generation + merge | Quick setup with standard retriever |
| **Manual query templates** | Hardcoded expansions for known domains | When LLM-generated variants are too unpredictable |

## 🔀 When to Use Which Type

**Use LLM-generated variants with a custom chain** for full control — the multi-query prompt is easy to tune, and you get to decide exactly how many queries to generate and how to merge them.

**Use `MultiQueryRetriever`** for rapid prototyping when you want multi-query with minimal code. In LangChain 1.x it lives in `langchain_classic`:

```python
from langchain_classic.retrievers.multi_query import MultiQueryRetriever

multi_retriever = MultiQueryRetriever.from_llm(retriever=base_retriever, llm=llm)
docs = multi_retriever.invoke("How much PTO do employees get?")
```

**Use manual templates** only for highly structured domains where the same query patterns repeat (e.g., always search by both "PTO" and "vacation days" for leave questions).

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Higher recall — finds docs that single-query misses | Extra LLM call for query generation (~100–200ms) |
| Works well with policy and knowledge-base documents | More retrieval calls (N queries × retrieval time) |
| Simple to implement as an LCEL chain | Merged set needs reranking to be useful |
| Complementary to hybrid search (different problem) | Not beneficial for exact-match or very specific queries |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

load_dotenv()

llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# ── Step 1: Build a query generator chain ────────────────────────────────
QUERY_GEN_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Generate 3 alternative phrasings of the given question.
Each phrasing should use different vocabulary while preserving the meaning.
Return one question per line. No numbering, no explanations."""),
    ("human", "Question: {question}"),
])

query_generator = (
    QUERY_GEN_PROMPT
    | llm
    | StrOutputParser()
    | RunnableLambda(lambda text: [q.strip() for q in text.strip().split("\n") if q.strip()])
)

# ── Step 2: Run and inspect generated queries ─────────────────────────────
queries = query_generator.invoke({"question": "How much PTO do employees get?"})
print("Generated queries:")
for q in queries:
    print(f"  - {q}")
# → ["What is the paid time off policy?",
#    "How many vacation days do employees receive?",
#    "What employee leave benefits are available?"]

# ── Step 3: Retrieve for each query and merge ─────────────────────────────
docs = [
    Document(page_content="Employees receive 18 vacation days annually.", metadata={"source": "hr_policy.txt"}),
    Document(page_content="Vacation requests must be submitted 2 weeks in advance.", metadata={"source": "hr_policy.txt"}),
    Document(page_content="P1 means full store outage.", metadata={"source": "it_kb.txt"}),
]
vectorstore = Chroma.from_documents(docs, embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

def retrieve_for_queries(queries: list[str]) -> list[Document]:
    """Run retrieval for each query, merge, and deduplicate by content."""
    seen = set()
    results = []
    for q in queries:
        for doc in retriever.invoke(q):
            if doc.page_content not in seen:
                seen.add(doc.page_content)
                results.append(doc)
    return results

all_results = retrieve_for_queries(queries)
print(f"\nMerged unique results: {len(all_results)}")
for doc in all_results:
    print(f"  [{doc.metadata['source']}] {doc.page_content[:80]}")
```

## 🔧 Real-World Example

RetailOps' multi-query pipeline — generates alternate queries, retrieves via hybrid search, merges, and reranks with a cross-encoder. It is **hand-written** in `app/multi_query.py` (the built-in equivalent is `MultiQueryRetriever`), and it is the code that actually runs inside the RAG chain.

How it is wired in: `build_rag_chain()` in `app/chains.py` first turns a follow-up question into a standalone one using chat history (doc 17; the first question of a conversation skips this step), then calls `retrieve_documents()`, which uses `retrieve_with_multi_query()` if `ENABLE_MULTI_QUERY=true` (the default) and otherwise calls the hybrid retriever once. `examples/21_multi_query_retrieval.py` runs only `generate_queries()` so you can see the generated variants.

```python
from functools import lru_cache

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.llm import get_llm
from app.config import settings

# ══════════════════════════════════════════════════════════════════════════
# app/multi_query.py — RetailOps multi-query retrieval
# Generates alternate phrasings → retrieves for each → merges → reranks
# ══════════════════════════════════════════════════════════════════════════

multi_query_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Generate 3 different search queries for retrieving relevant company policy or operations documents.

        Rules:
        - Return one query per line.
        - Do not answer the question.
        - Do not number the queries.
        - Keep each query concise.
        """
    ),
    (
        "human",
        """
        Original question:
        {question}
        """
    ),
])


@lru_cache(maxsize=1)  # build the chain (and its LLM client) once, not on every question
def build_multi_query_chain():
    """Build the LLM chain that generates alternate phrasings of a question.

    Input:  {"question": str}
    Output: str — raw LLM output, one query per line
    """
    llm = get_llm()
    parser = StrOutputParser()

    return multi_query_prompt | llm | parser


def generate_queries(question: str) -> list[str]:
    """Generate alternate queries for a question, deduplicated, original included.

    Runs the multi-query chain, splits the output into individual queries,
    inserts the original question at the front, and deduplicates
    case-insensitively. Returns at most 4 queries total.
    """
    chain = build_multi_query_chain()

    result = chain.invoke({
        "question": question
    })

    queries = [
        line.strip("- ").strip()
        for line in result.splitlines()
        if line.strip()
    ]

    queries.insert(0, question)

    deduped = []
    seen = set()

    for query in queries:
        normalized = query.lower()

        if normalized not in seen:
            seen.add(normalized)
            deduped.append(query)

    return deduped[:4]


def retrieve_with_multi_query(
    question: str,
    retriever,
    final_top_k: int | None = None,
) -> list:
    """Run multi-query retrieval end to end.

    Pipeline: generate queries → retrieve for each query → merge + dedupe
    by (source, content prefix) → rerank the merged set with the retriever's
    cross-encoder reranker (if enabled) → return the top `final_top_k` documents.
    """
    queries = generate_queries(question)

    all_docs = []
    seen = set()

    for query in queries:
        if hasattr(retriever, "get_candidates"):
            docs = retriever.get_candidates(query)
        else:
            docs = retriever.invoke(query)

        for doc in docs:
            key = (
                doc.metadata.get("source", ""),
                doc.page_content[:100],
            )

            if key not in seen:
                seen.add(key)
                all_docs.append(doc)

    top_k = final_top_k or settings.retrieval_k

    # Reuse the reranker the retriever loaded once at startup (loading the model
    # per question costs seconds). It is None when ENABLE_RERANKING=false, or when
    # the retriever is not a HybridRetriever; in both cases keep the pooled order.
    reranker = getattr(retriever, "reranker", None)

    if reranker is None:
        return all_docs[:top_k]

    return reranker.rerank(
        query=question,
        documents=all_docs,
        top_k=top_k,
    )
```

### Things to know about this implementation

- **The chain is built once.** `generate_queries()` calls `build_multi_query_chain()` on every question, but that function is wrapped in `functools.lru_cache`, so the LLM client and prompt chain are created only the first time.
- **It only reranks when the retriever has a reranker.** It reuses the one `HybridRetriever` loaded at startup (`retriever.reranker`), so `ENABLE_RERANKING=false` is honoured and the model is never reloaded per question. If you pass a retriever with no `reranker` attribute, the pooled results come back in pooled order.
- **The queries run one after another**, not in parallel, so latency grows with the number of queries (a good exercise: LCEL's `.batch()` from doc 06 can parallelize them).

> **Lesson from this project:** an earlier version of `retrieve_with_multi_query()` created a new `CrossEncoderReranker()` on *every question*. Nothing was wrong in the logic, and the answers were correct, but each question quietly spent about 2 seconds reloading the model plus roughly 36 network checks against Hugging Face. We only noticed because a log showed a retrieval step taking 6.4 seconds for a handful of chunks. After reusing the retriever's reranker, the same step takes under 1 second (about 0.6–0.9 s, including the LLM call that writes the extra queries). The rule: anything slow to load (models, clients, chains) is built once at start-up and passed in, never created inside a function that runs per request.

## 🏭 Production Best Practices

1. **Always include the original question in the query set** — The generated variants are additions, not replacements. The original question often has the highest retrieval precision; variants improve recall. **How:** `all_queries = [original_question] + generated_variants`.

2. **Limit to 3 alternate queries** — Each query adds latency (one retrieval call + context for the LLM generator). 3 variants + original = 4 total queries gives strong recall with acceptable latency. Going to 5–7 rarely justifies the cost. **How:** RetailOps hard-codes this in its prompt ("Generate 3 different search queries") and keeps at most 4 queries including the original. Making it configurable, for example `num_queries = int(os.getenv("MULTI_QUERY_COUNT", "3"))`, would be an easy upgrade (not in the repo).

3. **Always deduplicate by content, not by ID** — The same document chunk may be returned by multiple queries. Check `doc.page_content` to deduplicate, not just document IDs (which may differ between retrieval systems). **How:** `seen = set(); seen.add(doc.page_content)`.

4. **Pair with reranking** — Multi-query increases recall by creating a larger, noisier candidate set. Without reranking, that noise goes to the LLM. **How:** Run multi-query → merge → cross-encoder reranker → top `RETRIEVAL_K` (RetailOps does exactly this).

5. **Make it a feature flag** — Multi-query adds ~200–400ms. For streaming endpoints, users may notice latency. Allow it to be disabled. **How:** `ENABLE_MULTI_QUERY=true/false` env var.

6. **Log original vs rewritten queries** — When retrieval fails, comparing the original question with the generated queries reveals whether the generator is producing useful variants. **How:** LangSmith traces both the generator's input and output.

## ⚠️ Common Mistakes to Avoid

⚠️ **Using multi-query without reranking** — Multi-query retrieves more candidates, including more noise. Without a reranker to filter, the LLM gets a noisy context that dilutes the signal. Always pair with reranking.

⚠️ **Generating too many queries** — 8 alternate queries × 4 results each = 32 candidates to rerank. Latency compounds. 3 variants is the sweet spot for most use cases.

⚠️ **Not including the original question** — Generated variants sometimes drift from the user's intent. The original question is often the strongest signal; always include it in the retrieval set.

⚠️ **Using multi-query for exact ID lookups** — Generating "What is SKU DENIM-4421?" in 4 different ways doesn't help when BM25 on the original query would find it immediately. Reserve multi-query for conceptual questions.

⚠️ **Building models and chains inside a per-request function** — Loading a cross-encoder (or creating an LLM chain) on every call adds avoidable latency. Create these once and reuse them. RetailOps used to do this in `retrieve_with_multi_query()` (a new reranker per question) and in `generate_queries()` (a new LLM chain per question); it now reuses the retriever's reranker and caches the multi-query chain with `lru_cache`.

⚠️ **Confusing multi-query with hybrid search** — They solve different problems. Hybrid search improves the search mechanism (vector + BM25). Multi-query improves the search terms (multiple phrasings). They work well together.

## 🔗 How It Connects to Other Concepts

- **Prompt Engineering** (doc 04) — The multi-query generator prompt is a few-shot prompt pattern for rephrasing
- **Output Parsers** (doc 07) — `StrOutputParser() | RunnableLambda(split_lines)` extracts the list of queries
- **Retrievers** (doc 13) — Multi-query wraps any retriever; the base retriever runs once per query
- **Hybrid Search** (doc 14) — Combine: multi-query generates better queries; hybrid search runs a better search engine for each
- **Cross-Encoder Reranking** (doc 15) — Multi-query increases the candidate pool; reranking selects the best from that pool

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Generating N alternate phrasings of a question, retrieving for each, and merging results to improve recall |
| **Why** | A single query represents one vocabulary; documents may use different words for the same concept |
| **When** | Policy/knowledge-base RAG, vague user questions, when retrieval recall is insufficient |
| **Types** | LLM-generated variants (standard), `MultiQueryRetriever` (built-in), manual templates (domain-specific) |
| **Production gotcha** | Always include original question; limit to 3 variants; always pair with reranking; make it a feature flag |

## ➡️ Next Steps

- **Example file:** `app/multi_query.py` — RetailOps `build_multi_query_chain()`, `generate_queries()`, and `retrieve_with_multi_query()`
- **Runnable demo:** see `RUN.md` in this folder (`examples/21_multi_query_retrieval.py`)
- **Next doc:** `../17_history_aware_retrieval/README.md` — rewriting follow-up questions into standalone queries for conversational RAG
- **Official docs:** https://python.langchain.com/docs/how_to/MultiQueryRetriever/
