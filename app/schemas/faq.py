"""FAQ schemas."""
from pydantic import BaseModel


class FAQItem(BaseModel):
    """FAQ item schema."""
    id: str
    question: str
    answer: str


class FAQQuery(BaseModel):
    """FAQ query schema."""
    query: str
