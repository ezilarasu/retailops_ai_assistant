# Retrievers, Similarity Search & MMR
> The component that decides what context the LLM sees — and therefore what it can answer.

## 📌 What Is It?

A **retriever** is a LangChain component that takes a question (a string) and returns the most relevant `Document` chunks from a knowledge store. It implements the Runnable interface, so it plugs into LCEL chains with `|`.

```python
retriever.invoke("How much PTO do employees get?")
# → [Document(page_content="Employees receive 18 vacation days...", metadata={...}),
#    Document(page_content="Vacation requests must be submitted...", metadata={...}),
#    ...]
```

The retriever sits at the heart of every RAG system. It's the component that selects which chunks from your vector store become the LLM's context.

Two retrieval strategies are covered here:

| Strategy | Key Behavior |
|---|---|
| **Similarity search** | Returns the K chunks with highest cosine similarity to the query |
| **MMR (Maximum Marginal Relevance)** | Returns K chunks that are both relevant AND different from each other |

## ❓ Why Does It Exist?

The LLM can't see your entire document corpus — it can only see what the retriever passes into the context window. The retriever is the filter between "all 50,000 chunks in the vector store" and "the 4 chunks the LLM will use to answer this question."

The retrieval rule: **bad retrieval = bad answer**, regardless of how good your LLM is. If the right chunk isn't retrieved, the LLM literally cannot answer the question correctly. It will either hallucinate or say "I don't know."

## ⏰ When Should You Use It?

✅ Every RAG system — retrievers are the query-time component of RAG  
✅ Use `search_type="mmr"` as your default — avoids redundant context  
✅ Use similarity search when you need exact top-K by cosine score for debugging  
✅ Use metadata filters when users should only see specific documents  

❌ Don't use retrievers for real-time data (inventory, orders) — use Tools  
❌ Don't retrieve too many chunks (k > 8) — dilutes context and increases cost  
❌ Don't use retrieval alone for exact ID lookups — combine with BM25  

## 🗂️ Types / Variants

| Type | How It Retrieves | Best For |
|---|---|---|
| **Similarity search** | Top-K by cosine similarity score | Baseline; debuggable; consistent ordering |
| **MMR** | Relevant + diverse (penalizes near-duplicates) | Policy docs, manuals — anything with repeated themes |
| **BM25Retriever** | Keyword (term frequency) matching | Exact terms: IDs, codes, SKUs, dates |
| **MultiQueryRetriever** | Generates N queries, merges results | Improving recall on ambiguous questions |
| **ParentDocumentRetriever** | Small chunks for search, large for answering | When context completeness matters |
| **ContextualCompressionRetriever** | Trims retrieved docs to relevant sentences | Reducing token cost after retrieval |

## 🔀 When to Use Which Type

**Use `search_type="mmr"` as your default.** Similarity search tends to return near-duplicate chunks from the same section. MMR ensures diverse coverage of a topic — different aspects of the vacation policy rather than the same paragraph four times.

**Switch to `search_type="similarity"` when debugging** — the scores are easier to interpret and the ordering is deterministic.

**Add `BM25Retriever`** when your documents contain identifiers, SKUs, incident codes, or dates that semantic search struggles with. Combine it with the vector retriever via hybrid search (doc 14).

**Use `MultiQueryRetriever`** when users ask vague or short questions that might miss relevant chunks with a single embedding. It trades latency for recall.

### Contextual Compression — trimming retrieved content before generation

`ContextualCompressionRetriever` wraps a base retriever and strips each returned `Document` down to only the sentences relevant to the question, before the LLM ever sees it. The retriever still does the initial fetch (e.g. top 20 candidates); the compressor then throws away the noise.

```python
# In LangChain 1.x these built-in retrievers/compressors live in the langchain_classic package
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

cross_encoder = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
compressor = CrossEncoderReranker(model=cross_encoder, top_n=4)

# base_retriever fetches broadly, compressor trims to the relevant top_n
compressed_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vectorstore.as_retriever(search_kwargs={"k": 20}),
)
```

Compressors range from cheap to expensive:

| Compressor | How it decides what to keep | Tradeoff |
|---|---|---|
| Keyword | Keeps lines containing query terms | Fast, but "PTO" won't match "vacation days" |
| Embedding similarity | Keeps sentences with high embedding similarity to the query | Semantic, but adds an extra embedding pass |
| Cross-encoder | Scores query+sentence pairs jointly (same model as doc 15's reranker) | Most accurate, but adds latency |
| LLM | Asks the LLM to extract only relevant text | Best quality, but most expensive per call |

**The real risk with compression is over-trimming.** If a policy document has "Vacation Days," "Approval Process," and "Carry-over Rules" as separate sections, an aggressive compressor answering "explain vacation policy" might keep only the first section and silently drop the other two — the answer looks confident but is incomplete. Compression is a tool for cutting token cost on **large** documents (manuals, long policies); it adds risk without much benefit on small corpora, so don't reach for it before you actually have a token-cost or context-window problem. RetailOps's own document set is small enough that hybrid search + cross-encoder reranking (doc 15) already keeps context tight, so compression isn't enabled by default here — a reasonable architecture call, not a missing feature.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Runnable interface — plugs into any LCEL chain | Only as good as the chunks and embeddings behind it |
| MMR eliminates redundant context | Similarity search can return near-duplicate results |
| Metadata filters enable access control | Default similarity search misses exact IDs/codes |
| Consistent interface across all vector stores | Higher k increases LLM cost and can dilute context quality |
| Easy to swap strategies without changing the rest of the chain | |

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

# Build a small vector store for demonstration
docs = [
    Document(page_content="Employees receive 18 vacation days annually.", metadata={"dept": "HR"}),
    Document(page_content="Vacation requests require 2 weeks advance notice.", metadata={"dept": "HR"}),
    Document(page_content="Managers approve all vacation requests.", metadata={"dept": "HR"}),
    Document(page_content="New employees eligible after 90-day probation.", metadata={"dept": "HR"}),
    Document(page_content="P1 incidents mean full store outage.", metadata={"dept": "IT"}),
]
vectorstore = Chroma.from_documents(docs, embedding=embeddings)

# ── Similarity search: top-K by score ────────────────────────────────────
retriever_sim = vectorstore.as_retriever(
    search_type="similarity",   # default; returns top-K by cosine similarity
    search_kwargs={"k": 3},
)

results = retriever_sim.invoke("How many vacation days do employees get?")
for doc in results:
    print(f"[{doc.metadata['dept']}] {doc.page_content}")

# ── MMR: relevant AND diverse ─────────────────────────────────────────────
retriever_mmr = vectorstore.as_retriever(
    search_type="mmr",          # penalizes near-duplicate results
    search_kwargs={"k": 3},
)

# MMR may return fewer near-duplicates from the same section
results_mmr = retriever_mmr.invoke("Tell me about vacation policy.")
for doc in results_mmr:
    print(f"[MMR] {doc.page_content}")

# ── Retriever is a Runnable — use invoke(), batch(), stream() ─────────────
# Same interface as all LangChain components
results_batch = retriever_mmr.batch([
    "How much vacation time do employees get?",
    "What does P1 mean?",
])
for query_results in results_batch:
    print(f"Found {len(query_results)} docs")

# ── Plug into an LCEL chain ───────────────────────────────────────────────
from langchain_core.runnables import RunnableLambda

def format_docs(docs: list[Document]) -> str:
    """Convert list of Documents into a single context string."""
    return "\n\n".join(doc.page_content for doc in docs)

context_chain = retriever_mmr | RunnableLambda(format_docs)
context = context_chain.invoke("How much vacation do employees get?")
print(context)  # formatted string ready to insert into a prompt
```

## 🔧 Real-World Example

This is a **simplified** version of RetailOps' retrieval setup: an MMR retriever as the default, similarity search for debugging, and a small RAG chain connecting retrieval to generation. It is trimmed for teaching, so it differs from the real code in these ways:

- **`get_retriever()`** (`app/vectorstore.py`) is `get_retriever(db)`: always MMR, with `k = settings.retrieval_k` (the `RETRIEVAL_K` variable; `.env.example` sets it to 2). The `search_type` argument below is a teaching addition.
- **`format_docs()`** (`app/chains.py`) also prints each chunk's rerank score, not just its source.
- **`build_rag_chain()`** (`app/chains.py`) can be called with no arguments (it then builds the retriever, rewriter and answer step itself); the app passes in shared copies instead. It does not use `retriever | format_docs`; its retrieval step is a plain function (`retrieve_context`) that rewrites follow-up questions, expands the question into several queries, runs hybrid search and reranks (docs 14–17). Doc 18 walks through the real chain.
- `app/rag.py` only contains document loading and chunking: `load_documents()`, `split_documents()`, `semantic_split_documents()` and `chunk_documents()` (which picks between the two splitters).

> **Lesson from this project:** a retriever returns the *k best* chunks, not the *relevant* chunks. Run `examples/04_vectorstore_retriever.py` with `RETRIEVAL_K=2` and look at the second result for the vacation question: it is an unrelated returns-policy chunk, because MMR deliberately picks something different from the first hit and there is not much else to choose from in a tiny corpus. That is not a bug in MMR; it is why RetailOps follows retrieval with a reranker that scores every chunk and can drop the clearly irrelevant ones (doc 15).

```python
import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_core.documents import Document
from pydantic import BaseModel, Field

load_dotenv()

llm = ChatGroq(model=os.getenv("LLM_MODEL"), temperature=0)


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


# ══════════════════════════════════════════════════════════════════════════
# app/vectorstore.py — retriever construction (simplified)
# MMR retriever built on top of the Chroma vectorstore
# ══════════════════════════════════════════════════════════════════════════

def get_retriever(db: Chroma, search_type: str = "mmr"):
    """Get a retriever with configurable strategy.

    Args:
        db: Chroma vectorstore built by build_vectorstore()
        search_type: "mmr" (diverse, default) or "similarity" (for debugging)

    Returns:
        Retriever Runnable — invoke(question) → list[Document]
    """
    # The real code reads k from settings.retrieval_k (app/config.py) instead of os.getenv
    return db.as_retriever(
        search_type=search_type,
        search_kwargs={"k": int(os.getenv("RETRIEVAL_K", "4"))},
    )


# ══════════════════════════════════════════════════════════════════════════
# app/chains.py — context formatting + RAG chain (simplified versions;
# the real ones are described above and in doc 18)
# ══════════════════════════════════════════════════════════════════════════

def format_docs(docs: list[Document]) -> str:
    """Format retrieved documents into context string for the LLM.

    Includes source metadata so the LLM can cite sources in RAGResponse.
    """
    return "\n\n".join(
        f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    )


# ── Structured RAG response with source attribution ────────────────────────
class RAGResponse(BaseModel):
    answer: str = Field(description="Answer based ONLY on the provided context")
    sources: list[str] = Field(description="Source document names cited")
    confidence: str = Field(description="high | medium | low")


RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are RetailOps AI Assistant.
Answer ONLY using the provided context.
If the answer is not in the context, set answer to "I don't know based on available documents." """),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])


def build_rag_chain(retriever):
    """Build a full RAG chain: retrieve → format → generate → parse.

    Input:  {"question": str}
    Output: RAGResponse with answer, sources, confidence
    """
    # Step 1: Retrieve and format context while passing question through
    prep = RunnableParallel({
        "context": retriever | RunnableLambda(format_docs),
        "question": RunnablePassthrough() | RunnableLambda(lambda x: x["question"]),
    })

    # Step 2: Generate structured response
    rag_chain = prep | RAG_PROMPT | llm.with_structured_output(RAGResponse)

    return rag_chain


# ── MMR vs Similarity: when each is right ────────────────────────────────
def compare_strategies(vectorstore: Chroma, question: str) -> None:
    """Show the difference between MMR and similarity search results."""
    sim_retriever = get_retriever(vectorstore, search_type="similarity")
    mmr_retriever = get_retriever(vectorstore, search_type="mmr")

    sim_results = sim_retriever.invoke(question)
    mmr_results = mmr_retriever.invoke(question)

    print(f"Question: {question}\n")
    print("=== Similarity Search ===")
    for doc in sim_results:
        print(f"  {doc.page_content[:80]}")

    print("\n=== MMR (diverse) ===")
    for doc in mmr_results:
        print(f"  {doc.page_content[:80]}")
    # MMR likely returns different aspects of the policy
    # Similarity may return near-duplicate paragraphs


# ── Retriever with metadata filter ────────────────────────────────────────
def get_department_retriever(vectorstore: Chroma, department: str):
    """Restrict retrieval to a specific department's documents.

    Used for role-based access: HR users only see HR docs.
    """
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 4,
            "filter": {"department": department},
        },
    )
```

## 🏭 Production Best Practices

1. **Use `search_type="mmr"` as the default** — Similarity search too often returns near-identical paragraphs from the same section of a document. MMR ensures each returned chunk adds new information. **How:** `vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 4})`.

2. **Keep k small unless evaluation shows a problem** — More chunks = more tokens = higher cost. (4 is a common starting point; RetailOps' `.env.example` uses `RETRIEVAL_K=2` because its documents are short and reranking picks the best chunks.) If answers are incomplete, investigate the chunking and embedding quality first before increasing k. **How:** Run evaluation (doc 19) and look at which questions fail; the cause is usually chunking, not k.

3. **Use metadata filters for access control** — If your system has users with different access levels, filter by `department` or `access_level` at retrieval time. **How:** `search_kwargs={"filter": {"access_level": user.access_level}}`. Add this metadata at ingestion time (doc 09).

4. **Treat the retriever as a Runnable in LCEL chains** — The retriever's output is `list[Document]`. Add a `RunnableLambda(format_docs)` to convert it to a string before passing to the prompt. **How:** `retriever | RunnableLambda(format_docs)` — the standard LCEL pattern. (RetailOps does the same job inside its `retrieve_context` function in `build_rag_chain()`, because it also rewrites the question and reranks.)

5. **Log retrieved sources for every query** — When an answer is wrong, you need to know whether the right chunk was retrieved. **How:** Log `[doc.metadata['source'] for doc in results]` for each query. LangSmith traces this automatically.

6. **Evaluate retrieval separately from answer quality** — You can have good retrieval but a bad prompt, or bad retrieval but a prompt that papers over it. Measure source accuracy (did the right document appear in the results?) independently. **How:** Doc 19 covers the evaluation pipeline.

## ⚠️ Common Mistakes to Avoid

⚠️ **Using only similarity search** — Similarity search tends to return near-duplicates from dense sections. MMR almost always produces better context diversity for free. Switch from `search_type="similarity"` to `search_type="mmr"` as your first upgrade.

⚠️ **Blaming the LLM for retrieval failures** — "The AI gave a wrong answer" is usually a retrieval problem, not a generation problem. Before tweaking prompts, check whether the correct chunk was even retrieved.

⚠️ **Retrieving too many chunks (k > 8)** — More chunks dilute the signal and increase LLM cost. The LLM may ignore relevant chunks buried in a large context. Start at k=4.

⚠️ **No source tracking** — If you don't log which documents were retrieved, debugging wrong answers is guesswork. Always include `metadata['source']` in formatted context.

⚠️ **Confusing the retriever with the vector database** — The vector database is the storage layer (Chroma, Pinecone). The retriever is the access layer (`vectorstore.as_retriever()`). The retriever uses the vector database; they are not the same thing.

⚠️ **Reaching for contextual compression before you have a token-cost problem** — Compression trims retrieved text down to what looks relevant, which risks silently dropping a needed section (e.g. keeping "Vacation Days" but dropping "Carry-over Rules" from the same policy). Only add it once evaluation (doc 19) shows a real context-window or cost problem on large documents — don't add it by default.

## 🔗 How It Connects to Other Concepts

- **Vector Databases** (doc 12) — Retrievers wrap vector databases; `vectorstore.as_retriever()` creates a retriever on top of Chroma
- **Embeddings** (doc 11) — The retriever calls `embed_query()` on the user's question at query time to search the vector store
- **Hybrid Search** (next: doc 14) — Combines this vector retriever with BM25 retrieval for better coverage of exact terms
- **Embeddings & Vector Databases** (docs 11–12) are the previous concepts: this doc is about the query-time access layer on top of them
- **RAG Chains** (doc 18) — The retriever is wired into the RAG chain to fetch context before generation (via `RunnableParallel` in the teaching example above; via a `retrieve_context` function in RetailOps)
- **LCEL** (doc 05) — Retrievers are Runnables; they plug directly into `|` chains with `retriever | format_docs | prompt | llm`

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | LangChain component that takes a question and returns relevant `Document` chunks from a vector store |
| **Why** | Retrieval quality determines answer quality — the LLM can only answer from what the retriever provides |
| **When** | At query time in every RAG system; wired into chains as a Runnable |
| **Types** | Similarity search (top-K by score), MMR (relevant + diverse), BM25 (keyword), MultiQuery, ParentDocument |
| **Production gotcha** | Default to MMR; keep k small (RetailOps: 2); log sources; use metadata filters for access control; treat retrieval failures as retrieval problems, not LLM problems |

## ➡️ Next Steps

- **Example file:** `app/vectorstore.py` — RetailOps `get_retriever()`; `app/chains.py` — `build_rag_chain()`, `format_docs()`
- **Runnable demo:** see `RUN.md` in this folder (`examples/04_vectorstore_retriever.py`)
- **Next doc:** `../14_hybrid_search_and_bm25/README.md` — combining vector search with BM25 for better coverage of exact terms
- **Official docs:** https://python.langchain.com/docs/concepts/retrievers/
