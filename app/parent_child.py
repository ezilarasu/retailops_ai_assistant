from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.vectorstore import get_embeddings


def create_parent_child_chunks(
    documents: list[Document],
    parent_chunk_size: int = 1000,
    parent_chunk_overlap: int = 100,
):
    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=parent_chunk_size,
        chunk_overlap=parent_chunk_overlap,
    )

    semantic_child_splitter = SemanticChunker(
        embeddings=get_embeddings(),
        breakpoint_threshold_type="percentile",
    )

    parent_docs = parent_splitter.split_documents(documents)

    parent_store = {}
    child_docs = []

    for parent_index, parent_doc in enumerate(parent_docs):
        parent_id = f"parent-{parent_index}"

        parent_doc.metadata["parent_id"] = parent_id
        parent_store[parent_id] = parent_doc

        children = semantic_child_splitter.split_documents([parent_doc])

        for child_index, child_doc in enumerate(children):
            child_doc.metadata["parent_id"] = parent_id
            child_doc.metadata["child_id"] = f"{parent_id}-child-{child_index}"
            child_doc.metadata["source"] = parent_doc.metadata.get("source")

            child_docs.append(child_doc)

    return parent_store, child_docs


def get_parent_documents(
    child_documents: list[Document],
    parent_store: dict[str, Document],
    max_parents: int = 4,
) -> list[Document]:
    seen_parent_ids = set()
    parents = []

    for child_doc in child_documents:
        parent_id = child_doc.metadata.get("parent_id")

        if not parent_id:
            continue

        if parent_id in seen_parent_ids:
            continue

        parent_doc = parent_store.get(parent_id)

        if parent_doc:
            seen_parent_ids.add(parent_id)
            parents.append(parent_doc)

        if len(parents) >= max_parents:
            break

    return parents