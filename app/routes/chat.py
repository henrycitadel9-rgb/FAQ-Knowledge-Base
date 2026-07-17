"""Chat routes."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.db import session, models
from app.services import retrieval, ai
from app.schemas import chat
import time
from datetime import datetime
import os
import openai

router = APIRouter(prefix="/api/chat", tags=["Chat"])

def log_interaction(db: Session, interface_type: str, query: str, faq_id: int, answer: str, latency: int, source: str):
    """Log interaction to database."""
    log_entry = models.ChatLog(
        interface_type=interface_type,
        user_query=query,
        matched_faq_id=faq_id,
        system_answer=answer,
        source_ref=source,
        latency_ms=latency,
        created_at=datetime.utcnow().isoformat()
    )
    db.add(log_entry)
    db.commit()

@router.post("/message")
def send_message(request: chat.ChatRequest, db: Session = Depends(session.get_db)):
    """Send a chat message and get retrieval-based response."""
    start_time = time.time()
    
    result = retrieval.retrieve_answer(request.message, db)
    
    latency = int((time.time() - start_time) * 1000)
    
    # Log interaction
    try:
        log_interaction(
            db=db,
            interface_type="retrieval_chat",
            query=request.message,
            faq_id=result.get("faq_id"),
            answer=result["answer"],
            latency=latency,
            source=result["source"]
        )
    except Exception as e:
        print(f"Logging error: {e}")  # For debugging
    
    return chat.ChatResponse(
        question=result.get("question", ""),
        answer=result["answer"],
        source=result["source"],
        confidence=result["confidence"],
        response_type=result.get("response_type", "single"),
        matches=result.get("matches", [])
    )

@router.post("/ai-message")
def send_ai_message(request: chat.ChatRequest, db: Session = Depends(session.get_db)):
    """Send a chat message and get AI-powered conversational response."""
    start_time = time.time()
    
    result = ai.get_ai_response(request.message, db)
    
    latency = int((time.time() - start_time) * 1000)
    
    # Log interaction
    try:
        log_interaction(
            db=db,
            interface_type="ai_chat",
            query=request.message,
            faq_id=result.get("faq_id"),
            answer=result["answer"],
            latency=latency,
            source=result["source"]
        )
    except Exception as e:
        print(f"Logging error: {e}")  # For debugging
    
    return chat.ChatResponse(
        question=result.get("question", ""),
        answer=result["answer"],
        source=result["source"],
        confidence=result["confidence"],
        response_type=result.get("response_type", "single"),
        matches=result.get("matches", [])
    )

@router.post("/transcribe")
async def transcribe_audio(audio_file: UploadFile = File(...)):
    """Transcribe audio using OpenAI Whisper."""
    try:
        # Validate file type
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        # Read audio data
        audio_data = await audio_file.read()

        transcription_key = os.getenv("OPENAI_TRANSCRIPTION_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not transcription_key or transcription_key.startswith("sk-or-v1-"):
            raise HTTPException(
                status_code=400,
                detail="Voice transcription requires a real OpenAI API key in OPENAI_TRANSCRIPTION_API_KEY or OPENAI_API_KEY.",
            )

        client = openai.OpenAI(api_key=transcription_key)

        # Create a temporary file-like object for the audio
        from io import BytesIO
        audio_buffer = BytesIO(audio_data)
        audio_buffer.name = audio_file.filename or "audio.wav"

        # Transcribe using Whisper
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_buffer,
            language="en"  # Specify English for better accuracy
        )

        return {"text": transcript.text.strip()}

    except Exception as e:
        print(f"Whisper transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
