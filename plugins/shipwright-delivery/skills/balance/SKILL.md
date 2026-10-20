---
name: balance
description: Cost balance of the workspace — every task with its status, group (feature or priority band) and USD cost, a header with the total spent and statistics (by status, average/median per done task, most expensive, forecast for the remaining tasks) and the budget lines from shipwright.json when set. Use when the owner asks what things cost, how much is left, or before approving a batch.
disable-model-invocation: true
argument-hint: "[feature|priority] [--status done,ready] [--top 10]"
allowed-tools: Read, Glob, Grep, Bash(python3:*)
---
# /shipwright-delivery:balance

Run in the workspace: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/balance.py" --by <feature|priority from $ARGUMENTS, default feature> [--status …] [--top N]`. It writes `docs/BALANCE.md` and prints it. Grouping by feature uses `tasks/features.json` (`{"groups":[{"id","title","tasks":[…]}]}`, planner-maintained; tasks absent from it land in "Other"); without that file it groups by priority bands of ten.

Report to the owner, compactly and in this order:
1. **Header** — total spent (tasks + orchestration + unattributed), task counts and cost by status, average and median cost of a done task, the most expensive task, the forecast for the remaining tasks, and the budget lines (`shipwright.json` → `budget.total_usd`, `per_task_usd`, `warn_at`) when set.
2. **Groups** — one row per group: tasks, done, USD; then the per-task table of the groups the owner asked about (all of them when the backlog is small).
3. **Top tasks** — the most expensive, with one line of why when the evidence explains it (returned tasks, several parts, long device runs).
4. **Read-outs** — if a budget is set and the spend or forecast crosses `warn_at`, say so and ask before starting the next batch; if a task exceeds `per_task_usd`, name it in the hand-over. Never block on your own; the owner decides.

Notes: USD is API list-price equivalent from the same table as `docs/TOKEN-COSTS.md` (an estimate on a subscription); orchestration is the main session's own cost; runs that name several tasks are split evenly. To set a budget, add to `shipwright.json`: `"budget": {"total_usd": 500, "per_task_usd": 20, "warn_at": 0.8}`.
