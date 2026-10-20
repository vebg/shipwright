---
name: workflow
description: The Shipwright's shared delivery protocol — task states and index fields, the manual verification flow, the static-first UI work split, design and screenshot workflow, engineering discipline, multi-repository rules and session sizing. Load when an agent needs the exact rule for a hand-over, a status transition, a UI split or a cross-repository change and the workspace copy in docs/ is missing or silent on it.
---
# Shipwright protocol

The workspace's own copies — `docs/WORKFLOW.md`, `docs/DESIGN-WORKFLOW.md`, `docs/VISUAL-PROGRESS.md`, `docs/ENGINEERING.md`, `docs/MULTI-REPO.md` — are authoritative because the owner appends project-specific rules to them. The canonical texts live beside this file for workspaces that do not have them yet; read only the one the question needs:

- `${CLAUDE_PLUGIN_ROOT}/skills/workflow/references/WORKFLOW.md` — index fields, states, the manual verification flow, the UI work split, hand-over notes, session sizing and reading discipline.
- `${CLAUDE_PLUGIN_ROOT}/skills/workflow/references/DESIGN-WORKFLOW.md` — brand-aware UI work: roles, intake, briefs, implementation, review, evidence, cross-repository exports, accessibility checks.
- `${CLAUDE_PLUGIN_ROOT}/skills/workflow/references/VISUAL-PROGRESS.md` — real screenshots and recordings: when, how, where, captions, limits.
- `${CLAUDE_PLUGIN_ROOT}/skills/workflow/references/ENGINEERING.md` — implementation discipline: assumptions, smallest complete solution, diff hygiene, meaningful verification, proportional ceremony.
- `${CLAUDE_PLUGIN_ROOT}/skills/workflow/references/MULTI-REPO.md` — coordination workspace with separate application Git roots: ownership, contracts, cross-repository tasks, completion gates.

Summary of the loop: planner plans → owner says go → frontend-designer delivers a static design part (note "design part done <date>; planner inspection pending") → planner inspects and closes it → fullstack-developer implements and integrates, hands over with `verification: "pending"` → manual-tester verifies on the real software and sets `done`/`passed` or `ready`/`failed` → planner replans, updates docs/HANDOFF.md, reports the batch cost. One agent at a time; three tasks per batch; `Task: TASK-XXXX` first line in every agent prompt.
