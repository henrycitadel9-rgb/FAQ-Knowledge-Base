"""FAQ routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db import models, session
from datetime import datetime

router = APIRouter(prefix="/api/faq", tags=["FAQ"])

@router.get("/")
def get_faq(category: str = None, db: Session = Depends(session.get_db)):
    """Get FAQ items, optionally filtered by category."""
    query = db.query(models.FAQ).filter(models.FAQ.is_active == True)
    if category:
        query = query.filter(models.FAQ.category == category)
    faqs = query.all()
    return {"faqs": [{"id": faq.id, "faq_number": faq.faq_number, "category": faq.category, "question": faq.canonical_question, "answer": faq.official_answer, "source_ref": faq.source_ref} for faq in faqs]}

@router.get("/{faq_id}")
def get_faq_detail(faq_id: int, db: Session = Depends(session.get_db)):
    """Get detailed FAQ by ID."""
    faq = db.query(models.FAQ).filter(models.FAQ.id == faq_id, models.FAQ.is_active == True).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return {
        "id": faq.id,
        "faq_number": faq.faq_number,
        "category": faq.category,
        "question": faq.canonical_question,
        "answer": faq.official_answer,
        "source_needed": faq.source_needed,
        "tags": faq.tags,
        "keywords": faq.keywords,
        "source_ref": faq.source_ref,
        "created_at": faq.created_at
    }

@router.get("/search/")
def search_faqs(q: str, db: Session = Depends(session.get_db)):
    """Search FAQs by query string."""
    if not q:
        return {"faqs": []}
    search_term = f"%{q}%"
    faqs = db.query(models.FAQ).filter(
        models.FAQ.is_active == True,
        or_(
            models.FAQ.canonical_question.ilike(search_term),
            models.FAQ.official_answer.ilike(search_term),
            models.FAQ.tags.ilike(search_term),
            models.FAQ.keywords.ilike(search_term)
        )
    ).all()
    return {"faqs": [{"id": faq.id, "faq_number": faq.faq_number, "category": faq.category, "question": faq.canonical_question, "answer": faq.official_answer, "source_ref": faq.source_ref} for faq in faqs]}

@router.post("/log")
def log_interaction(log_data: dict, db: Session = Depends(session.get_db)):
    """Log FAQ interactions."""
    log_entry = models.ChatLog(
        interface_type=log_data.get("interface_type", "faq"),
        user_query=log_data.get("user_query", ""),
        matched_faq_id=log_data.get("matched_faq_id"),
        system_answer=log_data.get("system_answer", ""),
        source_ref=log_data.get("source_ref", ""),
        latency_ms=log_data.get("latency_ms", 0),
        created_at=datetime.utcnow().isoformat()
    )
    db.add(log_entry)
    db.commit()
    return {"status": "logged"}
