# ADR-0001 — Automated tests allowed; manual verification still gates completion
Status: Accepted — owner answer at workspace creation ({{DATE}}, `/shipwright-delivery:start`; `policies.automated_tests = "allowed"` in shipwright.json).

## Context
The owner allows automated tests in the repositories. The kit's proven evidence model — manual verification of every acceptance criterion on the real software, recorded in docs/evidence/ — stays in force because a passing suite does not demonstrate booking, authorization, privacy or realtime behaviour on real requests and devices.

## Decision
- The fullstack-developer may add tests where they pay for themselves (pure logic, contract serialization, regressions it reproduced); it never replaces a manual acceptance check with a test and never spends the batch on test infrastructure the task does not need.
- Acceptance criteria remain observable manual checks; the manual-tester verifies them on the real API/apps/browsers and records evidence; `done` requires `verification: "passed"`.
- Test commands run by agents are the repository's documented ones; the policy guard does not deny them in this workspace.

## Consequences
Two safety nets with different costs; the planner keeps the manual criteria focused and the developer keeps tests cheap. If the owner later forbids tests, this ADR is superseded and the policy changes to `forbidden`.
