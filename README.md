# issue-agent-runner

A minimal, self-hostable reference for turning a tracker ticket into a draft PR with the
coding agent of your choice. Where hosted first-party integrations lock you to one cloud,
one tracker, and a metered per-token bill in someone else's sandbox, this runs on your own
infra with a backend you wire yourself.

## What it does

One path, start to finish:

```
tracker ticket  ->  coding agent  ->  draft PR
```

You give it a ticket key. It reads the ticket from your tracker, hands the work to a coding
agent running on your own machine, and opens a draft pull request with the result. That's the
whole job. No always-on service, no plugin registry, no multi-provider matrix — a single
readable path you can follow end to end.

## How it works

```
 CLI: issue-agent-runner run KEY-1
        |
        v
   read work item from the tracker (REST)
        |
        v
   clone repo -> temp workdir  (local, ephemeral)
        |
        v
   run the agent backend  --  single seam: run_agent(task, workdir)
        |
        v
   git branch + commit + gh pr create --draft
        |
        v
   post a status comment back to the ticket
```

1. **Read** the work item from your tracker over its REST API.
2. **Clone** the target repo into a throwaway working directory.
3. **Run the agent backend** against that workdir — this is the one seam you control.
4. **Branch, commit, and open a draft PR** via `git` and the `gh` CLI.
5. **Comment** back on the ticket with a link to the draft PR.

The working directory is ephemeral and removed after the run.

## The agent backend is a swappable seam

The agent backend is exactly one function with a clear signature:

```python
def run_agent(task: str, workdir: str) -> None:
    ...
```

There is no registry and no plugin discovery — just this one function. Swap it by editing one
file. Two reference implementations ship with the repo:

- **Default: subprocess** — `run_agent` shells out to a command you supply (your own coding
  agent CLI, a wrapper script, anything that edits files in `workdir`). Configure it with an
  env var; no code change needed for the common case.
- **`examples/api_key_agent.py`** — a ~30-line example that calls a model API directly with
  your own API key, for readers who want to see the API-key path rather than a subprocess.
- **`echo_agent.sh`** — a tiny demo backend that writes a placeholder change, so you can run
  the full ticket -> PR flow end to end with no real agent and no API cost.

Whichever you use, the contract is the same: given a task description and a working directory,
make the edits. Everything around it (tracker read, clone, branch, PR, comment) stays put.

## Quickstart

**1. Configure.** Copy the example env file and fill in your tokens:

```bash
cp .env.example .env
```

`.env.example` documents the variables you need — a tracker base URL + token (read + comment),
a GitHub token (contents + PR write), and the agent backend command. Use least-privilege
tokens.

**2. Install.**

```bash
pip install -e .
```

You'll also need `git` and the GitHub `gh` CLI on your PATH, authenticated for the target repo.

**3. Run.**

```bash
issue-agent-runner run KEY-1
```

This reads ticket `KEY-1`, runs your agent backend against a fresh clone of the repo, opens a
draft PR (e.g. against `owner/example-repo`), and comments the PR link back on the ticket.

To try the whole flow with no real agent, point the backend at `echo_agent.sh` first.

## Why self-host

Hosted first-party tracker-to-PR integrations are convenient, but they make three choices for
you. Running your own copy puts those choices back in your hands:

- **Vendor lock-in** — hosted integrations tie you to one tracker, one cloud, and one agent.
  Self-hosting lets you pick your tracker, your VCS, and your agent backend, and change any of
  them by editing one file.
- **Data residency** — in a hosted integration your code is checked out and executed inside the
  vendor's sandbox. Here it runs in your own environment, on your own network — which matters
  for privacy and compliance.
- **Cost model** — a hosted integration bills you per token on the vendor's meter. Self-hosting
  gives you a predictable cost you control, against a backend you choose.

## For real automated use

This repo is a minimal teaching reference. It is a CLI you run by hand, kept small so the whole
path is readable in one sitting.

For production — webhook-driven wake on ticket events, sandbox orchestration, and managed token
injection — the official Claude Managed Agents self-hosted sandbox environment handles those
concerns for you. If you want an always-on automated integration rather than a worked example,
that is the path to reach for. This project exists to show how the pieces fit, not to replace it.

## Backend ToS note

Users are responsible for their chosen backend's terms of service.

## License

Apache License 2.0. See [LICENSE](LICENSE).
