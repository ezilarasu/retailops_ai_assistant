import json
from pathlib import Path

from langchain_chroma import Chroma

from app.config import settings
from app.rag import chunk_documents, load_documents
from app.vectorstore import EMBEDDING_MODEL_NAME, build_vectorstore, get_embeddings


def manifest_path() -> Path:
    # Next to the index folder, not inside it, so rebuilding the index never touches it.
    return Path(settings.vectorstore_dir).parent / "manifest.json"


def index_fingerprint() -> dict:
    """Everything that, if changed, makes an existing index out of date."""
    fingerprint = {
        "document_version": settings.document_version,
        "semantic_chunking": settings.enable_semantic_chunking,
        "embedding_model": EMBEDDING_MODEL_NAME,
    }

    # Chunk size and overlap only matter for the recursive splitter.
    if not settings.enable_semantic_chunking:
        fingerprint["chunk_size"] = settings.chunk_size
        fingerprint["chunk_overlap"] = settings.chunk_overlap

    return fingerprint


def get_manifest() -> dict | None:
    path = manifest_path()

    if not path.exists():
        return None

    with open(path, "r") as file:
        return json.load(file)


def write_manifest(chunk_count: int) -> None:
    path = manifest_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {**index_fingerprint(), "chunk_count": chunk_count}

    with open(path, "w") as file:
        json.dump(manifest, file, indent=2)


def rebuild_index() -> dict:
    store_path = Path(settings.vectorstore_dir)

    if store_path.exists():
        # Delete the collection through Chroma rather than deleting the folder: code that is
        # already running keeps the folder's database file open, and removing the file under
        # it causes "attempt to write a readonly database" errors.
        Chroma(
            persist_directory=str(store_path),
            embedding_function=get_embeddings(),
        ).delete_collection()

    chunks = chunk_documents(load_documents())

    build_vectorstore(chunks)

    write_manifest(chunk_count=len(chunks))

    return {
        "status": "rebuilt",
        "document_version": settings.document_version,
        "chunk_count": len(chunks),
    }


def ensure_index_current() -> dict:
    manifest = get_manifest()

    if (
        manifest is None
        or not Path(settings.vectorstore_dir).exists()
        or any(manifest.get(key) != value for key, value in index_fingerprint().items())
    ):
        return rebuild_index()

    return {
        "status": "current",
        "document_version": settings.document_version,
        "chunk_count": manifest.get("chunk_count"),
    }
