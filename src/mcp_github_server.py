import sys
import os
import httpx
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import GITHUB_REPO, GITHUB_TOKEN
from mcp.server.fastmcp import FastMCP

# Initialize the MCP Server
mcp = FastMCP("GitHub Knowledge Base Server")

async def fetch_file_content(client: httpx.AsyncClient, file_path: str) -> dict:
    """Fetch raw content for a single file from GitHub."""
    # Assuming the default branch is main. The raw content URL:
    raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{file_path}"
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    response = await client.get(raw_url, headers=headers)
    
    # If main branch fails, try master branch as fallback (common in some repos)
    if response.status_code == 404:
        raw_url_master = f"https://raw.githubusercontent.com/{GITHUB_REPO}/master/{file_path}"
        response = await client.get(raw_url_master, headers=headers)

    response.raise_for_status()
    
    # Parse path to get metadata just like the local ingest.py did
    # Example path: "knowledge_base/sql/deadlocks.md"
    parts = Path(file_path).parts
    
    # Try to determine technology category (usually the parent folder)
    if len(parts) >= 2:
        tech_category = parts[-2]
    else:
        tech_category = "General"

    doc_name = Path(file_path).stem
    
    return {
        "content": response.text.strip(),
        "source": file_path,
        "technology": tech_category,
        "doc_name": doc_name
    }

@mcp.tool()
async def fetch_repo_contents() -> str:
    """
    Fetch all markdown documents from the configured GitHub repository.
    Returns a list of dictionaries containing file content and metadata.
    """
    if not GITHUB_REPO:
        raise ValueError("GITHUB_REPO environment variable is not set. Please set it to 'owner/repo'.")

    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/git/trees/main?recursive=1"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DataGuru-MCP-Server"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    async with httpx.AsyncClient() as client:
        response = await client.get(api_url, headers=headers)
        
        # Fallback to master if main branch is not found
        if response.status_code == 404:
            api_url_master = f"https://api.github.com/repos/{GITHUB_REPO}/git/trees/master?recursive=1"
            response = await client.get(api_url_master, headers=headers)

        response.raise_for_status()
        tree_data = response.json().get("tree", [])

        # Filter for markdown files
        md_files = [item["path"] for item in tree_data if item["type"] == "blob" and item["path"].endswith(".md")]
        
        # Download files concurrently
        tasks = [fetch_file_content(client, path) for path in md_files]
        documents = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out any that failed
        successful_docs = [doc for doc in documents if not isinstance(doc, Exception) and doc["content"]]

        print(f"Fetched {len(successful_docs)} documents from {GITHUB_REPO} via MCP.")
        import json
        return json.dumps(successful_docs)

if __name__ == "__main__":
    # Start the FastMCP server connected to standard input/output
    print("Starting GitHub Knowledge Base MCP Server...", file=sys.stderr)
    mcp.run()
