from typing import Literal
from pydantic import BaseModel, Field


class RAGResponse(BaseModel):
    answer: str = Field(
        description="Answer to the user's question using only the provided context."
    )
    sources: list[str] = Field(
        description="Source document names used to answer the question."
    )
    confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence based only on the provided context."
    )
    
class RouteDecision(BaseModel):
    route: Literal["general", "rag", "tools"] = Field(
        description="The best route for the user question."
    )
    reason: str = Field(
        description="Short reason for the routing decision."
    )
    
from typing import Optional


class ChatRequest(BaseModel):
    question: str = Field(
        description="User question for the RetailOps AI Assistant."
    )
    session_id: str = Field(
        default="default",
        max_length=100,
        description="Conversation id. Requests with the same id share chat history.",
    )


class ChatResponse(BaseModel):
    request_id: str
    route: str
    reason: str
    answer: str
    sources: Optional[list[str]] = None
    confidence: Optional[str] = None
    latency_ms: float
    cache_hit: bool = False


class ErrorResponse(BaseModel):
    request_id: str
    route: str = "error"
    reason: str
    answer: str
    latency_ms: float
    error: Optional[str] = None
    
class JudgeResult(BaseModel):
    correct: bool
    grounded: bool
    complete: bool
    explanation: str