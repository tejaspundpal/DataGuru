"""
skill_generator.py — Level 2: Active Skill Generation

Analyzes the learned_patterns collection to detect repeated patterns,
clusters them by similarity, and generates structured skill files (.md)
that get ingested back into the knowledge base.

When enough similar incidents pile up (SKILL_PATTERN_THRESHOLD), the agent
recognizes it as a recurring team issue and creates a permanent skill document
with consolidated guidance.

Optionally pushes skill files to the GitHub knowledge repo.
"""

import sys
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import chromadb
import httpx
from sentence_transformers import SentenceTransformer
from groq import Groq

from config import (
    CHROMA_DB_DIR,
    EMBEDDING_MODEL,
    GROQ_MODEL,
    GROQ_API_KEY,
    LEARNED_COLLECTION_NAME,
    SKILLS_DIR,
    SKILL_PATTERN_THRESHOLD,
    SKILL_SIMILARITY_CLUSTER,
    GITHUB_REPO,
    GITHUB_TOKEN,
)


# ─────────────────────────────────────────────────────────────
# Skill Synthesis Prompt
# ─────────────────────────────────────────────────────────────

SKILL_SYNTHESIS_PROMPT = """You are a senior data engineering knowledge architect. You have been given a cluster of related incident resolution patterns that the team has encountered repeatedly.

Your job is to synthesize these patterns into a single, comprehensive SKILL DOCUMENT that serves as a permanent reference for the team.

INCIDENT PATTERNS (all related to the same recurring issue):
{patterns}

Create a professional Markdown document with this structure:

# [Descriptive Title — The Recurring Problem]

## Overview
Brief description of what this recurring issue is and why it matters.

## Symptoms & Error Patterns
- List all known error codes, messages, and symptoms from the incidents

## Root Causes
Explain the common root causes that lead to this issue.

## Resolution Steps
1. Step-by-step resolution guide (consolidated from all incidents)
2. Include commands, config changes, or code fixes where applicable

## Prevention & Best Practices
- How to prevent this from happening again
- Monitoring/alerting suggestions

## Related Technologies
- List the technologies involved

---
*Auto-generated skill document from {count} resolved incidents.*
*Last updated: {timestamp}*

Generate ONLY the Markdown document, no other text:"""


# ─────────────────────────────────────────────────────────────
# Clustering Logic
# ─────────────────────────────────────────────────────────────

def _get_all_learned_patterns() -> list[dict]:
    """Retrieve all patterns from the learned collection."""
    try:
        CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
        collection = client.get_or_create_collection(
            name=LEARNED_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        count = collection.count()
        if count == 0:
            return []

        results = collection.get(
            include=["documents", "metadatas", "embeddings"],
            limit=count,
        )

        patterns = []
        for i in range(len(results["ids"])):
            patterns.append({
                "id": results["ids"][i],
                "document": results["documents"][i],
                "metadata": results["metadatas"][i],
                "embedding": results["embeddings"][i],
            })
        return patterns

    except Exception:
        return []


def _cluster_patterns(patterns: list[dict]) -> list[list[dict]]:
    """
    Group patterns into clusters based on cosine similarity.
    Uses a simple greedy clustering approach.
    """
    if not patterns:
        return []

    model = SentenceTransformer(EMBEDDING_MODEL)
    import numpy as np

    embeddings = np.array([p["embedding"] for p in patterns])
    n = len(patterns)
    assigned = [False] * n
    clusters = []

    for i in range(n):
        if assigned[i]:
            continue

        cluster = [patterns[i]]
        assigned[i] = True

        for j in range(i + 1, n):
            if assigned[j]:
                continue

            # Cosine similarity between embeddings
            vec_i = embeddings[i]
            vec_j = embeddings[j]
            dot = np.dot(vec_i, vec_j)
            norm_i = np.linalg.norm(vec_i)
            norm_j = np.linalg.norm(vec_j)

            if norm_i == 0 or norm_j == 0:
                continue

            similarity = dot / (norm_i * norm_j)

            if similarity >= SKILL_SIMILARITY_CLUSTER:
                cluster.append(patterns[j])
                assigned[j] = True

        clusters.append(cluster)

    return clusters


def _get_existing_skill_hashes() -> set[str]:
    """Get hashes of already-generated skills to avoid regeneration."""
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    hashes = set()
    for skill_file in SKILLS_DIR.glob("*.md"):
        # Hash is stored in filename: skill_<hash>.md
        stem = skill_file.stem
        if stem.startswith("skill_"):
            hashes.add(stem.replace("skill_", ""))
    return hashes


def _cluster_hash(cluster: list[dict]) -> str:
    """Generate a stable hash for a cluster based on its pattern IDs."""
    ids = sorted([p["id"] for p in cluster])
    content = "|".join(ids)
    return hashlib.sha256(content.encode()).hexdigest()[:12]


# ─────────────────────────────────────────────────────────────
# Skill Document Generation
# ─────────────────────────────────────────────────────────────

def _synthesize_skill(cluster: list[dict]) -> str | None:
    """Use LLM to synthesize a cluster of patterns into a skill document."""
    if not GROQ_API_KEY:
        return None

    # Format patterns for the prompt
    pattern_texts = []
    for i, p in enumerate(cluster, 1):
        pattern_texts.append(f"--- Pattern {i} ---\n{p['document']}")

    patterns_block = "\n\n".join(pattern_texts)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    prompt = SKILL_SYNTHESIS_PROMPT.format(
        patterns=patterns_block,
        count=len(cluster),
        timestamp=timestamp,
    )

    client = Groq(api_key=GROQ_API_KEY)

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2048,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# GitHub Push (Optional)
# ─────────────────────────────────────────────────────────────

def _push_skill_to_github(skill_content: str, filename: str) -> bool:
    """
    Push a generated skill file to the GitHub knowledge repo.
    Requires GITHUB_TOKEN with repo write access.
    """
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return False

    import base64

    file_path = f"learned_skills/{filename}"
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DataGuru-SkillGenerator",
    }

    # Check if file already exists (for update vs create)
    existing_sha = None
    try:
        with httpx.Client() as client:
            resp = client.get(api_url, headers=headers)
            if resp.status_code == 200:
                existing_sha = resp.json().get("sha")
    except Exception:
        pass

    # Create or update the file
    payload = {
        "message": f"[DataGuru] Auto-generated skill: {filename}",
        "content": base64.b64encode(skill_content.encode()).decode(),
        "branch": "main",
    }
    if existing_sha:
        payload["sha"] = existing_sha

    try:
        with httpx.Client() as client:
            resp = client.put(api_url, headers=headers, json=payload)
            return resp.status_code in (200, 201)
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def generate_skills(push_to_github: bool = False) -> list[dict]:
    """
    Analyze learned patterns, cluster them, and generate skill documents
    for clusters that meet the threshold.

    Args:
        push_to_github: If True, also push generated skills to the GitHub repo.

    Returns:
        List of dicts with info about generated skills:
        [{"filename": str, "title": str, "pattern_count": int, "pushed": bool}]
    """
    # Step 1: Get all learned patterns
    patterns = _get_all_learned_patterns()
    if len(patterns) < SKILL_PATTERN_THRESHOLD:
        return []

    # Step 2: Cluster by similarity
    clusters = _cluster_patterns(patterns)

    # Step 3: Filter clusters that meet threshold
    eligible_clusters = [c for c in clusters if len(c) >= SKILL_PATTERN_THRESHOLD]
    if not eligible_clusters:
        return []

    # Step 4: Check which clusters already have generated skills
    existing_hashes = _get_existing_skill_hashes()

    generated_skills = []
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    for cluster in eligible_clusters:
        c_hash = _cluster_hash(cluster)

        # Skip if already generated
        if c_hash in existing_hashes:
            continue

        # Step 5: Synthesize skill document
        skill_content = _synthesize_skill(cluster)
        if not skill_content:
            continue

        # Step 6: Save locally
        filename = f"skill_{c_hash}.md"
        skill_path = SKILLS_DIR / filename
        skill_path.write_text(skill_content, encoding="utf-8")

        # Step 7: Optionally push to GitHub
        pushed = False
        if push_to_github:
            pushed = _push_skill_to_github(skill_content, filename)

        # Extract title from the generated content
        title = "Unknown Skill"
        for line in skill_content.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break

        generated_skills.append({
            "filename": filename,
            "title": title,
            "pattern_count": len(cluster),
            "pushed": pushed,
        })

    return generated_skills


def get_skills_summary() -> dict:
    """Get a summary of generated skills and learned patterns."""
    patterns = _get_all_learned_patterns()
    clusters = _cluster_patterns(patterns) if patterns else []

    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    existing_skills = list(SKILLS_DIR.glob("*.md"))

    eligible = [c for c in clusters if len(c) >= SKILL_PATTERN_THRESHOLD]

    return {
        "total_patterns": len(patterns),
        "total_clusters": len(clusters),
        "eligible_for_skill": len(eligible),
        "skills_generated": len(existing_skills),
        "skill_files": [f.name for f in existing_skills],
    }
