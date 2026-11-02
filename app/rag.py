from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)
from app.config import settings
from app.vectorstore import get_embeddings
from langchain_experimental.text_splitter import SemanticChunker
from app.config import settings


DATA_DIR = Path("data")

# Split after . ? ! but not right after a bare list number like " 6." or "\n12.".
SENTENCE_SPLIT_REGEX = r"(?<=[.?!])(?<!\s\d\.)(?<!\s\d\d\.)\s+"
SEMANTIC_MIN_CHUNK_SIZE = 300  # characters


def load_documents():
    documents = []

    for file_path in DATA_DIR.glob("*.txt"):
        loader = TextLoader(str(file_path))

        docs = loader.load()

        documents.extend(docs)

    return documents

def split_documents(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap
    )

    return splitter.split_documents(documents)

def chunk_documents(documents):
    """Split with the configured strategy: semantic by default, recursive otherwise.

    Index building and the retrievers must use the same strategy, so they all call this.
    """
    if settings.enable_semantic_chunking:
        return semantic_split_documents(documents)

    return split_documents(documents)


def semantic_split_documents(documents):
    """
    Production-style splitter: embedding/meaning-based.
    Splits documents where semantic topic shifts occur.
    """
    embeddings = get_embeddings()

    splitter = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="percentile",
        # The default sentence splitter cuts after every ".", so the "6." of a numbered
        # list counted as a sentence end and a checklist was split in half. This pattern
        # does not split after a bare list number.
        sentence_split_regex=SENTENCE_SPLIT_REGEX,
        # A percentile rule always finds some split point, even in a short single-topic
        # document. Ignore splits that would leave a fragment smaller than this.
        min_chunk_size=SEMANTIC_MIN_CHUNK_SIZE,
    )

    return splitter.split_documents(documents)