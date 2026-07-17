"""Evaluation routes."""
from fastapi import APIRouter

router = APIRouter(prefix="/eval", tags=["Evaluation"])

@router.post("/score")
def score_response(response: str):
    """Score a response."""
    return {"score": 0.0}
