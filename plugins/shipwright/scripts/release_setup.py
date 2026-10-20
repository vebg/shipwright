#!/usr/bin/env python3
"""Release setup: render scripts/release-tag.sh for this workspace from the reference script.

Reads `repos` from shipwright.json. The reference script handles the two-repository layout
(one shared product version tagged in both). With exactly two repositories it writes
scripts/release-tag.sh with their names/paths; with one repository it writes a single-repo
variant note instead of a script; with more it stops and explains. Never overwrites.

Usage: python3 release_setup.py [--root <workspace>] [--dry-run]
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_common import find_workspace, load_config  # noqa: E402

REF = Path(__file__).resolve().parents[1] / "skills" / "release" / "references" / "release-tag.example.sh"


def main():
    a = sys.argv[1:]
    root = Path(a[a.index("--root") + 1]).resolve() if "--root" in a else find_workspace(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
    if root is None:
        print("Not inside a Shipwright workspace.")
        return 1
    repos = load_config(root).get("repos") or []
    out = root / "scripts" / "release-tag.sh"
    if out.exists():
        print(f"{out} exists — not overwritten.")
        return 0
    if len(repos) == 2:
        text = REF.read_text(encoding="utf-8")
        text = text.replace("platform-repo", repos[0]["path"]).replace("apps-repo", repos[1]["path"])
        text = text.replace("RELEASE_PLATFORMS_REPO", f"RELEASE_{repos[0]['name'].upper().replace('-', '_')}_REPO") \
                   .replace("RELEASE_APPS_REPO", f"RELEASE_{repos[1]['name'].upper().replace('-', '_')}_REPO")
        if "--dry-run" in a:
            print(f"would write {out} for {repos[0]['path']} + {repos[1]['path']}")
            return 0
        out.write_text(text, encoding="utf-8")
        out.chmod(0o755)
        print(f"wrote {out} for repositories {repos[0]['path']} and {repos[1]['path']} (local annotated tags only, never pushes)")
        return 0
    if len(repos) <= 1:
        print("Single repository: tag with `git tag -a vX.Y.Z -m \"TASK-NNNN\" <commit>` on the newest commit naming the task and write "
              "docs/releases/vX.Y.Z.md with /shipwright:release note. The two-repository script is not needed.")
        return 0
    print(f"{len(repos)} repositories: the reference script tags two; extend it per repository or tag by hand following the same rules.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
