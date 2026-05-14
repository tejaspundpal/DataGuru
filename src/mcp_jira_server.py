"""
mcp_jira_server.py — MCP Server for Jira Integration

Provides tools to interact with Jira Cloud/Server:
  - fetch_issue: Get full issue details by key (e.g., PROJ-123)
  - search_issues: Search using JQL
  - create_issue: Create a new ticket
  - add_comment: Add a comment to a ticket
  - change_assignee: Reassign a ticket
  - transition_issue: Change issue status (To Do → In Progress → Done)
  - get_issue_comments: Get all comments on a ticket

Authentication: Basic Auth (email + API token for Jira Cloud)
Configuration: JIRA_DOMAIN, JIRA_EMAIL, JIRA_API_TOKEN from env/.env
"""

import sys
import os
import json
from pathlib import Path
from base64 import b64encode

sys.path.insert(0, str(Path(__file__).parent))

from config import JIRA_BASE_URL, JIRA_USERNAME, JIRA_PASSWORD, JIRA_VERIFY_SSL
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize the MCP Server
mcp = FastMCP("Jira Integration Server")


# ─────────────────────────────────────────────────────────────
# Runtime Config Helpers
# ─────────────────────────────────────────────────────────────

def _get_base_url() -> str:
    """Get Jira base URL (e.g., 'https://yourcompany.atlassian.net')."""
    url = os.getenv("JIRA_BASE_URL", "").strip() or JIRA_BASE_URL
    return url.rstrip("/")


def _get_username() -> str:
    return os.getenv("JIRA_USERNAME", "").strip() or JIRA_USERNAME


def _get_password() -> str:
    return os.getenv("JIRA_PASSWORD", "").strip() or JIRA_PASSWORD


def _get_verify_ssl() -> bool:
    val = os.getenv("JIRA_VERIFY_SSL", "").strip().lower()
    if val:
        return val not in ("false", "0", "no")
    return JIRA_VERIFY_SSL


def _get_auth_header() -> dict:
    """Build Basic Auth header for Jira API."""
    username = _get_username()
    password = _get_password()
    credentials = b64encode(f"{username}:{password}".encode()).decode()
    return {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _get_api_url() -> str:
    """Get the REST API base URL."""
    return f"{_get_base_url()}/rest/api/3"


# ─────────────────────────────────────────────────────────────
# Helper: Format issue for readable output
# ─────────────────────────────────────────────────────────────

def _format_issue(issue: dict) -> dict:
    """Extract key fields from a Jira issue response into a clean structure."""
    fields = issue.get("fields", {})

    # Extract assignee
    assignee_data = fields.get("assignee")
    assignee = assignee_data.get("displayName", "Unassigned") if assignee_data else "Unassigned"

    # Extract reporter
    reporter_data = fields.get("reporter")
    reporter = reporter_data.get("displayName", "Unknown") if reporter_data else "Unknown"

    # Extract status
    status_data = fields.get("status")
    status = status_data.get("name", "Unknown") if status_data else "Unknown"

    # Extract priority
    priority_data = fields.get("priority")
    priority = priority_data.get("name", "None") if priority_data else "None"

    # Extract issue type
    issuetype_data = fields.get("issuetype")
    issuetype = issuetype_data.get("name", "Unknown") if issuetype_data else "Unknown"

    # Extract project
    project_data = fields.get("project")
    project = project_data.get("key", "Unknown") if project_data else "Unknown"

    # Extract description (ADF → plain text)
    description = _adf_to_text(fields.get("description"))

    # Extract labels
    labels = fields.get("labels", [])

    # Extract components
    components = [c.get("name", "") for c in fields.get("components", [])]

    return {
        "key": issue.get("key", ""),
        "summary": fields.get("summary", ""),
        "description": description,
        "status": status,
        "priority": priority,
        "assignee": assignee,
        "reporter": reporter,
        "issue_type": issuetype,
        "project": project,
        "labels": labels,
        "components": components,
        "created": fields.get("created", ""),
        "updated": fields.get("updated", ""),
        "url": f"{_get_base_url()}/browse/{issue.get('key', '')}",
    }


def _adf_to_text(adf: dict | None) -> str:
    """
    Convert Atlassian Document Format (ADF) to plain text.
    ADF is used in Jira Cloud API v3 for description/comment bodies.
    """
    if not adf:
        return ""

    # If it's already a string (Jira Server API v2), return as-is
    if isinstance(adf, str):
        return adf

    text_parts = []

    def _extract_text(node):
        if isinstance(node, dict):
            if node.get("type") == "text":
                text_parts.append(node.get("text", ""))
            elif node.get("type") == "hardBreak":
                text_parts.append("\n")
            # Recurse into content
            for child in node.get("content", []):
                _extract_text(child)
        elif isinstance(node, list):
            for item in node:
                _extract_text(item)

    _extract_text(adf)
    return "".join(text_parts).strip()


def _text_to_adf(text: str) -> dict:
    """Convert plain text to Atlassian Document Format (ADF) for API v3."""
    paragraphs = text.split("\n\n") if "\n\n" in text else [text]
    content = []
    for para in paragraphs:
        if para.strip():
            content.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": para.strip()}]
            })
    return {
        "version": 1,
        "type": "doc",
        "content": content if content else [{"type": "paragraph", "content": [{"type": "text", "text": " "}]}]
    }


# ─────────────────────────────────────────────────────────────
# MCP Tools
# ─────────────────────────────────────────────────────────────

@mcp.tool()
async def fetch_issue(issue_key: str) -> str:
    """
    Fetch full details of a Jira issue by its key (e.g., 'PROJ-123').

    Returns structured issue data including summary, description, status,
    priority, assignee, reporter, labels, components, and timestamps.
    """
    issue_key = issue_key.strip().upper()
    base_url = _get_api_url()
    headers = _get_auth_header()

    async with httpx.AsyncClient(timeout=30.0, verify=_get_verify_ssl()) as client:
        response = await client.get(
            f"{base_url}/issue/{issue_key}",
            headers=headers,
        )

        if response.status_code == 404:
            return json.dumps({"error": f"Issue {issue_key} not found. Check the ticket number and project key."})
        elif response.status_code == 401:
            return json.dumps({"error": "Authentication failed. Check JIRA_EMAIL and JIRA_API_TOKEN."})
        elif response.status_code == 403:
            return json.dumps({"error": f"Permission denied. Your account may not have access to {issue_key}."})
        elif response.status_code != 200:
            return json.dumps({"error": f"Jira API error (HTTP {response.status_code}): {response.text[:500]}"})

        issue = response.json()
        formatted = _format_issue(issue)
        return json.dumps(formatted)


@mcp.tool()
async def search_issues(jql: str, max_results: int = 10) -> str:
    """
    Search Jira issues using JQL (Jira Query Language).

    Examples:
      - 'project = PROJ AND status = "In Progress"'
      - 'assignee = currentUser() AND resolution = Unresolved'
      - 'labels = "data-pipeline" ORDER BY priority DESC'
      - 'text ~ "OOM error" AND project = DATA'

    Args:
        jql: JQL query string
        max_results: Maximum issues to return (default 10, max 50)
    """
    base_url = _get_api_url()
    headers = _get_auth_header()
    max_results = min(max_results, 50)

    async with httpx.AsyncClient(timeout=30.0, verify=_get_verify_ssl()) as client:
        response = await client.get(
            f"{base_url}/search",
            headers=headers,
            params={
                "jql": jql,
                "maxResults": max_results,
                "fields": "summary,status,priority,assignee,reporter,issuetype,project,labels,components,created,updated",
            },
        )

        if response.status_code == 400:
            return json.dumps({"error": f"Invalid JQL query: {response.json().get('errorMessages', ['Unknown error'])}"})
        elif response.status_code == 401:
            return json.dumps({"error": "Authentication failed. Check JIRA_EMAIL and JIRA_API_TOKEN."})
        elif response.status_code != 200:
            return json.dumps({"error": f"Jira API error (HTTP {response.status_code}): {response.text[:500]}"})

        data = response.json()
        issues = [_format_issue(issue) for issue in data.get("issues", [])]
        return json.dumps({
            "total": data.get("total", 0),
            "returned": len(issues),
            "issues": issues,
        })


@mcp.tool()
async def create_issue(
    project_key: str,
    summary: str,
    description: str = "",
    issue_type: str = "Task",
    priority: str = "Medium",
    labels: list[str] | None = None,
    assignee_account_id: str = "",
) -> str:
    """
    Create a new Jira issue.

    Args:
        project_key: Project key (e.g., 'PROJ', 'DATA')
        summary: Issue title/summary
        description: Detailed description (plain text, will be converted to ADF)
        issue_type: Type of issue — 'Task', 'Bug', 'Story', 'Epic' (default: Task)
        priority: Priority level — 'Highest', 'High', 'Medium', 'Low', 'Lowest'
        labels: Optional list of labels (e.g., ['data-pipeline', 'urgent'])
        assignee_account_id: Optional Atlassian account ID to assign to
    """
    base_url = _get_api_url()
    headers = _get_auth_header()

    fields = {
        "project": {"key": project_key.strip().upper()},
        "summary": summary.strip(),
        "issuetype": {"name": issue_type},
        "priority": {"name": priority},
    }

    if description:
        fields["description"] = _text_to_adf(description)

    if labels:
        fields["labels"] = labels

    if assignee_account_id:
        fields["assignee"] = {"accountId": assignee_account_id}

    async with httpx.AsyncClient(timeout=30.0, verify=_get_verify_ssl()) as client:
        response = await client.post(
            f"{base_url}/issue",
            headers=headers,
            json={"fields": fields},
        )

        if response.status_code == 201:
            data = response.json()
            return json.dumps({
                "success": True,
                "key": data.get("key", ""),
                "id": data.get("id", ""),
                "url": f"{_get_base_url()}/browse/{data.get('key', '')}",
                "message": f"Issue {data.get('key')} created successfully.",
            })
        elif response.status_code == 400:
            errors = response.json().get("errors", {})
            error_msgs = response.json().get("errorMessages", [])
            return json.dumps({"error": "Bad request", "details": errors, "messages": error_msgs})
        elif response.status_code == 401:
            return json.dumps({"error": "Authentication failed. Check JIRA_EMAIL and JIRA_API_TOKEN."})
        elif response.status_code == 403:
            return json.dumps({"error": "Permission denied. You may not have permission to create issues in this project."})
        else:
            return json.dumps({"error": f"Jira API error (HTTP {response.status_code}): {response.text[:500]}"})


@mcp.tool()
async def add_comment(issue_key: str, comment_text: str) -> str:
    """
    Add a comment to a Jira issue.

    Args:
        issue_key: Issue key (e.g., 'PROJ-123')
        comment_text: The comment content (plain text)
    """
    issue_key = issue_key.strip().upper()
    base_url = _get_api_url()
    headers = _get_auth_header()

    body = {
        "body": _text_to_adf(comment_text)
    }

    async with httpx.AsyncClient(timeout=30.0, verify=_get_verify_ssl()) as client:
        response = await client.post(
            f"{base_url}/issue/{issue_key}/comment",
            headers=headers,
            json=body,
        )

        if response.status_code == 201:
            data = response.json()
            return json.dumps({
                "success": True,
                "comment_id": data.get("id", ""),
                "message": f"Comment added to {issue_key} successfully.",
            })
        elif response.status_code == 404:
            return json.dumps({"error": f"Issue {issue_key} not found."})
        elif response.status_code == 401:
            return json.dumps({"error": "Authentication failed."})
        else:
            return json.dumps({"error": f"Jira API error (HTTP {response.status_code}): {response.text[:500]}"})


@mcp.tool()
async def get_issue_comments(issue_key: str, max_results: int = 20) -> str:
    """
    Get all comments on a Jira issue.

    Args:
        issue_key: Issue key (e.g., 'PROJ-123')
        max_results: Maximum comments to return (default 20)
    """
    issue_key = issue_key.strip().upper()
    base_url = _get_api_url()
    headers = _get_auth_header()

    async with httpx.AsyncClient(timeout=30.0, verify=_get_verify_ssl()) as client:
        response = await client.get(
            f"{base_url}/issue/{issue_key}/comment",
            headers=headers,
            params={"maxResults": max_results, "orderBy": "-created"},
        )

        if response.status_code == 404:
            return json.dumps({"error": f"Issue {issue_key} not found."})
        elif response.status_code == 401:
            return json.dumps({"error": "Authentication failed."})
        elif response.status_code != 200:
            return json.dumps({"error": f"Jira API error (HTTP {response.status_code}): {response.text[:500]}"})

        data = response.json()
        comments = []
        for c in data.get("comments", []):
            author_data = c.get("author", {})
            comments.append({
                "id": c.get("id", ""),
                "author": author_data.get("displayName", "Unknown"),
                "body": _adf_to_text(c.get("body")),
                "created": c.get("created", ""),
                "updated": c.get("updated", ""),
            })

        return json.dumps({
            "issue_key": issue_key,
            "total": data.get("total", 0),
            "comments": comments,
        })


@mcp.tool()
async def change_assignee(issue_key: str, assignee_account_id: str) -> str:
    """
    Change the assignee of a Jira issue.

    Args:
        issue_key: Issue key (e.g., 'PROJ-123')
        assignee_account_id: Atlassian account ID of the new assignee.
                             Use search_users tool to find account IDs.
                             Pass empty string or '-1' to unassign.
    """
    issue_key = issue_key.strip().upper()
    base_url = _get_api_url()
    headers = _get_auth_header()

    # Unassign if empty or -1
    if not assignee_account_id or assignee_account_id == "-1":
        body = {"accountId": None}
    else:
        body = {"accountId": assignee_account_id.strip()}

    async with httpx.AsyncClient(timeout=30.0, verify=_get_verify_ssl()) as client:
        response = await client.put(
            f"{base_url}/issue/{issue_key}/assignee",
            headers=headers,
            json=body,
        )

        if response.status_code == 204:
            return json.dumps({
                "success": True,
                "message": f"Assignee updated for {issue_key}.",
            })
        elif response.status_code == 404:
            return json.dumps({"error": f"Issue {issue_key} not found."})
        elif response.status_code == 400:
            return json.dumps({"error": "Invalid account ID. Use search_users to find valid IDs."})
        elif response.status_code == 401:
            return json.dumps({"error": "Authentication failed."})
        else:
            return json.dumps({"error": f"Jira API error (HTTP {response.status_code}): {response.text[:500]}"})


@mcp.tool()
async def transition_issue(issue_key: str, transition_name: str) -> str:
    """
    Transition a Jira issue to a new status (e.g., 'In Progress', 'Done', 'To Do').

    The available transitions depend on the issue's current status and workflow.
    If the transition name doesn't match exactly, available transitions will be returned.

    Args:
        issue_key: Issue key (e.g., 'PROJ-123')
        transition_name: Target status name (e.g., 'In Progress', 'Done', 'Reopened')
    """
    issue_key = issue_key.strip().upper()
    base_url = _get_api_url()
    headers = _get_auth_header()

    async with httpx.AsyncClient(timeout=30.0, verify=_get_verify_ssl()) as client:
        # First, get available transitions
        response = await client.get(
            f"{base_url}/issue/{issue_key}/transitions",
            headers=headers,
        )

        if response.status_code == 404:
            return json.dumps({"error": f"Issue {issue_key} not found."})
        elif response.status_code != 200:
            return json.dumps({"error": f"Jira API error (HTTP {response.status_code}): {response.text[:500]}"})

        transitions = response.json().get("transitions", [])
        available = {t["name"].lower(): t["id"] for t in transitions}
        available_names = [t["name"] for t in transitions]

        # Find matching transition (case-insensitive)
        target = transition_name.strip().lower()
        transition_id = available.get(target)

        if not transition_id:
            return json.dumps({
                "error": f"Transition '{transition_name}' not available for {issue_key}.",
                "available_transitions": available_names,
                "hint": "Use one of the available transitions listed above.",
            })

        # Execute the transition
        response = await client.post(
            f"{base_url}/issue/{issue_key}/transitions",
            headers=headers,
            json={"transition": {"id": transition_id}},
        )

        if response.status_code == 204:
            return json.dumps({
                "success": True,
                "message": f"{issue_key} transitioned to '{transition_name}'.",
            })
        else:
            return json.dumps({"error": f"Transition failed (HTTP {response.status_code}): {response.text[:500]}"})


@mcp.tool()
async def search_users(query: str, max_results: int = 10) -> str:
    """
    Search for Jira users by name or email. Useful for finding account IDs
    needed by change_assignee and create_issue.

    Args:
        query: Search string (name or email)
        max_results: Max users to return (default 10)
    """
    base_url = _get_api_url()
    headers = _get_auth_header()

    async with httpx.AsyncClient(timeout=30.0, verify=_get_verify_ssl()) as client:
        response = await client.get(
            f"{base_url}/user/search",
            headers=headers,
            params={"query": query, "maxResults": max_results},
        )

        if response.status_code == 401:
            return json.dumps({"error": "Authentication failed."})
        elif response.status_code != 200:
            return json.dumps({"error": f"Jira API error (HTTP {response.status_code}): {response.text[:500]}"})

        users = []
        for user in response.json():
            users.append({
                "account_id": user.get("accountId", ""),
                "display_name": user.get("displayName", ""),
                "email": user.get("emailAddress", ""),
                "active": user.get("active", False),
            })

        return json.dumps({"users": users, "total": len(users)})


@mcp.tool()
async def get_issue_for_analysis(issue_key: str) -> str:
    """
    Fetch a Jira support ticket with all details needed for DataGuru analysis.
    Returns issue details + comments in a format optimized for LLM analysis
    to identify errors, suggest solutions, and prevention strategies.

    Args:
        issue_key: Issue key (e.g., 'SUPPORT-42', 'DATA-101')
    """
    issue_key = issue_key.strip().upper()
    base_url = _get_api_url()
    headers = _get_auth_header()

    async with httpx.AsyncClient(timeout=30.0, verify=_get_verify_ssl()) as client:
        # Fetch issue details
        response = await client.get(
            f"{base_url}/issue/{issue_key}",
            headers=headers,
            params={"expand": "renderedFields"},
        )

        if response.status_code == 404:
            return json.dumps({"error": f"Issue {issue_key} not found."})
        elif response.status_code == 401:
            return json.dumps({"error": "Authentication failed. Check JIRA_EMAIL and JIRA_API_TOKEN."})
        elif response.status_code != 200:
            return json.dumps({"error": f"Jira API error (HTTP {response.status_code}): {response.text[:500]}"})

        issue = response.json()
        formatted = _format_issue(issue)

        # Fetch comments for additional context
        comments_response = await client.get(
            f"{base_url}/issue/{issue_key}/comment",
            headers=headers,
            params={"maxResults": 30, "orderBy": "created"},
        )

        comments = []
        if comments_response.status_code == 200:
            for c in comments_response.json().get("comments", []):
                author_data = c.get("author", {})
                comments.append({
                    "author": author_data.get("displayName", "Unknown"),
                    "body": _adf_to_text(c.get("body")),
                    "created": c.get("created", ""),
                })

        # Build analysis-ready output
        analysis_data = {
            **formatted,
            "comments": comments,
            "analysis_context": (
                f"Support ticket {issue_key} in project {formatted['project']}.\n"
                f"Type: {formatted['issue_type']} | Priority: {formatted['priority']} | Status: {formatted['status']}\n"
                f"Summary: {formatted['summary']}\n"
                f"Description: {formatted['description']}\n"
                f"Comments: {len(comments)} comment(s) with investigation details."
            ),
        }

        return json.dumps(analysis_data)


# ─────────────────────────────────────────────────────────────
# Server Entry Point
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Starting Jira Integration MCP Server...", file=sys.stderr)
    mcp.run()
