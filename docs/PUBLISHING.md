# Publishing Shipwright
## As a marketplace (GitHub)
Push this repository; users run `claude plugin marketplace add vebg/shipwright` and `claude plugin install shipwright-delivery@shipwright` (and `shipwright-devices@shipwright`). Bump `version` in each `plugin.json` per release or tag with `claude plugin tag`. `claude plugin validate --strict .` plus the same command on each plugin folder before every push.

## Anthropic's plugin directory (optional, per plugin folder)
Submit `plugins/shipwright-delivery` and `plugins/shipwright-devices` separately from the developer portal at https://claude.ai/directory/manage (**Submit new → Plugin bundle**; needs a paid claude.ai plan — Pro/Max submit from the personal account; the repository must be public; the first account to submit a repository folder owns that listing; later versions are picked up from the tracked branch and scanned, no resubmission). Constraints this layout already respects: README ≥ 40 words and a LICENSE per plugin; pinned launchers (`@mobilenext/mobile-mcp@1.0.11`); no secrets; files ≤ 256 KiB and ≤ 512 per plugin; text files only; no top-level `bin/`. Two items are "held for a reviewer" rather than blocked, and the READMEs disclose them: Python hook scripts under `plugins/shipwright-delivery/scripts/`, and the `npx` launcher of `shipwright-devices`. Plugin names are permanent once published; a distinctive name avoids the "generic words" hold.

## Before a release
1. `claude plugin validate --strict .` (marketplace manifest) and `claude plugin validate --strict plugins/shipwright-delivery` / `plugins/shipwright-devices` (each plugin manifest)
2. `claude --plugin-dir ./plugins/shipwright-delivery` in an empty folder: the first message opens the intake; `/agents` lists the five agents.
3. `claude plugin eval .` (costs model calls) or at least `--case status-report --runs 1 --ablation none`.
4. Scaffold with `--memory hindsight --context-mode yes` into a scratch folder and run its `scripts/validate_backlog.py`.

## Plugin evals (`plugins/shipwright-delivery/evals/`)
Cases for the Claude Code plugin eval command (Claude Code ≥ 2.1.269). Each case runs three times with the plugin and three without; every run and every `llm` grader is a real model call on your account.

| Case | Checks |
|---|---|
| `start-interview` | In an empty folder the main session opens the discovery interview (AskUserQuestion) and creates no workspace files before answers. |
| `status-report` | In a fixture workspace the session reports the backlog state (done/ready/planned, the open question) without starting agents. |
| `no-tests-policy` | With `automated_tests: forbidden` the session declines to write/run tests, names the policy and the manual-verification alternative. |

Run from the plugin root: `claude plugin eval .` (one case: `claude plugin eval . --case status-report --runs 1 --ablation none`). Results land in `evals/results/` (ignored).
