#!/usr/bin/env python3
"""Balance: cost per task against the backlog, grouped by feature or priority, with totals.

Reads the same Claude Code transcripts as token_usage.py (one price table, one attribution
rule) and joins them with tasks/index.json. Groups come from tasks/features.json when it
exists (planner-maintained: {"groups": [{"id", "title", "tasks": [...]}]}), otherwise from
priority bands. Optional budget lines come from shipwright.json -> "budget".

Usage: python3 balance.py [--by feature|priority] [--status done,ready,...] [--top N]
                          [--json] [--summary] [--quiet] [--root <workspace>]
Writes docs/BALANCE.md (unless --summary/--json) and prints the report. Outside a workspace
it exits 0 silently, so it is safe in hooks.
"""
import json
import os
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import token_usage  # noqa: E402  (same folder; shares PRICES, read_usage, cost, TASK_LINE)

STATUS_ORDER = ["in_progress", "ready", "blocked", "planned", "done", "superseded"]


def arg(name, default=None):
    a = sys.argv[1:]
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else default


def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def per_task_costs(root):
    """{task_id: usd} from the transcripts (same attribution as token_usage.py), plus the
    orchestration/unattributed buckets and the number of runs per task."""
    project_dir = Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(root))
    overrides = load_json(root / "tasks" / "token-attribution.json", {})
    usd, runs = defaultdict(float), defaultdict(int)
    if not project_dir.is_dir():
        return usd, runs
    for main_log in project_dir.glob("*.jsonl"):
        sid = main_log.stem
        logs = [(main_log, "main", sid)]
        for sub in (project_dir / sid / "subagents").glob("agent-*.jsonl"):
            logs.append((sub, "agent", sub.stem.removeprefix("agent-")))
        for path, kind, rid in logs:
            totals, prompt, _, _ = token_usage.read_usage(path)
            if not totals:
                continue
            if rid in overrides:
                tasks = [overrides[rid]] if isinstance(overrides[rid], str) else list(overrides[rid])
            elif kind == "main":
                tasks = ["orchestration"]
            else:
                m = token_usage.TASK_LINE.search(prompt[:500])
                tasks = re.findall(r"TASK-\d{4}", m.group(1)) if m else ["unattributed"]
            total = sum((token_usage.cost(model, t) or 0) for model, t in totals.items())
            for task in tasks:
                usd[task] += total / len(tasks)
                runs[task] += 1
    return usd, runs


def groups_for(root, tasks, by):
    """Return (ordered list of (group_id, title), {task_id: group_id})."""
    mapping, order = {}, []
    if by == "feature":
        feats = load_json(root / "tasks" / "features.json", {})
        for g in feats.get("groups", []) if isinstance(feats, dict) else []:
            gid, title = g.get("id", "?"), g.get("title", g.get("id", "?"))
            order.append((gid, title))
            for tid in g.get("tasks", []):
                mapping.setdefault(tid, gid)
        if order:
            order.append(("other", "Other (not in tasks/features.json)"))
            for t in tasks:
                mapping.setdefault(t["id"], "other")
            return order, mapping
        by = "priority"  # no feature file: fall back
    bands = sorted({(t.get("priority", 0) // 10) * 10 for t in tasks})
    for b in bands:
        order.append((f"p{b:03d}", f"Priority {b}–{b + 9}"))
    for t in tasks:
        mapping[t["id"]] = f"p{(t.get('priority', 0) // 10) * 10:03d}"
    return order, mapping


def fmt_usd(v):
    return f"${v:,.2f}"


def build(root, by, status_filter, top):
    index = load_json(root / "tasks" / "index.json", {"tasks": []})
    tasks = [t for t in index.get("tasks", []) if isinstance(t, dict)]
    usd, runs = per_task_costs(root)
    config = load_json(root / "shipwright.json", None) or load_json(root / "delivery-kit.json", {})
    budget = (config or {}).get("budget") or {}
    order, mapping = groups_for(root, tasks, by)

    task_rows = []
    for t in tasks:
        if status_filter and t.get("status") not in status_filter:
            continue
        task_rows.append({
            "id": t["id"], "title": t.get("title", ""), "status": t.get("status", "?"),
            "verification": t.get("verification", ""), "priority": t.get("priority", 0),
            "owner": t.get("owner", ""), "group": mapping.get(t["id"], "other"),
            "usd": round(usd.get(t["id"], 0.0), 2), "runs": runs.get(t["id"], 0),
        })

    # statistics
    total_tasks = sum(usd[k] for k in usd if k.startswith("TASK-"))
    orchestration = usd.get("orchestration", 0.0)
    unattributed = usd.get("unattributed", 0.0)
    grand = total_tasks + orchestration + unattributed
    by_status = defaultdict(lambda: {"count": 0, "usd": 0.0})
    for r in task_rows:
        by_status[r["status"]]["count"] += 1
        by_status[r["status"]]["usd"] += r["usd"]
    done_costs = [r["usd"] for r in task_rows if r["status"] == "done" and r["usd"] > 0]
    remaining = [r for r in task_rows if r["status"] in ("planned", "ready", "blocked", "in_progress")]
    avg_done = statistics.mean(done_costs) if done_costs else 0.0
    median_done = statistics.median(done_costs) if done_costs else 0.0
    forecast = avg_done * len(remaining) if done_costs else None
    groups_out = []
    for gid, title in order:
        rows = [r for r in task_rows if r["group"] == gid]
        if not rows:
            continue
        rows.sort(key=lambda r: (STATUS_ORDER.index(r["status"]) if r["status"] in STATUS_ORDER else 99, r["priority"], r["id"]))
        groups_out.append({"id": gid, "title": title, "usd": round(sum(r["usd"] for r in rows), 2),
                           "count": len(rows), "done": sum(1 for r in rows if r["status"] == "done"), "tasks": rows})
    top_rows = sorted(task_rows, key=lambda r: -r["usd"])[:top]
    return {
        "generated": f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC", "by": by if order and order[0][0] != "p000" or by == "priority" else by,
        "grand_usd": round(grand, 2), "tasks_usd": round(total_tasks, 2),
        "orchestration_usd": round(orchestration, 2), "unattributed_usd": round(unattributed, 2),
        "task_count": len(tasks), "by_status": {k: {"count": v["count"], "usd": round(v["usd"], 2)} for k, v in by_status.items()},
        "avg_done_usd": round(avg_done, 2), "median_done_usd": round(median_done, 2),
        "max_task": (top_rows[0]["id"] if top_rows else None), "max_task_usd": (top_rows[0]["usd"] if top_rows else 0.0),
        "remaining_tasks": len(remaining), "forecast_remaining_usd": (round(forecast, 2) if forecast is not None else None),
        "budget": budget, "groups": groups_out, "top": top_rows,
    }


def budget_lines(b, rep):
    out = []
    total = b.get("total_usd")
    if total:
        pct = rep["grand_usd"] / total * 100 if total else 0
        left = total - rep["grand_usd"]
        flag = " ⚠️" if pct >= float(b.get("warn_at", 0.8)) * 100 else ""
        out.append(f"Budget: {fmt_usd(rep['grand_usd'])} of {fmt_usd(total)} spent ({pct:.0f}%), {fmt_usd(left)} left{flag}")
        if rep["forecast_remaining_usd"] is not None:
            over = rep["grand_usd"] + rep["forecast_remaining_usd"] - total
            out.append(f"Forecast at the current average: {fmt_usd(rep['grand_usd'] + rep['forecast_remaining_usd'])} total → "
                       + (f"over budget by {fmt_usd(over)}" if over > 0 else f"within budget by {fmt_usd(-over)}"))
    per_task = b.get("per_task_usd")
    if per_task:
        over = [r for r in rep["top"] if r["usd"] > per_task]
        if over:
            out.append(f"Tasks above the per-task budget ({fmt_usd(per_task)}): " + ", ".join(f"{r['id']} {fmt_usd(r['usd'])}" for r in over))
    return out


def summary_line(rep):
    s = rep["by_status"]
    parts = [f"{k} {v['count']}" for k, v in sorted(s.items(), key=lambda kv: STATUS_ORDER.index(kv[0]) if kv[0] in STATUS_ORDER else 99)]
    line = f"Balance: {fmt_usd(rep['grand_usd'])} total ({fmt_usd(rep['tasks_usd'])} on tasks, {fmt_usd(rep['orchestration_usd'])} orchestration); " \
           f"{rep['task_count']} tasks — " + ", ".join(parts) + f"; avg done task {fmt_usd(rep['avg_done_usd'])}"
    if rep["forecast_remaining_usd"] is not None:
        line += f"; forecast for the {rep['remaining_tasks']} remaining ≈ {fmt_usd(rep['forecast_remaining_usd'])}"
    bl = budget_lines(rep["budget"], rep)
    return line + (" | " + bl[0] if bl else "")


def markdown(rep):
    L = ["# Balance — cost per task", f"Generated by the Shipwright `balance.py` on {rep['generated']}; do not edit by hand. "
         "USD is API list-price equivalent (same table as docs/TOKEN-COSTS.md); on a subscription it is an estimate.", "",
         "## Totals", f"- **Total spent: {fmt_usd(rep['grand_usd'])}** — tasks {fmt_usd(rep['tasks_usd'])}, orchestration (main session) "
         f"{fmt_usd(rep['orchestration_usd'])}, unattributed {fmt_usd(rep['unattributed_usd'])}",
         f"- Tasks: {rep['task_count']} — " + ", ".join(f"{k} {v['count']} ({fmt_usd(v['usd'])})" for k, v in sorted(
             rep["by_status"].items(), key=lambda kv: STATUS_ORDER.index(kv[0]) if kv[0] in STATUS_ORDER else 99)),
         f"- Done task cost: average {fmt_usd(rep['avg_done_usd'])}, median {fmt_usd(rep['median_done_usd'])}, "
         f"most expensive {rep['max_task'] or '—'} {fmt_usd(rep['max_task_usd'])}"]
    if rep["forecast_remaining_usd"] is not None:
        L.append(f"- Forecast: {rep['remaining_tasks']} remaining tasks × average ≈ {fmt_usd(rep['forecast_remaining_usd'])}")
    L += [f"- {x}" for x in budget_lines(rep["budget"], rep)]
    L += ["", f"## By {rep['by']}", "| Group | Tasks | Done | USD |", "|---|---:|---:|---:|"]
    for g in rep["groups"]:
        L.append(f"| {g['title']} | {g['count']} | {g['done']} | {fmt_usd(g['usd'])} |")
    for g in rep["groups"]:
        L += ["", f"### {g['title']} — {fmt_usd(g['usd'])}", "| Task | Status | Pri | Runs | USD | Title |", "|---|---|---:|---:|---:|---|"]
        for r in g["tasks"]:
            st = r["status"] + (f" / {r['verification']}" if r["verification"] else "")
            L.append(f"| {r['id']} | {st} | {r['priority']} | {r['runs']} | {fmt_usd(r['usd'])} | {r['title'][:90]} |")
    L += ["", "## Most expensive tasks", "| Task | Status | USD | Title |", "|---|---|---:|---|"]
    for r in rep["top"]:
        L.append(f"| {r['id']} | {r['status']} | {fmt_usd(r['usd'])} | {r['title'][:90]} |")
    return "\n".join(L) + "\n"


def main():
    a = sys.argv[1:]
    quiet = "--quiet" in a
    root = token_usage.find_root()
    if root is None:
        if not quiet:
            print("Not inside a Shipwright workspace (tasks/index.json + docs/); nothing to balance.")
        return 0
    by = arg("--by", "feature")
    status_filter = set(arg("--status", "").split(",")) - {""}
    top = int(arg("--top", "10"))
    rep = build(root, by, status_filter, top)
    if "--json" in a:
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0
    if "--summary" in a:
        print(summary_line(rep))
        return 0
    out = root / "docs" / "BALANCE.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown(rep), encoding="utf-8")
    if not quiet:
        print(markdown(rep))
        print(f"Wrote {out.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
