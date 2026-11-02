import hashlib
from functools import lru_cache

from langchain_huggingface import (
    HuggingFaceEmbeddings
)
from langchain_chroma import Chroma
from app.config import settings
from app.hybrid_retriever import HybridRetriever


EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embeddings():
    # Cached: every HuggingFaceEmbeddings() reloads the model, so share one instance.

    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME
    )
    
def _chunk_id(chunk) -> str:
    key = f"{chunk.metadata.get('source', '')}\n{chunk.page_content}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def build_vectorstore(chunks):

    embeddings = get_embeddings()

    # Chroma upserts by ID. Content-based IDs make re-adding the same chunk a
    # no-op; the default random IDs appended a full duplicate copy on every call.
    unique_chunks = {_chunk_id(chunk): chunk for chunk in chunks}

    db = Chroma.from_documents(
        documents=list(unique_chunks.values()),
        ids=list(unique_chunks.keys()),
        embedding=embeddings,
        persist_directory=settings.vectorstore_dir
    )

    return db

def get_retriever(db):

    return db.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": settings.retrieval_k
        }
    )
    



def get_hybrid_retriever(db, chunks):
    vector_retriever = get_retriever(db)

    return HybridRetriever(
        vector_retriever=vector_retriever,
        documents=chunks,
        top_k=settings.retrieval_k,
    )