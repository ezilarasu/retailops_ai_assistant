import hashlib
import time


class SimpleTTLCache:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self.store: dict[str, tuple[float, dict]] = {}

    def _key(self, text: str) -> str:
        normalized = text.strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def get(self, text: str) -> dict | None:
        key = self._key(text)

        if key not in self.store:
            return None

        created_at, value = self.store[key]

        if time.time() - created_at > self.ttl_seconds:
            del self.store[key]
            return None

        return value

    def set(self, text: str, value: dict) -> None:
        key = self._key(text)
        self.store[key] = (time.time(), value)
    
    def size(self) -> int:
        return len(self.store)

    def clear(self) -> None:
        self.store.clear()


response_cache = SimpleTTLCache(ttl_seconds=300)