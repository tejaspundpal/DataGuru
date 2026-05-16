"""
DataGuru — Premium Web UI (Single-User)
A private Data Engineering knowledge assistant powered by RAG + Self-Learning.

Run: streamlit run app.py
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st

# ─── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="DataGuru",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Minimal Claude.ai-style Theme ────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

:root {
    --bg: #FFFFFF;
    --surface: #F9F9F9;
    --surface-2: #F4F4F4;
    --hover: #F5F5F5;
    --text: #1A1A1A;
    --text-muted: #666666;
    --text-faint: #999999;
    --border: #E5E5E5;
    --border-strong: #D9D9D9;
    --accent: #1A1A1A;
    --radius: 6px;
    --radius-lg: 12px;
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg: #1A1A1A;
        --surface: #2F2F2F;
        --surface-2: #262626;
        --hover: #333333;
        --text: #E8E8E8;
        --text-muted: #A0A0A0;
        --text-faint: #777777;
        --border: #3A3A3A;
        --border-strong: #4A4A4A;
        --accent: #E8E8E8;
    }
}

html, body, [class*="css"], button, input, textarea {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    -webkit-font-smoothing: antialiased;
}

#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }

.stApp { background: var(--bg) !important; color: var(--text) !important; }
.main { background: var(--bg) !important; }

.main .block-container {
    padding: 2rem 1.5rem 8rem 1.5rem;
    max-width: 760px;
}

/* ── Sidebar ─────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div { padding-top: 0 !important; }

[data-testid="stSidebar"] *,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div {
    color: var(--text) !important;
}

[data-testid="stSidebar"] .stTextInput > div > div > input,
[data-testid="stSidebar"] .stTextArea textarea {
    background: var(--bg) !important;
    border: 1px solid var(--border-strong) !important;
    color: var(--text) !important;
    border-radius: var(--radius) !important;
    font-size: 0.875rem !important;
    padding: 0.55rem 0.75rem !important;
    box-shadow: none !important;
    transition: border-color 0.15s ease !important;
}
[data-testid="stSidebar"] .stTextInput > div > div > input::placeholder,
[data-testid="stSidebar"] .stTextArea textarea::placeholder {
    color: var(--text-faint) !important;
}
[data-testid="stSidebar"] .stTextInput > div > div > input:focus,
[data-testid="stSidebar"] .stTextArea textarea:focus {
    border-color: var(--text) !important;
    box-shadow: none !important;
    outline: none !important;
}

[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] .stTextArea label,
[data-testid="stSidebar"] .stFileUploader label {
    color: var(--text-muted) !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
}

[data-testid="stSidebar"] hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1rem 0 !important;
}

/* ── Buttons (sidebar + main) ──────────────────────────── */
.stButton > button {
    background: transparent !important;
    color: var(--text) !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: var(--radius) !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    padding: 0.5rem 1rem !important;
    box-shadow: none !important;
    transition: background 0.15s ease, border-color 0.15s ease !important;
}
.stButton > button:hover {
    background: var(--hover) !important;
    border-color: var(--text) !important;
    color: var(--text) !important;
}
.stButton > button[kind="primary"],
.stButton > button[kind="primaryFormSubmit"],
.stButton button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-primary"] {
    background: var(--accent) !important;
    color: var(--bg) !important;
    border: 1px solid var(--accent) !important;
}
.stButton > button[kind="primary"] *,
.stButton button[data-testid="stBaseButton-primary"] *,
button[data-testid="stBaseButton-primary"] * {
    color: var(--bg) !important;
}
.stButton > button[kind="primary"]:hover,
.stButton button[data-testid="stBaseButton-primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover {
    background: var(--text) !important;
    border-color: var(--text) !important;
    color: var(--bg) !important;
    opacity: 0.92 !important;
}
.stButton > button:focus,
.stButton > button:active {
    box-shadow: none !important;
    outline: none !important;
}

/* ── Download buttons ──────────────────────────────────── */
.stDownloadButton > button {
    background: transparent !important;
    color: var(--text) !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: var(--radius) !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    box-shadow: none !important;
}
.stDownloadButton > button:hover {
    background: var(--hover) !important;
    border-color: var(--text) !important;
}

/* ── Sidebar section labels ────────────────────────────── */
.sec-label {
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin: 1rem 0 0.5rem 0;
}

/* ── Status pills ──────────────────────────────────────── */
.pill-connected, .pill-disconnected {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.3rem 0.65rem;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    background: var(--bg);
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text-muted);
}
.pulse-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--text);
    display: inline-block;
}
.pill-disconnected .pulse-dot,
.pill-disconnected::before { color: var(--text-faint); }

.file-pill {
    display: inline-flex;
    align-items: center;
    padding: 0.35rem 0.7rem;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-muted);
    font-size: 0.78rem;
    margin-top: 0.4rem;
}

/* ── Stat boxes ────────────────────────────────────────── */
.stat-box {
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.6rem 0.4rem;
    text-align: center;
    background: var(--bg);
}
.stat-val {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text);
}
.stat-lbl {
    font-size: 0.7rem;
    color: var(--text-muted);
    margin-top: 0.1rem;
}

/* ── Hero (first load) ─────────────────────────────────── */
.hero-container {
    text-align: center;
    padding: 3rem 1rem 2rem 1rem;
}
.hero-title {
    font-size: 2.2rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 0.6rem;
    letter-spacing: -0.01em;
}
.logo-accent { color: var(--text); }
.hero-subtitle {
    font-size: 0.95rem;
    color: var(--text-muted);
    max-width: 560px;
    margin: 0 auto 1.5rem;
    line-height: 1.55;
}
.hero-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    justify-content: center;
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.3rem 0.7rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-muted);
    font-size: 0.75rem;
    font-weight: 500;
}

/* ── Onboarding cards ──────────────────────────────────── */
.onboard-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    margin: 1.5rem 0 2rem;
}
.onboard-card {
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.2rem;
    background: var(--bg);
    transition: border-color 0.15s ease;
}
.onboard-card:hover { border-color: var(--text); }
.onboard-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 0.3rem;
}
.onboard-desc {
    font-size: 0.82rem;
    color: var(--text-muted);
    line-height: 1.5;
}

/* ── Empty chat state ──────────────────────────────────── */
.empty-chat-icon {
    font-size: 2rem;
    text-align: center;
    margin-top: 4rem;
    opacity: 0.4;
}
.empty-chat-title {
    text-align: center;
    font-size: 1.4rem;
    font-weight: 500;
    color: var(--text);
    margin-top: 1rem;
}
.empty-chat-desc {
    text-align: center;
    color: var(--text-muted);
    font-size: 0.9rem;
    margin-top: 0.4rem;
    max-width: 420px;
    margin-left: auto;
    margin-right: auto;
}

/* ── Source chips ──────────────────────────────────────── */
.sources-row {
    margin-top: 0.6rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
}
.src-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.2rem 0.55rem;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    font-size: 0.72rem;
    color: var(--text-muted);
}

/* ── Chat messages ─────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0.6rem 0 !important;
}
[data-testid="stChatMessageContent"] {
    background: transparent !important;
    color: var(--text) !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
}
[data-testid="stChatMessageContent"] p { color: var(--text) !important; }

/* User message subtle differentiation */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
    background: var(--surface) !important;
    border-radius: var(--radius-lg) !important;
    padding: 0.75rem 1rem !important;
}

/* ── Chat input bar (bottom) ───────────────────────────── */
[data-testid="stChatInput"] {
    background: var(--bg) !important;
    border-top: 1px solid var(--border) !important;
    padding: 1rem 0 !important;
}
[data-testid="stChatInput"] > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: none !important;
    transition: border-color 0.15s ease;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: var(--text) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: var(--text) !important;
    font-size: 0.95rem !important;
    border: none !important;
    box-shadow: none !important;
    caret-color: var(--text) !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: var(--text-faint) !important;
}
[data-testid="stChatInput"] button {
    background: transparent !important;
    color: var(--text-muted) !important;
    border: none !important;
    box-shadow: none !important;
}
[data-testid="stChatInput"] button:hover {
    color: var(--text) !important;
    background: var(--hover) !important;
}

/* ── Main inputs (text/select/textarea) ────────────────── */
.stTextInput > div > div > input,
.stTextArea textarea,
.stSelectbox > div > div {
    background: var(--bg) !important;
    border: 1px solid var(--border-strong) !important;
    color: var(--text) !important;
    border-radius: var(--radius) !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: var(--text) !important;
    box-shadow: none !important;
    outline: none !important;
}
.stTextInput label,
.stTextArea label,
.stSelectbox label,
.stFileUploader label {
    color: var(--text-muted) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
}

/* ── File uploader ─────────────────────────────────────── */
[data-testid="stFileUploader"] section {
    background: var(--surface) !important;
    border: 1px dashed var(--border-strong) !important;
    border-radius: var(--radius) !important;
}
[data-testid="stFileUploader"] section button {
    background: transparent !important;
    border: 1px solid var(--border-strong) !important;
    color: var(--text) !important;
}

/* ── Expander ──────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    background: var(--bg) !important;
    box-shadow: none !important;
}
[data-testid="stExpander"] summary {
    color: var(--text) !important;
    font-weight: 500 !important;
}

/* ── Alerts ────────────────────────────────────────────── */
[data-testid="stAlert"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-left: 3px solid var(--text) !important;
    color: var(--text) !important;
    border-radius: var(--radius) !important;
    box-shadow: none !important;
}
[data-testid="stAlert"] p { color: var(--text) !important; }

/* ── Captions and small text ───────────────────────────── */
.stCaption, .stCaption p {
    color: var(--text-muted) !important;
    font-size: 0.8rem !important;
}

/* ── Code blocks ───────────────────────────────────────── */
code {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 4px !important;
    padding: 0.1rem 0.35rem !important;
    font-size: 0.85em !important;
}
pre code {
    border: none !important;
    padding: 0 !important;
}
pre {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 0.75rem 1rem !important;
}

/* ── Dividers ──────────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
}

/* ── Toast ─────────────────────────────────────────────── */
[data-testid="stToast"] {
    background: var(--text) !important;
    color: var(--bg) !important;
    border-radius: var(--radius) !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
}

/* ── Subtle fade ───────────────────────────────────────── */
.fade-up {
    animation: fadeUp 0.3s ease-out;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ── Scrollbar ─────────────────────────────────────────── */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════

defaults = {
    "messages": [],
    "chat_history": [],
    "full_session_history": [],
    "attachment": None,
    "configured": False,
    "groq_api_key": "",
    "github_repo": "",
    "github_token": "",
    "jira_base_url": "",
    "jira_username": "",
    "jira_password": "",
    "ingested": False,
    "last_chroma_update": None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Load defaults from .env if present
if not st.session_state.configured:
    from config import GROQ_API_KEY, GITHUB_REPO, GITHUB_TOKEN, JIRA_BASE_URL, JIRA_USERNAME, JIRA_PASSWORD
    if GROQ_API_KEY and GITHUB_REPO:
        st.session_state.groq_api_key = GROQ_API_KEY
        st.session_state.github_repo = GITHUB_REPO
        st.session_state.github_token = GITHUB_TOKEN
        st.session_state.jira_base_url = JIRA_BASE_URL
        st.session_state.jira_username = JIRA_USERNAME
        st.session_state.jira_password = JIRA_PASSWORD
        st.session_state.configured = True


# ═══════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _db_dir() -> Path:
    """ChromaDB storage directory."""
    return Path(__file__).parent / "chroma_db"


def run_ingest_web():
    import asyncio
    from ingest import ingest_documents
    import retriever as _retriever

    with st.spinner("Fetching & indexing documents from your repository..."):
        try:
            asyncio.run(
                ingest_documents(
                    github_repo=st.session_state.github_repo,
                    github_token=st.session_state.github_token,
                    db_dir=_db_dir(),
                )
            )
            _retriever.reset_singletons()
            st.session_state.ingested = True
            st.toast("Knowledge base synced!", icon="✅")
        except Exception as e:
            st.error(f"Ingestion failed: {e}")


def handle_file_upload(uploaded_file):
    from file_handler import extract_diagnostics
    from config import MAX_ATTACHMENT_BYTES, MAX_ATTACHMENT_LINES

    content_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    if len(content_bytes) > MAX_ATTACHMENT_BYTES:
        st.toast(f"File too large ({len(content_bytes)//1024}KB). Max: {MAX_ATTACHMENT_BYTES//1024}KB", icon="⚠️")
        return

    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            content = content_bytes.decode("latin-1")
        except Exception:
            st.toast("Cannot decode file.", icon="❌")
            return

    content = content.replace("\x00", "")
    lines = content.splitlines(keepends=True)
    truncated = len(lines) > MAX_ATTACHMENT_LINES
    if truncated:
        content = "".join(lines[:MAX_ATTACHMENT_LINES])

    diagnostics = extract_diagnostics(content)
    st.session_state.attachment = {
        "file_name": uploaded_file.name,
        "file_path": uploaded_file.name,
        "content": content,
        "truncated": truncated,
        "diagnostics": diagnostics,
    }


def get_learned_patterns_count():
    try:
        from learning_agent import get_learned_count
        return get_learned_count(db_dir=_db_dir())
    except Exception:
        return 0


def update_chroma_from_current_session():
    from learning_agent import learn_from_session, store_session_memory_embeddings, get_learned_count
    import retriever as _retriever

    chat_history = st.session_state.full_session_history
    attachment = st.session_state.attachment

    with st.spinner("Updating ChromaDB with current chat and attachment embeddings..."):
        patterns = learn_from_session(
            chat_history,
            attachment,
            db_dir=_db_dir(),
            groq_api_key=st.session_state.groq_api_key,
        )
        memory_result = store_session_memory_embeddings(
            chat_history,
            attachment,
            db_dir=_db_dir(),
        )
        _retriever.reset_singletons()

    total_patterns = get_learned_count(db_dir=_db_dir())
    st.session_state.last_chroma_update = {
        "patterns_added": len(patterns),
        "memory_stored": bool(memory_result.get("stored")),
        "entry_id": memory_result.get("entry_id", ""),
        "reason": memory_result.get("reason", ""),
        "message_pairs": memory_result.get("message_pairs", 0),
        "has_attachment": bool(memory_result.get("has_attachment")),
        "total_patterns": total_patterns,
    }

    if len(patterns) > 0 or memory_result.get("stored"):
        st.toast("ChromaDB updated from this session.", icon="✅")
    else:
        st.toast("No new embedding stored (already saved or no chat yet).", icon="ℹ️")


# ─────────────────────────────────────────────────────────────
# Jira Issue Analysis Helper
# ─────────────────────────────────────────────────────────────

def _detect_and_fetch_jira(query: str) -> dict | None:
    """
    Detect Jira issue keys in a query (e.g., SCRUM-2, DATA-101) and fetch
    the issue details + comments for LLM analysis.
    Returns None if no Jira key found or Jira not configured.
    """
    import httpx
    from base64 import b64encode

    # Pattern: 2-10 uppercase letters followed by dash and 1-6 digits
    jira_pattern = re.compile(r'\b([A-Z]{2,10}-\d{1,6})\b')
    matches = jira_pattern.findall(query)
    if not matches:
        return None

    issue_key = matches[0]  # Use the first detected key

    # Check if Jira is configured
    jira_url = st.session_state.get("jira_base_url", "").strip()
    jira_user = st.session_state.get("jira_username", "").strip()
    jira_pass = st.session_state.get("jira_password", "").strip()

    if not all([jira_url, jira_user, jira_pass]):
        return None

    base_url = jira_url.rstrip("/")
    creds = b64encode(f"{jira_user}:{jira_pass}".encode()).decode()
    headers = {
        "Authorization": f"Basic {creds}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        # Fetch issue details
        r = httpx.get(
            f"{base_url}/rest/api/3/issue/{issue_key}",
            headers=headers,
            params={"expand": "renderedFields"},
            verify=True,
            timeout=15,
        )
        if r.status_code != 200:
            return None

        issue = r.json()
        fields = issue.get("fields", {})

        # Extract key fields
        summary = fields.get("summary", "")
        status = (fields.get("status") or {}).get("name", "Unknown")
        priority = (fields.get("priority") or {}).get("name", "None")
        issuetype = (fields.get("issuetype") or {}).get("name", "Unknown")
        assignee = (fields.get("assignee") or {}).get("displayName", "Unassigned")
        reporter = (fields.get("reporter") or {}).get("displayName", "Unknown")
        project = (fields.get("project") or {}).get("key", "Unknown")
        created = fields.get("created", "")[:10]
        labels = fields.get("labels", [])

        # Parse ADF description to plain text
        description = _adf_to_text(fields.get("description"))

        # Fetch comments
        r2 = httpx.get(
            f"{base_url}/rest/api/3/issue/{issue_key}/comment",
            headers=headers,
            params={"maxResults": 20, "orderBy": "created"},
            verify=True,
            timeout=15,
        )
        comments_text = ""
        if r2.status_code == 200:
            comments = r2.json().get("comments", [])
            for c in comments:
                author = (c.get("author") or {}).get("displayName", "Unknown")
                body = _adf_to_text(c.get("body"))
                date = c.get("created", "")[:10]
                comments_text += f"\n--- Comment by {author} ({date}) ---\n{body}\n"

        # Build full text for LLM
        full_text = (
            f"JIRA ISSUE: {issue_key}\n"
            f"{'=' * 50}\n"
            f"Summary: {summary}\n"
            f"Type: {issuetype} | Priority: {priority} | Status: {status}\n"
            f"Assignee: {assignee} | Reporter: {reporter}\n"
            f"Project: {project} | Created: {created}\n"
            f"Labels: {', '.join(labels) if labels else 'None'}\n"
            f"URL: {base_url}/browse/{issue_key}\n"
            f"{'─' * 50}\n"
            f"DESCRIPTION:\n{description}\n"
        )
        if comments_text:
            full_text += f"\n{'─' * 50}\nCOMMENTS:{comments_text}\n"

        # Extract search terms for KB retrieval (summary + key technology words)
        search_terms = f"{summary} {issuetype} {' '.join(labels)}"

        # Detect errors/warnings from description + comments
        all_text = f"{description}\n{comments_text}"
        errors = []
        warnings = []
        for line in all_text.split("\n"):
            line_lower = line.strip().lower()
            if any(kw in line_lower for kw in ["error", "exception", "traceback", "failed", "fatal"]):
                errors.append(line.strip())
            elif any(kw in line_lower for kw in ["warning", "warn", "deprecated", "timeout"]):
                warnings.append(line.strip())

        return {
            "key": issue_key,
            "summary": summary,
            "full_text": full_text,
            "search_terms": search_terms,
            "errors": errors[:10],  # Limit to avoid overflow
            "warnings": warnings[:5],
        }

    except Exception:
        return None


def _adf_to_text(adf) -> str:
    """Convert Atlassian Document Format to plain text."""
    if not adf:
        return ""
    if isinstance(adf, str):
        return adf

    text_parts = []

    def _extract(node):
        if isinstance(node, dict):
            if node.get("type") == "text":
                text_parts.append(node.get("text", ""))
            elif node.get("type") == "hardBreak":
                text_parts.append("\n")
            for child in node.get("content", []):
                _extract(child)
        elif isinstance(node, list):
            for item in node:
                _extract(item)

    _extract(adf)
    return "".join(text_parts).strip()


def get_answer(query: str) -> tuple[str, list[dict]]:
    from retriever import retrieve
    from llm_client import build_rag_prompt, GROQ_MODEL
    from file_handler import build_search_query_from_attachment
    from groq import Groq
    from config import CHAT_HISTORY_PAIRS

    search_query = query
    attachment = st.session_state.attachment

    # ── Detect Jira issue keys in the query (e.g., SCRUM-2, DATA-101) ──
    jira_context = _detect_and_fetch_jira(query)

    if attachment:
        attachment_query = build_search_query_from_attachment(attachment)
        search_query = f"{query} {attachment_query}"
    elif jira_context:
        # Use Jira issue content to enhance KB retrieval
        search_query = f"{query} {jira_context['search_terms']}"

    chunks = retrieve(search_query, db_dir=_db_dir())
    chat_history = st.session_state.chat_history

    # If Jira issue was detected, inject it as an attachment-like context
    effective_attachment = attachment
    if jira_context and not attachment:
        effective_attachment = {
            "file_name": f"Jira Issue: {jira_context['key']}",
            "content": jira_context["full_text"],
            "truncated": False,
            "diagnostics": {
                "errors": jira_context.get("errors", []),
                "warnings": jira_context.get("warnings", []),
            },
        }

    messages = build_rag_prompt(query, chunks, chat_history, effective_attachment)

    # For Jira analysis, enhance the system prompt with analysis instructions
    if jira_context:
        jira_analysis_instruction = (
            "\n\nIMPORTANT: The user is asking you to analyze a Jira issue/ticket. "
            "Structure your response as follows:\n"
            "1. **Issue Summary** — What this ticket is about\n"
            "2. **Error Analysis** — Identify the root cause of the error from the logs/description\n"
            "3. **Solution Ideas** — Provide concrete, actionable solutions (use knowledge base if applicable)\n"
            "4. **Prevention Strategy** — How to prevent this issue from recurring\n\n"
            "Use both the Jira ticket details AND the knowledge base context to provide the best answer. "
            "If the knowledge base has relevant documentation, cite it. "
            "You may also use your technical expertise to supplement the analysis."
        )
        messages[0]["content"] += jira_analysis_instruction

    client = Groq(api_key=st.session_state.groq_api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.1,
        max_tokens=2048,
        stream=True,
    )

    full_answer = ""
    answer_placeholder = st.empty()
    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            full_answer += delta
            answer_placeholder.markdown(full_answer + " ▍")
    answer_placeholder.markdown(full_answer)

    st.session_state.chat_history.append({"role": "user", "content": query})
    st.session_state.chat_history.append({"role": "assistant", "content": full_answer})
    st.session_state.full_session_history.append({"role": "user", "content": query})
    st.session_state.full_session_history.append({"role": "assistant", "content": full_answer})

    max_messages = CHAT_HISTORY_PAIRS * 2
    if len(st.session_state.chat_history) > max_messages:
        st.session_state.chat_history = st.session_state.chat_history[-max_messages:]

    return full_answer, chunks


# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════

with st.sidebar:
    # Brand
    st.markdown("""
    <div style="text-align:center; padding: 1.2rem 0 0.6rem 0;">
        <div style="font-size:2.2rem; margin-bottom:0.2rem;">⚡</div>
        <div style="font-size:1.4rem; font-weight:800; letter-spacing:-0.02em;
                    background: linear-gradient(135deg, #0891b2, #14b8a6);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            DataGuru
        </div>
        <div style="font-size:0.68rem; color:#6b7280; margin-top:0.2rem; font-weight:400;">
            Knowledge Assistant • v3.0
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ─ Credentials
    st.markdown('<div class="sec-label">🔐 CONNECTION</div>', unsafe_allow_html=True)

    groq_key = st.text_input("Groq API Key", value=st.session_state.groq_api_key, type="password", placeholder="gsk_...")
    github_repo = st.text_input("GitHub Repo", value=st.session_state.github_repo, placeholder="owner/repo-name")
    github_token = st.text_input("GitHub Token", value=st.session_state.github_token, type="password", placeholder="ghp_... (optional for public)")

    # Jira section (collapsible)
    with st.expander("🎫 Jira Integration (Optional)"):
        jira_url = st.text_input("Jira Base URL", value=st.session_state.jira_base_url, placeholder="https://yourcompany.atlassian.net")
        jira_user = st.text_input("Jira Username", value=st.session_state.jira_username, placeholder="your-email@company.com")
        jira_pass = st.text_input("Jira Password/Token", value=st.session_state.jira_password, type="password", placeholder="API token")

    if st.button("Connect", use_container_width=True, type="primary"):
        if not groq_key:
            st.toast("Groq API Key is required", icon="⚠️")
        elif not github_repo:
            st.toast("GitHub Repo is required", icon="⚠️")
        else:
            repo_clean = github_repo.replace("https://github.com/", "").replace("http://github.com/", "").strip("/")
            st.session_state.groq_api_key = groq_key
            st.session_state.github_repo = repo_clean
            st.session_state.github_token = github_token
            st.session_state.jira_base_url = jira_url.rstrip("/") if jira_url else ""
            st.session_state.jira_username = jira_user
            st.session_state.jira_password = jira_pass
            st.session_state.configured = True
            # Set env vars so MCP servers can access them
            import os
            os.environ["GROQ_API_KEY"] = groq_key
            os.environ["GITHUB_REPO"] = repo_clean
            os.environ["GITHUB_TOKEN"] = github_token
            os.environ["JIRA_BASE_URL"] = st.session_state.jira_base_url
            os.environ["JIRA_USERNAME"] = jira_user
            os.environ["JIRA_PASSWORD"] = jira_pass
            st.rerun()

    if st.session_state.configured:
        st.markdown(
            f'<div class="pill-connected"><span class="pulse-dot"></span> '
            f'{st.session_state.github_repo.split("/")[-1]}</div>',
            unsafe_allow_html=True,
        )
        if st.session_state.jira_base_url:
            jira_display = st.session_state.jira_base_url.replace("https://", "").split(".")[0]
            st.markdown(
                f'<div class="pill-connected" style="margin-top:0.3rem;"><span class="pulse-dot"></span> Jira: {jira_display}</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown('<div class="pill-disconnected">○ Not connected</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ─ Knowledge Base
    st.markdown('<div class="sec-label">📚 KNOWLEDGE BASE</div>', unsafe_allow_html=True)

    if st.session_state.configured:
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Sync Docs", use_container_width=True):
                run_ingest_web()
        with col2:
            if st.session_state.ingested:
                st.markdown("<div style='text-align:center; padding-top:0.35rem; font-size:1.1rem;'>✅</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align:center; padding-top:0.35rem; font-size:1.1rem;'>⏳</div>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.65rem; color:#6b7280 !important; margin-top:0.2rem;">One-time setup. Re-sync only when repo changes.</div>', unsafe_allow_html=True)
    else:
        st.caption("Connect first")

    st.markdown("---")

    # ─ File Upload
    st.markdown('<div class="sec-label">📎 ATTACH FILE</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Drag & drop file",
        type=["log", "txt", "sql", "csv", "json", "xml", "py", "sh", "yaml", "yml", "conf", "cfg", "ini", "md"],
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        handle_file_upload(uploaded_file)
        if st.session_state.attachment:
            att = st.session_state.attachment
            st.markdown(f'<div class="file-pill">📄 {att["file_name"]}</div>', unsafe_allow_html=True)
            diag = att["diagnostics"]
            if diag.get("errors"):
                st.caption(f"Found {len(diag['errors'])} issue(s)")
    elif st.session_state.attachment:
        att = st.session_state.attachment
        st.markdown(f'<div class="file-pill">📄 {att["file_name"]}</div>', unsafe_allow_html=True)
        if st.button("✕ Remove", key="detach_btn"):
            st.session_state.attachment = None
            st.rerun()

    st.markdown("---")

    # ─ Stats
    st.markdown('<div class="sec-label">📊 INTELLIGENCE</div>', unsafe_allow_html=True)

    if st.session_state.configured and st.session_state.ingested:
        learned = get_learned_patterns_count()
        msgs = len(st.session_state.messages)
        st.markdown(f"""
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.6rem; margin-bottom:1rem;">
            <div class="stat-box">
                <div class="stat-val">{learned}</div>
                <div class="stat-lbl">Patterns</div>
            </div>
            <div class="stat-box">
                <div class="stat-val">{msgs}</div>
                <div class="stat-lbl">Messages</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        can_update = len(st.session_state.full_session_history) >= 2
        if st.button("Update Chroma from Chat", use_container_width=True, disabled=not can_update):
            update_chroma_from_current_session()
            st.rerun()

        if not can_update:
            st.caption("Ask at least one question first.")

        status = st.session_state.last_chroma_update
        if status:
            icon = "✅" if (status["patterns_added"] > 0 or status["memory_stored"]) else "ℹ️"
            st.caption(
                f"{icon} Patterns +{status['patterns_added']}, "
                f"pairs: {status['message_pairs']}, "
                f"total: {status['total_patterns']}"
            )
    else:
        st.caption("Available after sync")

    st.markdown("---")

    # ─ Export Chat
    st.markdown('<div class="sec-label">📤 EXPORT CHAT</div>', unsafe_allow_html=True)

    if st.session_state.messages:
        export_col1, export_col2 = st.columns(2)
        with export_col1:
            from chat_export import export_chat_as_text
            txt_data = export_chat_as_text(st.session_state.messages, "User")
            st.download_button(
                "📄 TXT",
                data=txt_data,
                file_name=f"dataguru_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with export_col2:
            from chat_export import export_chat_as_pdf
            try:
                pdf_data = export_chat_as_pdf(st.session_state.messages, "User")
                st.download_button(
                    "📕 PDF",
                    data=pdf_data,
                    file_name=f"dataguru_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception:
                st.caption("PDF export requires fpdf2")
    else:
        st.caption("No chat to export yet.")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; padding:0.2rem 0;">
        <div style="font-size:0.72rem; color:#9ca3af; margin-bottom:0.4rem;">
            Made with <span style="color:#ef4444;">❤</span> by <strong style="color:#e5e7eb;">Tejas Pundpal</strong>
        </div>
        <a href="https://in.linkedin.com/in/tejas-pundpal-784105206" target="_blank"
           style="display:inline-flex; align-items:center; gap:0.3rem; color:#0a66c2;
                  text-decoration:none; font-size:0.68rem; padding:0.2rem 0.55rem;
                  background:rgba(10,102,194,0.08); border-radius:12px; border:1px solid rgba(10,102,194,0.15);">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="#0a66c2">
                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
            </svg>
            LinkedIn
        </a>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# MAIN CONTENT
# ═══════════════════════════════════════════════════════════════

# Hero
st.markdown("""
<div class="hero-container fade-up">
    <div class="hero-title">
        ⚡ <span class="logo-accent">DataGuru</span>
    </div>
    <div class="hero-subtitle">
        Your private knowledge assistant for Data Engineering — ask about pipelines, debug errors, analyze logs, investigate Jira tickets, and get instant answers from your own docs.
    </div>
    <div class="hero-badges">
        <span class="hero-badge"><span class="pulse-dot"></span> RAG-Powered</span>
        <span class="hero-badge">🧠 Self-Learning</span>
        <span class="hero-badge">📎 File Analysis</span>
        <span class="hero-badge">🎫 Jira Integration</span>
        <span class="hero-badge">🔒 Fully Private</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ─── Gated: Not Connected ────────────────────────────────────
if not st.session_state.configured:
    st.markdown("""
    <div class="onboard-grid">
        <div class="onboard-card fade-up fade-up-d1">
            <div class="onboard-icon onboard-icon-green">🔑</div>
            <div class="onboard-title">1. Connect</div>
            <div class="onboard-desc">Enter your free Groq API key and the GitHub repo that holds your knowledge base documents. Optionally add Jira credentials.</div>
        </div>
        <div class="onboard-card fade-up fade-up-d2">
            <div class="onboard-icon onboard-icon-amber">📥</div>
            <div class="onboard-title">2. Sync Once</div>
            <div class="onboard-desc">First time only — click "Sync Docs" to index your repo. After that, DataGuru remembers everything.</div>
        </div>
        <div class="onboard-card fade-up fade-up-d3">
            <div class="onboard-icon onboard-icon-blue">💬</div>
            <div class="onboard-title">3. Ask Anything</div>
            <div class="onboard-desc">Get instant answers with source citations. Drop a log file or paste a Jira ticket number for analysis.</div>
        </div>
        <div class="onboard-card fade-up fade-up-d4">
            <div class="onboard-icon onboard-icon-rose">🧠</div>
            <div class="onboard-title">4. Gets Smarter</div>
            <div class="onboard-desc">DataGuru learns patterns from every conversation and auto-generates reusable troubleshooting skills.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ─── Gated: Not Ingested ─────────────────────────────────────
if not st.session_state.ingested:
    db_dir = _db_dir()
    if db_dir.exists() and any(db_dir.iterdir()):
        st.session_state.ingested = True
    else:
        st.markdown("""
        <div class="onboard-grid fade-up">
            <div class="onboard-card" style="grid-column:1/-1; text-align:center; padding:2.5rem 2rem;">
                <div class="onboard-icon onboard-icon-amber" style="margin:0 auto 1rem;">📥</div>
                <div class="onboard-title" style="font-size:1.1rem;">First-Time Setup: Sync Your Knowledge Base</div>
                <div class="onboard-desc" style="max-width:450px; margin:0.5rem auto 0; font-size:0.85rem;">
                    Click <strong>"Sync Docs"</strong> in the sidebar to fetch and index documents from your GitHub repo.
                    This is a one-time step — re-sync only when you add new files.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()


# ═══════════════════════════════════════════════════════════════
# CHAT INTERFACE
# ═══════════════════════════════════════════════════════════════

# Previous messages
for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "⚡"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg.get("sources"):
            chips = "".join(
                f'<span class="src-chip {"learned" if "learned" in s.lower() else ""}">'
                f'{"🧠" if "learned" in s.lower() else "📄"} {s}</span>'
                for s in msg["sources"]
            )
            st.markdown(f'<div class="sources-row">{chips}</div>', unsafe_allow_html=True)

# File indicator
if st.session_state.attachment:
    st.markdown(
        f'<div class="file-pill">📎 Analyzing: {st.session_state.attachment["file_name"]}</div>',
        unsafe_allow_html=True
    )

# Empty state
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-chat fade-up">
        <div class="empty-chat-icon">💬</div>
        <div class="empty-chat-title">What can I help you with?</div>
        <div class="empty-chat-desc">Ask about your data pipelines, troubleshoot errors, or analyze attached files.</div>
    </div>
    """, unsafe_allow_html=True)

    suggestions = [
        "What are common Informatica session failures?",
        "How do I optimize a slow SQL query?",
        "Explain our ETL pipeline architecture",
        "Best practices for data quality checks",
    ]
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(suggestion, key=f"suggest_{i}", use_container_width=True):
                st.session_state["_pending_input"] = suggestion
                st.rerun()

# Handle suggestion click
if "_pending_input" in st.session_state:
    pending = st.session_state.pop("_pending_input")
    st.session_state.messages.append({"role": "user", "content": pending})
    with st.chat_message("user", avatar="👤"):
        st.markdown(pending)
    with st.chat_message("assistant", avatar="⚡"):
        try:
            answer, chunks = get_answer(pending)
            sources = []
            seen = set()
            for chunk in chunks:
                src = chunk["source"]
                if src not in seen:
                    sources.append(f"{src} ({chunk['score']})")
                    seen.add(src)
            if sources:
                chips = "".join(
                    f'<span class="src-chip {"learned" if "learned" in s.lower() else ""}">'
                    f'{"🧠" if "learned" in s.lower() else "📄"} {s}</span>'
                    for s in sources
                )
                st.markdown(f'<div class="sources-row">{chips}</div>', unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
        except Exception as e:
            st.error(f"Error: {e}")

# Chat input
if user_input := st.chat_input("Ask DataGuru anything..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="⚡"):
        try:
            answer, chunks = get_answer(user_input)
            sources = []
            seen = set()
            for chunk in chunks:
                src = chunk["source"]
                if src not in seen:
                    sources.append(f"{src} ({chunk['score']})")
                    seen.add(src)

            if sources:
                chips = "".join(
                    f'<span class="src-chip {"learned" if "learned" in s.lower() else ""}">'
                    f'{"🧠" if "learned" in s.lower() else "📄"} {s}</span>'
                    for s in sources
                )
                st.markdown(f'<div class="sources-row">{chips}</div>', unsafe_allow_html=True)

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources,
            })

        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "auth" in error_msg.lower():
                st.error("Invalid API key — check your credentials in the sidebar.")
            else:
                st.error(f"Something went wrong: {error_msg}")
