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

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from groq import Groq
from dotenv import load_dotenv
from config import GROQ_MODEL

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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
7. If the question is completely unrelated to data engineering, politely say this assistant only covers data engineering topics."""


# ─────────────────────────────────────────────────────────────
# Prompt Builder
# ─────────────────────────────────────────────────────────────

def build_rag_prompt(query: str, retrieved_chunks: list[dict]) -> list[dict]:
    """
    Constructs the messages list for the Groq API call.

    Args:
        query:            User's natural language question.
        retrieved_chunks: List of dicts from retriever.retrieve().

    Returns:
        Messages list in OpenAI chat format.
    """
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        context_parts.append(
            f"[Context {i}]\n"
            f"Source     : {chunk['source']}\n"
            f"Technology : {chunk['technology']}\n"
            f"Relevance  : {chunk['score']}\n\n"
            f"{chunk['text']}"
        )

    context_block = "\n\n" + ("─" * 50) + "\n\n".join(context_parts)

    user_message = (
        f"Use ONLY the following internal documentation context to answer the question.\n"
        f"Do not use outside knowledge.\n\n"
        f"CONTEXT:\n{context_block}\n\n"
        f"{'─' * 50}\n\n"
        f"QUESTION: {query}\n\n"
        f"Provide a clear, technical answer. Cite your sources at the end."
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_message},
    ]


# ─────────────────────────────────────────────────────────────
# Generate Answer
# ─────────────────────────────────────────────────────────────

def generate_answer(query: str, retrieved_chunks: list[dict]) -> str:
    """
    Send the RAG prompt to Groq and return the generated answer.

    Args:
        query:            User's question.
        retrieved_chunks: Chunks returned by retriever.retrieve().

    Returns:
        LLM-generated answer string.
    """
    if not retrieved_chunks:
        return (
            "No relevant documents found in the knowledge base for your query. "
            "Please try rephrasing, or add relevant documents to the knowledge base."
        )

    messages = build_rag_prompt(query, retrieved_chunks)

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.1,    # Low = factual and consistent
            max_tokens=1024,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"Error calling Groq API: {e}"
