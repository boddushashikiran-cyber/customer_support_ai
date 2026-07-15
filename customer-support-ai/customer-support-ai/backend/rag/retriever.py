"""
Retrieval side of RAG. Loads the FAISS index built by ingest.py and returns
the top-k most relevant chunks for a query.
"""
import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "vectorstore")
INDEX_PATH = os.path.join(INDEX_DIR, "faiss.index")
META_PATH = os.path.join(INDEX_DIR, "meta.json")

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model = None
_index = None
_metadata = None


def _load():
    global _model, _index, _metadata
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    if _index is None:
        if not os.path.exists(INDEX_PATH):
            return False
        _index = faiss.read_index(INDEX_PATH)
        with open(META_PATH, "r", encoding="utf-8") as f:
            _metadata = json.load(f)
    return True


def retrieve(query: str, top_k: int = 4):
    """Returns a list of {source, text, score} dicts, most relevant first."""
    if not _load():
        return []  # no knowledge base built yet

    query_vec = _model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(query_vec)

    scores, ids = _index.search(query_vec, top_k)
    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx == -1:
            continue
        meta = _metadata[idx]
        results.append({"source": meta["source"], "text": meta["text"], "score": float(score)})
    return results


def format_context(chunks):
    """Turns retrieved chunks into a single context string for the LLM prompt."""
    if not chunks:
        return "No relevant company documents were found."
    parts = []
    for c in chunks:
        parts.append(f"[Source: {c['source']}]\n{c['text']}")
    return "\n\n".join(parts)
