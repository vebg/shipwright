#!/usr/bin/env python3
"""Build docs/TOKEN-COSTS.md from the Claude Code transcripts of a Shipwright workspace.

Reads ~/.claude/projects/<workspace-slug>/*.jsonl (main conversations) and
<session>/subagents/agent-*.jsonl (agents), dedupes streamed entries by message
id, and prices usage with the table below (API list prices, USD per 1M tokens).
Runs are attributed to a task by, in order: tasks/token-attribution.json
(agentId or sessionId -> "TASK-XXXX"), a "Task: TASK-XXXX" line at the start of
the agent prompt, else "unattributed". Main conversations are "orchestration".

Usage: python3 token_usage.py [--quiet] [--root <workspace>]
Without --root the nearest workspace above the current directory (or
$CLAUDE_PROJECT_DIR) is used. Outside a workspace the script exits 0 silently, so it
is safe as a Stop/SubagentStop hook.
"""
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# USD per 1M tokens: input, output, cache write 5m, cache write 1h, cache read.
# Checked 2026-09-27. Cache-write prices assume the standard 1.25x (5m) / 2x (1h)
# input multipliers; update when Anthropic changes prices or adds models.
PRICES = {
    "claude-opus-5-5": (4.00, 20.00, 5.00, 8.00, 0.20),
    "claude-opus-5": (5.00, 25.00, 6.25, 10.00, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00, 2.50, 4.00, 0.20),
    "claude-sonnet-5": (2.00, 10.00, 2.50, 4.00, 0.20),
    "claude-haiku-5-5": (1.00, 5.00, 1.25, 2.00, 0.10),
    "claude-haiku-4-5": (1.00, 5.00, 1.25, 2.00, 0.10),
    "claude-fable-5-1": (10.00, 50.00, 12.50, 20.00, 0.25),
}
TASK_LINE = re.compile(r"^\s*Task:\s*((?:TASK-\d{4}[,\s]*)+)", re.M)


def find_root():
    args = sys.argv[1:]
    if "--root" in args:
        return Path(args[args.index("--root") + 1]).resolve()
    start = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd()).resolve()
    for d in (start, *start.parents):
        if (d / "tasks" / "index.json").is_file() and (d / "docs").is_dir():
            return d
    return None


def price_key(model):
    for key in sorted(PRICES, key=len, reverse=True):
        if model and model.startswith(key):
            return key
    return None


def read_usage(path):
    by_msg, prompt, stamps = {}, None, []
    for line in path.open(encoding="utf-8"):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("timestamp"):
            stamps.append(d["timestamp"])
        msg = d.get("message")
        if not isinstance(msg, dict):
            continue
        if prompt is None and d.get("type") == "user":
            c = msg.get("content")
            prompt = c if isinstance(c, str) else " ".join(
                b.get("text", "") for b in c or [] if isinstance(b, dict))
        if d.get("type") == "assistant" and msg.get("usage"):
            by_msg[msg.get("id") or d.get("uuid")] = (msg.get("model"), msg["usage"])
    totals = defaultdict(lambda: defaultdict(int))
    for model, u in by_msg.values():
        if model == "<synthetic>":
            continue
        t = totals[model]
        cc = u.get("cache_creation") or {}
        w1h = cc.get("ephemeral_1h_input_tokens", 0)
        t["input"] += u.get("input_tokens", 0)
        t["output"] += u.get("output_tokens", 0)
        t["cache_write_1h"] += w1h
        t["cache_write_5m"] += u.get("cache_creation_input_tokens", 0) - w1h
        t["cache_read"] += u.get("cache_read_input_tokens", 0)
        t["requests"] += 1
    return totals, prompt or "", (min(stamps) if stamps else ""), (max(stamps) if stamps else "")


def cost(model, t):
    key = price_key(model)
    if not key:
        return None
    p = PRICES[key]
    return (t["input"] * p[0] + t["output"] * p[1] + t["cache_write_5m"] * p[2]
            + t["cache_write_1h"] * p[3] + t["cache_read"] * p[4]) / 1_000_000


def main():
    quiet = "--quiet" in sys.argv
    root = find_root()
    if root is None:
        if not quiet:
            print("Not inside a Shipwright workspace (tasks/index.json + docs/); nothing written.")
        return 0
    project_dir = Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(root))
    out = root / "docs" / "TOKEN-COSTS.md"
    attribution = root / "tasks" / "token-attribution.json"
    if not project_dir.is_dir():
        if not quiet:
            print(f"No transcripts at {project_dir}")
        return 0
    overrides = json.loads(attribution.read_text(encoding="utf-8")) if attribution.exists() else {}
    runs = []
    for main_log in project_dir.glob("*.jsonl"):
        sid = main_log.stem
        logs = [(main_log, "main", sid, None)]
        for sub in (project_dir / sid / "subagents").glob("agent-*.jsonl"):
            aid = sub.stem.removeprefix("agent-")
            meta = sub.with_suffix(".meta.json")
            info = json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else {}
            logs.append((sub, info.get("agentType", "agent"), aid, info.get("description")))
        for path, agent, rid, desc in logs:
            totals, prompt, start, end = read_usage(path)
            if not totals:
                continue
            if rid in overrides:
                tasks = [overrides[rid]] if isinstance(overrides[rid], str) else overrides[rid]
            elif agent == "main":
                tasks = ["orchestration"]
            else:
                m = TASK_LINE.search(prompt[:500])
                tasks = re.findall(r"TASK-\d{4}", m.group(1)) if m else ["unattributed"]
            for model, t in totals.items():
                runs.append(dict(session=sid[:8], run=rid[:12], agent=agent, desc=desc or "",
                                 tasks=tasks, model=model, start=start[:16].replace("T", " "),
                                 end=end[:16].replace("T", " "), t=t, usd=cost(model, t)))
    runs.sort(key=lambda r: r["start"])

    def fmt(n):
        return f"{n:,}"

    def usd(v):
        return "n/a" if v is None else f"${v:,.2f}"

    per_task = defaultdict(lambda: [0, 0.0])
    for r in runs:
        share = 1 / len(r["tasks"])
        tokens = sum(r["t"][k] for k in ("input", "output", "cache_write_5m", "cache_write_1h", "cache_read"))
        for task in r["tasks"]:
            per_task[task][0] += tokens * share
            per_task[task][1] += (r["usd"] or 0) * share
    grand = sum(v[1] for v in per_task.values())

    lines = [
        "# Token usage and cost",
        f"Generated by the Shipwright `token_usage.py` on {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC; do not edit by hand.",
        "USD is API list-price equivalent (see PRICES in the script); on a Claude subscription it is an estimate, not a bill.",
        "Attribution: `tasks/token-attribution.json` overrides, else a `Task: TASK-XXXX` first line in the agent prompt. "
        "Runs naming several tasks are split evenly. Main-conversation turns count as orchestration.",
        "",
        "## By task",
        "| Task | Tokens | USD |",
        "|---|---:|---:|",
    ]
    for task in sorted(per_task):
        lines.append(f"| {task} | {fmt(round(per_task[task][0]))} | {usd(per_task[task][1])} |")
    lines += [f"| **Total** | | **{usd(grand)}** |", "", "## By run",
              "| Start (UTC) | Session | Agent | Run | Tasks | Model | Requests | Input | Output | Cache write | Cache read | USD |",
              "|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in runs:
        t = r["t"]
        label = r["agent"] + (f" — {r['desc']}" if r["desc"] else "")
        lines.append(
            f"| {r['start']} | {r['session']} | {label} | {r['run']} | {', '.join(r['tasks'])} | {r['model']} | "
            f"{t['requests']} | {fmt(t['input'])} | {fmt(t['output'])} | "
            f"{fmt(t['cache_write_5m'] + t['cache_write_1h'])} | {fmt(t['cache_read'])} | {usd(r['usd'])} |")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not quiet:
        print(f"Wrote {out.relative_to(root)}: {len(runs)} runs, total {usd(grand)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
