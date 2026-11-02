import hmac

from fastapi import Header, HTTPException, status

from app.config import DEFAULT_API_KEY, settings


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    # compare_digest takes the same time however many leading characters match,
    # so response timing does not leak how close a guess was.
    if x_api_key is None or not hmac.compare_digest(
        x_api_key.encode("utf-8"), settings.app_api_key.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )


def check_api_key_configured() -> None:
    """Refuse to start with the well-known default key anywhere except local development."""
    if settings.app_env != "local" and settings.app_api_key == DEFAULT_API_KEY:
        raise RuntimeError(
            "APP_API_KEY is still the default value. Set a private APP_API_KEY in .env "
            "(or set APP_ENV=local for local development)."
        )
