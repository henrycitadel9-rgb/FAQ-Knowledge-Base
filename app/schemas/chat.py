"""Chat schemas."""
from pydantic import BaseModel, Field
from typing import List, Optional


class ChatRequest(BaseModel):
    """Chat request schema."""
    message: str


class ChatMatch(BaseModel):
    """Matched FAQ payload for disambiguation or multi-result responses."""
    faq_id: int
    question: str
    answer: str
    source: str
    confidence: float
    matched_terms: List[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Chat response schema."""
    question: str
    answer: str
    source: str
    confidence: float
    response_type: str = "single"
    matches: List[ChatMatch] = Field(default_factory=list)
