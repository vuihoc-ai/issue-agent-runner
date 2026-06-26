"""Command-line entry point: ``issue-agent-runner run <ISSUE_KEY>``.

Ties the pieces together end to end:

  load config -> read the Jira issue -> clone the repo into a temp dir ->
  create branch ``agent/<KEY>`` -> run the agent backend -> commit any changes ->
  open a draft PR -> comment the PR link back on the ticket -> clean up.

If the agent makes no changes, no PR is opened and a "no changes" comment is
posted instead. The temporary workdir is always removed.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile

from . import vcs
from .agent import run_agent
from .config import load
from .jira import JiraClient


def _run(issue_key: str) -> int:
    """Execute the full pipeline for one issue key. Returns a process exit code."""
    try:
        settings = load()
    except Exception as exc:  # pydantic ValidationError or similar
        print(f"error: could not load configuration: {exc}", file=sys.stderr)
        print("hint: copy .env.example to .env and fill it in.", file=sys.stderr)
        return 2

    # run_agent() reads AGENT_CMD from the environment; make sure it is present
    # even when AGENT_CMD only lived in the .env file.
    os.environ.setdefault("AGENT_CMD", settings.agent_cmd)

    branch = f"agent/{issue_key}"
    workdir = tempfile.mkdtemp(prefix="issue-agent-runner-")
    jira = JiraClient(
        settings.jira_base_url, settings.jira_email, settings.jira_api_token
    )

    try:
        print(f"[1/6] reading {issue_key} from Jira...")
        task = jira.get_issue(issue_key)
        print(f"      {task['summary']!r}")

        print(f"[2/6] cloning {settings.github_repo}...")
        vcs.clone(settings.github_repo, workdir)

        print(f"[3/6] creating branch {branch}...")
        vcs.create_branch(workdir, branch)

        print("[4/6] running agent backend...")
        run_agent(task, workdir)

        print("[5/6] committing changes...")
        committed = vcs.commit_all(workdir, f"{issue_key}: {task['summary']}")

        if not committed:
            print("      agent made no changes — no PR opened.")
            jira.add_comment(
                issue_key,
                "issue-agent-runner: the agent produced no changes; no pull "
                "request was opened.",
            )
            return 0

        print("[6/6] opening draft pull request...")
        pr_url = vcs.open_draft_pr(
            repo=settings.github_repo,
            workdir=workdir,
            head_branch=branch,
            base=settings.default_branch,
            title=f"{issue_key}: {task['summary']}",
            body=(
                f"Draft PR generated for **{issue_key}** by issue-agent-runner.\n\n"
                f"{task['description']}"
            ),
        )
        print(f"      {pr_url}")
        jira.add_comment(
            issue_key, f"issue-agent-runner opened a draft PR: {pr_url}"
        )
        return 0

    except Exception as exc:
        print(f"error: pipeline failed: {exc}", file=sys.stderr)
        # Surface subprocess stderr when available — it's the most useful part.
        stderr = getattr(exc, "stderr", None)
        if stderr:
            print(stderr, file=sys.stderr)
        return 1
    finally:
        jira.close()
        shutil.rmtree(workdir, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="issue-agent-runner",
        description="Turn a tracker ticket into a draft PR using a coding agent.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run_cmd = sub.add_parser("run", help="run the pipeline for one issue")
    run_cmd.add_argument("issue_key", help="Jira issue key, e.g. PROJ-123")

    args = parser.parse_args(argv)
    if args.command == "run":
        return _run(args.issue_key)
    parser.error(f"unknown command: {args.command}")
    return 2  # unreachable; parser.error exits


if __name__ == "__main__":
    raise SystemExit(main())
