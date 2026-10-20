#!/usr/bin/env python3
"""Owner checklist: what the owner must do to release — gathered, not invented.

Collects, from the workspace:
- docs/releases/vX.Y.Z.md notes newer than the last deployed version (--since vX.Y.Z or the
  "deployed" field of shipwright.json → project), with their tasks;
- lines in those notes and in docs/evidence/<task>.md "For the owner" sections that name
  environment variables (Key__Sub=... or KEY=...), migrations, store steps;
- docs/QUESTIONS.md section 1 (open questions) and docs/HANDOFF.md "Waiting on the owner".
Prints Markdown the planner edits into the final checklist. Standard library only; read-only.

Usage: python3 owner_checklist.py [--since vX.Y.Z] [--root <workspace>]
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_common import find_workspace  # noqa: E402

ENV_RE = re.compile(r"`?([A-Z][A-Za-z0-9]+(?:__[A-Za-z0-9]+)+=[^`\s]*|[A-Z][A-Z0-9_]{3,}=[^`\s]*)`?")
MIG_RE = re.compile(r"migration[s]?\b[^\n]*", re.I)
STORE_RE = re.compile(r"(App Store|Google Play|Play Console|TestFlight|store build|data.safety|listing)[^\n]*", re.I)


def vtuple(v):
    m = re.match(r"v?(\d+)\.(\d+)\.(\d+)", v or "")
    return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)


def section(text, heading_re):
    m = re.search(heading_re, text, re.M)
    if not m:
        return ""
    rest = text[m.end():]
    n = re.search(r"^## ", rest, re.M)
    return rest[: n.start()] if n else rest


def main():
    a = sys.argv[1:]
    root = Path(a[a.index("--root") + 1]).resolve() if "--root" in a else find_workspace(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
    if root is None:
        print("Not inside a Shipwright workspace.")
        return 0
    since = a[a.index("--since") + 1] if "--since" in a else None
    if not since:
        try:
            cfg = json.loads((root / "shipwright.json").read_text(encoding="utf-8"))
            since = (cfg.get("project") or {}).get("deployed_version")
        except (OSError, ValueError):
            since = None
    notes = sorted((root / "docs" / "releases").glob("v*.md"), key=lambda p: vtuple(p.stem))
    newer = [p for p in notes if not since or vtuple(p.stem) > vtuple(since)]
    out = [f"# Owner checklist — generated from the workspace ({'since ' + since if since else 'all release notes'})",
           "Edit before sending: keep only what the owner must do; never add steps the notes do not support.", ""]
    out.append("## Versions to release" if newer else "## Versions to release\n- (no release note newer than the deployed version)")
    env_lines, mig_lines, store_lines, tasks = [], [], [], []
    for p in newer:
        txt = p.read_text(encoding="utf-8", errors="replace")
        ts = sorted(set(re.findall(r"TASK-\d{4}", txt)))
        tasks += ts
        first = next((l.strip("# ").strip() for l in txt.splitlines() if l.strip()), p.stem)
        out.append(f"- **{p.stem}** — {', '.join(ts) or 'no task id'} — {first[:120]}")
        env_lines += [(p.stem, m.group(1)) for m in ENV_RE.finditer(txt)]
        mig_lines += [(p.stem, m.group(0).strip()) for m in MIG_RE.finditer(txt)]
        store_lines += [(p.stem, m.group(0).strip()) for m in STORE_RE.finditer(txt)]
    # evidence "For the owner" sections of the released tasks
    for t in sorted(set(tasks)):
        ev = root / "docs" / "evidence" / f"{t}.md"
        if not ev.is_file():
            continue
        txt = ev.read_text(encoding="utf-8", errors="replace")
        sec = section(txt, r"^##+ .*For the owner.*$")
        if sec.strip():
            out.append(f"\n### {t} — \"For the owner\" (from docs/evidence/{t}.md)")
            out += [l for l in sec.strip().splitlines()[:40]]
        env_lines += [(t, m.group(1)) for m in ENV_RE.finditer(txt)]
    if env_lines:
        out += ["", "## Environment / configuration lines mentioned", "| Where | Line |", "|---|---|"]
        seen = set()
        for where, line in env_lines:
            if line not in seen:
                seen.add(line)
                out.append(f"| {where} | `{line}` |")
    if mig_lines:
        out += ["", "## Migrations mentioned"]
        out += [f"- {w}: {l[:160]}" for w, l in mig_lines]
    if store_lines:
        out += ["", "## Store steps mentioned"]
        out += [f"- {w}: {l[:160]}" for w, l in store_lines]
    q = root / "docs" / "QUESTIONS.md"
    if q.is_file():
        sec = section(q.read_text(encoding="utf-8", errors="replace"), r"^## 1\. Open questions.*$")
        rows = [l for l in sec.splitlines() if l.startswith("| ") and not l.startswith("| ID") and not l.startswith("|---")]
        if rows:
            out += ["", "## Open questions (docs/QUESTIONS.md §1)"] + rows[:30]
    h = root / "docs" / "HANDOFF.md"
    if h.is_file():
        sec = section(h.read_text(encoding="utf-8", errors="replace"), r"^## Waiting on the owner.*$")
        if sec.strip():
            out += ["", "## Waiting on the owner (docs/HANDOFF.md)"] + sec.strip().splitlines()[:30]
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
