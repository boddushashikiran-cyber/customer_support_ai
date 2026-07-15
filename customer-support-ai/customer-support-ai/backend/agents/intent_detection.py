"""
Intent Detection Agent (Module 3)

Classifies a customer query into one or more of:
  billing, technical, product, complaint, faq

Uses simple, fast keyword scoring by default (no API cost, deterministic,
good enough for routing). If you want LLM-based classification instead,
swap detect_intents() to call llm.chat_completion() with a classification
prompt and parse the JSON it returns.
"""
import re

INTENT_KEYWORDS = {
    "billing": [
        "pay", "paid", "payment", "invoice", "subscription", "charge", "charged",
        "refund", "bill", "billing", "renew", "renewal", "premium", "plan", "price",
    ],
    "technical": [
        "login", "log in", "password", "install", "installation", "error", "bug",
        "crash", "not working", "doesn't work", "locked", "reset", "update", "app",
    ],
    "product": [
        "feature", "features", "pricing", "compare", "comparison", "available",
        "availability", "spec", "specs", "product", "model",
    ],
    "complaint": [
        "complaint", "unhappy", "disappointed", "angry", "frustrated", "escalate",
        "manager", "terrible", "worst", "unacceptable", "refund my money",
    ],
    "faq": [
        "policy", "hours", "contact", "shipping", "delivery", "warranty",
        "how do i", "what is", "where is",
    ],
}


def detect_intents(query: str) -> list[str]:
    """
    Returns a list of matched intent labels, e.g. ["billing", "technical"].
    Falls back to ["faq"] if nothing matches (general question handling).
    """
    text = query.lower()
    matched = []
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(re.search(re.escape(kw), text) for kw in keywords):
            matched.append(intent)
    return matched or ["faq"]
