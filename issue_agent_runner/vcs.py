"""Version-control operations, implemented by shelling out to ``git`` and ``gh``.

We deliberately avoid a git library: ``git`` and the GitHub CLI (``gh``) are
battle-tested and already installed on most dev machines. No tokens are handled
here — ``gh`` uses its own stored authentication (``gh auth login``).
"""

from __future__ import annotations

import subprocess


def _run(args: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    """Run a command, capturing output, raising on a non-zero exit.

    On failure the CalledProcessError carries stderr, so callers can show the
    reader a useful message instead of a bare traceback.
    """
    return subprocess.run(
        args, cwd=cwd, check=True, capture_output=True, text=True
    )


def clone(repo: str, workdir: str) -> None:
    """Clone ``owner/name`` into ``workdir`` using the GitHub CLI.

    ``gh repo clone`` respects the user's existing ``gh`` auth, so this works
    for private repos without any token plumbing in this code.
    """
    _run(["gh", "repo", "clone", repo, workdir])


def create_branch(workdir: str, name: str) -> None:
    """Create and check out a new branch in the cloned repo."""
    _run(["git", "checkout", "-b", name], cwd=workdir)


def commit_all(workdir: str, msg: str) -> bool:
    """Stage everything and commit.

    Returns ``True`` if a commit was made, ``False`` if there was nothing to
    commit (a clean tree means the agent produced no changes).
    """
    _run(["git", "add", "-A"], cwd=workdir)
    # `git diff --cached --quiet` exits 0 when the index has no staged changes.
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=workdir)
    if staged.returncode == 0:
        return False
    _run(["git", "commit", "-m", msg], cwd=workdir)
    return True


def open_draft_pr(
    repo: str, workdir: str, head_branch: str, base: str, title: str, body: str
) -> str:
    """Push the branch and open a draft PR via ``gh``; return the PR URL.

    First the branch is pushed to ``origin``; then ``gh pr create --draft``
    opens the pull request and prints its URL to stdout, which we return.
    """
    _run(["git", "push", "-u", "origin", head_branch], cwd=workdir)
    result = _run(
        [
            "gh",
            "pr",
            "create",
            "--repo",
            repo,
            "--draft",
            "--base",
            base,
            "--head",
            head_branch,
            "--title",
            title,
            "--body",
            body,
        ],
        cwd=workdir,
    )
    return result.stdout.strip()
