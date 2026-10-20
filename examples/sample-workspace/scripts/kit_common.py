#!/usr/bin/env python3
"""Shared helpers for the Shipwright hook scripts (standard library only).

A Shipwright workspace is recognised by `shipwright.json` (or the pre-rename `delivery-kit.json`) at its root (written by
/shipwright-delivery:start) or, for workspaces created before that file existed, by the pair
`tasks/index.json` + `docs/HANDOFF.md`.
"""
import json
import os
import sys
from pathlib import Path

DEFAULT_CONFIG = {
    "schema_version": 1,
    "project": {"name": "", "product_language": "en", "deployed_version": None},
    # Optional cost budget read by balance.py and the SessionStart line (USD, list-price equivalent).
    "budget": {},
    "policies": {
        # "forbidden": the proven setting — no automated tests anywhere, manual verification
        # by the manual-tester agent with evidence. "allowed": tests may exist; manual
        # verification still gates `done`.
        "automated_tests": "forbidden",
        # Commands the policy guard always denies, besides the test commands above.
        "deny_commands": [
            "git push --force",
            "git push -f",
            "git reset --hard",
            "dotnet ef database drop",
        ],
        # Design skills reserved for the frontend-designer agent (skill names, no prefix).
        "designer_only_skills": [
            "animate", "animation-vocabulary", "apple-design", "emil-design-eng",
            "find-animation-opportunities", "improve-animations", "mobile-native",
            "prototype", "review-animations", "impeccable", "design-taste-frontend",
            "design-taste-frontend-v1", "full-output-enforcement", "high-end-visual-design",
            "industrial-brutalist-ui", "minimalist-ui", "redesign-existing-projects",
            "frontend-design",
        ],
        # Helper agents only the frontend-designer may start (and the only ones it may start).
        "designer_helper_agents": [
            "impeccable-asset-producer", "impeccable-documenter",
            "impeccable-finish-reviewer", "impeccable-manual-edit-applier",
        ],
    },
    "repos": [],
}

TEST_COMMAND_PATTERNS = [
    "dotnet test", "flutter test", "dart test", "melos run test", "melos test",
    "dotnet new xunit", "dotnet new nunit", "dotnet new mstest", "dotnet new bunit",
    "npm test", "npm run test", "pnpm test", "yarn test", "bun test", "npx jest", "npx vitest",
    "npx playwright test", "pytest", "python -m pytest", "python3 -m pytest", "go test",
    "cargo test", "mvn test", "gradle test", "./gradlew test", "swift test",
]


def read_payload():
    try:
        return json.load(sys.stdin)
    except (ValueError, OSError):
        return {}


def project_dir(payload=None):
    for candidate in ((payload or {}).get("cwd"), os.environ.get("CLAUDE_PROJECT_DIR"), os.getcwd()):
        if candidate:
            return Path(candidate)
    return Path.cwd()


def find_workspace(start):
    """Walk up from `start` to the nearest Shipwright workspace root, or None."""
    p = Path(start).resolve()
    for d in (p, *p.parents):
        if (d / "shipwright.json").is_file() or (d / "delivery-kit.json").is_file():
            return d
        if (d / "tasks" / "index.json").is_file() and (d / "docs" / "HANDOFF.md").is_file():
            return d
    return None


def load_config(root):
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if root is None:
        return cfg
    f = Path(root) / "shipwright.json"
    if not f.is_file():
        f = Path(root) / "delivery-kit.json"  # workspaces scaffolded before the rename
    if not f.is_file():
        return cfg
    try:
        user = json.loads(f.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return cfg
    for key in ("project", "policies", "budget"):
        if isinstance(user.get(key), dict):
            cfg[key].update(user[key])
    if isinstance(user.get("repos"), list):
        cfg["repos"] = user["repos"]
    return cfg


def agent_name(payload):
    """The calling agent's short name ('main session' when there is none).

    Plugin agents are reported with their scoped name (plugin:agent); the last
    segment is the agent name the kit reasons about.
    """
    raw = str(payload.get("agent_type") or "").strip()
    if not raw:
        return "main session"
    return raw.split(":")[-1]


def deny(reason):
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    return 0
