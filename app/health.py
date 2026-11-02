from app.cache import response_cache
from app.container import get_container
from app.config import settings


def get_health_status() -> dict:
    status = {
        "status": "ok",
        "app_env": settings.app_env,
        "app_version": settings.app_version,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "tools_llm_model": settings.tools_llm_model,
        "vectorstore_dir": settings.vectorstore_dir,
        "cache_size": response_cache.size(),
        "components": {},
        
    }

    try:
        container = get_container()
        status["index_status"] = container.index_status
        status["components"] = {
            "general_chat_chain": container.general_chat_chain is not None,
            "rag_chain": container.rag_chain is not None,
            "tool_agent": container.tool_agent is not None,
            "router_chain": container.router_chain is not None,
        }

    except Exception:
        status["status"] = "degraded"
        status["components"] = {
            "container": False
        }

    return status