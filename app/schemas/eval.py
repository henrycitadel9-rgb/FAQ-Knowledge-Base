"""Evaluation schemas."""
from pydantic import BaseModel


class EvalRequest(BaseModel):
    """Evaluation request schema."""
    task_id: str
    answer: str


class EvalResponse(BaseModel):
    """Evaluation response schema."""
    score: float
    feedback: str
