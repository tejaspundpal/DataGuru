"""
main.py — CLI Entry Point for DataGuru

Usage:
    python src/main.py

Commands during chat:
    attach <path> — Attach a file (log, txt, sql, etc.) for analysis
    detach        — Remove the currently attached file
    ingest        — Re-index all documents in knowledge_base/
    skills        — Generate skill documents from learned patterns
    stats         — Show learning statistics
    setup         — Reconfigure credentials (API key, repo, token)
    clear         — Clear the terminal screen
    quit          — Exit the assistant (triggers learning agent)
"""

import os
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from user_config import is_configured, run_setup
from ingest import ingest_documents
import retriever as _retriever
from retriever import retrieve
from llm_client import stream_answer
from file_handler import load_attachment, build_search_query_from_attachment
from learning_agent import learn_from_session, get_learned_count
from skill_generator import generate_skills, get_skills_summary
from config import CHROMA_DB_DIR, TOP_K, CHAT_HISTORY_PAIRS

# ─────────────────────────────────────────────────────────────
# Banner
# ─────────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║                     🧠  DataGuru  v2.1                           ║
║    Your Private Data Engineering Knowledge Assistant             ║
║  LLM      : LLaMA 3.3 70b via Groq                               ║
║  Vector DB: ChromaDB  |  Embeddings: Sentence-Transformers        ║
║  Features : RAG · File Attach · Self-Learning · Skill Gen         ║
╠══════════════════════════════════════════════════════════════════╣
║  Commands: attach | detach | ingest | skills | stats | setup | quit║
╚══════════════════════════════════════════════════════════════════╝
"""

SEPARATOR = "─" * 66


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def db_is_ready() -> bool:
    """Return True if ChromaDB directory exists and is non-empty."""
    return CHROMA_DB_DIR.exists() and any(CHROMA_DB_DIR.iterdir())


def print_sources(chunks: list[dict]) -> None:
    """Print deduplicated source citations for retrieved chunks."""
    seen = set()
    print("\n  📚 Sources consulted:")
    for chunk in chunks:
        src = chunk["source"]
        if src not in seen:
            print(f"     • {src}  (relevance: {chunk['score']})")
            seen.add(src)


def run_ingest() -> None:
    """Run ingestion via MCP and reset retriever singletons."""
    asyncio.run(ingest_documents())
    _retriever.reset_singletons()   # force reload of collection after re-index


# ─────────────────────────────────────────────────────────────
# Main Chat Loop
# ─────────────────────────────────────────────────────────────

def main():
    print(BANNER)

    # ── First-time setup: prompt for credentials if not configured ──
    if not is_configured():
        run_setup()
        # Reload config module after setup
        import importlib
        import config
        importlib.reload(config)

    # Auto-ingest if vector DB hasn't been built yet
    if not db_is_ready():
        print("⚠️  Knowledge base not indexed yet. Running ingestion first...\n")
        run_ingest()

    learned_count = get_learned_count()
    print("✅  Ready! Ask me anything about our data engineering knowledge base.")
    print(f"    (Retrieved top-{TOP_K} chunks per query)")
    if learned_count > 0:
        print(f"    🧠 Learned patterns available: {learned_count}")
    print("    💡 Tip: Use 'attach <filepath>' to attach a log/config file for analysis.\n")
    print(SEPARATOR + "\n")

    chat_history = []       # Conversational Memory
    full_session_history = []  # Complete session history for learning agent
    current_attachment = None  # Currently attached file data
    session_attachment = None  # Track attachment used during session for learning

    while True:
        try:
            # Show attachment indicator in prompt
            if current_attachment:
                prompt = f"You [📎 {current_attachment['file_name']}]: "
            else:
                prompt = "You: "
            user_input = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            _run_learning_on_exit(full_session_history, session_attachment)
            print("Bye! Happy engineering. 🚀")
            break

        if not user_input:
            continue

        # ── Commands ──────────────────────────────────────────
        if user_input.lower() == "quit":
            _run_learning_on_exit(full_session_history, session_attachment)
            print("Bye! Happy engineering. 🚀")
            break

        if user_input.lower() == "clear":
            os.system("cls" if os.name == "nt" else "clear")
            print(BANNER)
            continue

        if user_input.lower() == "ingest":
            run_ingest()
            continue

        if user_input.lower() == "setup":
            run_setup(force=True)
            # Reload config to pick up new credentials
            import importlib
            import config
            importlib.reload(config)
            print("  ✅ Config reloaded. New credentials are active.\n")
            continue

        if user_input.lower() == "stats":
            _show_stats()
            continue

        if user_input.lower() == "skills":
            _run_skill_generation()
            continue

        if user_input.lower() == "detach":
            if current_attachment:
                print(f"  📎 Detached: {current_attachment['file_name']}\n")
                current_attachment = None
            else:
                print("  No file currently attached.\n")
            continue

        if user_input.lower().startswith("attach"):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                print("  Usage: attach <file_path>")
                print("  Example: attach C:\\logs\\workflow_error.log\n")
                continue

            file_path = parts[1].strip().strip('"').strip("'")
            attachment, error = load_attachment(file_path)

            if error:
                print(f"  ❌ {error}\n")
                continue

            current_attachment = attachment
            session_attachment = attachment  # remember for learning
            diag = attachment["diagnostics"]
            print(f"\n  📎 Attached: {attachment['file_name']}")
            print(f"     {diag['summary']}")
            if diag["errors"]:
                print(f"     Top errors:")
                for err_line in diag["errors"][:5]:
                    print(f"       • {err_line}")
            if attachment["truncated"]:
                print(f"     ⚠️  File was truncated to fit context limits.")
            print(f"\n  Now ask a question about this file (or type 'detach' to remove it).\n")
            continue

        # ── RAG Pipeline (with optional attachment) ───────────
        print("\n  🔍 Searching knowledge base...")

        # Build search query: combine user question with attachment diagnostics
        search_query = user_input
        if current_attachment:
            attachment_query = build_search_query_from_attachment(current_attachment)
            search_query = f"{user_input} {attachment_query}"

        chunks = retrieve(search_query)

        if not chunks and not chat_history and not current_attachment:
            print("DataGuru:\n  I'm sorry, I don't see any internal documentation about that. "
                  "(It fell below our semantic similarity threshold.)\n")
            print("\n" + SEPARATOR + "\n")
            continue

        print("  🤖 Generating answer...\n")

        print("DataGuru:\n", end="", flush=True)
        full_answer = ""
        for chunk_text in stream_answer(user_input, chunks, chat_history, current_attachment):
            print(chunk_text, end="", flush=True)
            full_answer += chunk_text
        print("\n")

        # Update chat memory (sliding window for LLM context)
        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "assistant", "content": full_answer})

        # Keep full session history for learning agent
        full_session_history.append({"role": "user", "content": user_input})
        full_session_history.append({"role": "assistant", "content": full_answer})

        # Enforce memory buffer size limits (1 pair = 2 messages)
        max_messages = CHAT_HISTORY_PAIRS * 2
        if len(chat_history) > max_messages:
            chat_history = chat_history[-max_messages:]

        if chunks:
            print_sources(chunks)
        print("\n" + SEPARATOR + "\n")


# ─────────────────────────────────────────────────────────────
# Learning & Skills Helpers
# ─────────────────────────────────────────────────────────────

def _run_learning_on_exit(session_history: list[dict], attachment: dict | None) -> None:
    """Trigger the learning agent on session exit."""
    if not session_history:
        return

    print("\n  🧠 Learning agent analyzing this session...")
    try:
        patterns = learn_from_session(session_history, attachment)
        if patterns:
            print(f"  ✅ Captured {len(patterns)} new pattern(s):")
            for p in patterns:
                print(f"     • {p['title']} [{p['technology']}]")
        else:
            print("  ℹ️  No new patterns extracted from this session.")
    except Exception as e:
        print(f"  ⚠️  Learning agent encountered an error: {e}")
    print()


def _show_stats() -> None:
    """Display learning and skill statistics."""
    summary = get_skills_summary()
    learned = get_learned_count()

    print(f"\n  📊 DataGuru Learning Stats")
    print(f"  {'─' * 40}")
    print(f"  🧠 Learned patterns   : {learned}")
    print(f"  📦 Pattern clusters   : {summary['total_clusters']}")
    print(f"  🎯 Ready for skills   : {summary['eligible_for_skill']}")
    print(f"  📄 Skills generated   : {summary['skills_generated']}")
    if summary["skill_files"]:
        print(f"  📁 Skill files:")
        for f in summary["skill_files"]:
            print(f"       • {f}")
    print(f"  {'─' * 40}\n")


def _run_skill_generation() -> None:
    """Trigger skill generation from learned patterns."""
    print("\n  🔧 Analyzing learned patterns for skill generation...")
    try:
        skills = generate_skills(push_to_github=False)
        if skills:
            print(f"  ✅ Generated {len(skills)} new skill document(s):")
            for s in skills:
                print(f"     • {s['title']} (from {s['pattern_count']} patterns) → {s['filename']}")
            print(f"\n  💡 Run 'ingest' to add these skills to the knowledge base.")
        else:
            summary = get_skills_summary()
            if summary["total_patterns"] < 3:
                print(f"  ℹ️  Not enough patterns yet ({summary['total_patterns']}/3 minimum).")
                print(f"      Keep using DataGuru — patterns are captured automatically on exit.")
            else:
                print(f"  ℹ️  No new skills to generate. All clusters already have skill docs.")
    except Exception as e:
        print(f"  ⚠️  Skill generation error: {e}")
    print()


if __name__ == "__main__":
    main()
