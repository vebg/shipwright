---
name: design
description: Start the frontend-designer on the ready design parts (static-first UI) after the owner's go, then inspect its screenshots and evidence and close or return each design part. Use when ready tasks name the frontend-designer.
disable-model-invocation: true
argument-hint: "[TASK-IDs]"
---
# /shipwright:design

Tasks given: `$ARGUMENTS` (empty = the `ready` design parts whose body names frontend-designer, by priority then ID, up to the batch size in shipwright.json; one large design part runs alone, as parts if its brief says so).

1. Confirm the owner's go for these tasks is in this conversation; if not, ask and stop.
2. For each selected task confirm the definition of ready: Design inputs filled (brief, asset IDs/token revision, states, viewports, capture list), dependencies done, repository and paths named.
3. Start one `frontend-designer` run (Agent tool) with a prompt that begins `Task: TASK-XXXX[, TASK-YYYY]` and names: the tasks, the repository and paths, the brief and token revision, the design routes location from the repository's CLAUDE.md, the capture list, the hand-over note to set ("design part done <date>; planner inspection pending"), the limits (static presentation only, no application code, no tests, scratch files outside repositories) and any authorization the owner gave (commits, installs). Never run two agents on the same repository at once.
4. When it returns, verify its claims against `docs/evidence/<ID>.md` and `tasks/index.json`. Inspect the contact sheets (open single captures only on doubt) against the brief and the visual criteria. Relay the screenshot paths with captions to the owner.
5. Close each design part that meets its visual criteria: status `done`, `verification: "passed"`, note "closed by planner inspection <date>; visual criteria carried into TASK-XXXX" (the linked integration task), and copy the designer's list of hardcoded values and maintenance notes into the integration task's Implementation notes. A design part that falls short goes back to the designer only for design changes (new work or a further part), never for defects — those are the developer's after integration.
6. Update `docs/HANDOFF.md`, run `python3 scripts/validate_backlog.py`, run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/token_usage.py"` and report the batch cost from docs/TOKEN-COSTS.md.
