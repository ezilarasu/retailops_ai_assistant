# Document Loaders
> The entry point for any RAG system — converting files into LangChain's standard knowledge format.

## 📌 What Is It?

A **Document Loader** reads external data (files, web pages, databases) and converts it into `Document` objects — LangChain's standard container for text content.

Think of it like an immigration checkpoint:
```
PDF files, Word docs, web pages, databases  →  [Document Loader]  →  Document objects
```

Every document that enters a RAG system must pass through a loader. The loader handles the messy reality of different file formats so that the rest of your pipeline — chunking, embeddings, retrieval — only ever sees the same clean `Document` structure.

## ❓ Why Does It Exist?

LLMs can't read files. They process text. And real-world knowledge lives in PDFs, HTML pages, SharePoint sites, Confluence wikis, S3 buckets, and database tables.

Without document loaders, you'd need to write custom extraction code for every format:
```python
# Manual for every format:
text = extract_text_from_pdf(path)
soup = BeautifulSoup(html, "html.parser")
text = soup.get_text()
# etc.
```

With document loaders:
```python
loader = PyPDFLoader("employee_handbook.pdf")
docs = loader.load()   # always returns list[Document]
```

Same `.load()` method, same `Document` output, regardless of source. Your chunking, embedding, and retrieval code never changes when you add a new document type.

## ⏰ When Should You Use It?

✅ Any time you're ingesting external documents into a RAG system  
✅ When building a knowledge base from files (PDFs, TXTs, Word docs)  
✅ When ingesting web pages, Confluence, or SharePoint content  
✅ Any time you need to load multiple files from a directory  

❌ Don't use loaders for real-time operational data (inventory, orders, incidents) — use **Tools** instead  
❌ Don't reload documents on every user request — load once at ingestion time, store in vector DB  
❌ Don't use RAG for data that changes by the minute — use tools for live queries  

## 🗂️ Types / Variants

| Type | Class | Source | Best For |
|---|---|---|---|
| Text file | `TextLoader` | `.txt` files | Simple policy docs, SOPs, FAQs |
| PDF | `PyPDFLoader` | PDF files | Employee handbooks, contracts, manuals |
| Directory | `DirectoryLoader` | Folder of files | Bulk ingestion of multiple files |
| Web page | `WebBaseLoader` | URLs | External documentation, Confluence pages |
| CSV | `CSVLoader` | `.csv` files | Tabular knowledge (product catalogs, FAQs) |
| Word | `Docx2txtLoader` | `.docx` files | Internal documentation |
| Unstructured | `UnstructuredFileLoader` | Mixed formats | Auto-detect and extract from any format |

## 🔀 When to Use Which Type

**`TextLoader`** for simple plain-text files — fastest, no dependencies, no parsing edge cases. RetailOps uses this for all its current `.txt` knowledge documents.

**`PyPDFLoader`** for PDFs — produces one `Document` per page, which is important to know because you'll need to chunk further anyway.

**`DirectoryLoader`** when you have a folder of similar documents and want to load them all at once. Pair with a glob pattern: `DirectoryLoader("data/", glob="**/*.txt")`.

**`WebBaseLoader`** for web pages. Be aware: it loads the full HTML text, which includes navigation menus and footers — you may need to filter the output.

**Tools (not loaders)** for anything operational or real-time: current inventory counts, order statuses, open incidents. These change too fast to index and should be queried live.

## ⚖️ Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Consistent output — all loaders produce `list[Document]` | PDF extraction can be messy (tables, multi-column layouts) |
| Handles format-specific complexity | Web loaders include nav/footer text requiring cleanup |
| Metadata is automatically captured | No built-in deduplication |
| Large ecosystem (100+ loaders in `langchain_community`) | Large PDFs = one `Document` per page = expensive chunking |
| Easy to swap formats without changing downstream pipeline | CSV/tabular data needs special handling for structured content |

## 💻 Basic Example

```python
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    DirectoryLoader,
    CSVLoader,
)
from langchain_core.documents import Document

load_dotenv()

# ── TextLoader: simplest loader ───────────────────────────────────────────
loader = TextLoader("data/hr_policy.txt")
docs = loader.load()   # returns list[Document]

print(f"Loaded {len(docs)} document(s)")
print(f"Content preview: {docs[0].page_content[:100]}")
print(f"Metadata: {docs[0].metadata}")
# → {"source": "data/hr_policy.txt"}

# ── PyPDFLoader: one Document per page ────────────────────────────────────
pdf_loader = PyPDFLoader("employee_handbook.pdf")
pdf_docs = pdf_loader.load()

print(f"Pages loaded: {len(pdf_docs)}")
print(f"Page 1 metadata: {pdf_docs[0].metadata}")
# → {"source": "employee_handbook.pdf", "page": 0}

# ── DirectoryLoader: load all .txt files in a folder ─────────────────────
dir_loader = DirectoryLoader(
    "data/",
    glob="**/*.txt",   # only load .txt files (recursive)
    loader_cls=TextLoader,
)
all_docs = dir_loader.load()
print(f"Loaded {len(all_docs)} documents from directory")

# ── Inspecting the Document object ────────────────────────────────────────
doc = all_docs[0]
print(f"Type: {type(doc)}")            # Document
print(f"Content: {doc.page_content[:80]}")
print(f"Source: {doc.metadata['source']}")
```

## 🔧 Real-World Example

This is RetailOps' ingestion pipeline. Notice the metadata enrichment — adding department, version, and document type so the vector store can filter by metadata in the future.

```python
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_core.documents import Document

load_dotenv()

# ══════════════════════════════════════════════════════════════════════════
# app/rag.py — RetailOps document loading with metadata enrichment
# The real load_documents() in app/rag.py is simpler: it globs data/*.txt,
# loads each file with TextLoader(str(file_path)) (no encoding argument) and
# adds NO extra metadata beyond TextLoader's {"source": "data/<file>.txt"}.
# The department/version/access values below are illustrative (they are not
# in the repo); this version shows the production upgrade.
# Note: data/inventory.csv, vendors.csv and incidents.json are NOT loaded here —
# the tools in app/tools.py read them directly with pandas/json (doc 20).
# ══════════════════════════════════════════════════════════════════════════

# Metadata map — define what each document is about for future filtering
DOCUMENT_METADATA = {
    "hr_policy.txt": {
        "department": "HR",
        "doc_type": "policy",
        "version": "v2",
        "access": "all_employees",
    },
    "returns_refunds_policy.txt": {
        "department": "Operations",
        "doc_type": "policy",
        "version": "v3",
        "access": "all_employees",
    },
    "store_operations_sop.txt": {
        "department": "Operations",
        "doc_type": "sop",
        "version": "v1",
        "access": "store_managers",
    },
    "it_support_kb.txt": {
        "department": "IT",
        "doc_type": "knowledge_base",
        "version": "v2",
        "access": "all_employees",
    },
}

def load_documents(data_dir: str = "data/") -> list[Document]:
    """Load all knowledge documents and enrich with metadata.

    Returns:
        list[Document] — all documents ready for chunking and indexing
    """
    all_docs = []

    for filename, extra_metadata in DOCUMENT_METADATA.items():
        filepath = Path(data_dir) / filename

        if not filepath.exists():
            print(f"Warning: {filepath} not found — skipping")
            continue

        # Load the file
        loader = TextLoader(str(filepath), encoding="utf-8")
        docs = loader.load()  # typically 1 Document per .txt file

        # Enrich each Document with additional metadata
        for doc in docs:
            doc.metadata.update({
                "filename": filename,
                **extra_metadata,
            })
            all_docs.append(doc)

    print(f"Loaded {len(all_docs)} document(s) from {data_dir}")
    return all_docs


def load_documents_from_directory(data_dir: str = "data/") -> list[Document]:
    """Alternative: load all .txt files from a directory automatically."""
    loader = DirectoryLoader(
        data_dir,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    return loader.load()


# ── Verify metadata is captured ───────────────────────────────────────────
if __name__ == "__main__":
    # Create a mock doc to test structure
    sample = Document(
        page_content="Employees receive 18 days of paid vacation annually.",
        metadata={
            "source": "data/hr_policy.txt",
            "filename": "hr_policy.txt",
            "department": "HR",
            "doc_type": "policy",
            "version": "v2",
            "access": "all_employees",
        }
    )

    print(f"Content:  {sample.page_content}")
    print(f"Source:   {sample.metadata['source']}")
    print(f"Dept:     {sample.metadata['department']}")
    print(f"Access:   {sample.metadata['access']}")

    # This metadata enables future filtering:
    # retriever.search(query, filter={"department": "HR"})
    # retriever.search(query, filter={"access": "all_employees"})
```

## 🏭 Production Best Practices

1. **Always enrich metadata at load time** — The default `{"source": "file.txt"}` is too thin for production. Add `department`, `doc_type`, `version`, `access_level`, and `last_updated` at ingestion. **Why:** Metadata enables filtering (only show HR docs to HR users), source attribution, and audit trails. It cannot be added later without reindexing.

2. **Separate ingestion from serving** — Load and index documents once (on startup or via a scheduled job). Don't reload files on every user request. **How:** In RetailOps, `load_documents()` in `app/rag.py` runs when the RAG chain is built (at startup) and when the index is rebuilt, before splitting and embedding. (The `/debug/retrieval` endpoint reloads and re-indexes on every call — fine for debugging, not a pattern to copy for user traffic.)

3. **Use `DirectoryLoader` for bulk ingestion** — When adding document types, drop files in the data folder rather than updating code. **How:** `DirectoryLoader("data/", glob="**/*.pdf")` — add PDFs without changing ingestion code.

4. **Validate documents after loading** — Empty `page_content`, corrupt PDFs, and encoding errors are common. Check before indexing. **How:**
   ```python
   valid = [d for d in docs if d.page_content.strip()]
   print(f"Skipped {len(docs) - len(valid)} empty documents")
   ```

5. **Track document versions** — When a policy changes, reindex with a new version tag. **How:** Use `metadata["version"] = "v3"` and a `DOCUMENT_VERSION` environment variable in your ingestion pipeline. Your evaluation reports can then track answer quality across versions.

6. **Use Tools for operational data, not loaders** — Inventory levels, order statuses, and incident tickets change constantly. Loading them into a vector store means stale data. Query them live via tools. **Rule:** if the data changes more than once a day, it belongs in a tool, not a RAG index.

## ⚠️ Common Mistakes to Avoid

⚠️ **Ignoring metadata** — Loading documents without metadata means no source attribution, no filtering, and no access control. Add metadata at load time — it costs nothing and enables enterprise features later.

⚠️ **Using RAG for live operational data** — "How many units of SKU-123 are in stock?" cannot be answered by a vector store that was indexed yesterday. Use a tool that queries the inventory system live.

⚠️ **Reloading documents on every request** — Loading and parsing all documents per user query is catastrophically slow. Load once, store embeddings in a vector database, serve from there.

⚠️ **Loading PDFs as one huge Document** — `PyPDFLoader` returns one `Document` per page. A 100-page handbook produces 100 documents, each needing further chunking. Understand what your loader produces before wiring it into chunking.

⚠️ **Assuming all loaders handle encoding** — `TextLoader` defaults to the system encoding, which may not be UTF-8. Always specify `encoding="utf-8"` explicitly to avoid silent corruption.

## 🔗 How It Connects to Other Concepts

- **Text Splitters & Chunking** (next: doc 10) — Documents from loaders are the input to chunking; the pipeline is `Loader → Splitter → Embeddings`
- **Embeddings** (doc 11) — Chunked Documents become embeddings; the `Document.page_content` is what gets embedded
- **Vector Databases** (doc 12) — The indexed store for embedded Documents; `vectorstore.add_documents(docs)` is the API
- **Retrievers** (doc 13) — Query the vector store at query time to find relevant Documents; opposite of loaders
- **Tools** (doc 20) — The alternative for real-time / operational data that shouldn't go through a loader

## 📚 Summary Table

| | Detail |
|---|---|
| **What** | Components that convert external files/data into `Document(page_content, metadata)` objects |
| **Why** | Standardizes heterogeneous sources into one format for chunking, embedding, and retrieval |
| **When** | Ingestion time only — when building or updating the knowledge base; not at query time |
| **Types** | `TextLoader` (txt), `PyPDFLoader` (pdf), `DirectoryLoader` (bulk), `WebBaseLoader` (URLs), `CSVLoader` (tables) |
| **Production gotcha** | Always enrich metadata at load time; validate non-empty content; separate ingestion from serving; use Tools for live data |

## ➡️ Next Steps

- **Example file:** `app/rag.py` — RetailOps `load_documents()` (see `app/rag.py:16-26`)
- **Runnable demo:** see `RUN.md` in this folder (`examples/02_document_loading.py`)
- **Next doc:** `../10_text_splitters_and_chunking/README.md` — splitting loaded documents into retrieval-quality chunks
- **Official docs:** https://python.langchain.com/docs/concepts/document_loaders/
