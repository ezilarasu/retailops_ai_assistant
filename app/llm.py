import logging

import groq
from langchain_groq import ChatGroq

from app.config import settings
from app.exceptions import (
    LLMError,
    ModelRefusalError,
    ModelUnavailableError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


def get_llm(model: str | None = None):
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is missing. Add it to your .env file.")

    return ChatGroq(
        model=model or settings.llm_model,
        temperature=settings.temperature,
        api_key=settings.groq_api_key,
    )


def _error_field(error: Exception, field: str) -> str:
    body = getattr(error, "body", None)
    inner = body.get("error", body) if isinstance(body, dict) else None
    value = inner.get(field) if isinstance(inner, dict) else None
    return value if isinstance(value, str) else ""


def _is_retryable(error: Exception) -> bool:
    if isinstance(error, (groq.APIConnectionError, groq.APITimeoutError, groq.InternalServerError)):
        return True

    if isinstance(error, groq.BadRequestError):
        code = _error_field(error, "code")
        # The model produced something unparseable (or nothing). Another attempt usually works.
        if code == "output_parse_failed":
            return True
        # tool_use_failed with no text means a hiccup; with text it is a refusal (see translate_llm_error).
        return code == "tool_use_failed" and not _error_field(error, "failed_generation").strip()

    return False


def translate_llm_error(error: Exception) -> LLMError:
    """Turn a provider exception into one of our typed errors."""
    if isinstance(error, groq.RateLimitError):
        return RateLimitError(str(error))

    if isinstance(error, groq.NotFoundError):
        return ModelUnavailableError(str(error))

    if isinstance(error, groq.BadRequestError):
        code = _error_field(error, "code")
        # The structured-output call requires the model to call a tool. If it answered in
        # prose instead ("I can't comply"), it refused; retrying will not change that.
        if code == "tool_use_failed" and _error_field(error, "failed_generation").strip():
            return ModelRefusalError(str(error))

    return LLMError(str(error))


def invoke_with_retry(call, attempts: int = 2):
    """Run `call()` (a function that invokes a chain or agent).

    Retries once on transient failures (unparseable model output, connection problems,
    5xx). Rate limits, refusals and missing models are not retried. Provider errors are
    raised as typed RetailOpsError subclasses; anything else passes through unchanged.
    """
    for attempt in range(1, attempts + 1):
        try:
            return call()
        except (groq.APIError, groq.APIConnectionError) as error:
            if _is_retryable(error) and attempt < attempts:
                logger.warning(
                    "llm_retry attempt=%s error_type=%s code=%s",
                    attempt,
                    type(error).__name__,
                    _error_field(error, "code"),
                )
                continue

            raise translate_llm_error(error) from error
