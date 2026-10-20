# ADR-0001 — No automated tests; manual verification by the manual-tester agent and the owner
Status: Accepted — owner answer at workspace creation ({{DATE}}, `/shipwright-delivery:start`; `policies.automated_tests = "forbidden"` in shipwright.json). Only the owner can revisit it.

## Context
Automated test suites cost agent time and context on every task and, in the delivery workflow this kit comes from, did not provide the evidence that mattered: booking races, authorization, privacy and realtime recovery still needed real requests, persisted-state queries and device runs. The owner chose manual verification with recorded evidence instead.

## Decision
- No repository contains unit, widget, integration, golden or e2e tests, test projects, `test/` or `integration_test/` folders, or test-only dependencies. Generated test stubs are deleted; test project templates are never used. The plugin's policy guard denies test runners and test templates to the agents.
- Workflow: fullstack-developer implements and self-checks (build, analyze, format, the app starts, the implemented path) and hands over with `verification: "pending"`; the manual-tester verifies every acceptance criterion by running the real API/apps/browsers and records steps, observed results and screenshots in docs/evidence/TASK-NNNN.md; it sets the task `done` (`verification: "passed"`) or returns it to `ready` (`verification: "failed"`) with defects (docs/WORKFLOW.md).
- Acceptable techniques: HTTP requests with status and body inspection, queries of persisted state, genuinely concurrent ad-hoc requests for races, two browser contexts or devices for realtime, ad-hoc browser automation for screenshots, emulator/simulator runs, network toggling for reconnect. Ad-hoc scripts live in a scratch directory or inline in evidence and are never committed as test suites.
- Acceptance criteria are written as observable checks with expected results; "test passes" wording is not used.

## Consequences
Regression safety relies on repeating recorded manual checks for affected consumers, so evidence files list exact commands. Verification takes agent time per task; the planner keeps acceptance criteria focused. If the owner later allows automated tests, this ADR is superseded and tasks get follow-ups rather than silent edits.
