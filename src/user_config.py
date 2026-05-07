"""
user_config.py — Per-User Credential Management

Each user provides their own:
  - Groq API Key
  - GitHub Repository (owner/repo)
  - GitHub Token (optional for public repos)

Credentials are stored locally in the user's home directory:
  ~/.dataguru/config.json

This file is NOT committed to git. Each person who uses DataGuru
enters their own credentials on first run.
"""

import json
import os
from pathlib import Path


# ─────────────────────────────────────────────────────────────
# Storage Location
# ─────────────────────────────────────────────────────────────

_CONFIG_DIR = Path.home() / ".dataguru"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

_REQUIRED_KEYS = ["GROQ_API_KEY", "GITHUB_REPO"]
_OPTIONAL_KEYS = ["GITHUB_TOKEN"]


# ─────────────────────────────────────────────────────────────
# Load / Save
# ─────────────────────────────────────────────────────────────

def _load_config() -> dict:
    """Load saved user config from disk."""
    if not _CONFIG_FILE.exists():
        return {}
    try:
        data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _save_config(config: dict) -> None:
    """Save user config to disk with restricted permissions."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(
        json.dumps(config, indent=2),
        encoding="utf-8",
    )
    # Restrict file permissions (owner-only on Unix)
    try:
        os.chmod(_CONFIG_FILE, 0o600)
    except OSError:
        pass  # Windows doesn't support Unix chmod, that's fine


# ─────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────

def is_configured() -> bool:
    """Check if all required credentials are present."""
    config = _load_config()
    return all(config.get(key) for key in _REQUIRED_KEYS)


def get_config() -> dict:
    """
    Get the current user config. Returns dict with keys:
    GROQ_API_KEY, GITHUB_REPO, GITHUB_TOKEN
    """
    return _load_config()


def get_value(key: str) -> str:
    """Get a single config value."""
    return _load_config().get(key, "")


# ─────────────────────────────────────────────────────────────
# Interactive Setup (CLI)
# ─────────────────────────────────────────────────────────────

def run_setup(force: bool = False) -> dict:
    """
    Interactive credential setup. Prompts user for required values.

    Args:
        force: If True, re-prompt even if already configured.

    Returns:
        The saved config dict.
    """
    existing = _load_config()

    if not force and is_configured():
        return existing

    print("\n" + "═" * 62)
    print("  🔧 DataGuru — First-Time Setup")
    print("═" * 62)
    print("\n  Each user needs to provide their own credentials.")
    print("  These are stored locally at: ~/.dataguru/config.json")
    print("  They are NEVER shared or committed to git.\n")

    # Groq API Key
    current_groq = existing.get("GROQ_API_KEY", "")
    masked = f"***{current_groq[-4:]}" if len(current_groq) > 4 else ""
    prompt = f"  Groq API Key [{masked}]: " if masked else "  Groq API Key: "
    groq_key = input(prompt).strip()
    if not groq_key and current_groq:
        groq_key = current_groq
    elif not groq_key:
        print("  ❌ Groq API Key is required. Get one at https://console.groq.com")
        return existing

    # GitHub Repo
    current_repo = existing.get("GITHUB_REPO", "")
    prompt = f"  GitHub Repo (owner/repo) [{current_repo}]: " if current_repo else "  GitHub Repo (owner/repo): "
    github_repo = input(prompt).strip()
    if not github_repo and current_repo:
        github_repo = current_repo
    elif not github_repo:
        print("  ❌ GitHub Repo is required (e.g. yourusername/knowledge-base)")
        return existing

    # Sanitize repo URL if user pasted full link
    github_repo = github_repo.replace("https://github.com/", "").replace("http://github.com/", "").strip("/")

    # GitHub Token (optional)
    current_token = existing.get("GITHUB_TOKEN", "")
    masked_token = f"***{current_token[-4:]}" if len(current_token) > 4 else "none"
    prompt = f"  GitHub Token (optional, for private repos) [{masked_token}]: "
    github_token = input(prompt).strip()
    if not github_token:
        github_token = current_token

    # Save
    config = {
        "GROQ_API_KEY": groq_key,
        "GITHUB_REPO": github_repo,
        "GITHUB_TOKEN": github_token,
    }
    _save_config(config)

    print(f"\n  ✅ Configuration saved!")
    print(f"     Repo   : {github_repo}")
    print(f"     API Key: ***{groq_key[-4:]}")
    print(f"     Token  : {'set' if github_token else 'not set (public repo)'}")
    print("═" * 62 + "\n")

    return config


def clear_config() -> None:
    """Remove saved credentials."""
    if _CONFIG_FILE.exists():
        _CONFIG_FILE.unlink()
        print("  🗑️  Configuration cleared.")
