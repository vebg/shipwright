#!/usr/bin/env python3
"""Doctor: check the machine and the workspace before agents run. Read-only, standard library.

Usage: python3 doctor.py [--root <workspace>] [--json]
Prints one line per check: OK / WARN / MISSING with the fix command. Exit code 0 always
(the report is the result; the planner decides).
"""
import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_common import find_workspace, load_config  # noqa: E402


def run(cmd, timeout=8):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (p.stdout or p.stderr).strip().splitlines()[0] if (p.stdout or p.stderr).strip() else ""
    except (OSError, subprocess.SubprocessError):
        return None


def port_open(url):
    try:
        u = urlparse(url)
        with socket.create_connection((u.hostname or "127.0.0.1", u.port or 80), timeout=1.5):
            return True
    except OSError:
        return False


def main():
    a = sys.argv[1:]
    root = Path(a[a.index("--root") + 1]).resolve() if "--root" in a else find_workspace(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
    checks = []

    def add(name, state, detail, fix=""):
        checks.append({"check": name, "state": state, "detail": detail, "fix": fix})

    # tools
    for tool, fix in (("python3", "install Python 3 (python.org or brew install python)"),
                      ("git", "install Git (brew install git)"),
                      ("node", "install Node.js (brew install node) — needed by Hindsight hooks and mobile-mcp"),
                      ("npx", "comes with Node.js"),
                      ("claude", "install Claude Code: npm install -g @anthropic-ai/claude-code")):
        path = shutil.which(tool)
        add(tool, "OK" if path else "MISSING", (run([tool, "--version"]) or path) if path else "not on PATH", "" if path else fix)
    # claude code version
    v = run(["claude", "--version"]) if shutil.which("claude") else None
    if v:
        add("claude version", "OK", v, "")

    # workspace
    if root is None:
        add("workspace", "WARN", "not inside a Shipwright workspace (no shipwright.json / tasks/index.json + docs/HANDOFF.md)",
            "run /shipwright:start here, or cd into the workspace")
    else:
        cfg = load_config(root)
        add("workspace", "OK", f"{root} — tests {cfg['policies'].get('automated_tests')}, repos {len(cfg.get('repos') or [])}", "")
        for rel in ("tasks/index.json", "docs/HANDOFF.md", "scripts/validate_backlog.py", "scripts/token_usage.py", "CLAUDE.md"):
            add(rel, "OK" if (root / rel).is_file() else "MISSING", "" if (root / rel).is_file() else "expected kit file",
                "" if (root / rel).is_file() else "re-run the scaffold in adopt mode (never overwrites)")
        if (root / "scripts" / "validate_backlog.py").is_file():
            out = run([sys.executable, str(root / "scripts" / "validate_backlog.py"), "--root", str(root)], timeout=20)
            add("backlog validator", "OK" if out and out.startswith("Backlog valid") else "WARN", out or "no output", "fix the index before planning")
        for r in cfg.get("repos") or []:
            p = root / r.get("path", "")
            git = (p / ".git").exists()
            add(f"repo {r.get('name')}", "OK" if git else "MISSING", str(p) + ("" if git else " — not a Git root"),
                "" if git else "git init / clone the repository into that folder")
        # settings and hooks
        settings = root / ".claude" / "settings.json"
        s = {}
        if settings.is_file():
            try:
                s = json.loads(settings.read_text(encoding="utf-8"))
            except ValueError:
                add(".claude/settings.json", "WARN", "invalid JSON", "fix the file")
        hooks = json.dumps(s.get("hooks", {}))
        # Hindsight
        hcfg = root / ".hindsight" / "coding-agent.json"
        if hcfg.is_file():
            runtime = Path.home() / ".hindsight" / "coding-agents" / "dist" / "mcp-server.js"
            add("hindsight runtime", "OK" if runtime.is_file() else "MISSING", str(runtime.parent.parent) if runtime.is_file() else "~/.hindsight/coding-agents absent",
                "" if runtime.is_file() else "npx @vectorize-io/hindsight-coding-agents install claude-code")
            try:
                api = json.loads(hcfg.read_text(encoding="utf-8")).get("apiUrl", "")
            except ValueError:
                api = ""
            if api:
                add("hindsight server", "OK" if port_open(api) else "WARN", api + ("" if port_open(api) else " not reachable"),
                    "" if port_open(api) else "start the Hindsight server (Docker) or fix apiUrl; agents continue without memory")
            add("hindsight hooks", "OK" if "hindsight" in hooks else "WARN", "" if "hindsight" in hooks else "no Hindsight hook in .claude/settings.json",
                "" if "hindsight" in hooks else "python3 <plugin>/skills/start/scripts/scaffold.py --target . --name <project> --mode adopt --memory hindsight")
        else:
            add("hindsight", "WARN", "not wired (optional)", "/shipwright:start memory")
        # context-mode
        env = s.get("env", {})
        plugins = s.get("enabledPlugins", {})
        cm_cache = list((Path.home() / ".claude" / "plugins" / "cache" / "context-mode").glob("*/*")) if (Path.home() / ".claude" / "plugins" / "cache" / "context-mode").is_dir() else []
        if "CONTEXT_MODE_DIR" in env or plugins.get("context-mode@context-mode"):
            add("context-mode", "OK" if cm_cache else "WARN", "plugin cached" if cm_cache else "configured but the plugin is not installed",
                "" if cm_cache else "claude plugin marketplace add mksglu/context-mode && claude plugin install context-mode@context-mode")
        else:
            add("context-mode", "WARN", "not enabled (optional)", "/shipwright:start context")
        # kit hooks (plugin or project)
        add("kit guards", "OK" if ("skill_guard" in hooks or "agent_guard" in hooks) else "WARN",
            "project hooks present" if ("skill_guard" in hooks) else "no project guard hooks — fine when the shipwright plugin is enabled (its hooks apply)", "")
        # ignore files
        gi = (root / ".gitignore").read_text(encoding="utf-8", errors="replace") if (root / ".gitignore").is_file() else ""
        for line in ("/.hindsight/logs/", "/.context-mode/"):
            if (line == "/.hindsight/logs/" and hcfg.is_file()) or (line == "/.context-mode/" and "CONTEXT_MODE_DIR" in env):
                add(f".gitignore {line}", "OK" if line in gi else "WARN", "" if line in gi else "missing", "" if line in gi else f"append `{line}` to .gitignore")

    # mobile tooling (only informative)
    for tool, what in (("xcrun", "Xcode command line tools (iOS simulators)"), ("adb", "Android platform-tools (emulators)"),
                       ("flutter", "Flutter SDK"), ("dotnet", ".NET SDK"), ("magick", "ImageMagick (contact sheets)"),
                       ("montage", "ImageMagick montage (contact sheets)"), ("ffmpeg", "ffmpeg (recordings, contact-sheet fallback)")):
        add(tool, "OK" if shutil.which(tool) else "WARN", what if shutil.which(tool) else f"{what} not found (needed only if the project uses it)", "")

    if "--json" in a:
        print(json.dumps(checks, indent=2))
        return 0
    width = max(len(c["check"]) for c in checks)
    for c in checks:
        line = f"{c['state']:<8}{c['check']:<{width}}  {c['detail']}"
        if c["fix"]:
            line += f"\n        → {c['fix']}"
        print(line)
    missing = sum(1 for c in checks if c["state"] == "MISSING")
    warn = sum(1 for c in checks if c["state"] == "WARN")
    print(f"\n{len(checks)} checks: {missing} missing, {warn} warnings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
