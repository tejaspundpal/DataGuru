from pathlib import Path

import os
from dotenv import load_dotenv

load_dotenv()

# ── User Config (per-user credentials) ───────────────────────
# Priority: user_config (~/.dataguru/config.json) > .env > empty
from user_config import get_config as _get_user_config
_user_cfg = _get_user_config()

def _resolve(key: str) -> str:
    """Resolve a config value: user config takes priority over .env."""
    return _user_cfg.get(key, "") or os.getenv(key, "")

# ── Base paths ────────────────────────────────────────────────
BASE_DIR          = Path(__file__).parent.parent
_DATA_DIR         = Path(os.environ.get("DATA_DIR", str(BASE_DIR)))
KNOWLEDGE_BASE_DIR = _DATA_DIR / "knowledge_base"
CHROMA_DB_DIR     = _DATA_DIR / "chroma_db"

# ── GitHub MCP ────────────────────────────────────────────────
_raw_repo = _resolve("GITHUB_REPO")
# Sanitize URL to just owner/repo if user pasted the full link
GITHUB_REPO = _raw_repo.replace("https://github.com/", "").replace("http://github.com/", "").strip("/")
GITHUB_TOKEN = _resolve("GITHUB_TOKEN")  # Optional for public repos

# ── Jira Integration ──────────────────────────────────────────
JIRA_BASE_URL    = _resolve("JIRA_BASE_URL")     # e.g., https://yourcompany.atlassian.net
JIRA_USERNAME    = _resolve("JIRA_USERNAME")      # email or username
JIRA_PASSWORD    = _resolve("JIRA_PASSWORD")      # API token (Jira Cloud) or password (Jira Server)
JIRA_VERIFY_SSL  = _resolve("JIRA_VERIFY_SSL").lower() not in ("false", "0", "no", "")

# ── Groq / LLM ───────────────────────────────────────────────
GROQ_API_KEY = _resolve("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

# File types the MCP server will fetch from the repo
MCP_SUPPORTED_EXTENSIONS = {
    ".md", ".txt", ".log", ".sql", ".csv",
    ".json", ".xml", ".yaml", ".yml",
    ".py", ".sh", ".conf", ".cfg", ".ini",
    ".pdf", ".docx",
}
# Max file size to download from GitHub (prevents OOM on large binaries)
MCP_MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB


# ── Embedding (local, free — no API key needed) ───────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ── ChromaDB ──────────────────────────────────────────────────
COLLECTION_NAME = "dataguru_knowledge"

# ── Chunking ─────────────────────────────────────────────────
CHUNK_SIZE_CHARS    = 1500   # ~375 tokens
CHUNK_OVERLAP_CHARS = 200    # overlap to preserve context across chunks

# ── Retrieval ────────────────────────────────────────────────
TOP_K = 5   # number of chunks to retrieve per query
SIMILARITY_THRESHOLD = 0.3    # minimum cosine similarity score to consider a chunk relevant

# ── Chat Memory ──────────────────────────────────────────────
CHAT_HISTORY_PAIRS = 5  # number of QA pairs to remember in memory

# ── File Attachment ──────────────────────────────────────────
ALLOWED_EXTENSIONS = {
    ".log", ".txt", ".sql", ".csv", ".json", ".xml",
    ".py", ".sh", ".yaml", ".yml", ".conf", ".cfg",
    ".ini", ".properties", ".env.example", ".md",
}
MAX_ATTACHMENT_BYTES = 50 * 1024  # 50 KB hard limit
MAX_ATTACHMENT_LINES = 500        # truncate beyond this for LLM context efficiency

# ── Learning Agent (Level 1 — Passive Learning) ──────────────
LEARNED_COLLECTION_NAME = "dataguru_learned_patterns"
DEDUP_SIMILARITY_THRESHOLD = 0.85  # skip storing if existing pattern is this similar
MIN_CHAT_PAIRS_TO_LEARN = 1        # minimum Q&A pairs before learning triggers
LEARNED_TOP_K = 3                  # chunks to retrieve from learned patterns

# ── Skill Generator (Level 2 — Active Skills) ────────────────
SKILLS_DIR = BASE_DIR / "learned_skills"
SKILL_PATTERN_THRESHOLD = 3        # minimum similar patterns before generating a skill
SKILL_SIMILARITY_CLUSTER = 0.70    # cosine threshold to consider patterns as related