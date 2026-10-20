---
name: resume
description: Resume a Shipwright workspace — read the handoff and the backlog, recheck interrupted work, and propose the next batch (returned tasks first, then design parts awaiting inspection, then hand-overs awaiting the tester, then the next ready tasks). Use at the start of a session in an existing workspace.
disable-model-invocation: true
---
# /shipwright-delivery:resume

Read, in this order and nothing else yet: `CLAUDE.md`, `docs/HANDOFF.md`, `tasks/index.json`, `shipwright.json`. Then run `python3 scripts/validate_backlog.py` (fallback `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_backlog.py" --root .`) and `git status --short` in the workspace and in every repository listed under `repos`.

Report compactly:
1. State from the handoff (one paragraph) and any drift between the handoff and the index.
2. Interrupted work: `in_progress` tasks without `verification` and without a "planner inspection pending" note — inspect their evidence and diff before deciding resume/block.
3. The resume order with task IDs: (a) `ready` tasks with `verification: "failed"` → fullstack-developer; (b) design parts with note "planner inspection pending" → you inspect the contact sheets/evidence and close or return them; (c) `in_progress` + `verification: "pending"` → manual-tester; (d) next `ready` tasks by priority then ID → frontend-designer (design parts) or fullstack-developer.
4. Blockers that need the owner (decisions in docs/QUESTIONS.md, inputs, credentials, tooling).
5. The proposed next batch (max three tasks, one agent, one repository at a time) and the cost of the last batch from docs/TOKEN-COSTS.md.

Then wait for the owner's go before starting any agent. Do not re-read files already read this session.
