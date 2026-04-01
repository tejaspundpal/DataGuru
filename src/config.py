from pathlib import Path

# ── Base paths ────────────────────────────────────────────────
BASE_DIR          = Path(__file__).parent.parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
CHROMA_DB_DIR     = BASE_DIR / "chroma_db"

# ── Embedding (local, free — no API key needed) ───────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ── ChromaDB ──────────────────────────────────────────────────
COLLECTION_NAME = "dataguru_knowledge"

# ── Groq / LLM ───────────────────────────────────────────────
GROQ_MODEL = "llama-3.3-70b-versatile"

# ── Chunking ─────────────────────────────────────────────────
CHUNK_SIZE_CHARS    = 1500   # ~375 tokens
CHUNK_OVERLAP_CHARS = 200    # overlap to preserve context across chunks

# ── Retrieval ────────────────────────────────────────────────
TOP_K = 5   # number of chunks to retrieve per query