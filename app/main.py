"""Main FastAPI application."""
import os

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import session, models
from app.db.init_db import init_db

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup_event():
    init_db()


def is_transcription_enabled() -> bool:
    """Return whether a real OpenAI key is available for Whisper transcription."""
    transcription_key = os.getenv("OPENAI_TRANSCRIPTION_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not transcription_key:
        return False
    if transcription_key.startswith("sk-or-v1-"):
        return False
    if "PASTE_A_REAL_OPENAI_KEY_HERE" in transcription_key:
        return False
    return True

# Include routers (import submodules directly to avoid package import quirks)
import importlib

faq = importlib.import_module('app.routes.faq')
chat = importlib.import_module('app.routes.chat')
eval_mod = importlib.import_module('app.routes.eval')
health = importlib.import_module('app.routes.health')
tasks = importlib.import_module('app.routes.tasks')

app.include_router(faq.router)
app.include_router(chat.router)
app.include_router(eval_mod.router)
app.include_router(health.router)
app.include_router(tasks.router)

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/faq")
def faq_page(request: Request):
    return templates.TemplateResponse("faq.html", {"request": request})

@app.get("/faq/{faq_id}")
def faq_detail_page(faq_id: int, request: Request, db: Session = Depends(session.get_db)):
    faq = db.query(models.FAQ).filter(models.FAQ.id == faq_id, models.FAQ.is_active == True).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    faq_data = {
        "id": faq.id,
        "faq_number": faq.faq_number,
        "category": faq.category,
        "canonical_question": faq.canonical_question,
        "official_answer": faq.official_answer,
        "source_needed": faq.source_needed,
        "tags": faq.tags,
        "keywords": faq.keywords,
        "source_ref": faq.source_ref,
        "created_at": faq.created_at
    }
    return templates.TemplateResponse("faq_detail.html", {"request": request, "faq": faq_data})


@app.get("/ai_chat")
def ai_chat_page(request: Request):
    return templates.TemplateResponse(
        "ai_chat.html",
        {"request": request, "transcription_enabled": is_transcription_enabled()},
    )


@app.get("/ai")
def ai_short_page(request: Request):
    return templates.TemplateResponse(
        "ai_chat.html",
        {"request": request, "transcription_enabled": is_transcription_enabled()},
    )


@app.get("/retrieval_chat")
def retrieval_chat_page(request: Request):
    return templates.TemplateResponse("retrieval_chat.html", {"request": request})


@app.get("/retrieval")
def retrieval_short_page(request: Request):
    return templates.TemplateResponse("retrieval_chat.html", {"request": request})

@app.get("/chat")
def chat_page(request: Request):
    return templates.TemplateResponse("retrieval_chat.html", {"request": request})

@app.get("/ai-chat")
def ai_chat_path(request: Request):
    return templates.TemplateResponse(
        "ai_chat.html",
        {"request": request, "transcription_enabled": is_transcription_enabled()},
    )
