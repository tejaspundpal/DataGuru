"""
llm_client.py — RAG-Aware LLM Response Generation

Flow:
  Retrieved chunks + user query
       → build RAG prompt (system + context + question)
       → call Groq API (LLaMA 3.3 70b)
       → return grounded answer

Key design decisions:
  - temperature=0.1 for factual, consistent answers
  - LLM is instructed to ONLY answer from context (no hallucination)
  - If context lacks the answer, a clear "not found" message is returned
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from groq import Groq
from config import GROQ_MODEL, GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

# ─────────────────────────────────────────────────────────────
# System Prompt
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are DataGuru — a private AI knowledge assistant for a data engineering team.

You have access to the team's private knowledge base containing:
- Informatica runbooks, mapping error guides, workflow SOPs
- SQL query optimization guides and deadlock incident reports
- Python scripting patterns and pandas troubleshooting guides
- Apache Spark / PySpark OOM incidents, skew fixes, and performance tuning docs
- Unix cron job SOPs and permission issue resolutions
- Data Engineering pipeline architecture docs and incident history

STRICT RULES YOU MUST FOLLOW:
1. Answer ONLY from the provided CONTEXT below. Do not use your general training knowledge.
2. If the answer cannot be found in the context, respond with:
   "I don't have specific documentation on this in our knowledge base. Please check with the senior engineer or refer to official documentation."
3. Be technically precise and concise.
4. Always end your answer with source citations in the format: [Source: <filename>]
5. If multiple sources are used, cite all of them.
6. Never fabricate incident numbers, dates, ticket IDs, or technical details not present in the context.
7. If the question is completely unrelated to data engineering, politely say this assistant only covers data engineering topics.
8. When an ATTACHED DOCUMENT is provided, analyze it thoroughly — identify errors, root causes, and correlate them with the knowledge base context to provide actionable solutions.
9. For attached documents, structure your answer as: Issue Summary → Root Cause → Resolution Steps → Prevention Tips (if available in context)."""


# ─────────────────────────────────────────────────────────────
# Prompt Builder
# ─────────────────────────────────────────────────────────────

def build_rag_prompt(query: str, retrieved_chunks: list[dict], chat_history: list[dict] = None, attachment: dict = None) -> list[dict]:
    """
    Constructs the messages list for the Groq API call.

    Args:
        query:            User's natural language question.
        retrieved_chunks: List of dicts from retriever.retrieve().
        chat_history:     List of previous conversation messages.
        attachment:       Optional dict from file_handler.load_attachment().

    Returns:
        Messages list in OpenAI chat format.
    """
    if chat_history is None:
        chat_history = []
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        context_parts.append(
            f"[Context {i}]\n"
            f"Source     : {chunk['source']}\n"
            f"Technology : {chunk['technology']}\n"
            f"Relevance  : {chunk['score']}\n\n"
            f"{chunk['text']}"
        )

    if context_parts:
        context_block = "\n\n" + ("─" * 50) + "\n\n".join(context_parts)
    else:
        context_block = "(No new internal document chunks matched this follow-up query. Rely on previous conversation history.)"

    # Build attachment section if present
    attachment_block = ""
    if attachment:
        diag = attachment["diagnostics"]
        attachment_block = (
            f"\n\n{'═' * 50}\n"
            f"ATTACHED DOCUMENT: {attachment['file_name']}\n"
            f"{'═' * 50}\n"
        )
        if diag["errors"]:
            attachment_block += "\n── ERRORS DETECTED ──\n"
            attachment_block += "\n".join(diag["errors"])
            attachment_block += "\n"
        if diag["warnings"]:
            attachment_block += "\n── WARNINGS DETECTED ──\n"
            attachment_block += "\n".join(diag["warnings"])
            attachment_block += "\n"

        attachment_block += (
            f"\n── FULL CONTENT ──\n"
            f"{attachment['content']}\n"
        )
        if attachment["truncated"]:
            attachment_block += "(Content was truncated due to size limits)\n"

    user_message = (
        f"Use ONLY the following internal documentation context (or previous chat history) to answer the question.\n"
        f"Do not use outside knowledge.\n\n"
        f"KNOWLEDGE BASE CONTEXT:\n{context_block}\n\n"
        f"{attachment_block}"
        f"{'─' * 50}\n\n"
        f"QUESTION: {query}\n\n"
        f"Provide a clear, technical answer. Cite your sources at the end if applicable."
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": user_message})

    return messages


# ─────────────────────────────────────────────────────────────
# Generate Answer
# ─────────────────────────────────────────────────────────────

def stream_answer(query: str, retrieved_chunks: list[dict], chat_history: list[dict] = None, attachment: dict = None):
    """
    Send the RAG prompt to Groq and YIELD the generated answer live.

    Args:
        query:            User's question.
        retrieved_chunks: Chunks returned by retriever.retrieve().
        chat_history:     Previous chat context.
        attachment:       Optional attachment data from file_handler.

    Yields:
        LLM-generated answer chunks as they stream in.
    """
    if not retrieved_chunks and not chat_history and not attachment:
        yield (
            "No relevant documents found in the knowledge base for your query. "
            "It may be mathematically unrelated to our docs, or the knowledge base is empty. "
            "Please try rephrasing, or add relevant documents."
        )
        return

    messages = build_rag_prompt(query, retrieved_chunks, chat_history, attachment)

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.1,    # Low = factual and consistent
            max_tokens=1024,
            stream=True         # Enable LLM streaming
        )
        
        for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    except Exception as e:
        yield f"Error calling Groq API: {e}"
