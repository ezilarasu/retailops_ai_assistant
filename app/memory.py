from langchain_core.chat_history import InMemoryChatMessageHistory

DEFAULT_SESSION = "default"

# One conversation history per session id, kept in this process's memory only.
# (It is lost on restart and not shared between workers; see docs/24_memory.)
_histories: dict[str, InMemoryChatMessageHistory] = {}


def _history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in _histories:
        _histories[session_id] = InMemoryChatMessageHistory()

    return _histories[session_id]


def add_user_message(message: str, session_id: str = DEFAULT_SESSION):
    _history(session_id).add_user_message(message)


def add_ai_message(message: str, session_id: str = DEFAULT_SESSION):
    _history(session_id).add_ai_message(message)


def get_messages(session_id: str = DEFAULT_SESSION):
    history = _histories.get(session_id)

    return history.messages if history else []


def clear_memory(session_id: str = DEFAULT_SESSION):
    _histories.pop(session_id, None)
