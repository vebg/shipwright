#!/usr/bin/env python3
"""PreToolUse guard for the Skill tool.

The design skills listed in `policies.designer_only_skills` (shipwright.json, with the
kit defaults) may be invoked only by the frontend-designer agent. Every other caller —
the planner main session, fullstack-developer, manual-tester — is denied so that design
taste and motion skills shape only the designer's work. A user typing a skill command
in the main session runs it there; this guard only sees tool calls made by the model.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_common import agent_name, deny, find_workspace, load_config, project_dir, read_payload  # noqa: E402

ALLOWED_AGENT = "frontend-designer"


def main():
    payload = read_payload()
    if payload.get("tool_name") != "Skill":
        return 0
    tool_input = payload.get("tool_input") or {}
    skill = str(tool_input.get("skill") or "").strip().lstrip("/")
    name = skill.split(":")[-1]
    cfg = load_config(find_workspace(project_dir(payload)))
    guarded = set((cfg.get("policies") or {}).get("designer_only_skills") or [])
    if name not in guarded:
        return 0
    caller = agent_name(payload)
    if caller == ALLOWED_AGENT:
        return 0
    return deny(
        f"Skill '{name}' is reserved for the {ALLOWED_AGENT} agent (caller: {caller}). "
        "Do not retry; continue without it."
    )


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
