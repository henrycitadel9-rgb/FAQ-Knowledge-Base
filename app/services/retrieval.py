"""Retrieval service for FAQ knowledge base."""
import re
from typing import Dict, List, Set
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db import models

# common words we don't want influencing search results
STOP_WORDS = {
    'how', 'what', 'are', 'can', 'i', 'the', 'a', 'an', 'do', 'is', 'for',
    'to', 'in', 'of', 'my', 'and', 'or', 'if', 'on', 'when', 'why', 'where',
    'who', 'which', 'will', 'shall', 'should', 'could', 'would', 'may', 'might'
}

MIN_TOKEN_LENGTH = 3
MIN_MATCH_RATIO = 0.5
MIN_SCORE = 4
AMBIGUOUS_MATCH_LIMIT = 5
AMBIGUOUS_SCORE_FACTOR = 0.6
AMBIGUOUS_FULL_MATCH_SCORE_FACTOR = 0.4

def normalize_query(query: str) -> str:
    """Normalize user query for better matching.

    - Lowercase
    - Remove punctuation
    - Remove stop words
    - Collapse whitespace
    """
    query = query.lower().strip()
    query = re.sub(r'[^\w\s]', '', query)
    words = [w for w in query.split() if w not in STOP_WORDS]
    return ' '.join(words)


def tokenize_text(text: str) -> Set[str]:
    """Tokenize arbitrary text into searchable terms."""
    normalized = normalize_query(text or "")
    return {word for word in normalized.split() if len(word) >= MIN_TOKEN_LENGTH}


def build_match_payload(candidate, score: int, matched_terms: Set[str]) -> Dict:
    """Serialize a ranked FAQ candidate for API responses."""
    confidence = min(0.95, 0.45 + (score / 20))
    return {
        "faq_id": candidate.id,
        "question": candidate.canonical_question,
        "answer": candidate.official_answer,
        "source": candidate.source_ref or "",
        "confidence": confidence,
        "matched_terms": sorted(matched_terms),
    }


def rank_candidates(words: List[str], candidates: List[models.FAQ]) -> List[Dict]:
    """Rank FAQ candidates based on keyword coverage and field relevance."""
    ranked = []
    word_set = {word for word in words if len(word) >= MIN_TOKEN_LENGTH}

    for candidate in candidates:
        question_terms = tokenize_text(candidate.canonical_question)
        answer_terms = tokenize_text(candidate.official_answer)
        tag_terms = tokenize_text(candidate.tags)
        keyword_terms = tokenize_text(candidate.keywords)
        alias_terms = set()

        score = 0
        matched_terms: Set[str] = set()

        for word in word_set:
            if word in question_terms:
                score += 5
                matched_terms.add(word)
            if word in keyword_terms:
                score += 4
                matched_terms.add(word)
            if word in tag_terms:
                score += 2
                matched_terms.add(word)
            if word in answer_terms:
                score += 1
                matched_terms.add(word)
            if word in alias_terms:
                score += 5
                matched_terms.add(word)

        if not matched_terms:
            continue

        coverage_ratio = len(matched_terms) / max(1, len(word_set))
        if coverage_ratio < MIN_MATCH_RATIO or score < MIN_SCORE:
            continue

        if candidate.canonical_question:
            normalized_question = normalize_query(candidate.canonical_question)
            normalized_query = ' '.join(words)
            if normalized_query and normalized_query in normalized_question:
                score += 3

        ranked.append(
            {
                "candidate": candidate,
                "score": score,
                "matched_terms": matched_terms,
                "coverage_ratio": coverage_ratio,
            }
        )

    ranked.sort(
        key=lambda item: (
            item["coverage_ratio"],
            item["score"],
            len(item["matched_terms"]),
        ),
        reverse=True,
    )
    return ranked


def collect_close_matches(ranked: List[Dict]) -> List[Dict]:
    """Return similarly relevant matches that should trigger a clarification step."""
    if not ranked:
        return []

    best_match = ranked[0]
    close_matches = []

    for item in ranked[:AMBIGUOUS_MATCH_LIMIT]:
        score_gap = best_match["score"] - item["score"]
        has_similar_coverage = item["coverage_ratio"] >= best_match["coverage_ratio"] - 0.2
        is_full_term_match = best_match["coverage_ratio"] >= 0.99 and item["coverage_ratio"] >= 0.99
        has_strong_score = item["score"] >= max(MIN_SCORE, best_match["score"] * AMBIGUOUS_SCORE_FACTOR)
        has_full_match_score = item["score"] >= max(MIN_SCORE, best_match["score"] * AMBIGUOUS_FULL_MATCH_SCORE_FACTOR)

        if (has_similar_coverage and score_gap <= 6 and has_strong_score) or (is_full_term_match and has_full_match_score):
            close_matches.append(
                build_match_payload(item["candidate"], item["score"], item["matched_terms"])
            )

    return close_matches

def retrieve_answer(query: str, db: Session) -> dict:
    """Retrieve matching FAQ answer(s) with ambiguity and off-topic handling."""
    normalized = normalize_query(query)

    if not normalized:
        return {
            "question": "",
            "answer": "Please provide a valid question.",
            "source": "",
            "confidence": 0,
            "response_type": "no_match",
            "matches": [],
        }

    # First, try exact match on aliases
    alias = db.query(models.FAQAlias).filter(
        models.FAQAlias.alias_question.ilike(f"%{normalized}%")
    ).first()

    if alias:
        faq = db.query(models.FAQ).filter(models.FAQ.id == alias.faq_id).first()
        if faq:
            return {
                "faq_id": faq.id,
                "question": faq.canonical_question,
                "answer": faq.official_answer,
                "source": faq.source_ref or "",
                "confidence": 0.9,
                "response_type": "single",
                "matches": [],
            }

    # Then, search in FAQ content using ILIKE for each word
    words = normalized.split()
    conditions = []
    for word in words:
        if len(word) > 2:  # Ignore short words
            conditions.extend([
                models.FAQ.canonical_question.ilike(f"%{word}%"),
                models.FAQ.official_answer.ilike(f"%{word}%"),
                models.FAQ.tags.ilike(f"%{word}%"),
                models.FAQ.keywords.ilike(f"%{word}%")
            ])
    
    if conditions:
        candidates = db.query(models.FAQ).filter(
            models.FAQ.is_active == True,
            or_(*conditions)
        ).all()

        ranked = rank_candidates(words, candidates)
        if ranked:
            best_match = ranked[0]
            best_payload = build_match_payload(
                best_match["candidate"],
                best_match["score"],
                best_match["matched_terms"],
            )

            close_matches = collect_close_matches(ranked)

            unique_match_ids = {match["faq_id"] for match in close_matches}
            if len(unique_match_ids) > 1:
                return {
                    "faq_id": None,
                    "question": "",
                    "answer": "I found a few FAQ topics that overlap with your question. Choose the closest option below, and I'll show the exact answer for that one.",
                    "source": "",
                    "confidence": max(match["confidence"] for match in close_matches),
                    "response_type": "multiple",
                    "matches": close_matches,
                }

            return {
                "faq_id": best_payload["faq_id"],
                "question": best_payload["question"],
                "answer": best_payload["answer"],
                "source": best_payload["source"],
                "confidence": best_payload["confidence"],
                "response_type": "single",
                "matches": [],
            }

    return {
        "question": "",
        "answer": "I couldn't find a reliable FAQ match for that question. Please rephrase it or ask about a topic covered in the student support knowledge base.",
        "source": "",
        "confidence": 0,
        "response_type": "no_match",
        "matches": [],
    }
