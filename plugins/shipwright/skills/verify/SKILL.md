---
name: verify
description: Start the manual-tester on the tasks handed over with verification pending, then read its evidence, replan follow-ups and update the handoff. Use after a developer hand-over.
disable-model-invocation: true
argument-hint: "[TASK-IDs]"
---
# /shipwright:verify

Tasks given: `$ARGUMENTS` (empty = `in_progress` tasks with `verification: "pending"`, by priority then ID, up to the batch size in shipwright.json).

1. Confirm the owner's go covers verification of these tasks (a go for a batch covers its developer → tester sequence); if not, ask and stop.
2. Start one `manual-tester` run (Agent tool) with a prompt that begins `Task: TASK-XXXX[, TASK-YYYY]` and names: the tasks, where the acceptance criteria and the Implementation evidence are, the run commands' location (each repository's CLAUDE.md), the local environment the owner provides (database, devices, simulators; credentials only by reference to user-supplied configuration), the capture requirements (docs/VISUAL-PROGRESS.md), the release-tagging step if the workspace uses it, and the limits (no application code, no tests, local devices only, nothing deployed or sent).
3. When it returns, read the Manual verification section of each `docs/evidence/<ID>.md` and the index changes: `done` + `passed` with evidence listed, or `ready` + `failed` with actionable defects, or still pending/blocked with the reason. Check that each observation actually demonstrates the criterion it claims (not a proxy, not a screenshot for a data-privacy rule).
4. Replan: follow-up tasks for defects that reveal missing scope, dependents promoted only if their definition of ready holds, impacts on done work recorded. Relay screenshots/recordings to the owner with captions; list "For the owner" items.
5. Update `docs/HANDOFF.md`, run `python3 scripts/validate_backlog.py` and `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/token_usage.py"`; report passed/returned/blocked IDs, the batch cost and the next batch proposal.
