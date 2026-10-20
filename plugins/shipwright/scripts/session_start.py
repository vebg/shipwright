#!/usr/bin/env python3
"""SessionStart hook: tell the main session where it is and what to do first.

Prints a short context block (plain stdout is added to Claude's context on SessionStart):
- inside a Shipwright workspace: the backlog counts, policies and the resume order;
- elsewhere: the offer to run /shipwright:start.
Never fails the session: any error prints nothing and exits 0.
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_common import find_workspace, load_config, project_dir, read_payload  # noqa: E402


def main():
    payload = read_payload()
    cwd = project_dir(payload)
    root = find_workspace(cwd)
    if root is None:
        print(
            "Shipwright is enabled but this directory is not a Shipwright workspace "
            f"({cwd}). On the user's first message, before any other work, open the Shipwright "
            "intake: greet briefly, say you will ask a few rounds of questions about the product "
            "(what it is and for whom, surfaces, inspiration links/videos/apps, technologies already "
            "decided, constraints, brand, working agreement) and then run /shipwright:start, which "
            "conducts that discovery interview with AskUserQuestion and scaffolds the workspace only "
            "after the answers. Other entries: adopt this repository, resume a workspace, set up "
            "memory (Hindsight), context-mode or device tools. Do not scaffold anything without the "
            "user's answers."
        )
        return 0

    cfg = load_config(root)
    name = (cfg.get("project") or {}).get("name") or root.name
    tests = (cfg.get("policies") or {}).get("automated_tests", "forbidden")
    lines = [f"Shipwright workspace: {name} ({root})."]
    index = root / "tasks" / "index.json"
    try:
        tasks = json.loads(index.read_text(encoding="utf-8")).get("tasks", [])
        status = Counter(t.get("status") for t in tasks)
        pending = sum(1 for t in tasks if t.get("verification") == "pending")
        failed = sum(1 for t in tasks if t.get("verification") == "failed")
        inspect = sum(1 for t in tasks if "planner inspection pending" in str(t.get("note", "")))
        lines.append(
            f"Backlog: {len(tasks)} tasks — done {status.get('done', 0)}, ready {status.get('ready', 0)}, "
            f"in_progress {status.get('in_progress', 0)} (verification pending {pending}, "
            f"planner inspection pending {inspect}), returned with verification failed {failed}, "
            f"blocked {status.get('blocked', 0)}, planned {status.get('planned', 0)}, "
            f"superseded {status.get('superseded', 0)}."
        )
    except (OSError, ValueError):
        lines.append("Backlog: tasks/index.json missing or invalid — run the validator before planning.")
    try:
        import balance  # noqa: WPS433 (same folder)
        rep = balance.build(root, "priority", set(), 3)
        lines.append(balance.summary_line(rep))
    except Exception:  # noqa: BLE001 — the balance line is informative only
        pass
    repos = cfg.get("repos") or []
    if repos:
        lines.append("Code repositories (separate Git roots): " + ", ".join(
            f"{r.get('name')} ({r.get('path')})" for r in repos))
    lines.append(
        f"Policies: automated tests {tests}; verification is manual with evidence in docs/evidence/. "
        "Read CLAUDE.md, docs/HANDOFF.md and tasks/index.json first; resume order: tasks returned "
        "with verification failed → design parts awaiting planner inspection → tasks with "
        "verification pending (manual-tester) → next ready tasks. Agents run sequentially, "
        "three tasks per batch by default, and start only when the user says go."
    )
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # never break a session start
        sys.exit(0)
