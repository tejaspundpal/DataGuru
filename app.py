"""
DataGuru — Premium Web UI
A private Data Engineering knowledge assistant powered by RAG + Self-Learning.

Run: streamlit run app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st

# ─── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="DataGuru",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Premium CSS Theme — Emerald & Gold ───────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --primary: #0891b2;
    --primary-light: #06b6d4;
    --primary-dark: #0e7490;
    --accent: #14b8a6;
    --accent-light: #2dd4bf;
    --surface: #ffffff;
    --surface-2: #f8fdfd;
    --bg: #f0fdfa;
    --text: #1a1a2e;
    --text-muted: #6b7280;
    --border: #e5e7eb;
    --border-light: #f3f4f6;
    --success: #0d9488;
    --warning: #d97706;
    --error: #dc2626;
    --gradient-brand: linear-gradient(135deg, #0891b2 0%, #06b6d4 40%, #14b8a6 100%);
    --gradient-dark: linear-gradient(160deg, #1e3a4a 0%, #234e5e 50%, #1a3d4d 100%);
    --gradient-card: linear-gradient(135deg, #ffffff 0%, #f0fdfa 100%);
    --shadow-xs: 0 1px 2px rgba(0,0,0,0.04);
    --shadow-sm: 0 2px 4px rgba(0,0,0,0.06);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
    --shadow-lg: 0 8px 24px rgba(0,0,0,0.10);
    --shadow-glow: 0 0 30px rgba(8,145,178,0.12);
    --radius: 14px;
    --radius-sm: 10px;
    --radius-xs: 6px;
    --radius-full: 9999px;
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

.main .block-container {
    padding: 1.2rem 2.5rem 4rem 2.5rem;
    max-width: 1100px;
}

/* ── Sidebar ──────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--gradient-dark) !important;
    border-right: 1px solid rgba(255,255,255,0.04);
}
section[data-testid="stSidebar"] > div {
    padding-top: 0 !important;
}
[data-testid="stSidebar"] * {
    color: #d1d5db !important;
}
[data-testid="stSidebar"] .stTextInput > div > div > input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #f3f4f6 !important;
    border-radius: var(--radius-xs);
    font-size: 0.85rem !important;
    padding: 0.55rem 0.75rem !important;
    transition: all 0.2s ease;
}
[data-testid="stSidebar"] .stTextInput > div > div > input:focus {
    border-color: var(--primary-light) !important;
    box-shadow: 0 0 0 2px rgba(6,182,212,0.2) !important;
    background: rgba(255,255,255,0.08) !important;
}
[data-testid="stSidebar"] .stTextInput label {
    color: #9ca3af !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.01em;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.06) !important;
    margin: 0.8rem 0 !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: var(--gradient-brand) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius-xs) !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    padding: 0.55rem 1rem !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 3px 10px rgba(8,145,178,0.25) !important;
    letter-spacing: 0.01em !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 5px 16px rgba(8,145,178,0.35) !important;
    filter: brightness(1.05) !important;
}
[data-testid="stSidebar"] .stFileUploader {
    background: rgba(255,255,255,0.03) !important;
    border: 1px dashed rgba(255,255,255,0.12) !important;
    border-radius: var(--radius-xs) !important;
    padding: 0.4rem !important;
}
[data-testid="stSidebar"] .stFileUploader label {
    color: #6b7280 !important;
    font-size: 0.75rem !important;
}

/* ── Hero ─────────────────────────────────────────────────── */
.hero-container {
    background: var(--gradient-dark);
    border-radius: 20px;
    padding: 2.8rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-lg), var(--shadow-glow);
    border: 1px solid rgba(255,255,255,0.04);
}
.hero-container::before {
    content: '';
    position: absolute;
    top: -40%;
    right: -15%;
    width: 380px;
    height: 380px;
    background: radial-gradient(circle, rgba(6,182,212,0.18) 0%, transparent 65%);
    border-radius: 50%;
    animation: float 8s ease-in-out infinite;
}
.hero-container::after {
    content: '';
    position: absolute;
    bottom: -35%;
    left: 5%;
    width: 280px;
    height: 280px;
    background: radial-gradient(circle, rgba(20,184,166,0.12) 0%, transparent 65%);
    border-radius: 50%;
    animation: float 10s ease-in-out infinite reverse;
}
@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-12px); }
}
.hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    color: #ffffff;
    margin: 0;
    position: relative;
    z-index: 1;
    letter-spacing: -0.02em;
}
.hero-title .logo-accent {
    background: var(--gradient-brand);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-subtitle {
    color: #9ca3af;
    font-size: 1.05rem;
    margin-top: 0.6rem;
    position: relative;
    z-index: 1;
    font-weight: 400;
    line-height: 1.5;
    max-width: 600px;
}
.hero-badges {
    display: flex;
    gap: 0.5rem;
    margin-top: 1.4rem;
    position: relative;
    z-index: 1;
    flex-wrap: wrap;
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: var(--radius-full);
    padding: 0.35rem 0.8rem;
    font-size: 0.75rem;
    color: #d1d5db;
    font-weight: 500;
    backdrop-filter: blur(8px);
    transition: all 0.2s ease;
}
.hero-badge:hover {
    background: rgba(255,255,255,0.1);
    border-color: rgba(255,255,255,0.15);
}
.pulse-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--primary-light);
    animation: pulse 2.5s ease-in-out infinite;
    box-shadow: 0 0 6px rgba(6,182,212,0.4);
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.6; transform: scale(1.4); }
}

/* ── Onboarding Cards ─────────────────────────────────────── */
.onboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1rem;
    margin-top: 1.8rem;
}
.onboard-card {
    background: var(--gradient-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.6rem 1.4rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: default;
    position: relative;
    overflow: hidden;
}
.onboard-card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-md);
    border-color: var(--primary-light);
}
.onboard-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--gradient-brand);
    opacity: 0;
    transition: opacity 0.3s ease;
}
.onboard-card:hover::after { opacity: 1; }
.onboard-icon {
    width: 42px;
    height: 42px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    margin-bottom: 1rem;
}
.onboard-icon-green { background: #ecfeff; border: 1px solid #a5f3fc; }
.onboard-icon-amber { background: #ecfeff; border: 1px solid #99f6e4; }
.onboard-icon-blue { background: #f0fdfa; border: 1px solid #5eead4; }
.onboard-icon-rose { background: #f0f9ff; border: 1px solid #7dd3fc; }
.onboard-title {
    font-weight: 600;
    font-size: 0.92rem;
    color: var(--text);
    margin-bottom: 0.4rem;
}
.onboard-desc {
    font-size: 0.8rem;
    color: var(--text-muted);
    line-height: 1.55;
}

/* ── Chat Messages ────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: var(--surface) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: var(--radius) !important;
    padding: 1.1rem 1.3rem !important;
    margin-bottom: 0.8rem !important;
    box-shadow: var(--shadow-xs) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stChatMessage"]:hover {
    box-shadow: var(--shadow-sm) !important;
    border-color: var(--border) !important;
}

/* ── Source Chips ─────────────────────────────────────────── */
.sources-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    margin-top: 0.75rem;
    padding-top: 0.6rem;
    border-top: 1px solid var(--border-light);
}
.src-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    background: #f9fafb;
    border: 1px solid var(--border);
    border-radius: var(--radius-full);
    padding: 0.2rem 0.6rem;
    font-size: 0.68rem;
    color: var(--text-muted);
    font-weight: 500;
    font-family: 'JetBrains Mono', monospace;
    transition: all 0.15s ease;
}
.src-chip:hover { background: #f3f4f6; color: var(--text); }
.src-chip.learned {
    background: #ecfeff;
    border-color: #a5f3fc;
    color: #0e7490;
}

/* ── Attachment Pill ──────────────────────────────────────── */
.file-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: var(--radius-full);
    padding: 0.3rem 0.8rem;
    font-size: 0.78rem;
    color: #92400e;
    font-weight: 500;
    margin-bottom: 0.6rem;
}

/* ── Status Pills ─────────────────────────────────────────── */
.pill-connected {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: rgba(8,145,178,0.08);
    border: 1px solid rgba(8,145,178,0.18);
    border-radius: var(--radius-full);
    padding: 0.25rem 0.7rem;
    font-size: 0.73rem;
    color: #0891b2;
    font-weight: 500;
}
.pill-disconnected {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: rgba(217,119,6,0.08);
    border: 1px solid rgba(217,119,6,0.18);
    border-radius: var(--radius-full);
    padding: 0.25rem 0.7rem;
    font-size: 0.73rem;
    color: #b45309;
    font-weight: 500;
}

/* ── Stat Boxes ───────────────────────────────────────────── */
.stat-box {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: var(--radius-sm);
    padding: 0.7rem 0.5rem;
    text-align: center;
}
.stat-val {
    font-size: 1.5rem;
    font-weight: 700;
    background: var(--gradient-brand);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.2;
}
.stat-lbl {
    font-size: 0.65rem;
    color: #6b7280 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 0.15rem;
    font-weight: 600;
}

/* ── Chat Input ───────────────────────────────────────────── */
[data-testid="stChatInput"] {
    border-radius: var(--radius) !important;
    border: 1.5px solid var(--border) !important;
    transition: all 0.2s ease !important;
    box-shadow: var(--shadow-xs) !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: var(--primary-light) !important;
    box-shadow: 0 0 0 3px rgba(6,182,212,0.1) !important;
}

/* ── Section Labels ───────────────────────────────────────── */
.sec-label {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #6b7280 !important;
    font-weight: 600;
    margin-bottom: 0.4rem;
}

/* ── Suggestion Buttons ───────────────────────────────────── */
div.stButton > button {
    transition: all 0.2s ease !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: var(--radius-sm) !important;
    font-size: 0.8rem !important;
    font-weight: 400 !important;
    text-align: left !important;
    padding: 0.7rem 1rem !important;
    box-shadow: var(--shadow-xs) !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button:hover {
    border-color: var(--primary-light) !important;
    background: var(--surface-2) !important;
    box-shadow: var(--shadow-sm) !important;
    transform: translateY(-1px) !important;
}

/* ── Empty Chat State ─────────────────────────────────────── */
.empty-chat {
    text-align: center;
    padding: 3rem 1rem 1.5rem;
}
.empty-chat-icon {
    width: 56px;
    height: 56px;
    margin: 0 auto 1rem;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
}
.empty-chat-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 0.3rem;
}
.empty-chat-desc {
    font-size: 0.83rem;
    color: var(--text-muted);
}

/* ── Scrollbar ────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #9ca3af; }

/* ── Animations ───────────────────────────────────────────── */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(14px); }
    to { opacity: 1; transform: translateY(0); }
}
.fade-up { animation: fadeUp 0.5s cubic-bezier(0.4, 0, 0.2, 1) forwards; }
.fade-up-d1 { animation-delay: 0.05s; opacity: 0; }
.fade-up-d2 { animation-delay: 0.1s; opacity: 0; }
.fade-up-d3 { animation-delay: 0.15s; opacity: 0; }
.fade-up-d4 { animation-delay: 0.2s; opacity: 0; }
</style>
""", unsafe_allow_html=True)


# ─── Session State ────────────────────────────────────────────
def init_session_state():
    defaults = {
        "messages": [],
        "chat_history": [],
        "full_session_history": [],
        "attachment": None,
        "configured": False,
        "groq_api_key": "",
        "github_repo": "",
        "github_token": "",
        "ingested": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()


# ─── Core Functions ───────────────────────────────────────────
def apply_user_config():
    import os
    import config
    config.GROQ_API_KEY = st.session_state.groq_api_key
    config.GITHUB_REPO = st.session_state.github_repo
    config.GITHUB_TOKEN = st.session_state.github_token
    os.environ["GROQ_API_KEY"] = st.session_state.groq_api_key
    os.environ["GITHUB_REPO"] = st.session_state.github_repo
    os.environ["GITHUB_TOKEN"] = st.session_state.github_token


def run_ingest_web():
    import asyncio
    apply_user_config()
    from ingest import ingest_documents
    import retriever as _retriever

    with st.spinner("Fetching & indexing documents from your repository..."):
        try:
            asyncio.run(ingest_documents())
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
        return get_learned_count()
    except Exception:
        return 0


def get_answer(query: str) -> tuple[str, list[dict]]:
    apply_user_config()

    from retriever import retrieve
    from llm_client import build_rag_prompt, GROQ_MODEL
    from file_handler import build_search_query_from_attachment
    from groq import Groq
    from config import CHAT_HISTORY_PAIRS

    search_query = query
    attachment = st.session_state.attachment
    if attachment:
        attachment_query = build_search_query_from_attachment(attachment)
        search_query = f"{query} {attachment_query}"

    chunks = retrieve(search_query)
    chat_history = st.session_state.chat_history
    messages = build_rag_prompt(query, chunks, chat_history, attachment)

    client = Groq(api_key=st.session_state.groq_api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.1,
        max_tokens=1024,
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


# ─── Sidebar ──────────────────────────────────────────────────
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
            Knowledge Assistant • v2.1
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ─ Credentials
    st.markdown('<div class="sec-label">🔐 CONNECTION</div>', unsafe_allow_html=True)

    groq_key = st.text_input("Groq API Key", value=st.session_state.groq_api_key, type="password", placeholder="gsk_...")
    github_repo = st.text_input("GitHub Repo", value=st.session_state.github_repo, placeholder="owner/repo-name")
    github_token = st.text_input("GitHub Token", value=st.session_state.github_token, type="password", placeholder="ghp_... (private repos)")

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
            st.session_state.configured = True
            st.rerun()

    if st.session_state.configured:
        st.markdown(f'<div class="pill-connected"><span class="pulse-dot"></span> {st.session_state.github_repo.split("/")[-1]}</div>', unsafe_allow_html=True)
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
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.4rem;">
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
    else:
        st.caption("Available after sync")

    # Footer — Author
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
        <div style="font-size:0.58rem; color:#4b5563; margin-top:0.35rem;">Credentials stay in browser only</div>
    </div>
    """, unsafe_allow_html=True)


# ─── Main Content ────────────────────────────────────────────

# Hero
st.markdown("""
<div class="hero-container fade-up">
    <div class="hero-title">
        ⚡ <span class="logo-accent">DataGuru</span>
    </div>
    <div class="hero-subtitle">
        Your private knowledge assistant for Data Engineering — ask about pipelines, debug errors, analyze logs, and get instant answers from your own docs.
    </div>
    <div class="hero-badges">
        <span class="hero-badge"><span class="pulse-dot"></span> RAG-Powered</span>
        <span class="hero-badge">🧠 Self-Learning</span>
        <span class="hero-badge">📎 File Analysis</span>
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
            <div class="onboard-desc">Enter your free Groq API key and the GitHub repo that holds your knowledge base documents.</div>
        </div>
        <div class="onboard-card fade-up fade-up-d2">
            <div class="onboard-icon onboard-icon-amber">📥</div>
            <div class="onboard-title">2. Sync Once</div>
            <div class="onboard-desc">First time only — click "Sync Docs" to index your repo. After that, DataGuru remembers everything. Re-sync only when you add new files.</div>
        </div>
        <div class="onboard-card fade-up fade-up-d3">
            <div class="onboard-icon onboard-icon-blue">💬</div>
            <div class="onboard-title">3. Ask Anything</div>
            <div class="onboard-desc">Get instant answers with source citations from your docs. Drop a log file for root-cause analysis.</div>
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
    from config import CHROMA_DB_DIR
    if CHROMA_DB_DIR.exists() and any(CHROMA_DB_DIR.iterdir()):
        st.session_state.ingested = True
    else:
        st.markdown("""
        <div class="onboard-grid fade-up">
            <div class="onboard-card" style="grid-column:1/-1; text-align:center; padding:2.5rem 2rem;">
                <div class="onboard-icon onboard-icon-amber" style="margin:0 auto 1rem;">📥</div>
                <div class="onboard-title" style="font-size:1.1rem;">First-Time Setup: Sync Your Knowledge Base</div>
                <div class="onboard-desc" style="max-width:450px; margin:0.5rem auto 0; font-size:0.85rem;">
                    This is a <strong>one-time step</strong>. Click <strong>"Sync Docs"</strong> in the sidebar to fetch and index documents from your GitHub repo.
                    After syncing, DataGuru will remember the index — you won't need to do this again unless you add new files to the repo.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()


# ─── Chat Interface ──────────────────────────────────────────

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
