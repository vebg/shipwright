---
name: status
description: Report the state of a Shipwright workspace — backlog counts by status and verification, next ready tasks, open questions, blockers, Git status per repository and the token cost so far. Use when the owner asks where things stand.
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Bash(python3:*), Bash(git status:*), Bash(git log:*)
---
# /shipwright-delivery:status

Run, in the workspace:
- `python3 scripts/validate_backlog.py` (fallback `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_backlog.py" --root .`)
- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/token_usage.py"` and read the "By task" totals from `docs/TOKEN-COSTS.md`
- `git status --short` and `git log -1 --oneline` in the workspace and in every repository listed under `repos` in `shipwright.json`

Then read `tasks/index.json` and the "State" section of `docs/HANDOFF.md` and report in this shape, compactly:
1. Counts: total; done, ready, in_progress (verification pending / planner inspection pending), returned (verification failed), blocked, planned, superseded.
2. Next in order: returned tasks, design parts to inspect, hand-overs to verify, next ready tasks (ID — title — owner/executing agent — priority).
3. Open questions (docs/QUESTIONS.md section 1) and blockers with what the owner must supply.
4. Repository state: branch, last commit, dirty files per repository; the newest release tag when the workspace tags releases.
5. Cost: total USD-equivalent and the three most expensive tasks.

Do not start agents from this skill.
