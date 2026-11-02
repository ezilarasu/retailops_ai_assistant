from app.config import settings


def trace_config(route: str, request_id: str) -> dict:
    return {
        "tags": [
            "retailops",
            route,
            settings.app_env,
        ],
        "metadata": {
            "request_id": request_id,
            "environment": settings.app_env,
            "app_version": settings.app_version,
            "route": route,
        },
    }