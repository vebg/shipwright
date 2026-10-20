---
name: develop
description: Start the fullstack-developer on the next eligible tasks after the owner's go — returned tasks (verification failed) first, then ready backend and integration tasks — and record the hand-over. Use when ready implementation tasks exist.
disable-model-invocation: true
argument-hint: "[TASK-IDs]"
---
# /shipwright-delivery:develop

Tasks given: `$ARGUMENTS` (empty = `ready` tasks with `verification: "failed"` first, then `ready` tasks owned by fullstack-developer whose dependencies are done and whose design part, if any, is closed; by priority then ID; up to the batch size in shipwright.json, or one large task alone).

1. Confirm the owner's go for these tasks is in this conversation; if not, ask and stop.
2. Confirm each task's definition of ready (acceptance criteria as manual checks, decisions settled, repository and impact filled, verification approach stated). Send a task that is not ready back to planning instead of starting the developer.
3. Start one `fullstack-developer` run (Agent tool) with a prompt that begins `Task: TASK-XXXX[, TASK-YYYY]` and names: the tasks and their order, the relevant decisions (ADR IDs, coding standards location), the repositories and branch rule, the design hand-over to integrate (evidence section with the values to bind), the verification policy, the hand-over expectation (`verification: "pending"`, evidence Implementation section, HANDOFF block, validator) and any authorization the owner gave (commits, installs, credentials). Never run two agents on the same repository at once.
4. When it returns, verify its claims against `docs/evidence/<ID>.md`, `tasks/index.json` and `git status`/`git log` in each affected repository (commits on the agreed branch, task ID in the subject, nothing pushed). Relay screenshot paths with captions if any. Record blockers and "For the owner" items in `docs/HANDOFF.md`.
5. Run `python3 scripts/validate_backlog.py` and `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/token_usage.py"`; report the batch cost, the tasks now awaiting the manual-tester and the next command (`/shipwright-delivery:verify`).
