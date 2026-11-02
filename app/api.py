from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse

from app.cache import response_cache
from app.container import get_container
from app.debug import debug_retrieval
from app.exceptions import HTTP_STATUS_BY_CODE
from app.health import get_health_status
from app.indexing import rebuild_index
from app.logging_config import configure_logging
from app.memory import DEFAULT_SESSION, clear_memory
from app.schemas import ChatRequest, ChatResponse
from app.security import check_api_key_configured, verify_api_key
from app.services import assistant_service

configure_logging()
check_api_key_configured()

app = FastAPI(
    title="RetailOps AI Assistant",
    version="1.0.0",
    description="Production-style LangChain RAG assistant for retail operations.",
)


@app.get("/health")
def health_check():
    return get_health_status()


@app.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[Depends(verify_api_key)],
)
def chat(request: ChatRequest):
    result = assistant_service.ask(request.question, request.session_id)

    if result["route"] == "error":
        return JSONResponse(
            status_code=HTTP_STATUS_BY_CODE.get(result.get("error"), 500),
            content=result,
        )

    return result


@app.post(
    "/memory/clear",
    dependencies=[Depends(verify_api_key)],
)
def clear_chat_memory(session_id: str = DEFAULT_SESSION):
    clear_memory(session_id)
    return {"status": "memory cleared", "session_id": session_id}


@app.post(
    "/index/rebuild",
    dependencies=[Depends(verify_api_key)],
)
def rebuild_vector_index():
    result = rebuild_index()

    # The running chains still hold the old index (and an in-memory BM25 copy of the old
    # chunks), and cached answers came from the old documents. Drop both, then rebuild the
    # chains on the fresh index so no restart is needed.
    get_container.cache_clear()
    response_cache.clear()
    get_container()

    return result


@app.post(
    "/debug/retrieval",
    dependencies=[Depends(verify_api_key)],
)
def debug_retrieval_endpoint(request: ChatRequest):
    return debug_retrieval(request.question, request.session_id)
