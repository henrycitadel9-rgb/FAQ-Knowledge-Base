"""AI service for conversational FAQ responses."""
import hashlib
import json
import os
import re
from typing import Dict, List, Optional, Tuple

import openai
from sqlalchemy.orm import Session

from app.services import retrieval

# Simple in-memory cache
_cache: Dict[str, str] = {}


def is_openrouter_key(api_key: Optional[str]) -> bool:
    """Return True when the configured key appears to be an OpenRouter key."""
    return bool(api_key and api_key.startswith("sk-or-v1-"))


def get_chat_provider_config() -> Tuple[Optional[str], str, Dict[str, str], str]:
    """Resolve provider configuration for conversational chat generation."""
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    default_key = os.getenv("OPENAI_API_KEY")

    if openrouter_key:
        api_key = openrouter_key
    else:
        api_key = default_key

    if not api_key or api_key.startswith("sk-..."):
        return None, "", {}, ""

    if is_openrouter_key(api_key):
        site_url = os.getenv("OPENROUTER_SITE_URL", "http://127.0.0.1:8000")
        app_name = os.getenv("OPENROUTER_APP_NAME", "FAQ Chat Application")
        headers = {
            "HTTP-Referer": site_url,
            "X-Title": app_name,
        }
        model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        return api_key, "https://openrouter.ai/api/v1", headers, model

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return api_key, "", {}, model

def get_cache_key(query: str, faq_answer: str) -> str:
    """Generate a cache key from query and FAQ answer."""
    content = f"{query}|{faq_answer}"
    return hashlib.md5(content.encode()).hexdigest()

def get_cached_response(cache_key: str) -> Optional[str]:
    """Get cached AI response if available."""
    return _cache.get(cache_key)

def cache_response(cache_key: str, response: str):
    """Cache the AI response."""
    _cache[cache_key] = response


def safe_json_loads(text: str) -> Optional[Dict]:
    """Extract and parse a JSON object from model output."""
    if not text:
        return None

    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def serialize_semantic_match(faq, query: str, confidence: float) -> Dict:
    """Convert a semantic FAQ match into the shared API payload shape."""
    query_terms = retrieval.tokenize_text(query)
    faq_terms = retrieval.tokenize_text(
        " ".join(
            part for part in [faq.canonical_question, faq.keywords, faq.tags, faq.official_answer] if part
        )
    )
    matched_terms = sorted(query_terms & faq_terms)
    return {
        "faq_id": faq.id,
        "question": faq.canonical_question,
        "answer": faq.official_answer,
        "source": faq.source_ref or "",
        "confidence": confidence,
        "matched_terms": matched_terms,
    }


def semantic_select_faqs(query: str, db: Session) -> Optional[Dict]:
    """Use the AI provider to map paraphrased or typo-heavy questions to FAQ entries."""
    api_key, base_url, default_headers, model_name = get_chat_provider_config()
    if not api_key:
        return None

    faqs = db.query(retrieval.models.FAQ).filter(retrieval.models.FAQ.is_active == True).order_by(retrieval.models.FAQ.id).all()
    faq_catalog = [
        {
            "id": faq.id,
            "category": faq.category or "",
            "question": faq.canonical_question,
            "keywords": faq.keywords or "",
            "tags": faq.tags or "",
        }
        for faq in faqs
    ]

    catalog_text = "\n".join(
        f"ID {item['id']} | Category: {item['category']} | Question: {item['question']} | Keywords: {item['keywords']} | Tags: {item['tags']}"
        for item in faq_catalog
    )

    prompt = f"""Map the student's question to the FAQ catalog below.

Student question: {query}

Rules:
- Handle paraphrases, synonyms, typos, and indirect wording.
- Choose \"single\" if one FAQ is clearly the same meaning.
- Choose \"multiple\" if 2 to 5 FAQs are all plausible and the user should clarify.
- Choose \"none\" if the question is unrelated to the catalog.
- Use only FAQ IDs from the catalog.
- Return JSON only.

JSON format:
{{"decision":"single|multiple|none","faq_ids":[1,2],"confidence":0.0,"reason":"short reason"}}

FAQ catalog:
{catalog_text}
"""

    try:
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        if default_headers:
            client_kwargs["default_headers"] = default_headers
        client = openai.OpenAI(**client_kwargs)

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise FAQ routing assistant. You identify semantic matches between student questions and a fixed FAQ catalog. Return strict JSON only.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_tokens=300,
            temperature=0,
        )
        content = response.choices[0].message.content.strip()
        parsed = safe_json_loads(content)
        if not parsed:
            return None

        decision = parsed.get("decision")
        faq_ids = parsed.get("faq_ids") or []
        confidence = float(parsed.get("confidence", 0.7))
        selected_faqs = [faq for faq in faqs if faq.id in faq_ids]

        if decision == "single" and selected_faqs:
            match = serialize_semantic_match(selected_faqs[0], query, max(0.65, min(confidence, 0.95)))
            return {
                "faq_id": match["faq_id"],
                "question": match["question"],
                "answer": match["answer"],
                "source": match["source"],
                "confidence": match["confidence"],
                "response_type": "single",
                "matches": [],
            }

        if decision == "multiple" and selected_faqs:
            matches = [
                serialize_semantic_match(faq, query, max(0.6, min(confidence - (index * 0.03), 0.9)))
                for index, faq in enumerate(selected_faqs[:5])
            ]
            return {
                "question": "",
                "answer": "I found a few likely FAQ matches for that phrasing. Pick the one you mean, and I'll answer from that exact entry.",
                "source": "",
                "confidence": max(match["confidence"] for match in matches),
                "response_type": "disambiguation",
                "matches": matches,
            }

        return {
            "question": "",
            "answer": "I couldn't find a reliable FAQ match for that question. Please rephrase it or ask about a topic covered in the student support knowledge base.",
            "source": "",
            "confidence": 0,
            "response_type": "no_match",
            "matches": [],
        }
    except Exception as exc:
        print(f"Semantic FAQ selection error: {exc}")
        return None

def generate_conversational_response(query: str, faq_question: str, faq_answer: str) -> str:
    """Generate a conversational response using AI, grounded in the FAQ answer."""
    api_key, base_url, default_headers, model_name = get_chat_provider_config()
    if not api_key:
        print("No valid AI provider key configured; using plain FAQ answer as fallback.")
        return faq_answer

    try:
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        if default_headers:
            client_kwargs["default_headers"] = default_headers
        client = openai.OpenAI(**client_kwargs)

        prompt = f"""You are an enthusiastic, welcoming student support advisor chatting one-on-one with a student. 

Student's question: "{query}"

Official info you have: "{faq_answer}"

Transform this official info into a warm, conversational response. Be yourself! Use:
- Casual tone with contractions (can't, I'm, you'll, etc.)
- Genuine enthusiasm and personality
- Relatable language (like you're texting a friend)
- A touch of humor when appropriate
- Direct eye contact through words (address them as "you")

Examples of conversational style:
Instead of: "The maximum credit load is 12 credits"
Say: "So here's the deal—you can load up to 12 credits without needing approval. Pretty standard, right?"

Instead of: "Students must submit applications by March 1"
Say: "Mark your calendar for March 1st—that's when we need to see your application in!"

KEY RULES:
- DO NOT make up any info or go beyond what's in the official info
- DO NOT add disclaimers or formal language
- DO sound like a real person who cares about helping them
- DO keep responses concise but natural (2-3 sentences max, longer only if needed)
- DO reference their specific question to show you listened

Now rewrite the info in a genuinely conversational, helpful way:"""

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are an enthusiastic, warm student support advisor. You help with admissions, financial aid, housing, registration, transcripts, billing, and student services. You speak naturally like a real person, not an official. You're genuinely interested in helping students. Never sound formal or robotic. Always stay 100% true to the official information provided."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=350,
            temperature=0.7  # Higher temp for more natural, varied responses
        )

        result = response.choices[0].message.content.strip()
        print("AI response generated successfully (not cached)")
        return result

    except Exception as e:
        print(f"AI generation error: {e}")
        # Fallback to original answer if AI fails
        print(f"Falling back to FAQ answer due to error: {str(e)}")
        return faq_answer

def get_ai_response(query: str, db: Session) -> dict:
    """Get AI-powered conversational response based on FAQ retrieval."""
    retrieval_result = retrieval.retrieve_answer(query, db)

    if retrieval_result["response_type"] == "no_match":
        semantic_result = semantic_select_faqs(query, db)
        if semantic_result:
            retrieval_result = semantic_result

    if retrieval_result["response_type"] == "no_match":
        return retrieval_result

    if retrieval_result["response_type"] == "multiple":
        options = retrieval_result.get("matches", [])[:5]
        return {
            "question": "",
            "answer": "I found a few dataset-backed interpretations of your question. Pick the one that matches what you mean, and I'll answer it in a more natural way using that exact FAQ entry.",
            "source": "",
            "confidence": retrieval_result["confidence"],
            "response_type": "disambiguation",
            "matches": options,
        }

    # Generate cache key
    cache_key = get_cache_key(query, retrieval_result["answer"])

    # Check cache
    cached_response = get_cached_response(cache_key)
    if cached_response:
        return {
            "question": retrieval_result["question"],
            "answer": cached_response,
            "source": retrieval_result["source"],
            "confidence": retrieval_result["confidence"],
            "response_type": "single",
            "matches": [],
            "cached": True
        }

    # Generate new AI response
    ai_response = generate_conversational_response(
        query=query,
        faq_question=retrieval_result["question"],
        faq_answer=retrieval_result["answer"]
    )

    # Cache the response
    cache_response(cache_key, ai_response)

    return {
        "question": retrieval_result["question"],
        "answer": ai_response,
        "source": retrieval_result["source"],
        "confidence": retrieval_result["confidence"],
        "response_type": "single",
        "matches": [],
        "cached": False
    }
