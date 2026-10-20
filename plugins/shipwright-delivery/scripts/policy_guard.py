#!/usr/bin/env python3
"""PreToolUse guard for Bash: the project policies a plugin cannot ship as permission rules.

- When `policies.automated_tests` is "forbidden" (the kit default), test runners and test
  project templates are denied (`dotnet test`, `flutter test`, `npm test`, `pytest`, ...).
- `policies.deny_commands` (force pushes, hard resets, database drops by default) are
  always denied, in every mode, for every agent.
Only the model's Bash calls pass through here; the user's own shell is untouched.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_common import TEST_COMMAND_PATTERNS, deny, find_workspace, load_config, project_dir, read_payload  # noqa: E402


def normalise(cmd):
    return re.sub(r"\s+", " ", cmd).strip().lower()


def main():
    payload = read_payload()
    if payload.get("tool_name") != "Bash":
        return 0
    command = normalise(str((payload.get("tool_input") or {}).get("command") or ""))
    if not command:
        return 0
    cfg = load_config(find_workspace(project_dir(payload)))
    policies = cfg.get("policies") or {}
    for pattern in policies.get("deny_commands") or []:
        p = normalise(pattern)
        if p and p in command:
            return deny(f"'{pattern}' is denied by the workspace policy (shipwright.json). Ask the user to run it.")
    if policies.get("automated_tests", "forbidden") == "forbidden":
        for pattern in TEST_COMMAND_PATTERNS:
            if re.search(r"(^|[;&|]\s*|\s)" + re.escape(pattern) + r"(\s|$)", command):
                return deny(
                    f"'{pattern}' is denied: this workspace has no automated tests (policy automated_tests=forbidden). "
                    "Verification is manual by the manual-tester agent with evidence; do not create tests or test projects."
                )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
