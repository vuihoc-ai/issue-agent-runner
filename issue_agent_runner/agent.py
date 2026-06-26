"""The agent backend — THE ONE SWAPPABLE SEAM of this project.

``run_agent(task, workdir)`` is the single function you replace to plug in the
coding agent of your choice. Everything else (reading the ticket, cloning,
branching, committing, opening the PR) stays the same.

The default implementation shells out to a user-supplied command
(``AGENT_CMD`` from config) inside the cloned repo. The task is exposed two ways
so any backend can consume it however it likes:

  * environment variables: ``TASK_KEY``, ``TASK_SUMMARY``, ``TASK_DESCRIPTION``
  * the full task as JSON on stdin

A backend is expected to edit files in ``workdir``; the pipeline commits
whatever changed afterwards. To swap in a real agent, either point ``AGENT_CMD``
at your own script (see ``examples/echo_agent.sh`` and
``examples/api_key_agent.py``) or replace the body of this function.
"""

from __future__ import annotations

import json
import os
import subprocess


def run_agent(task: dict, workdir: str) -> None:
    """Run the configured agent backend against the cloned repo.

    Args:
        task: ``{"key", "summary", "description"}`` describing the work item.
        workdir: path to the cloned repo the agent should modify in place.

    The command is read from ``AGENT_CMD`` in the environment so this default
    impl has no hard dependency on the config module. It is run through the
    shell (``shell=True``) so users can pass a normal command line.
    """
    agent_cmd = os.environ.get("AGENT_CMD")
    if not agent_cmd:
        raise RuntimeError(
            "AGENT_CMD is not set — point it at your agent backend command "
            "(see examples/echo_agent.sh) or replace run_agent() in agent.py."
        )

    # Pass the task both as env vars (convenient) and as JSON on stdin (complete).
    env = {
        **os.environ,
        "TASK_KEY": task.get("key", ""),
        "TASK_SUMMARY": task.get("summary", ""),
        "TASK_DESCRIPTION": task.get("description", ""),
    }
    subprocess.run(
        agent_cmd,
        shell=True,
        cwd=workdir,
        env=env,
        input=json.dumps(task),
        text=True,
        check=True,
    )
