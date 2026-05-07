"""
file_handler.py — Secure File Attachment Processing

Handles:
  - File validation (size, type, encoding)
  - Safe reading with encoding detection
  - Error/warning extraction from logs and structured files
  - Content truncation for LLM context window efficiency
"""

import os
import re
from pathlib import Path

from config import ALLOWED_EXTENSIONS, MAX_ATTACHMENT_BYTES, MAX_ATTACHMENT_LINES


# ─────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────

def validate_file(file_path: str) -> tuple[bool, str]:
    """
    Validate that a file is safe to read and within configured limits.

    Returns:
        (is_valid, error_message)
    """
    path = Path(file_path).resolve()

    # Existence check
    if not path.exists():
        return False, f"File not found: {path}"

    if not path.is_file():
        return False, f"Path is not a file: {path}"

    # Extension check
    suffix = path.suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        return False, f"Unsupported file type '{suffix}'. Allowed: {allowed}"

    # Size check
    file_size = path.stat().st_size
    if file_size == 0:
        return False, "File is empty."

    if file_size > MAX_ATTACHMENT_BYTES:
        limit_kb = MAX_ATTACHMENT_BYTES // 1024
        actual_kb = file_size // 1024
        return False, f"File too large ({actual_kb} KB). Maximum allowed: {limit_kb} KB."

    return True, ""


# ─────────────────────────────────────────────────────────────
# Safe File Reading
# ─────────────────────────────────────────────────────────────

def read_file_safe(file_path: str) -> tuple[str, str]:
    """
    Read a file safely with encoding fallback.

    Returns:
        (content, error_message). If error_message is non-empty, content is empty.
    """
    path = Path(file_path).resolve()

    # Try UTF-8 first, then fall back to latin-1 (never fails for byte streams)
    for encoding in ("utf-8", "latin-1"):
        try:
            content = path.read_text(encoding=encoding)
            # Strip null bytes (common in corrupted logs)
            content = content.replace("\x00", "")
            return content, ""
        except (UnicodeDecodeError, ValueError):
            continue

    return "", "Unable to decode file. It may be a binary file."


def truncate_content(content: str) -> tuple[str, bool]:
    """
    Truncate content to MAX_ATTACHMENT_LINES to stay within LLM context budget.

    Returns:
        (truncated_content, was_truncated)
    """
    lines = content.splitlines(keepends=True)
    if len(lines) <= MAX_ATTACHMENT_LINES:
        return content, False

    truncated = "".join(lines[:MAX_ATTACHMENT_LINES])
    return truncated, True


# ─────────────────────────────────────────────────────────────
# Error & Warning Extraction
# ─────────────────────────────────────────────────────────────

# Patterns that indicate errors or warnings in common log formats
_ERROR_PATTERNS = re.compile(
    r"(?i)"
    r"(?:^|\s)"
    r"("
    r"error|err|fatal|critical|exception|traceback|failure|failed"
    r"|panic|abort|segfault|oom|out\s*of\s*memory|killed"
    r"|denied|refused|timeout|timed?\s*out|unreachable"
    r"|cmn_\d+|tm_\d+|rep_\d+|wrt_\d+"  # Informatica error codes
    r"|ora-\d+|sp2-\d+"                   # Oracle error codes
    r"|sqlstate|deadlock|lock\s*wait"      # SQL errors
    r"|errno|exit\s*code\s*[1-9]"
    r")"
)

_WARNING_PATTERNS = re.compile(
    r"(?i)"
    r"(?:^|\s)"
    r"("
    r"warn|warning|deprecated|slow|retry|retrying|skipped|skip"
    r"|degraded|high\s*latency|throttl"
    r")"
)


def extract_diagnostics(content: str) -> dict:
    """
    Extract errors, warnings, and key diagnostic lines from file content.

    Returns:
        {
            "errors": [list of error lines],
            "warnings": [list of warning lines],
            "summary": "brief text summary of issues found"
        }
    """
    errors = []
    warnings = []

    for line_num, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue

        if _ERROR_PATTERNS.search(stripped):
            errors.append(f"L{line_num}: {stripped}")
        elif _WARNING_PATTERNS.search(stripped):
            warnings.append(f"L{line_num}: {stripped}")

    # Cap extracted lines to avoid bloating the prompt
    errors = errors[:30]
    warnings = warnings[:20]

    # Build summary
    parts = []
    if errors:
        parts.append(f"{len(errors)} error(s)")
    if warnings:
        parts.append(f"{len(warnings)} warning(s)")

    summary = f"Found {' and '.join(parts)}." if parts else "No obvious errors or warnings detected."

    return {
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }


# ─────────────────────────────────────────────────────────────
# Public API: Load & Analyze Attachment
# ─────────────────────────────────────────────────────────────

def load_attachment(file_path: str) -> tuple[dict | None, str]:
    """
    Validate, read, and analyze an attached file.

    Returns:
        (attachment_data, error_message)

        attachment_data dict:
            {
                "file_name": str,
                "file_path": str,
                "content": str,
                "truncated": bool,
                "diagnostics": {...}
            }
    """
    # Validate
    is_valid, error = validate_file(file_path)
    if not is_valid:
        return None, error

    # Read
    content, error = read_file_safe(file_path)
    if error:
        return None, error

    # Truncate if needed
    content, was_truncated = truncate_content(content)

    # Extract diagnostics
    diagnostics = extract_diagnostics(content)

    path = Path(file_path).resolve()

    return {
        "file_name": path.name,
        "file_path": str(path),
        "content": content,
        "truncated": was_truncated,
        "diagnostics": diagnostics,
    }, ""


def build_search_query_from_attachment(attachment: dict) -> str:
    """
    Build an optimized search query from the attached file's diagnostics.
    This query is used to retrieve relevant knowledge base chunks.

    Extracts key technical terms from errors to improve retrieval relevance.
    """
    diagnostics = attachment["diagnostics"]
    errors = diagnostics["errors"]
    warnings = diagnostics["warnings"]

    # Collect unique technical keywords from error lines
    keywords = set()

    # Extract Informatica/Oracle/SQL error codes
    code_pattern = re.compile(r"(?i)(cmn_\d+|tm_\d+|rep_\d+|wrt_\d+|ora-\d+|sp2-\d+|sqlstate\s*\S+)")
    # Extract common error keywords
    term_pattern = re.compile(
        r"(?i)(deadlock|timeout|oom|out of memory|connection refused|permission denied"
        r"|null pointer|stack overflow|heap|segfault|killed|broken pipe"
        r"|workflow|session|mapping|transformation|source qualifier"
        r"|spark|executor|driver|shuffle|partition|skew)"
    )

    lines_to_scan = errors[:15] + warnings[:10]
    for line in lines_to_scan:
        for match in code_pattern.finditer(line):
            keywords.add(match.group(1).upper())
        for match in term_pattern.finditer(line):
            keywords.add(match.group(1).lower())

    if keywords:
        return " ".join(sorted(keywords)[:10])

    # Fallback: use first few error lines as-is (stripped of line numbers)
    if errors:
        fallback_lines = [re.sub(r"^L\d+:\s*", "", e) for e in errors[:3]]
        return " ".join(fallback_lines)[:300]

    # Last resort: use filename as query hint
    return f"troubleshoot {attachment['file_name']}"
