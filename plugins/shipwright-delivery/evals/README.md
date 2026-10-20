# Shipwright evals
Cases for `claude plugin eval` (Claude Code ≥ 2.1.269). Each case runs three times with the plugin and three without; every run and every `llm` grader is a real model call on your account.

| Case | Checks |
|---|---|
| `start-interview` | In an empty folder the main session opens the discovery interview (AskUserQuestion) and creates no workspace files before answers. |
| `status-report` | In a fixture workspace the session reports the backlog state (done/ready/planned, the open question) without starting agents. |
| `no-tests-policy` | With `automated_tests: forbidden` the session declines to write/run tests, names the policy and the manual-verification alternative. |

Run from the plugin root: `claude plugin eval .` (one case: `claude plugin eval . --case status-report --runs 1 --ablation none`). Results land in `evals/results/` (ignored).
