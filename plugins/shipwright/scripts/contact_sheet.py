#!/usr/bin/env python3
"""Contact sheet: one labelled PNG from the screenshots of a task, for planner inspection.

Uses ImageMagick (`montage`/`magick`) when present, else ffmpeg's tile filter; never
re-encodes the originals. Standard library only on the Python side.

Usage:
  python3 contact_sheet.py <TASK-ID> [--surface <name>] [--cols 3] [--width 420]
                           [--root <workspace>] [--out <file.png>]
Reads docs/evidence/screenshots/<TASK-ID>/[<surface>/]*.png|jpg (sorted by name), labels
each tile with its file name (viewport/state are in the name by convention), writes
docs/evidence/screenshots/<TASK-ID>/contact-sheet[-<surface>].png and prints the path.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_common import find_workspace  # noqa: E402


def arg(name, default=None):
    a = sys.argv[1:]
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else default


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a:
        print(__doc__)
        return 2
    task = a[0]
    root = Path(arg("--root")).resolve() if arg("--root") else find_workspace(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
    if root is None:
        print("Not inside a Shipwright workspace.")
        return 1
    surface = arg("--surface")
    cols = int(arg("--cols", "3"))
    width = int(arg("--width", "420"))
    folder = root / "docs" / "evidence" / "screenshots" / task / (surface or "")
    files = sorted(p for p in folder.glob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp") and not p.name.startswith("contact-sheet"))
    if not files:
        print(f"No screenshots under {folder}")
        return 1
    out = Path(arg("--out")) if arg("--out") else folder / (f"contact-sheet-{surface}.png" if surface else "contact-sheet.png")
    if shutil.which("montage") or shutil.which("magick"):
        cmd = ["montage"] if shutil.which("montage") else ["magick", "montage"]
        cmd += ["-label", "%t", "-font", "Helvetica", "-pointsize", "14", "-tile", f"{cols}x", "-geometry", f"{width}x+8+8",
                "-background", "#111", "-fill", "#eee", *[str(p) for p in files], str(out)]
        tool = "ImageMagick"
    elif shutil.which("ffmpeg"):
        rows = -(-len(files) // cols)
        inputs = []
        for p in files:
            inputs += ["-i", str(p)]
        scale = ";".join(f"[{i}:v]scale={width}:-2,pad={width}:ih+24:0:24:0x111111,drawtext=text='{p.stem}':x=4:y=4:fontsize=14:fontcolor=white[v{i}]"
                         for i, p in enumerate(files))
        tiles = "".join(f"[v{i}]" for i in range(len(files)))
        cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex",
               f"{scale};{tiles}xstack=inputs={len(files)}:layout={ffmpeg_layout(len(files), cols, width)}:fill=0x111111[out]",
               "-map", "[out]", str(out)]
        tool = "ffmpeg"
    else:
        print("Neither ImageMagick (montage) nor ffmpeg is installed: brew install imagemagick  (or ffmpeg)")
        return 1
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"{tool} failed: {e.stderr.strip()[:400]}")
        return 1
    print(f"{out} ({len(files)} captures, {tool})")
    return 0


def ffmpeg_layout(n, cols, width):
    # xstack layout for same-width tiles of unknown height: use h0 references per row.
    cells = []
    for i in range(n):
        r, c = divmod(i, cols)
        x = "+".join(["0"] + [f"w{j}" for j in range(c)]) if c else "0"
        y = "+".join(["0"] + [f"h{j * cols}" for j in range(r)]) if r else "0"
        cells.append(f"{x}_{y}")
    return "|".join(cells)


if __name__ == "__main__":
    sys.exit(main())
