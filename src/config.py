from pathlib import Path

import os
from dotenv import load_dotenv

load_dotenv()

# ── Base paths ────────────────────────────────────────────────
BASE_DIR          = Path(__file__).parent.parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
CHROMA_DB_DIR     = BASE_DIR / "chroma_db"

# ── GitHub MCP ────────────────────────────────────────────────
_raw_repo = os.getenv("GITHUB_REPO", "")
# Sanitize URL to just owner/repo if user pasted the full link
GITHUB_REPO = _raw_repo.replace("https://github.com/", "").replace("http://github.com/", "").strip("/")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "") # Optional for public repos


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
SIMILARITY_THRESHOLD = 0.3    # minimum cosine similarity score to consider a chunk relevant

# ── Chat Memory ──────────────────────────────────────────────
CHAT_HISTORY_PAIRS = 5  # number of QA pairs to remember in memory