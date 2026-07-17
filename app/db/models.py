"""Database models."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class FAQ(Base):
    __tablename__ = "faqs"
    
    id = Column(Integer, primary_key=True)
    faq_number = Column(Integer)
    category = Column(String)
    canonical_question = Column(String, nullable=False)
    official_answer = Column(String, nullable=False)
    source_needed = Column(String)
    tags = Column(String)
    keywords = Column(String)
    source_ref = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(String)  # Assuming it's stored as string

class FAQAlias(Base):
    __tablename__ = "faq_aliases"
    
    id = Column(Integer, primary_key=True)
    faq_id = Column(Integer)
    alias_question = Column(String, nullable=False)

class ChatLog(Base):
    __tablename__ = "chat_logs"
    
    id = Column(Integer, primary_key=True)
    interface_type = Column(String)
    user_query = Column(String)
    matched_faq_id = Column(Integer)
    system_answer = Column(String)
    source_ref = Column(String)
    latency_ms = Column(Integer)
    created_at = Column(String)

class AICache(Base):
    __tablename__ = "ai_cache"
    
    id = Column(Integer, primary_key=True)
    normalized_query = Column(String)
    matched_faq_id = Column(Integer)
    cached_answer = Column(String)
    model_name = Column(String)
    created_at = Column(String)
