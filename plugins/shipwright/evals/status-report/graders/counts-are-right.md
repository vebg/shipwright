---
type: llm
---
PASS if the reply states that one task is done (TASK-0001), one is ready (TASK-0002, the next to start) and one is planned (TASK-0003), and it mentions the open question Q-1 or that a question is pending for the owner.
FAIL if it invents tasks or statuses not in tasks/index.json, starts implementing anything, or reports no state at all.
