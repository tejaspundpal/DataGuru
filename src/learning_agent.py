"""
learning_agent.py — Level 1: Passive Learning Agent

After each meaningful session, this agent:
  1. Analyzes the chat history (and any attached documents)
  2. Extracts structured "incident cards" via the LLM
  3. Checks for duplicates against existing learned patterns (cosine dedup)
  4. Stores new patterns in a dedicated ChromaDB collection

Future queries will retrieve from BOTH the main knowledge base
and the learned_patterns collection — making the system smarter over time.
"""

import sys
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq

from config import (
    CHROMA_DB_DIR,
    EMBEDDING_MODEL,
    GROQ_MODEL,
    GROQ_API_KEY,
    LEARNED_COLLECTION_NAME,
    DEDUP_SIMILARITY_THRESHOLD,
    MIN_CHAT_PAIRS_TO_LEARN,
)


# ─────────────────────────────────────────────────────────────
# Extraction Prompt
# ─────────────────────────────────────────────────────────────

EXTRACTION_PROMPT = """You are a knowledge extraction agent. Your job is to analyze a completed support conversation and extract structured incident resolution patterns.

Given the following chat history (and optionally an attached document that was analyzed), extract ZERO or MORE incident cards. Only extract cards if the conversation contains a clear problem → diagnosis → resolution flow.

RULES:
1. Do NOT fabricate information. Only extract what is explicitly discussed.
2. If the conversation is casual/exploratory with no clear resolution, return an empty list.
3. Each card must have a clear error pattern and resolution.
4. Keep each field concise (1-3 sentences max).

Return a JSON array of objects with this exact structure:
[
  {
    "title": "Short descriptive title of the incident pattern",
    "technology": "Primary technology (e.g., Informatica, Spark, SQL, Python, Unix)",
    "error_pattern": "The specific error codes, messages, or symptoms that identify this issue",
    "root_cause": "What caused the issue",
    "resolution": "Step-by-step fix that was identified",
    "prevention": "How to prevent recurrence (if discussed)",
    "keywords": ["keyword1", "keyword2", "keyword3"]
  }
]

If no meaningful patterns can be extracted, return: []

CONVERSATION:
{conversation}

ATTACHED DOCUMENT (if any):
{attachment}

Extract incident cards as JSON (return ONLY the JSON array, no other text):"""


# ─────────────────────────────────────────────────────────────
# Core Learning Functions
# ─────────────────────────────────────────────────────────────

def _get_groq_client() -> Groq:
    """Get Groq client with validated API key."""
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not configured. Run 'setup' command.")
    return Groq(api_key=GROQ_API_KEY)


def _get_learned_collection():
    """Get or create the learned_patterns ChromaDB collection."""
    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    return client.get_or_create_collection(
        name=LEARNED_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _get_embedding_model() -> SentenceTransformer:
    """Load the sentence transformer model."""
    return SentenceTransformer(EMBEDDING_MODEL)


def _build_conversation_text(chat_history: list[dict], attachment: dict | None) -> str:
    """Format chat history into readable text for the extraction prompt."""
    lines = []
    for msg in chat_history:
        role = "User" if msg["role"] == "user" else "DataGuru"
        lines.append(f"{role}: {msg['content']}")
    return "\n\n".join(lines)


def _build_attachment_text(attachment: dict | None) -> str:
    """Format attachment info for the extraction prompt."""
    if not attachment:
        return "(No document attached)"

    diag = attachment["diagnostics"]
    parts = [f"File: {attachment['file_name']}"]

    if diag["errors"]:
        parts.append("Errors found:")
        parts.extend(diag["errors"][:10])
    if diag["warnings"]:
        parts.append("Warnings found:")
        parts.extend(diag["warnings"][:5])

    return "\n".join(parts)


def _extract_patterns(chat_history: list[dict], attachment: dict | None) -> list[dict]:
    """Use LLM to extract incident patterns from the conversation."""
    conversation_text = _build_conversation_text(chat_history, attachment)
    attachment_text = _build_attachment_text(attachment)

    prompt = EXTRACTION_PROMPT.format(
        conversation=conversation_text,
        attachment=attachment_text,
    )

    client = _get_groq_client()

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,  # deterministic extraction
            max_tokens=2048,
        )
        raw_text = response.choices[0].message.content.strip()

        # Parse JSON — handle cases where LLM wraps in markdown code block
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]  # remove ```json line
            raw_text = raw_text.rsplit("```", 1)[0]  # remove closing ```

        patterns = json.loads(raw_text)

        if not isinstance(patterns, list):
            return []

        # Validate each pattern has required fields
        required_fields = {"title", "technology", "error_pattern", "root_cause", "resolution"}
        validated = []
        for p in patterns:
            if isinstance(p, dict) and required_fields.issubset(p.keys()):
                validated.append(p)

        return validated

    except (json.JSONDecodeError, KeyError, IndexError):
        return []
    except Exception:
        return []


def _is_duplicate(embedding: list[float], collection) -> bool:
    """Check if a similar pattern already exists in the learned collection."""
    try:
        count = collection.count()
        if count == 0:
            return False

        results = collection.query(
            query_embeddings=[embedding],
            n_results=1,
            include=["distances"],
        )

        if results["distances"] and results["distances"][0]:
            distance = results["distances"][0][0]
            similarity = 1.0 - distance
            return similarity >= DEDUP_SIMILARITY_THRESHOLD

    except Exception:
        pass

    return False


def _generate_doc_id(pattern: dict) -> str:
    """Generate a deterministic ID for a pattern based on content."""
    content = f"{pattern['title']}|{pattern['error_pattern']}|{pattern['resolution']}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _pattern_to_document(pattern: dict) -> str:
    """Convert a pattern dict into a searchable document string."""
    parts = [
        f"# {pattern['title']}",
        f"Technology: {pattern['technology']}",
        f"Error Pattern: {pattern['error_pattern']}",
        f"Root Cause: {pattern['root_cause']}",
        f"Resolution: {pattern['resolution']}",
    ]
    if pattern.get("prevention"):
        parts.append(f"Prevention: {pattern['prevention']}")
    if pattern.get("keywords"):
        parts.append(f"Keywords: {', '.join(pattern['keywords'])}")
    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def learn_from_session(
    chat_history: list[dict],
    attachment: dict | None = None,
) -> list[dict]:
    """
    Extract and store learned patterns from a completed chat session.

    Args:
        chat_history: Full conversation messages list.
        attachment:   Optional attachment that was analyzed during the session.

    Returns:
        List of patterns that were successfully stored (empty if none learned).
    """
    # Guard: need minimum conversation to extract meaningful patterns
    qa_pairs = len(chat_history) // 2
    if qa_pairs < MIN_CHAT_PAIRS_TO_LEARN:
        return []

    # Step 1: Extract patterns via LLM
    patterns = _extract_patterns(chat_history, attachment)
    if not patterns:
        return []

    # Step 2: Embed and deduplicate
    model = _get_embedding_model()
    collection = _get_learned_collection()

    stored_patterns = []
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    for pattern in patterns:
        doc_text = _pattern_to_document(pattern)
        embedding = model.encode([doc_text]).tolist()[0]

        # Dedup check
        if _is_duplicate(embedding, collection):
            continue

        # Step 3: Store in ChromaDB
        doc_id = _generate_doc_id(pattern)
        metadata = {
            "source": f"🧠 Learned: {pattern['title']}",
            "technology": pattern["technology"],
            "doc_name": f"learned_{doc_id}",
            "learned_at": timestamp,
            "pattern_type": "incident_resolution",
        }

        collection.add(
            embeddings=[embedding],
            documents=[doc_text],
            metadatas=[metadata],
            ids=[doc_id],
        )

        stored_patterns.append(pattern)

    return stored_patterns


def get_learned_count() -> int:
    """Return the total number of learned patterns stored."""
    try:
        collection = _get_learned_collection()
        return collection.count()
    except Exception:
        return 0
