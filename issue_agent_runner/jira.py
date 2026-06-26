"""Minimal Jira Cloud REST v3 client: read an issue, post a comment.

Only the two operations the pipeline needs are implemented. Authentication is
HTTP Basic with ``email:api_token`` (the standard for Jira Cloud API tokens).
The token is passed to httpx but is never written to logs or printed.
"""

from __future__ import annotations

import httpx


class JiraClient:
    """Talks to one Jira Cloud site.

    Args:
        base_url: e.g. ``https://your-org.atlassian.net`` (no trailing slash needed).
        email: account email used as the Basic-auth username.
        token: Jira Cloud API token used as the Basic-auth password (secret).
    """

    def __init__(self, base_url: str, email: str, token: str) -> None:
        self._base_url = base_url.rstrip("/")
        # httpx keeps the credentials internal; they are not part of repr/log output.
        self._client = httpx.Client(
            base_url=f"{self._base_url}/rest/api/3",
            auth=(email, token),
            headers={"Accept": "application/json"},
            timeout=30.0,
        )

    def get_issue(self, key: str) -> dict:
        """Fetch one issue and return a small, plain dict.

        Returns ``{"key", "summary", "description"}`` where ``description`` is
        flattened to plain text from Jira's Atlassian Document Format (ADF).
        """
        resp = self._client.get(
            f"/issue/{key}", params={"fields": "summary,description"}
        )
        resp.raise_for_status()
        fields = resp.json().get("fields", {})
        return {
            "key": key,
            "summary": fields.get("summary") or "",
            "description": _adf_to_text(fields.get("description")),
        }

    def add_comment(self, key: str, text: str) -> None:
        """Post a plain-text comment on the issue.

        The Jira v3 API expects an ADF document body, so the plain text is
        wrapped in a minimal single-paragraph ADF node.
        """
        resp = self._client.post(
            f"/issue/{key}/comment", json={"body": _text_to_adf(text)}
        )
        resp.raise_for_status()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "JiraClient":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()


def _text_to_adf(text: str) -> dict:
    """Wrap plain text in a minimal ADF paragraph document."""
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            }
        ],
    }


def _adf_to_text(node) -> str:
    """Recursively flatten an ADF node tree to plain text.

    Jira descriptions come back as a nested ADF document. We only need the
    readable text to hand to the agent, so we concatenate every ``text`` node
    and insert newlines between paragraphs. Returns "" for a null description.
    """
    if not node:
        return ""
    if isinstance(node, dict):
        if node.get("type") == "text":
            return node.get("text", "")
        children = "".join(_adf_to_text(c) for c in node.get("content", []))
        # Block-level nodes get a trailing newline so paragraphs stay separated.
        if node.get("type") in {"paragraph", "heading"}:
            return children + "\n"
        return children
    if isinstance(node, list):
        return "".join(_adf_to_text(c) for c in node)
    return ""
