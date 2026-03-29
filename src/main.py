"""
main.py — CLI Entry Point for DataGuru

Usage:
    python src/main.py

Commands during chat:
    ingest   — Re-index all documents in knowledge_base/
    clear    — Clear the terminal screen
    quit     — Exit the assistant
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ingest import ingest_documents
import retriever as _retriever
from retriever import retrieve
from llm_client import generate_answer
from config import CHROMA_DB_DIR, TOP_K

# ─────────────────────────────────────────────────────────────
# Banner
# ─────────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║                     🧠  DataGuru  v1.0                           ║
║    Your Private Data Engineering Knowledge Assistant             ║
║  LLM      : LLaMA 3.3 70b via Groq                               ║
║  Vector DB: ChromaDB  |  Embeddings: Sentence-Transformers        ║
║  Topics   : Informatica · SQL · Python · Spark · Unix · DE        ║
╠══════════════════════════════════════════════════════════════════╣
║  Commands:  ingest | clear | quit                                 ║
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
    """Run ingestion and reset retriever singletons."""
    ingest_documents()
    _retriever.reset_singletons()   # force reload of collection after re-index


# ─────────────────────────────────────────────────────────────
# Main Chat Loop
# ─────────────────────────────────────────────────────────────

def main():
    print(BANNER)

    # Auto-ingest if vector DB hasn't been built yet
    if not db_is_ready():
        print("⚠️  Knowledge base not indexed yet. Running ingestion first...\n")
        run_ingest()

    print("✅  Ready! Ask me anything about our data engineering knowledge base.")
    print(f"    (Retrieved top-{TOP_K} chunks per query)\n")
    print(SEPARATOR + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nBye! Happy engineering. 🚀")
            break

        if not user_input:
            continue

        # ── Commands ──────────────────────────────────────────
        if user_input.lower() == "quit":
            print("Bye! Happy engineering. 🚀")
            break

        if user_input.lower() == "clear":
            os.system("cls" if os.name == "nt" else "clear")
            print(BANNER)
            continue

        if user_input.lower() == "ingest":
            run_ingest()
            continue

        # ── RAG Pipeline ──────────────────────────────────────
        print("\n  🔍 Searching knowledge base...")
        chunks = retrieve(user_input)

        print("  🤖 Generating answer...\n")
        answer = generate_answer(user_input, chunks)

        print(f"DataGuru:\n{answer}")
        print_sources(chunks)
        print("\n" + SEPARATOR + "\n")


if __name__ == "__main__":
    main()
