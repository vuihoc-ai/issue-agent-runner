#!/usr/bin/env python3
"""Example agent backend that calls a real LLM via a provider credential (illustrative).

This is NOT run by default. It shows how a reader would wire a real coding
agent. Point AGENT_CMD at it, e.g. AGENT_CMD="python /path/to/this_script.py".

It is provider-agnostic: read whatever credential your provider uses from the
environment and call its SDK. The actual model call is left as a pseudo-call so
no provider is hard-coded as a dependency. The contract is the same as any
backend: read the task, edit files in the current directory; the runner commits
whatever changed.
"""

import json
import os
import sys

# The runner passes the task as JSON on stdin AND as TASK_* env vars.
task = json.load(sys.stdin) if not sys.stdin.isatty() else {}
summary = task.get("summary", os.environ.get("TASK_SUMMARY", ""))
description = task.get("description", os.environ.get("TASK_DESCRIPTION", ""))

# Read whatever credential your chosen provider uses. Nothing here is required
# by the runner — swap in your provider of choice.
provider_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
if not provider_key:
    sys.exit("set a provider credential env var for your chosen backend")

prompt = f"Implement this task in the current repo.\n\n{summary}\n\n{description}"

# --- pseudo-call: replace with your provider's SDK ---
# from your_provider import Client
# client = Client(credential=provider_key)
# patch = client.generate_code(prompt)        # returns file edits / a diff
# apply_patch(patch)                           # write the edits into the cwd
patch = f"# TODO: real model output for: {summary}\n"
with open("AGENT_OUTPUT.md", "w") as f:
    f.write(patch)
