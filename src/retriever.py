"""
retriever.py — Semantic Retrieval from ChromaDB

Flow:
  User query (string)
       → embed with same sentence-transformers model used at ingest
       → cosine similarity search in ChromaDB (both knowledge base + learned patterns)
       → return top-K most relevant chunks with metadata + score

Singleton pattern: model and collections are loaded once and reused
across all queries in a session for performance.
"""

import sys
import os
import logging
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))

import chromadb
from sentence_transformers import SentenceTransformer
from config import (
    CHROMA_DB_DIR, COLLECTION_NAME, EMBEDDING_MODEL,
    TOP_K, SIMILARITY_THRESHOLD,
    LEARNED_COLLECTION_NAME, LEARNED_TOP_K,
)

# ── Singletons (loaded once per session) ─────────────────────
_model: SentenceTransformer | None = None
_collection = None
_learned_collection = None


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


def get_learned_collection():
    """Get the learned patterns collection (returns None if it doesn't exist yet)."""
    global _learned_collection
    if _learned_collection is None:
        try:
            client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
            _learned_collection = client.get_collection(LEARNED_COLLECTION_NAME)
        except Exception:
            # Collection doesn't exist yet — no patterns learned
            return None
    return _learned_collection


def reset_singletons():
    """Call this after re-ingestion to force reload of collections."""
    global _model, _collection, _learned_collection
    _model = None
    _collection = None
    _learned_collection = None


# ─────────────────────────────────────────────────────────────
# Main retrieval function
# ─────────────────────────────────────────────────────────────

def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Retrieves the top-K most semantically similar chunks for a query.
    Searches BOTH the main knowledge base and learned patterns collection.

    Args:
        query:  The user's natural language question.
        top_k:  Number of chunks to retrieve from main KB (default from config).

    Returns:
        List of dicts:
            {
              "text":       chunk text,
              "source":     relative file path (used for citation),
              "technology": parent folder name (e.g. "spark_pyspark"),
              "score":      cosine similarity score (0–1, higher = more relevant)
            }
    """
    model = get_model()

    # Embed the query using the SAME model as ingestion
    query_vector = model.encode([query]).tolist()

    retrieved = []

    # ── Search main knowledge base ───────────────────────────
    collection = get_collection()
    results = collection.query(
        query_embeddings=query_vector,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

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

    # ── Search learned patterns ───────────────────────────────
    learned_col = get_learned_collection()
    if learned_col and learned_col.count() > 0:
        try:
            learned_results = learned_col.query(
                query_embeddings=query_vector,
                n_results=min(LEARNED_TOP_K, learned_col.count()),
                include=["documents", "metadatas", "distances"],
            )

            for text, meta, dist in zip(
                learned_results["documents"][0],
                learned_results["metadatas"][0],
                learned_results["distances"][0],
            ):
                score = round(1.0 - dist, 4)
                if score >= SIMILARITY_THRESHOLD:
                    retrieved.append({
                        "text":       text,
                        "source":     meta.get("source", f"🧠 Learned Pattern"),
                        "technology": meta.get("technology", "unknown"),
                        "score":      score,
                    })
        except Exception:
            pass  # Graceful degradation — learned patterns are optional

    # Sort all results by score (highest first) and return top combined
    retrieved.sort(key=lambda x: x["score"], reverse=True)

    return retrieved
