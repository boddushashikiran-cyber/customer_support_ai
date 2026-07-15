"""
RAG ingestion pipeline:
  documents -> chunk -> embed -> store in FAISS index (+ metadata json)

Supports .txt, .md, and .pdf files in the knowledge_base folder.
Run this file directly to (re)build the vector index:
    python -m rag.ingest
"""
import os
import json
import glob
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

KB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base")
INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "vectorstore")
INDEX_PATH = os.path.join(INDEX_DIR, "faiss.index")
META_PATH = os.path.join(INDEX_DIR, "meta.json")

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 500       # characters per chunk
CHUNK_OVERLAP = 80


def read_text_file(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def read_pdf_file(path):
    from pypdf import PdfReader
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def load_documents():
    docs = []
    for path in glob.glob(os.path.join(KB_DIR, "*")):
        ext = os.path.splitext(path)[1].lower()
        if ext in (".txt", ".md"):
            text = read_text_file(path)
        elif ext == ".pdf":
            text = read_pdf_file(path)
        else:
            continue
        docs.append({"source": os.path.basename(path), "text": text})
    return docs


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]


def build_index():
    os.makedirs(INDEX_DIR, exist_ok=True)
    docs = load_documents()
    if not docs:
        print(f"No documents found in {KB_DIR}. Add .txt/.md/.pdf files and re-run.")
        return

    model = SentenceTransformer(EMBED_MODEL_NAME)

    all_chunks = []
    metadata = []
    for doc in docs:
        chunks = chunk_text(doc["text"])
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            metadata.append({"source": doc["source"], "chunk_id": i, "text": chunk})

    print(f"Embedding {len(all_chunks)} chunks from {len(docs)} documents...")
    embeddings = model.encode(all_chunks, show_progress_bar=True, convert_to_numpy=True)
    embeddings = embeddings.astype("float32")
    faiss.normalize_L2(embeddings)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine similarity via normalized inner product
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f)

    print(f"Index built with {index.ntotal} vectors. Saved to {INDEX_DIR}")


if __name__ == "__main__":
    build_index()
