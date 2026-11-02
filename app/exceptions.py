class RetailOpsError(Exception):
    """Base class. Each error carries a short code, a user-safe message and an HTTP status."""

    code = "internal_error"
    user_message = "Sorry, I could not process your request right now. Please try again later."
    http_status = 500


class LLMError(RetailOpsError):
    """The model provider failed (after any retry)."""

    code = "llm_error"
    http_status = 502  # the upstream service failed, not this app


class ModelRefusalError(LLMError):
    """The model declined to produce the structured output we required."""

    code = "model_refused"
    user_message = "I can't help with that request. Please rephrase your question."
    http_status = 422


class RateLimitError(LLMError):
    """The provider's rate limit was still exceeded after the SDK's own retries."""

    code = "rate_limited"
    user_message = "The AI service is busy right now. Please wait a moment and try again."
    http_status = 429


class ModelUnavailableError(LLMError):
    """The configured model does not exist or has been retired."""

    code = "model_unavailable"
    user_message = "The configured AI model is not available. Ask an administrator to check LLM_MODEL."
    http_status = 503


# Lets the API turn the `error` code in a result dict into an HTTP status.
HTTP_STATUS_BY_CODE = {
    cls.code: cls.http_status
    for cls in (
        RetailOpsError,
        LLMError,
        ModelRefusalError,
        RateLimitError,
        ModelUnavailableError,
    )
}
