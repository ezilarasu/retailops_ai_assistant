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
| **LLM-generated variants** | Chain: `question → LLM → 3 alternate phrasings` | General questions, policy docs |
| **`MultiQueryRetriever`** | LangChain built-in that handles generation + merge | Quick setup with standard retriever |
| **Manual query templates** | Hardcoded expansions for known domains | When LLM-generated variants are too unpredictable |

## 🔀 When to Use Which Type

**Use LLM-generated variants with a custom chain** for full control — the multi-query prompt is easy to tune, and you get to decide exactly how many queries to generate and how to merge them.

**Use `MultiQueryRetriever`** for rapid prototyping when you want multi-query with minimal code.

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
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
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

RetailOps' multi-query pipeline — generates alternate queries, retrieves via hybrid search, merges, and prepares for cross-encoder reranking.

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_core.documents import Document

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# ══════════════════════════════════════════════════════════════════════════
# app/multi_query.py — RetailOps multi-query retrieval
# Generates alternate phrasings → retrieves for each → merges → reranks
# ══════════════════════════════════════════════════════════════════════════

MULTI_QUERY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an assistant that generates search queries for a retail operations knowledge base.

Given a question, generate {num_queries} alternative phrasings that cover different vocabulary
and perspectives while preserving the original meaning.

Rules:
- Return ONLY the questions, one per line
- No numbering, no explanations, no extra text
- Keep each question concise (under 20 words)"""),
    ("human", "Original question: {question}"),
])


def build_query_generator(num_queries: int = 3):
    """Build a chain that generates N alternate phrasings of a question.

    Input:  {"question": str}
    Output: list[str] of alternate queries
    """
    return (
        MULTI_QUERY_PROMPT.partial(num_queries=str(num_queries))
        | llm
        | StrOutputParser()
        | RunnableLambda(
            lambda text: [q.strip() for q in text.strip().split("\n") if q.strip()]
        )
    )


def build_multi_query_retriever(base_retriever, num_queries: int = 3):
    """Build a retriever that expands queries before retrieval.

    Args:
        base_retriever: Any Runnable retriever (hybrid, MMR, BM25)
        num_queries: Number of alternate queries to generate

    Returns:
        Function: question → list[Document] (merged, deduplicated)
    """
    query_generator = build_query_generator(num_queries)

    def multi_query_retrieve(question: str) -> list[Document]:
        """Generate queries, retrieve for each, merge and deduplicate."""
        # Generate alternate phrasings
        alt_queries = query_generator.invoke({"question": question})
        # Include the original question
        all_queries = [question] + alt_queries

        # Retrieve for all queries
        seen_content = set()
        merged_docs = []

        for q in all_queries:
            for doc in base_retriever.invoke(q):
                if doc.page_content not in seen_content:
                    seen_content.add(doc.page_content)
                    merged_docs.append(doc)

        return merged_docs

    return RunnableLambda(multi_query_retrieve)


# ── Multi-query RAG chain ─────────────────────────────────────────────────
def build_multi_query_rag_chain(multi_query_retriever, reranker=None):
    """Build a RAG chain that uses multi-query retrieval.

    Pipeline:
      question → multi-query retrieval → (optional rerank) → format → LLM

    Input:  {"question": str}
    Output: str answer
    """
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    RAG_PROMPT = ChatPromptTemplate.from_messages([
        ("system", """You are RetailOps AI Assistant.
Answer ONLY using the provided context. Cite sources where possible.
If the answer is not in context, say "I don't know based on available documents." """),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ])

    def format_docs(docs: list[Document]) -> str:
        return "\n\n".join(
            f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
            for doc in docs
        )

    # Optionally pass through a reranker after multi-query retrieval
    retrieval_step = multi_query_retriever
    if reranker:
        retrieval_step = multi_query_retriever | RunnableLambda(
            lambda docs: reranker.compress_documents(docs, "")
        )

    return (
        RunnableParallel({
            "context": RunnableLambda(lambda x: x["question"]) | multi_query_retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough() | RunnableLambda(lambda x: x["question"]),
        })
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )


# ── Feature flag: enable/disable multi-query ─────────────────────────────
# RetailOps exposes ENABLE_MULTI_QUERY env var so multi-query can be
# toggled off for low-latency use cases (e.g., streaming endpoints).
ENABLE_MULTI_QUERY = os.getenv("ENABLE_MULTI_QUERY", "true").lower() == "true"
```

## 🏭 Production Best Practices

1. **Always include the original question in the query set** — The generated variants are additions, not replacements. The original question often has the highest retrieval precision; variants improve recall. **How:** `all_queries = [original_question] + generated_variants`.

2. **Limit to 3 alternate queries** — Each query adds latency (one retrieval call + context for the LLM generator). 3 variants + original = 4 total queries gives strong recall with acceptable latency. Going to 5–7 rarely justifies the cost. **How:** `num_queries = int(os.getenv("MULTI_QUERY_COUNT", "3"))`.

3. **Always deduplicate by content, not by ID** — The same document chunk may be returned by multiple queries. Check `doc.page_content` to deduplicate, not just document IDs (which may differ between retrieval systems). **How:** `seen = set(); seen.add(doc.page_content)`.

4. **Pair with reranking** — Multi-query increases recall by creating a larger, noisier candidate set. Without reranking, that noise goes to the LLM. **How:** Run multi-query → merge → cross-encoder reranker → top 4.

5. **Make it a feature flag** — Multi-query adds ~200–400ms. For streaming endpoints, users may notice latency. Allow it to be disabled. **How:** `ENABLE_MULTI_QUERY=true/false` env var.

6. **Log original vs rewritten queries** — When retrieval fails, comparing the original question with the generated queries reveals whether the generator is producing useful variants. **How:** LangSmith traces both the generator's input and output.

## ⚠️ Common Mistakes to Avoid

⚠️ **Using multi-query without reranking** — Multi-query retrieves more candidates, including more noise. Without a reranker to filter, the LLM gets a noisy context that dilutes the signal. Always pair with reranking.

⚠️ **Generating too many queries** — 8 alternate queries × 4 results each = 32 candidates to rerank. Latency compounds. 3 variants is the sweet spot for most use cases.

⚠️ **Not including the original question** — Generated variants sometimes drift from the user's intent. The original question is often the strongest signal; always include it in the retrieval set.

⚠️ **Using multi-query for exact ID lookups** — Generating "What is SKU DENIM-4421?" in 4 different ways doesn't help when BM25 on the original query would find it immediately. Reserve multi-query for conceptual questions.

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

- **Example file:** `app/multi_query.py` — RetailOps `build_query_generator()` and `build_multi_query_retriever()`
- **Next doc:** `17_history_aware_retrieval.md` — rewriting follow-up questions into standalone queries for conversational RAG
- **Official docs:** https://python.langchain.com/docs/how_to/MultiQueryRetriever/
