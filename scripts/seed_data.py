#!/usr/bin/env python3
"""Seed database with initial data using SQLAlchemy models."""
import sys
import json
import os
from datetime import datetime
from pathlib import Path

# Ensure project root is on sys.path so `from app...` imports work when running this script directly
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.db.session import engine, SessionLocal
from app.db.models import Base, FAQ


def seed_data():
    """Load data from data/kb.json into the database via SQLAlchemy."""
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "kb.json")
    if not os.path.exists(path):
        path = os.path.join(os.getcwd(), "data", "kb.json")
    if not os.path.exists(path):
        print(f"kb.json not found at expected locations: {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        kb_items = json.load(f)
    # Support files where KB is under a top-level "items" key
    if isinstance(kb_items, dict) and "items" in kb_items:
        kb_items = kb_items["items"]

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        for item in kb_items:
            faq_number_val = item.get("faq_number") or item.get("id") or 0
            # Skip if an entry with this faq_number already exists
            existing = db.query(FAQ).filter(FAQ.faq_number == faq_number_val).first()
            if existing:
                continue

            faq = FAQ(
                faq_number=faq_number_val,
                category=item.get("category") or "",
                canonical_question=item.get("canonical_question") or item.get("question") or "",
                official_answer=item.get("official_answer") or item.get("answer") or "",
                source_needed=item.get("source_needed") or "",
                tags=(",".join(item.get("tags", [])) if isinstance(item.get("tags"), list) else item.get("tags")) or "",
                keywords=(",".join(item.get("keywords", [])) if isinstance(item.get("keywords"), list) else item.get("keywords")) or "",
                source_ref=item.get("source_ref") or "",
                is_active=item.get("is_active", True),
                created_at=item.get("created_at") or datetime.utcnow().isoformat(),
            )
            db.add(faq)

        db.commit()
        print("Database seeded successfully with kb.json items.")
    except Exception as exc:
        db.rollback()
        print(f"Error seeding database: {exc}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
