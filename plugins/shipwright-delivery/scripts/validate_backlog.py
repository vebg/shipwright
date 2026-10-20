#!/usr/bin/env python3
"""Validate the Shipwright task index and dependency DAG; standard library only.

Usage: python3 validate_backlog.py [--root <workspace>]
Default root: the nearest Shipwright workspace above the current directory, else the
directory above this script (when the script was copied into <workspace>/scripts/).
Exit 1 with one ERROR line per problem; exit 0 with a one-line confirmation.
"""
from pathlib import Path
import json
import re
import sys

STATES = {'planned', 'ready', 'in_progress', 'blocked', 'done', 'superseded'}
OWNERS = {'planner', 'fullstack-developer'}
VERIFICATION = {'pending', 'passed', 'failed'}
SECTIONS = ['Requirement links', 'Outcome', 'Scope', 'Acceptance criteria',
            'Implementation notes', 'Verification', 'Completion evidence']


def find_root():
    args = sys.argv[1:]
    if '--root' in args:
        return Path(args[args.index('--root') + 1]).resolve()
    p = Path.cwd().resolve()
    for d in (p, *p.parents):
        if (d / 'tasks' / 'index.json').is_file():
            return d
    return Path(__file__).resolve().parents[1]


def validate(root):
    errors = []
    try:
        data = json.loads((root / 'tasks/index.json').read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        return [f'Cannot read task index: {exc}']
    if not isinstance(data, dict) or data.get('schema_version') != 1 or not isinstance(data.get('tasks'), list):
        return ['Expected schema_version 1 and a tasks array']
    tasks = data['tasks']
    ids = {}
    paths = set()
    for t in tasks:
        if not isinstance(t, dict):
            errors.append('Every task must be an object')
            continue
        tid = t.get('id')
        if not isinstance(tid, str) or not re.fullmatch(r'TASK-\d{4,}', tid):
            errors.append(f'Invalid task ID: {tid!r}')
            continue
        if tid in ids:
            errors.append(f'Duplicate ID: {tid}')
        ids[tid] = t
        if not isinstance(t.get('title'), str) or not t['title'].strip():
            errors.append(f'{tid}: missing title')
        if t.get('owner') not in OWNERS:
            errors.append(f'{tid}: invalid owner (allowed: {", ".join(sorted(OWNERS))})')
        if t.get('status') not in STATES:
            errors.append(f'{tid}: invalid status')
        if 'verification' in t and t['verification'] not in VERIFICATION:
            errors.append(f'{tid}: invalid verification value')
        if type(t.get('priority')) is not int or t['priority'] < 0:
            errors.append(f'{tid}: priority must be nonnegative integer')
        deps = t.get('depends_on')
        if not isinstance(deps, list) or any(not isinstance(x, str) for x in deps):
            errors.append(f'{tid}: depends_on must contain IDs')
            deps = []
        if len(set(deps)) != len(deps):
            errors.append(f'{tid}: duplicate dependency')
        if t.get('status') == 'blocked' and not t.get('blocker'):
            errors.append(f'{tid}: missing blocker')
        fp = t.get('file')
        if not isinstance(fp, str):
            errors.append(f'{tid}: missing file')
            continue
        path = (root / fp).resolve()
        if path in paths:
            errors.append(f'{tid}: duplicate task file')
        paths.add(path)
        if not path.is_relative_to((root / 'tasks').resolve()):
            errors.append(f'{tid}: task file outside tasks directory')
            continue
        if not path.is_file():
            errors.append(f'{tid}: missing task file')
            continue
        body = path.read_text(encoding='utf-8')
        if not body.startswith('# ' + tid + ' '):
            errors.append(f'{tid}: title ID mismatch')
        for s in SECTIONS:
            if '## ' + s not in body:
                errors.append(f'{tid}: missing section {s}')
        if t.get('status') == 'done':
            evidence = t.get('evidence')
            if not isinstance(evidence, list) or not evidence:
                errors.append(f'{tid}: done requires evidence')
                continue
            for ep in evidence:
                if not isinstance(ep, str):
                    errors.append(f'{tid}: invalid evidence path')
                    continue
                p = (root / ep).resolve()
                if not p.is_relative_to(root.resolve()) or not p.is_file() or not p.stat().st_size:
                    errors.append(f'{tid}: missing/invalid evidence {ep}')
    visiting, visited = set(), set()

    def walk(tid):
        if tid in visiting:
            errors.append(f'Dependency cycle at {tid}')
            return
        if tid in visited:
            return
        visiting.add(tid)
        deps = ids[tid].get('depends_on', [])
        if not isinstance(deps, list):
            deps = []
        for dep in deps:
            if not isinstance(dep, str):
                continue
            if dep not in ids:
                errors.append(f'{tid}: unknown dependency {dep}')
                continue
            if ids[tid].get('status') in {'ready', 'in_progress', 'done'} and ids[dep].get('status') != 'done':
                errors.append(f'{tid}: dependency {dep} is not done')
            walk(dep)
        visiting.remove(tid)
        visited.add(tid)

    for tid in ids:
        walk(tid)
    return errors


if __name__ == '__main__':
    root = find_root()
    errors = validate(root)
    if errors:
        print('\n'.join('ERROR: ' + e for e in errors))
        sys.exit(1)
    print(f'Backlog valid ({root}). Structure only; application behavior and evidence truth require separate checks.')
