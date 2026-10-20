#!/usr/bin/env python3
"""PreToolUse guard for the Agent tool (nested delegation).

- frontend-designer may start only the design helper agents listed in
  `policies.designer_helper_agents` (the Impeccable helpers by default) — never the
  developer, the tester or any other type.
- nobody else may start those helper agents.
- fullstack-developer and manual-tester never start agents.
- the planner (main session) is unaffected: it starts frontend-designer,
  fullstack-developer, manual-tester and store-compliance-reviewer sequentially.

A subagent's `tools: Agent(...)` type list is not enforced by Claude Code for
subagents, so this hook is what enforces the delegation rules.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_common import agent_name, deny, find_workspace, load_config, project_dir, read_payload  # noqa: E402

DESIGNER = "frontend-designer"
NO_DELEGATION = {"fullstack-developer", "manual-tester", "store-compliance-reviewer"}


def main():
    payload = read_payload()
    if payload.get("tool_name") not in ("Agent", "Task"):
        return 0
    tool_input = payload.get("tool_input") or {}
    target = str(tool_input.get("subagent_type") or "").strip().split(":")[-1]
    caller = agent_name(payload)
    cfg = load_config(find_workspace(project_dir(payload)))
    helpers = set((cfg.get("policies") or {}).get("designer_helper_agents") or [])

    if caller == DESIGNER:
        if target in helpers:
            return 0
        return deny(
            f"{DESIGNER} may start only its design helper agents ({', '.join(sorted(helpers)) or 'none'}); "
            f"'{target or 'unspecified'}' is not allowed. Do the work yourself or report it to the planner."
        )
    if caller in NO_DELEGATION:
        return deny(f"{caller} does not start agents; report the need to the planner instead.")
    if target in helpers:
        return deny(
            f"Agent '{target}' is reserved for the {DESIGNER} agent (caller: {caller}). "
            "Do not retry; continue without it."
        )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
