"""
retriever.py — Semantic Retrieval from ChromaDB

Flow:
  User query (string)
       → embed with same sentence-transformers model used at ingest
       → cosine similarity search in ChromaDB
       → return top-K most relevant chunks with metadata + score

Singleton pattern: model and collection are loaded once and reused
across all queries in a session for performance.
"""

import sys
import os
import logging
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))

import chromadb
from sentence_transformers import SentenceTransformer
from config import CHROMA_DB_DIR, COLLECTION_NAME, EMBEDDING_MODEL, TOP_K, SIMILARITY_THRESHOLD

# ── Singletons (loaded once per session) ─────────────────────
_model: SentenceTransformer | None = None
_collection = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
        _collection = client.get_collection(COLLECTION_NAME)
    return _collection


def reset_singletons():
    """Call this after re-ingestion to force reload of collection."""
    global _model, _collection
    _model = None
    _collection = None


# ─────────────────────────────────────────────────────────────
# Main retrieval function
# ─────────────────────────────────────────────────────────────

def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Retrieves the top-K most semantically similar chunks for a query.

    Args:
        query:  The user's natural language question.
        top_k:  Number of chunks to retrieve (default from config).

    Returns:
        List of dicts:
            {
              "text":       chunk text,
              "source":     relative file path (used for citation),
              "technology": parent folder name (e.g. "spark_pyspark"),
              "score":      cosine similarity score (0–1, higher = more relevant)
            }
    """
    model      = get_model()
    collection = get_collection()

    # Embed the query using the SAME model as ingestion
    query_vector = model.encode([query]).tolist()

    # Query ChromaDB — returns distances (lower = more similar for cosine space)
    results = collection.query(
        query_embeddings=query_vector,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []
    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        score = round(1.0 - dist, 4)   # convert distance → similarity
        if score >= SIMILARITY_THRESHOLD:
            retrieved.append({
                "text":       text,
                "source":     meta.get("source", "unknown"),
                "technology": meta.get("technology", "unknown"),
                "score":      score,
            })

    return retrieved
