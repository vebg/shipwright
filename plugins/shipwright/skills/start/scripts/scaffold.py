#!/usr/bin/env python3
"""Scaffold a Shipwright workspace (standard library only; never overwrites).

Usage:
  scaffold.py --target DIR --name NAME [--mode new|adopt] [--tests forbidden|allowed]
              [--language en] [--stack "summary"] [--mobile yes|no] [--web yes|no]
              [--repo "name=folder:stack" ...] [--memory none|hindsight] [--hindsight-url URL]
              [--hindsight-mode self-hosted|cloud] [--context-mode yes|no] [--plugin-root PATH] [--dry-run]

Creates the kit folders, renders the templates under skills/start/assets/workspace/,
copies the validator, the token report and the protocol references from the plugin,
and writes shipwright.json, tasks/index.json and the first ADRs. Existing files are
left untouched and reported as skipped — with one exception: --memory hindsight and
--context-mode yes MERGE the entries they need into an existing .claude/settings.json and
.mcp.json (missing keys are added; nothing of yours is removed or replaced).
"""
import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve()
PLUGIN_ROOT_DEFAULT = HERE.parents[3]  # skills/start/scripts/scaffold.py -> plugin root
ASSETS = HERE.parents[1] / "assets" / "workspace"
MEMORY_ASSETS = HERE.parents[1] / "assets" / "memory"
HINDSIGHT_RUNTIME = Path.home() / ".hindsight" / "coding-agents"

KIT_DIRS = [
    ".claude", "docs/decisions", "docs/diagrams", "docs/evidence/screenshots", "docs/releases",
    "requirements/inbox", "requirements/context", "tasks", "templates", "scripts",
    "design/briefs", "design/tokens", "design/assets", "design/references", "design/exports",
    "design/inbox", "design/source",
]

READ_ONLY_ALLOW = [
    "Bash(git status:*)", "Bash(git diff:*)", "Bash(git log:*)", "Bash(git branch:*)",
    "Bash(git rev-parse:*)", "Bash(git show:*)", "Bash(cat:*)", "Bash(head:*)", "Bash(tail:*)",
    "Bash(sed -n:*)", "Bash(wc:*)", "Bash(ls:*)", "Bash(find:*)", "Bash(grep:*)", "Bash(rg:*)",
    "Bash(python3 scripts/validate_backlog.py:*)", "Bash(python3 scripts/token_usage.py:*)",
]
BASE_DENY = ["Bash(git push --force:*)", "Bash(git reset --hard:*)", "Read(./**/.env)", "Read(./**/*.pem)"]
TEST_DENY = [
    "Bash(dotnet test:*)", "Bash(flutter test:*)", "Bash(dart test:*)", "Bash(melos run test:*)",
    "Bash(dotnet new xunit:*)", "Bash(dotnet new nunit:*)", "Bash(dotnet new mstest:*)", "Bash(dotnet new bunit:*)",
    "Bash(npm test:*)", "Bash(npx jest:*)", "Bash(npx vitest:*)", "Bash(npx playwright test:*)", "Bash(pytest:*)",
]


class Writer:
    def __init__(self, target, dry_run):
        self.target, self.dry_run = target, dry_run
        self.created, self.skipped, self.merged = [], [], []

    def write(self, rel, text):
        p = self.target / rel
        if p.exists():
            self.skipped.append(rel)
            return
        if not self.dry_run:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        self.created.append(rel)

    def merge_json(self, rel, mutate):
        """Load an existing JSON file (or {}), apply mutate(obj) -> changed?, write back."""
        p = self.target / rel
        try:
            obj = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        except ValueError:
            self.skipped.append(rel + " (invalid JSON, not merged)")
            return
        existed = p.exists()
        if not mutate(obj):
            if existed:
                self.skipped.append(rel + " (already wired)")
            return
        if not self.dry_run:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if rel in self.created:
            return
        (self.merged if existed else self.created).append(rel)

    def copy(self, src, rel):
        p = self.target / rel
        if p.exists():
            self.skipped.append(rel)
            return
        if not self.dry_run:
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, p)
        self.created.append(rel)


def parse_repo(spec):
    if "=" not in spec:
        raise argparse.ArgumentTypeError("--repo expects name=folder:stack")
    name, rest = spec.split("=", 1)
    folder, _, stack = rest.partition(":")
    return {"name": name.strip(), "path": (folder or name).strip().strip("/"), "stack": stack.strip() or "undecided"}


def render(text, values):
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def _add_hook(hooks, event, command, timeout):
    """Append a hook group for `event` unless a hook with the same command exists. Returns changed?"""
    groups = hooks.setdefault(event, [])
    for g in groups:
        for h in g.get("hooks", []):
            if h.get("command") == command:
                return False
    groups.append({"hooks": [{"type": "command", "command": command, "timeout": timeout}]})
    return True


def wire_hindsight(w, target, a, values):
    """Project-level Hindsight wiring, as used in the proven workspace: tracked config, env + hooks in
    .claude/settings.json, the two MCP servers in .mcp.json, the runtime's companion skill. Installs nothing."""
    ws = str(target)
    bank = a.name
    tmpl = (MEMORY_ASSETS / "hindsight.coding-agent.json.tmpl").read_text(encoding="utf-8")
    cfg = render(tmpl, {**values, "WORKSPACE_PATH": ws, "BANK": bank,
                        "HINDSIGHT_API_URL": a.hindsight_url.rstrip("/"),
                        "HINDSIGHT_SERVER_MODE": a.hindsight_mode})
    w.write(".hindsight/coding-agent.json", cfg)
    env = {
        "HINDSIGHT_CONFIG": f"{ws}/.hindsight/coding-agent.json",
        "HINDSIGHT_LOG_FILE": f"{ws}/.hindsight/logs/plugin.log",
        "HINDSIGHT_DIAG_FILE": f"{ws}/.hindsight/logs/diag.jsonl",
        "HINDSIGHT_USAGE_FILE": f"{ws}/.hindsight/logs/usage.jsonl",
    }
    runtime = '"$HOME/.hindsight/coding-agents/dist/'

    def mutate_settings(obj):
        changed = False
        e = obj.setdefault("env", {})
        for k, v in env.items():
            if k not in e:
                e[k] = v
                changed = True
        hooks = obj.setdefault("hooks", {})
        changed |= _add_hook(hooks, "SessionStart", f"node {runtime}claude-sessionstart-hook.js\"", 30)
        changed |= _add_hook(hooks, "UserPromptSubmit", f"node {runtime}claude-hook.js\"", 30)
        changed |= _add_hook(hooks, "Stop", f"node {runtime}claude-stop-hook.js\"", 60)
        servers = obj.setdefault("enabledMcpjsonServers", [])
        for name in ("hindsight", "hindsight-bank"):
            if name not in servers:
                servers.append(name)
                changed = True
        return changed

    def mutate_mcp(obj):
        changed = False
        servers = obj.setdefault("mcpServers", {})
        if "hindsight" not in servers:
            servers["hindsight"] = {
                "type": "stdio", "command": "node",
                "args": [str(HINDSIGHT_RUNTIME / "dist" / "mcp-server.js")],
                "env": {"HINDSIGHT_MCP_HARNESS": "claude-code", **env},
            }
            changed = True
        if "hindsight-bank" not in servers:
            servers["hindsight-bank"] = {"type": "http", "url": f"{a.hindsight_url.rstrip('/')}/mcp/{bank}/"}
            changed = True
        return changed

    w.merge_json(".claude/settings.json", mutate_settings)
    w.merge_json(".mcp.json", mutate_mcp)
    skill = HINDSIGHT_RUNTIME / "skill" / "SKILL.md"
    if skill.is_file():
        w.copy(skill, ".claude/skills/hindsight-coding-agent/SKILL.md")


def wire_context_mode(w, target):
    def mutate_settings(obj):
        e = obj.setdefault("env", {})
        if "CONTEXT_MODE_DIR" in e:
            return False
        e["CONTEXT_MODE_DIR"] = f"{target}/.context-mode"
        return True
    w.merge_json(".claude/settings.json", mutate_settings)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--mode", choices=["new", "adopt"], default="new")
    ap.add_argument("--tests", choices=["forbidden", "allowed"], default="forbidden")
    ap.add_argument("--language", default="en")
    ap.add_argument("--stack", default="undecided — the planner proposes a stack in docs/ARCHITECTURE.md")
    ap.add_argument("--mobile", choices=["yes", "no"], default="no")
    ap.add_argument("--web", choices=["yes", "no"], default="yes")
    ap.add_argument("--repo", action="append", type=parse_repo, default=[])
    ap.add_argument("--memory", choices=["none", "hindsight"], default="none")
    ap.add_argument("--hindsight-url", default="http://127.0.0.1:8888")
    ap.add_argument("--hindsight-mode", choices=["self-hosted", "cloud"], default="self-hosted")
    ap.add_argument("--context-mode", choices=["yes", "no"], default="no")
    ap.add_argument("--budget-usd", type=float, default=0.0, help="optional total budget for balance.py")
    ap.add_argument("--chat-updates", choices=["yes", "no"], default="no", help="copy docs/CHAT-UPDATES.md (chat plugin in use)")
    ap.add_argument("--plugin-root", default=str(PLUGIN_ROOT_DEFAULT))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    target = Path(a.target).expanduser().resolve()
    plugin_root = Path(a.plugin_root).resolve()
    refs = plugin_root / "skills" / "workflow" / "references"
    scripts = plugin_root / "scripts"
    for needed in (ASSETS, refs, scripts / "validate_backlog.py", scripts / "token_usage.py"):
        if not needed.exists():
            sys.exit(f"scaffold: missing {needed} (run from the installed plugin, or pass --plugin-root)")
    if not a.dry_run:
        target.mkdir(parents=True, exist_ok=True)
    w = Writer(target, a.dry_run)
    multi = len(a.repo) > 1 or (len(a.repo) == 1 and a.mode == "new")
    today = date.today().isoformat()

    # shipwright.json
    config = {
        "schema_version": 1,
        "project": {"name": a.name, "created": today, "mode": a.mode, "product_language": a.language,
                    "mobile_in_scope": a.mobile == "yes", "web_in_scope": a.web == "yes", "deployed_version": None},
        "budget": ({"total_usd": a.budget_usd, "warn_at": 0.8} if a.budget_usd else {}),
        "policies": {
            "automated_tests": a.tests,
            "deny_commands": ["git push --force", "git push -f", "git reset --hard", "dotnet ef database drop"],
            "designer_only_skills": [
                "animate", "animation-vocabulary", "apple-design", "emil-design-eng",
                "find-animation-opportunities", "improve-animations", "mobile-native", "prototype",
                "review-animations", "impeccable", "design-taste-frontend", "design-taste-frontend-v1",
                "full-output-enforcement", "high-end-visual-design", "industrial-brutalist-ui",
                "minimalist-ui", "redesign-existing-projects", "frontend-design",
            ],
            "designer_helper_agents": [
                "impeccable-asset-producer", "impeccable-documenter",
                "impeccable-finish-reviewer", "impeccable-manual-edit-applier",
            ],
            "batch_size": 3,
        },
        "repos": a.repo,
    }
    w.write("shipwright.json", json.dumps(config, indent=2, ensure_ascii=False) + "\n")

    # template values
    if a.repo:
        repos_table = "| Git repository | Folder | Stack |\n|---|---|---|\n" + "\n".join(
            f"| {r['name']} | `{r['path']}/` | {r['stack']} |" for r in a.repo)
        repo_rule = (
            "Separate Git roots: " + ", ".join(f"`{r['path']}`" for r in a.repo) +
            " are children of this workspace, ignored by the parent `.gitignore`. This workspace tracks "
            "coordination only (docs, tasks, requirements, design, scripts, templates). Read docs/MULTI-REPO.md "
            "before structural work; qualify code paths with their repository; check Git status separately in "
            "every affected repository; never assume an atomic commit across repositories; never duplicate the backlog."
        ) if multi else (
            "Single repository: application code and the workspace share this Git root. Keep the kit folders "
            "(docs, tasks, requirements, design, templates, scripts) at the root."
        )
    else:
        repos_table = "| Git repository | Folder | Stack |\n|---|---|---|\n| (this repository) | `.` | " + a.stack + " |"
        repo_rule = (
            "Single repository: application code and the workspace share this Git root. Keep the kit folders "
            "(docs, tasks, requirements, design, templates, scripts) at the root."
        )
    tests_line = (
        "No automated tests (ADR-0001): never create unit, widget, integration, golden or e2e tests, test projects, "
        "`test/`/`integration_test/` folders or test dependencies in any repository; delete generated test stubs; "
        "never use test project templates. Verification is manual by the manual-tester agent with evidence in docs/evidence/."
        if a.tests == "forbidden" else
        "Automated tests are allowed (ADR-0001) but never replace manual verification: the manual-tester agent verifies "
        "every acceptance criterion on the real software and records evidence in docs/evidence/ before a task is done."
    )
    memory_line = (
        "Hindsight is wired at project level (`.hindsight/coding-agent.json`, hooks and `HINDSIGHT_*` env in "
        "`.claude/settings.json`, the `hindsight` and `hindsight-bank` MCP servers in `.mcp.json`; logs in "
        "`.hindsight/logs/`, ignored). Agents search the knowledge pages before re-deriving decisions, credit what "
        "they used, and correct stale memory with `Correction: <topic>`. Memory is a past record: docs/HANDOFF.md, "
        "tasks/index.json, task bodies, docs/QUESTIONS.md, requirements/inbox/USER-DECISIONS-*.md and docs/evidence/ "
        "stay authoritative; a remembered decision never authorizes new work. Never store secrets or server addresses. "
        "If the server is unreachable, say so once and continue."
        if a.memory == "hindsight" else
        "Not wired. To add Hindsight memory later run `/shipwright:start memory` (self-hosted server + the "
        "`@vectorize-io/hindsight-coding-agents` runtime are installed by the owner; the scaffold writes only the "
        "project-level wiring). Until then the agents skip their memory sections."
    )
    context_line = (
        "The `context-mode` plugin is enabled for this project (`CONTEXT_MODE_DIR=.context-mode`, ignored). Every agent "
        "routes builds, analyzers, logs, JSON bodies and big files through `ctx_execute` / `ctx_batch_execute` / "
        "`ctx_execute_file` and long documents through `ctx_index` / `ctx_search`; evidence files keep the complete output. "
        "`/context-mode:ctx-stats` shows the savings; `/context-mode:ctx-doctor` checks the install."
        if a.context_mode == "yes" else
        "Not enabled. To add it later: `claude plugin marketplace add mksglu/context-mode`, `claude plugin install "
        "context-mode@context-mode`, then `/shipwright:start context`. Until then the agents skip their context-budget sections."
    )
    values = {
        "PROJECT_NAME": a.name, "DATE": today, "STACK_SUMMARY": a.stack, "PRODUCT_LANGUAGE": a.language,
        "REPOS_TABLE": repos_table, "REPO_RULE": repo_rule, "TESTS_POLICY_LINE": tests_line,
        "MOBILE_IN_SCOPE": "yes" if a.mobile == "yes" else "no", "WEB_IN_SCOPE": "yes" if a.web == "yes" else "no",
        "MEMORY_LINE": memory_line, "CONTEXT_MODE_LINE": context_line,
    }

    # folders
    for d in KIT_DIRS:
        if not a.dry_run:
            (target / d).mkdir(parents=True, exist_ok=True)

    # templates (every file under assets/workspace, rendered; *.tmpl loses the suffix)
    for src in sorted(ASSETS.rglob("*")):
        if src.is_dir():
            continue
        rel = src.relative_to(ASSETS).as_posix()
        if rel.endswith(".tmpl"):
            rel = rel[:-5]
        if rel == "docs/MULTI-REPO.md" and not multi:
            continue
        if rel.startswith("templates/REPO-CLAUDE.md"):
            continue  # rendered per repository below
        if rel == ".gitignore" and (target / ".gitignore").exists():
            continue  # never touch an existing ignore file; the summary prints the lines to add
        text = render(src.read_text(encoding="utf-8"), values)
        if rel == ".gitignore":
            text = text.replace("{{CHILD_IGNORES}}", "\n".join(f"/{r['path']}/" for r in a.repo) if multi else "")
        w.write(rel, text)

    # per-repository instruction files
    repo_tmpl = (ASSETS / "templates" / "REPO-CLAUDE.md.tmpl").read_text(encoding="utf-8")
    for r in a.repo:
        text = render(repo_tmpl, {**values, "REPO_NAME": r["name"], "REPO_PATH": r["path"], "REPO_STACK": r["stack"]})
        child = target / r["path"]
        if child.is_dir() and not (child / "CLAUDE.md").exists():
            w.write(f"{r['path']}/CLAUDE.md", text)
        else:
            w.write(f"templates/{r['name']}-CLAUDE.md", text)

    # protocol references and scripts from the plugin
    for name in ("WORKFLOW.md", "DESIGN-WORKFLOW.md", "VISUAL-PROGRESS.md", "ENGINEERING.md", "MULTI-REPO.md", "CHAT-UPDATES.md"):
        if name == "MULTI-REPO.md" and not multi:
            continue
        if name == "CHAT-UPDATES.md" and a.chat_updates != "yes":
            continue
        w.write(f"docs/{name}", render((refs / name).read_text(encoding="utf-8"), values))
    w.copy(scripts / "validate_backlog.py", "scripts/validate_backlog.py")
    w.copy(scripts / "token_usage.py", "scripts/token_usage.py")
    w.copy(scripts / "balance.py", "scripts/balance.py")
    w.copy(scripts / "kit_common.py", "scripts/kit_common.py")

    # backlog and attribution
    w.write("tasks/index.json", json.dumps({"schema_version": 1, "tasks": []}, indent=2) + "\n")
    w.write("tasks/token-attribution.json", "{}\n")

    # project settings
    deny = BASE_DENY + (TEST_DENY if a.tests == "forbidden" else [])
    settings = {"permissions": {"allow": READ_ONLY_ALLOW, "deny": deny, "defaultMode": "acceptEdits"}}
    w.write(".claude/settings.json", json.dumps(settings, indent=2) + "\n")

    # optional companions: Hindsight memory (project-level wiring) and context-mode
    if a.memory == "hindsight":
        wire_hindsight(w, target, a, values)
    if a.context_mode == "yes":
        wire_context_mode(w, target)

    # first decisions
    adr1 = (ASSETS.parent / "adr" / ("ADR-0001-no-automated-tests.md" if a.tests == "forbidden" else "ADR-0001-tests-allowed.md"))
    w.write("docs/decisions/ADR-0001-verification-policy.md", render(adr1.read_text(encoding="utf-8"), values))
    if multi:
        adr2 = ASSETS.parent / "adr" / "ADR-0002-multi-repository-workspace.md"
        w.write("docs/decisions/ADR-0002-multi-repository-workspace.md", render(adr2.read_text(encoding="utf-8"), values))

    # summary
    verb = "Would create" if a.dry_run else "Created"
    print(f"{verb} {len(w.created)} files in {target}")
    for rel in w.created:
        print(f"  + {rel}")
    if w.merged:
        print(f"Merged entries into {len(w.merged)} existing files (keys added, nothing removed):")
        for rel in w.merged:
            print(f"  ~ {rel}")
    if w.skipped:
        print(f"Skipped {len(w.skipped)} existing files (not overwritten):")
        for rel in w.skipped:
            print(f"  = {rel}")
    if a.memory == "hindsight":
        if not HINDSIGHT_RUNTIME.is_dir():
            print(f"Note: the Hindsight runtime was not found at {HINDSIGHT_RUNTIME}; install it with "
                  "`npx @vectorize-io/hindsight-coding-agents install claude-code` (and run a Hindsight server) "
                  "before the hooks and MCP servers can work. The wiring is in place either way.")
        print("Memory: restart Claude Code in the workspace; the 🧠 banner and the mcp__hindsight tools confirm the wiring. "
              "Edit .hindsight/coding-agent.json → customPages to the project's own questions.")
    if a.context_mode == "yes":
        print("context-mode: make sure the plugin is installed (claude plugin marketplace add mksglu/context-mode; "
              "claude plugin install context-mode@context-mode) — /context-mode:ctx-doctor checks it.")
    gi = target / ".gitignore"
    if gi.exists() and ".gitignore" not in w.created and (a.memory == "hindsight" or a.context_mode == "yes"):
        present = gi.read_text(encoding="utf-8", errors="replace")
        wanted = ([ "/.hindsight/logs/"] if a.memory == "hindsight" else []) + (["/.context-mode/"] if a.context_mode == "yes" else [])
        missing = [line for line in wanted if line not in present]
        if missing:
            print("Existing .gitignore kept. Add these lines:")
            for line in missing:
                print(f"  {line}")
    if multi and (target / ".gitignore").exists() and ".gitignore" not in w.created:
        print("Existing .gitignore kept. Make sure it contains these lines before staging anything:")
        for r in a.repo:
            print(f"  /{r['path']}/")
    print("Next: put requirements in requirements/inbox/, fill requirements/INTAKE.md, restart Claude Code here and run /shipwright:plan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
