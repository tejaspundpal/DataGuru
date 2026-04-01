"""
Flow:
  knowledge_base/ (.md files)
       → load documents
       → chunk text (sliding window with overlap)
       → embed chunks (sentence-transformers, local)
       → store in ChromaDB (persistent on disk)
"""

import sys
import os
import logging
from pathlib import Path

# Silence Hugging Face and Transformer warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import transformers
transformers.utils.logging.set_verbosity_error()
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

sys.path.insert(0, str(Path(__file__).parent))

import chromadb
from sentence_transformers import SentenceTransformer
from config import (
    KNOWLEDGE_BASE_DIR,
    CHROMA_DB_DIR,
    EMBEDDING_MODEL,
    COLLECTION_NAME,
    CHUNK_SIZE_CHARS,
    CHUNK_OVERLAP_CHARS,
)


# Step 1: Load Documents

def load_documents(kb_dir: Path) -> list[dict]:
    """
    Recursively walk the knowledge_base/ directory.
    Read every .md and .txt file.
    Tag each document with metadata derived from its folder name.

    Returns:
        List of dicts: {content, source, technology, doc_name}
    """
    documents = []

    for file_path in sorted(kb_dir.rglob("*.md")):
        tech_category = file_path.parent.name   
        doc_name      = file_path.stem           
        source        = str(file_path.relative_to(kb_dir.parent)) 

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            print(f">>>>>>> Skipping empty file: {source}")
            continue

        documents.append({
            "content":    content,
            "source":     source,
            "technology": tech_category,
            "doc_name":   doc_name,
        })
        print(f"  Loaded: {source}")

    return documents


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
        start = end - overlap
        if start >= text_len - (chunk_size // 10): # If we are very close to end, just stop
            break
        if start < 0: start = 0 # Safety for very short files

    return chunks


# Step 3 + 4: Embed & Store

def ingest_documents():
    """
    Main ingestion pipeline:
    1. Load all docs from knowledge_base/
    2. Chunk each document
    3. Embed all chunks locally (sentence-transformers)
    4. Upsert into ChromaDB persistent collection
    """
    print("\n" + "=" * 62)
    print("  DataGuru Knowledge Assistant — Document Ingestion")
    print("=" * 62)

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

    # ── Load Documents ────────────────────────────────────────
    print(f"\n[3/4] Loading documents from: {KNOWLEDGE_BASE_DIR}")
    documents = load_documents(KNOWLEDGE_BASE_DIR)

    if not documents:
        print("\n  ERROR: No documents found. Check knowledge_base/ folder.")
        return

    print(f"  Total documents loaded: {len(documents)}")

    # ── Chunk → Embed → Store ─────────────────────────────────
    print(f"\n[4/4] Chunking, embedding, and storing...")
    total_chunks = 0

    for doc in documents:
        chunks = chunk_text(doc["content"])
        if not chunks:
            continue

        # Batch embed all chunks for this document
        embeddings = model.encode(chunks, show_progress_bar=False).tolist()

        # Build ChromaDB payloads
        ids       = [f"{doc['doc_name']}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source":     doc["source"],
                "technology": doc["technology"],
                "doc_name":   doc["doc_name"],
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
        print(f"  ✓  {doc['source']:<55} → {len(chunks):>2} chunks")

    # ── Summary ───────────────────────────────────────────────
    print(f"\n{'=' * 62}")
    print(f"  ✅ Ingestion complete!")
    print(f"  Documents : {len(documents)}")
    print(f"  Chunks    : {total_chunks}")
    print(f"  Vector DB : {CHROMA_DB_DIR}")
    print(f"{'=' * 62}\n")


if __name__ == "__main__":
    ingest_documents()
