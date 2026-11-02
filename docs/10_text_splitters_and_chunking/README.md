# Text Splitters & Chunking Strategies
> The most underestimated RAG component — chunk quality directly determines retrieval quality.

## 📌 What Is It?

**Chunking** is the process of breaking large documents into smaller pieces before generating embeddings. The resulting pieces — called **chunks** — become the search units in your vector store.

Think of it like building a filing system:
```
One huge folder (entire document) → hard to find one specific thing
Many labeled folders (chunks)     → find exactly what you need
```

The key insight: **chunk quality = retrieval quality.** A retriever can only return what the chunks contain. If a chunk mixes "vacation policy" and "incident management" topics, queries for either topic will get noisy, diluted results.

LangChain provides four strategies, each making a different trade-off:

| Strategy | Question It Answers |
|---|---|
| `RecursiveCharacterTextSplitter` | Where do 300 characters end? |
| `SemanticChunker` | Where does the topic change? |
| Parent-Child Retrieval | Can I search with small chunks but answer with big ones? |
| Contextual Compression | Can I trim retrieved context before sending to the LLM? |

## ❓ Why Does It Exist?

**Why not just embed the whole document?** Suppose your HR policy covers vacation days, remote work, dress code, and benefits — all in one file.

When a user asks "How many vacation days do employees get?", the whole-document embedding contains a mixed signal from all four topics. The retriever sees semantic noise and returns a low-relevance result.

Chunked into focused pieces:
```
Chunk A → vacation days content         ← high relevance to vacation query
Chunk B → remote work content           ← low relevance
Chunk C → dress code content            ← low relevance
```

Now the retriever can find exactly the right chunk.

## ⏰ When Should You Use It?

✅ Every RAG system — chunking is not optional  
✅ Before generating embeddings, always  
✅ When document quality is poor (mixed topics, dense PDFs) — use semantic chunking  
✅ When documents are large and individual questions need context — consider parent-child  
✅ When LLM context costs are high — consider contextual compression  

❌ Never skip chunking and embed entire documents  
❌ Don't use semantic chunking when `RecursiveCharacterTextSplitter` already produces good retrieval results  
❌ Don't add parent-child complexity until basic chunking is working well  

## 🗂️ Types / Variants

| Strategy | Class | How It Splits | Best For |
|---|---|---|---|
| **Recursive character** | `RecursiveCharacterTextSplitter` | By paragraphs → sentences → characters | Starting point for all projects; stable and fast |
| **Semantic** | `SemanticChunker` (langchain_experimental; importing it prints a notice that the package is being sunset, so check its status before depending on it in production) | By topic/meaning using embeddings | Mixed-topic documents; when recursive produces noisy chunks |
| **Parent-Child** | `ParentDocumentRetriever` | Small child for search, large parent for answering | Long policies/manuals where context around a fact matters |
| **Contextual Compression** | `ContextualCompressionRetriever` | Trims retrieved context to relevant sentences only | Cost/latency optimization after retrieval |

## 🔀 When to Use Which Type

**Always start with `RecursiveCharacterTextSplitter`.** It's fast, simple, and effective for well-structured documents. Build your baseline with this before adding complexity.

**Upgrade to `SemanticChunker`** when you observe mixed-topic chunks in your baseline retrieval — when a query about vacation policy retrieves chunks that also mention incident management. Semantic chunking respects topic boundaries regardless of character count. The cost: slower indexing and requires an embedding model during splitting.

**Add Parent-Child Retrieval** when evaluation shows answers are incomplete — the right chunk is found but doesn't include enough surrounding context for a full answer. Classic case: employee handbook sections where a rule is found but the approval process and exceptions are in adjacent paragraphs. Note: increases token usage significantly.

**Use Contextual Compression** when you've added parent-child and token costs are too high. Compression trims retrieved parent documents to only the sentences relevant to the query before sending them to the LLM.

**Decision order:** Recursive → Semantic → Parent-Child → Compression. Don't skip steps.

## ⚖️ Pros & Cons

| Strategy | ✅ Pros | ❌ Cons |
|---|---|---|
| **Recursive** | Fast, simple, stable, no extra dependencies | Not meaning-aware; splits mid-topic |
| **Semantic** | Respects topic boundaries, better retrieval precision | Slower indexing, requires embedding model at split time |
| **Parent-Child** | Better context for answering complex questions | Higher token cost, more complex pipeline |
| **Compression** | Reduces token cost and context noise | Can discard relevant content; adds latency |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter  # splitters live in their own package
from langchain_core.documents import Document

load_dotenv()

# ── RecursiveCharacterTextSplitter: the baseline ──────────────────────────
splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,        # max characters per chunk
    chunk_overlap=50,      # overlap prevents meaning split at chunk boundaries
    separators=["\n\n", "\n", " ", ""],  # tries in order: paragraph → line → word → char
)

# Load a document and split it
loader = TextLoader("data/hr_policy.txt", encoding="utf-8")
docs = loader.load()

chunks = splitter.split_documents(docs)

print(f"Documents: {len(docs)}")
print(f"Chunks: {len(chunks)}")
print(f"\nChunk 0 preview:\n{chunks[0].page_content[:200]}")
print(f"\nMetadata: {chunks[0].metadata}")
# metadata carries through from the original document

# ── Understanding chunk_size and chunk_overlap ─────────────────────────────
# Bad: chunk_size=3000 — too large, mixes multiple topics in one chunk
# Bad: chunk_size=50   — too small, no context in each chunk
# Good starting point: 200-400 for policy documents, 400-800 for manuals

# chunk_overlap prevents sentences from being split across chunk boundaries:
# Without overlap:   chunk1="...receive 18 vacation" | chunk2="days annually."
# With overlap=50:   chunk1="...receive 18 vacation days" | chunk2="18 vacation days annually."

# ── Splitting plain text (not loaded from file) ────────────────────────────
raw_text = """Vacation Policy

Employees receive 18 days of paid vacation annually.
Managers approve all vacation requests.

Incident Management

P1 incidents mean full store outage.
All P1 incidents must be reported immediately."""

text_chunks = splitter.split_text(raw_text)
for i, chunk in enumerate(text_chunks):
    print(f"\nChunk {i}:\n{chunk}")
```

## 🔧 Real-World Example

This walks through all four strategies. What RetailOps itself does (`app/rag.py`): **recursive** splitting (`CHUNK_SIZE=300`, `CHUNK_OVERLAP=50` from `.env.example`) and **semantic** splitting with `SemanticChunker`, which is the default (`ENABLE_SEMANTIC_CHUNKING=true`). `chunk_documents()` picks between the two, and both the index builder (`app/indexing.py`) and the retriever (`app/chains.py`) call it, so they always chunk the same way. RetailOps' semantic splitter has two extra settings you will not see in the snippet below: `sentence_split_regex` and `min_chunk_size`. The default sentence splitter cuts after every full stop, so the `6.` in a numbered checklist counted as a sentence end and the store-opening checklist was split in half; the custom pattern does not split after a bare list number. And because a percentile rule always finds *some* split point, even in a short single-topic document, splits that would leave a fragment under `SEMANTIC_MIN_CHUNK_SIZE` (300 characters) are ignored. Parent-child is not part of the default pipeline: `app/parent_child.py` has a small hand-written version (large recursive parents, semantic children) that nothing calls yet. Contextual compression is not used in RetailOps at all — it is shown here as a teaching example.

> **Lesson from this project:** with the default settings, `SemanticChunker` cut the store-opening checklist in half, and the assistant then answered "6. (step not specified)" even though the step was in the documents. Two causes: the default sentence splitter treats the `6.` of a numbered list as the end of a sentence, and a percentile rule *always* picks some split point, even in a short single-topic document. After the fix (a sentence pattern that skips list numbers, plus `min_chunk_size=300`), the same documents give 6 chunks instead of 8 and the checklist stays whole. For comparison, plain recursive chunking at 300/50 never split it. When an answer is wrong but the fact is in your documents, print the chunks (`examples/19_semantic_chunking.py` does this) before you touch the prompt. The snippets below use the standard LangChain classes, which in LangChain 1.x live in `langchain_classic` (retrievers) and `langchain_core` (stores).

```python
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_chroma import Chroma

load_dotenv()

# ── Strategy 1: RecursiveCharacterTextSplitter (baseline) ─────────────────
def chunk_recursive(docs: list[Document]) -> list[Document]:
    """Production baseline. Fast, simple, works well for structured docs."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""],
        add_start_index=True,   # adds metadata["start_index"] for debugging
    )
    chunks = splitter.split_documents(docs)
    print(f"Recursive: {len(docs)} docs → {len(chunks)} chunks")
    return chunks


# ── Strategy 2: SemanticChunker (production upgrade) ──────────────────────
def chunk_semantic(docs: list[Document]) -> list[Document]:
    """Uses embedding similarity to detect topic boundaries.
    Upgrade from recursive when retrieval quality is insufficient.
    Requires: pip install langchain-experimental
    """
    from langchain_experimental.text_splitter import SemanticChunker
    from langchain_huggingface import HuggingFaceEmbeddings

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # The splitter embeds each sentence, measures how different neighbouring sentences
    # are, and cuts where the difference is unusually large.
    # breakpoint_threshold_type decides what "unusually large" means:
    # "percentile" (default, 95): cut at the biggest 5% of differences
    # "standard_deviation" (default 3): cut where a difference is > 3 std devs above average
    splitter = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="percentile",
    )

    chunks = splitter.split_documents(docs)
    print(f"Semantic: {len(docs)} docs → {len(chunks)} chunks")
    return chunks


# ── Strategy 3: Parent-Child (context completeness) ───────────────────────
def demonstrate_parent_child():
    """
    Parent-Child Retrieval: use small child chunks to find relevant content,
    but return the larger parent chunk to the LLM for richer context.

    Architecture:
        Document  →  Parent chunks (large, for answering)
                  →  Child chunks  (small, for searching)

    At query time:
        Question → Find matching child → Look up parent → Send parent to LLM
    """
    from langchain_classic.retrievers import ParentDocumentRetriever  # built-in version (not used by RetailOps)
    from langchain_core.stores import InMemoryStore

    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,    # small for precise retrieval
        chunk_overlap=20,
    )
    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,    # larger for richer context
        chunk_overlap=100,
    )

    # Child chunks stored in vector DB; parents stored in docstore
    # (In production: use persistent ChromaDB + Redis/filesystem docstore)
    from langchain_huggingface import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Chroma(embedding_function=embeddings)
    docstore = InMemoryStore()

    retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=docstore,
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,
    )

    return retriever


# ── Strategy 4: Contextual Compression (token optimization) ───────────────
def add_contextual_compression(base_retriever):
    """
    Trim retrieved documents to only the sentences relevant to the query.
    Use after parent-child to control token costs.

    Architecture:
        Query → Retriever → Documents → Compressor → Relevant Sentences → LLM
    """
    from langchain_classic.retrievers.document_compressors import EmbeddingsFilter
    from langchain_classic.retrievers import ContextualCompressionRetriever
    from langchain_huggingface import HuggingFaceEmbeddings

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # EmbeddingsFilter: keep only sentences with similarity > threshold
    compressor = EmbeddingsFilter(
        embeddings=embeddings,
        similarity_threshold=0.76,  # tune based on your documents
    )

    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=base_retriever,
    )

    return compression_retriever


# ══════════════════════════════════════════════════════════════════════════
# RetailOps chunking pipeline (app/rag.py)
# app/rag.py defines two real functions instead of a single toggle function:
#   - split_documents(documents)          → recursive splitting (baseline)
#   - semantic_split_documents(documents) → semantic splitting (the default)
#   - chunk_documents(documents)          → picks one using ENABLE_SEMANTIC_CHUNKING
# build_retriever() in app/chains.py and rebuild_index() in app/indexing.py both
# call chunk_documents(), so the index and the in-memory BM25 copy always use the
# same chunks (see doc 31). The real semantic splitter also passes
# sentence_split_regex and min_chunk_size to SemanticChunker (described above).
# ══════════════════════════════════════════════════════════════════════════
def split_documents(documents: list[Document]) -> list[Document]:
    """Recursive splitting baseline — mirrors app/rag.py's split_documents().

    Args:
        documents: Documents from load_documents()

    Returns:
        list[Document] — chunks ready for embedding
    """
    return chunk_recursive(documents)


def semantic_split_documents(documents: list[Document]) -> list[Document]:
    """Semantic splitting upgrade — mirrors app/rag.py's semantic_split_documents().

    Args:
        documents: Documents from load_documents()

    Returns:
        list[Document] — chunks ready for embedding
    """
    return chunk_semantic(documents)


# ── Demo ──────────────────────────────────────────────────────────────────
sample_doc = Document(
    page_content="""Vacation Policy

Employees receive 18 days of paid vacation annually.
New employees are eligible after 90 days of employment.
Vacation requests must be submitted 2 weeks in advance.
Managers approve all vacation requests.

Incident Management

P1 incidents mean full store outage. Report immediately to IT.
P2 incidents mean partial outage. Report within 1 hour.
P3 incidents are single-device issues. Report within 24 hours.""",
    metadata={"source": "hr_policy.txt", "department": "HR"},
)

# Recursive chunks
recursive_chunks = chunk_recursive([sample_doc])
print(f"\n=== Recursive: {len(recursive_chunks)} chunks ===")
for i, c in enumerate(recursive_chunks):
    print(f"Chunk {i}: {c.page_content[:80]}...")
```

## 🏭 Production Best Practices

1. **Start with `RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)`** — This is your baseline. Don't add complexity until you have evidence it's needed. **Why:** Premature optimization is the biggest chunking mistake. Many systems perform well with recursive chunking on well-structured documents.

2. **Evaluate chunk quality before upgrading** — Run retrieval evaluation with your golden dataset. If source accuracy (did retrieval find the right document?) is below ~70%, improve chunking. **How:** `chunk_size` 200–400 for policy docs, 400–800 for manuals. Measure, don't guess.

3. **Always use `chunk_overlap`** — Set overlap to 10–20% of `chunk_size`. Without overlap, sentences split across chunk boundaries lose their meaning. **How:** `chunk_size=300, chunk_overlap=50`.

4. **Upgrade to semantic chunking when documents have mixed topics** — If your documents mix multiple subject areas (policy + procedures + FAQs in one file), semantic chunking will produce dramatically cleaner chunks. **Signal:** retrieval evaluation shows correct source but irrelevant content within chunks.

5. **Preserve source metadata through chunking** — Metadata from the original `Document` carries through to every chunk automatically. But add chunk-specific metadata too. **How:** Set `add_start_index=True` in `RecursiveCharacterTextSplitter` to get byte offsets for debugging.

6. **Reindex whenever you change chunking strategy** — Chunks and embeddings must match. If you switch from recursive to semantic chunking, you must rebuild the entire vector store from scratch. **How:** version your index with `DOCUMENT_VERSION` env var.

7. **Measure ROI before adding parent-child** — Parent-child increases token cost significantly. If MMR + hybrid search + cross-encoder reranking already produce good answers, parent-child adds complexity for limited benefit on small document sets.

## ⚠️ Common Mistakes to Avoid

⚠️ **Chunks that are too large (2000+ tokens)** — Large chunks mix multiple topics, degrading embedding precision and retrieval relevance. Start at 300 characters and expand only if context completeness is the problem.

⚠️ **Chunks that are too small (20-50 tokens)** — No context means no answer. A chunk containing only "18 vacation days" doesn't tell the LLM who gets them, when they're earned, or how to request them.

⚠️ **No chunk overlap** — Without overlap, the split "...employees receive 18 vacation | days annually..." creates two meaningless chunks. Always set `chunk_overlap` to 10–20% of `chunk_size`.

⚠️ **Never evaluating chunk quality** — Most teams build chunking, test 5 queries manually, and move on. This misses systematic failures. Measure source accuracy with a golden dataset after chunking.

⚠️ **Assuming semantic chunking is always better** — On short, well-structured documents, semantic chunking adds indexing cost and produces similar results, and it can cut lists and numbered steps in awkward places (see the lesson above). Measure before upgrading, and always look at the chunks it produces.

⚠️ **Changing chunking strategy without reindexing** — Chunks in the vector store must match the embeddings. If you change the splitter, you must re-embed and rebuild the index. Running mixed strategies silently produces nonsense retrieval.

## 🔗 How It Connects to Other Concepts

- **Document Loaders** (doc 09) — Loaders produce Documents; chunking is always the next step after loading
- **Embeddings** (next: doc 11) — Chunks are what gets embedded; chunk quality directly affects embedding quality
- **Vector Databases** (doc 12) — Chunks are stored in the vector DB after embedding; retrieval quality depends on chunk quality
- **Retrievers** (doc 13) — Retrievers search the chunked, embedded documents at query time
- **RAG Evaluation** (doc 19) — Source accuracy metrics reveal whether chunking is the bottleneck
- **Previous concept:** Document Loaders (doc 09) produce the `Document` objects that you split here

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Splitting large documents into smaller chunks that become the search units in a vector store |
| **Why** | Chunk quality = retrieval quality; whole-document embeddings produce noisy, imprecise retrieval |
| **When** | Always, at ingestion time, before generating embeddings |
| **Types** | `RecursiveCharacterTextSplitter` (baseline), `SemanticChunker` (meaning-aware), Parent-Child (precision + context), Contextual Compression (token optimization) |
| **Production gotcha** | Start recursive; measure with golden dataset; use overlap (10–20% of chunk_size); reindex after strategy changes; measure ROI before adding parent-child |

## ➡️ Next Steps

- **Example file:** `app/rag.py` — RetailOps `split_documents()` (recursive), `semantic_split_documents()` (semantic) and `chunk_documents()` (chooses between them)
- **Runnable demo:** see `RUN.md` in this folder (`examples/03_text_splitting.py`, `examples/19_semantic_chunking.py`)
- **Next doc:** `../11_embeddings/README.md` — converting chunks into vector representations for semantic search
- **Official docs:** https://python.langchain.com/docs/concepts/text_splitters/
