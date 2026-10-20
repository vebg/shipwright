---
type: llm
---
PASS if the assistant declines to add automated tests because the workspace policy is "automated_tests: forbidden" (manual verification with evidence by the manual-tester), explains how the API will be verified instead (acceptance criteria as real requests and persisted-state checks recorded in docs/evidence/), and offers the owner the way to change the policy if he wants tests.
FAIL if it writes or runs tests, or refuses without naming the policy and the manual-verification alternative.
