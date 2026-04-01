"""
Flow:
  MCP Server (GitHub remote repository)
       → connect via stdio MCP Client
       → call `fetch_repo_contents` tool
       → receive documents (content + metadata)
       → chunk text (sliding window with overlap)
       → embed chunks (sentence-transformers, local)
       → store in ChromaDB (persistent on disk)
"""

import sys
import os
import logging
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import chromadb
from sentence_transformers import SentenceTransformer
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from config import (
    CHROMA_DB_DIR,
    EMBEDDING_MODEL,
    COLLECTION_NAME,
    CHUNK_SIZE_CHARS,
    CHUNK_OVERLAP_CHARS,
    GITHUB_REPO
)


# Step 1: Load Documents via MCP Server
async def load_documents_via_mcp() -> list[dict]:
    """
    Connect to the local GitHub MCP server over stdio,
    and request it to fetch all markdown files from the target GitHub repo.
    """
    server_script = Path(__file__).parent / "mcp_github_server.py"

    server_params = StdioServerParameters(
        command=sys.executable,  # Uses the current Python interpreter (.venv)
        args=[str(server_script)],
        env=os.environ.copy()
    )

    print(f"  [MCP] Connecting to GitHub MCP Server...")
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                print(f"  [MCP] Session initialized. Requesting documents from repository...")
                # Calling the tool defined in mcp_github_server.py
                result = await session.call_tool("fetch_repo_contents", arguments={})
                
                # The tool returns JSON data. For fastmcp, tools return text/json content blocks
                # We need to extract the data. Usually it returns a list of dictionaries if JSON.
                if result.content and len(result.content) > 0:
                    try:
                        import json
                        # Depending on the MCP version, the content is text
                        data = json.loads(result.content[0].text)
                        return data
                    except Exception as e:
                        print(f"  [MCP] Error parsing result from server: {e}")
                        return []
                return []
    except Exception as e:
        print(f"  [MCP Error]: Failed to fetch documents via MCP. Make sure everything is configured. Error: {e}")
        return []


# Step 2: Chunk Text
def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> list[str]:
    """
    Split text into overlapping chunks using a sliding window.
    Ensures that we move forward efficiently while respecting paragraph breaks where possible.
    """
    chunks = []
    start  = 0
    text_len = len(text)

    if text_len <= chunk_size:
        return [text] if text.strip() else []

    while start < text_len:
        # Determine the initial end point
        end = min(start + chunk_size, text_len)
        
        # If we're not at the very end, try to find a nice break point (newline)
        if end < text_len:
            # Look for newline in the last 25% of the chunk
            search_start = end - (chunk_size // 4)
            break_point = text.rfind("\n", search_start, end)
            if break_point != -1:
                end = break_point

        chunk = text[start:end].strip()
        if len(chunk) > 50: # Only save meaningful chunks
            chunks.append(chunk)

        # Move start forward, ensuring we always progress by at least (size - overlap)
        # to avoid the infinite loop/tiny step bug.
        new_start = end - overlap
        if new_start <= start:
            new_start = start + 1  # Force progress if overlap causes backward movement
        start = new_start

        if end == text_len:             
            break 

        if start >= text_len - (chunk_size // 10): # If we are very close to end, just stop
            break
        if start < 0: start = 0 # Safety for very short files

    return chunks


# Step 3 + 4: Embed & Store
async def ingest_documents():
    """
    Main ingestion pipeline:
    1. Fetch all docs from GitHub via MCP Server
    2. Chunk each document
    3. Embed all chunks locally (sentence-transformers)
    4. Upsert into ChromaDB persistent collection
    """
    print("\n" + "=" * 62)
    print("  DataGuru Knowledge Assistant — Data Ingestion (MCP Client)")
    print("=" * 62)

    if not GITHUB_REPO:
        print("\n  ❌ ERROR: GITHUB_REPO not set in .env or config.py.")
        print("  Please set it (e.g. yourusername/dataguru-knowledge-base) and try again.")
        return

    # ── Init ChromaDB ─────────────────────────────────────────
    print("\n[1/4] Initializing ChromaDB...")
    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

    # Fresh start — drop existing collection if present
    try:
        client.delete_collection(COLLECTION_NAME)
        print("  Cleared existing collection.")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},   # cosine similarity for semantic search
    )

    # ── Load Embedding Model ──────────────────────────────────
    print(f"\n[2/4] Loading embedding model: {EMBEDDING_MODEL} (local, no API needed)...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("  Model ready.")

    # ── Load Documents via MCP ────────────────────────────────
    print(f"\n[3/4] Requesting documents from GitHub repo: {GITHUB_REPO} via MCP Server...")
    documents = await load_documents_via_mcp()

    if not documents:
        print("\n  ERROR: No documents retrieved from MCP Server.")
        return

    print(f"  Total documents received: {len(documents)}")

    # ── Chunk → Embed → Store ─────────────────────────────────
    print(f"\n[4/4] Chunking, embedding, and storing...")
    total_chunks = 0

    for doc in documents:
        # Standardize the structure we expect from the MCP server
        content = doc.get("content", "")
        source = doc.get("source", "unknown")
        technology = doc.get("technology", "General")
        doc_name = doc.get("doc_name", "doc")

        chunks = chunk_text(content)
        if not chunks:
            continue

        # Batch embed all chunks for this document
        embeddings = model.encode(chunks, show_progress_bar=False).tolist()

        # Build ChromaDB payloads
        ids       = [f"{doc_name}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source":     source,
                "technology": technology,
                "doc_name":   doc_name,
            }
            for _ in chunks
        ]

        collection.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
            ids=ids,
        )

        total_chunks += len(chunks)
        print(f"  ✓  {source:<55} → {len(chunks):>2} chunks")

    # ── Summary ───────────────────────────────────────────────
    print(f"\n{'=' * 62}")
    print(f"  ✅ Ingestion complete via MCP!")
    print(f"  Documents : {len(documents)}")
    print(f"  Chunks    : {total_chunks}")
    print(f"  Vector DB : {CHROMA_DB_DIR}")
    print(f"{'=' * 62}\n")


if __name__ == "__main__":
    asyncio.run(ingest_documents())
