#!/usr/bin/env python3
"""Copy the engine, the sprite packs and the playground's runtime from PyIDE.

    python3 vendor.py                    # from ~/pyide
    python3 vendor.py --from ~/pyide
    python3 vendor.py --check            # verify, change nothing

WHY THIS SITE VENDORS RATHER THAN LINKS

The playground here runs the same engine, on the same sprite packs, through
the same four JavaScript modules as PyIDE. It could fetch them from
pyide.onrender.com and stay in step for free. It does not, for two reasons.

A static site with a cross-origin dependency is not a static site. It is a
static site plus somebody else's uptime, somebody else's CORS headers, and a
second hostname a school network can block independently of the first. The
whole point of this being a Render Static Site is that there is nothing to be
down.

And the engine a reader is trying out should be the engine the page around it
documents. Pointing at a live PyIDE means the playground silently changes
under the API reference whenever PyIDE is deployed.

WHAT IS COPIED, AND WHAT IS NOT

Copied byte for byte, so `--check` can compare hashes:

    static/py/kaypy_bundle.json  ->  dist/engine/kaypy_bundle.json
    static/py/kaypy.json         ->  dist/engine/kaypy.json   (the version stamp)
    static/assets/               ->  dist/assets/
    static/{game,runtime,export,sprites,complete}.js -> dist/play/

Not copied: app.js, account.js, notes.js, demo.js, zip.js. Those are the
editor shell, sign-in, the notes pane, the demo viewer and the multi-file
download — PyIDE's product, not the engine. The playground has its own shell
in play/, with no accounts in it.

NOTHING IS REWRITTEN ON THE WAY THROUGH

The four modules fetch the engine and the sprite packs by URL, and PyIDE's
URLs are not this site's. The obvious fix is to rewrite those constants while
copying. Do not: a regex that edits somebody else's source is a regex that
quietly stops matching the day they reformat the line, and what it produces
then is a 404 inside a game engine — which surfaces as a student pressing Run
and getting nothing, with no error anybody will connect to a vendoring script.

So the modules read `window.PyIDEPaths` if the page sets one, and play.html
sets it. The copies here are identical to PyIDE's, and `--check` proves it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import sys
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
DIST = HERE / "dist"
STAMP = HERE / "vendored.json"

# The modules the playground needs, and what each is for. Anything not on this
# list is PyIDE's own product and stays there.
MODULES = {
    "runtime.js": "booting Pyodide, piping print() to the page, trimming tracebacks",
    "game.js": "loading the engine into Pyodide, the canvas, run and stop",
    "export.js": "building the one-file download from kaypy's own template",
    "sprites.js": "the sprite picker's insert helpers",
    "complete.js": "name completion for the editor",
    "zip.js": "a zip writer with no dependencies, for the download",
}

# PyIDE's stylesheet, vendored for the same reason as the modules: the
# playground is a full-page PyIDE without the school in it, and an imitation
# of a look drifts from it. It carries its own complete palette, so the
# playground does NOT load site.css — the two both define --bg and --line.
STYLES = {
    "style.css": "PyIDE's chrome: the bar, the panes, the sprite grid",
}


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def sources(pyide: pathlib.Path):
    """Every file to copy, as (source, destination-relative-to-dist)."""
    static = pyide / "static"
    yield static / "py" / "kaypy_bundle.json", pathlib.Path("engine/kaypy_bundle.json")
    yield static / "py" / "kaypy.json", pathlib.Path("engine/kaypy.json")
    for name in list(MODULES) + list(STYLES):
        yield static / name, pathlib.Path("play") / name
    assets = static / "assets"
    for item in sorted(assets.rglob("*")):
        if item.is_file() and "__pycache__" not in item.parts:
            yield item, pathlib.Path("assets") / item.relative_to(assets)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", default=os.path.expanduser("~/pyide"),
                    help="the PyIDE checkout to copy from (default ~/pyide)")
    ap.add_argument("--check", action="store_true",
                    help="compare what is here against the source; copy nothing")
    args = ap.parse_args()

    pyide = pathlib.Path(args.src).expanduser().resolve()
    if not (pyide / "static" / "py" / "kaypy_bundle.json").is_file():
        sys.exit("No PyIDE at %s — pass --from.\n"
                 "  (looked for static/py/kaypy_bundle.json)" % pyide)

    planned = list(sources(pyide))
    missing = [s for s, _ in planned if not s.is_file()]
    if missing:
        sys.exit("PyIDE is missing files this site needs:\n" +
                 "\n".join("  %s" % m.relative_to(pyide) for m in missing))

    if args.check:
        return check(planned)

    copied = bytes_ = 0
    files = {}
    for source, rel in planned:
        target = DIST / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        files[str(rel)] = digest(source)
        copied += 1
        bytes_ += source.stat().st_size

    engine = json.loads((DIST / "engine" / "kaypy.json").read_text())
    STAMP.write_text(json.dumps({
        "kaypy": engine.get("version"),
        "kaypy_commit": engine.get("commit"),
        "from": str(pyide),
        "vendored_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "files": files,
    }, indent=1) + "\n")

    print("kaypy %s (%s) from %s"
          % (engine.get("version"), engine.get("commit"), pyide))
    print("  %d files, %.0f KB into dist/" % (copied, bytes_ / 1024))
    for name, why in list(MODULES.items()) + list(STYLES.items()):
        print("    play/%-12s %s" % (name, why))
    print("  vendored.json records a hash of each; `--check` compares them")
    if (engine.get("commit") or "").endswith("+dirty"):
        print("\n  NOTE: that engine was vendored into PyIDE from a kaypy")
        print("        working tree with uncommitted changes. Fine to test")
        print("        with, not something to deploy.")
    return 0


def check(planned) -> int:
    """Has anything here drifted from PyIDE, or PyIDE from here?"""
    if not STAMP.is_file():
        print("  no vendored.json — run vendor.py first")
        return 1
    recorded = json.loads(STAMP.read_text())["files"]

    stale, absent, unexpected = [], [], []
    for source, rel in planned:
        key = str(rel)
        here = DIST / rel
        if not here.is_file():
            absent.append(key)
        elif digest(here) != digest(source):
            stale.append(key)
        elif recorded.get(key) != digest(here):
            # The file matches PyIDE but not what was written down, which
            # means it was copied by something other than this script.
            unexpected.append(key)

    for label, names in (("missing from dist/", absent),
                         ("differs from PyIDE", stale),
                         ("not what vendored.json recorded", unexpected)):
        if names:
            print("  %s (%d):" % (label, len(names)))
            for n in names[:8]:
                print("      %s" % n)
            if len(names) > 8:
                print("      ... and %d more" % (len(names) - 8))

    if absent or stale or unexpected:
        print("\n  run: python3 vendor.py")
        return 1
    print("  %d vendored files, all identical to PyIDE" % len(planned))
    return 0


if __name__ == "__main__":
    sys.exit(main())
