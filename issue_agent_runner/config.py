"""Configuration loaded from environment variables or a local ``.env`` file.

All settings live in one place so the rest of the code never reads ``os.environ``
directly. Secrets (the Jira API token) are held here but never logged.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application configuration.

    Values are read from the process environment first, then from a ``.env``
    file in the current working directory. See ``.env.example`` for the full
    list with descriptions.
    """

    # --- Jira (the work-item source) ---
    jira_base_url: str  # e.g. https://your-org.atlassian.net
    jira_email: str  # the account email used for Basic auth
    jira_api_token: str  # Jira Cloud API token — secret, never logged

    # --- GitHub (where the draft PR is opened) ---
    github_repo: str  # "owner/name"

    # --- Agent backend ---
    agent_cmd: str  # shell command that runs your coding agent in the workdir

    # --- VCS defaults ---
    default_branch: str = "main"  # base branch the PR targets

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def load() -> Settings:
    """Load and validate settings.

    Raises a clear ``pydantic.ValidationError`` if a required variable is
    missing, listing exactly which one — so first-run setup is obvious.
    """
    return Settings()  # type: ignore[call-arg]
