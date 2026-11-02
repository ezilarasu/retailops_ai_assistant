from functools import lru_cache

from app.chains import (
    build_general_chat_chain,
    build_question_rewriter_chain,
    build_rag_chain,
    build_rag_generator,
    build_retriever,
    build_router_chain,
    build_tool_agent,
)
from app.indexing import ensure_index_current


class AppContainer:
    def __init__(self):
        self.index_status = ensure_index_current()

        # The pieces of the RAG pipeline, built once and shared by the RAG chain,
        # the /debug/retrieval endpoint and the LangGraph version (app/graph).
        self.retriever = build_retriever()
        self.rewriter_chain = build_question_rewriter_chain()
        self.rag_generator = build_rag_generator()

        self.general_chat_chain = build_general_chat_chain()
        self.rag_chain = build_rag_chain(
            self.retriever, self.rewriter_chain, self.rag_generator
        )
        self.tool_agent = build_tool_agent()
        self.router_chain = build_router_chain()


@lru_cache(maxsize=1)
def get_container() -> AppContainer:
    return AppContainer()
