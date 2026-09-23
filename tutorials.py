#!/usr/bin/env python3
"""Build content/tutorials.md out of kaypy's examples/ folder.

    python3 tutorials.py                  # from ~/kaypy
    python3 tutorials.py --from ~/kaypy
    python3 tutorials.py --check          # verify, change nothing

WHY THE CODE ON THIS PAGE IS COPIED RATHER THAN WRITTEN

A tutorial page is worth exactly as much as the odds that the code on it
runs. Retyped into markdown, a program is correct on the day it is pasted and
slowly stops being correct afterwards: a name changes in the engine, the
example in the repository is fixed, and the copy on the website goes on
telling people to write the old thing. Nothing fails. The page still builds.

So the listings are read out of `examples/` at build time, which means the
code a reader copies is the file the project actually runs its own checks
against. If it breaks, it breaks where somebody will see it.

WHY EACH FEATURED EXAMPLE MUST HAVE A DOCSTRING

Its docstring is its description on this page. That is not a convenience: it
means the explanation lives next to the code it explains, and a person
changing the program has the paragraph about it on screen. A featured example
without one stops the build rather than getting a blank space or, worse, a
description invented here that nothing keeps honest.

WHAT IS FEATURED, AND WHAT IS LISTED

FEATURED are the complete games — read in full, source included. The thirteen
lesson programs are only LISTED, in a table, because the guide already walks
through each of them line by line; reprinting them here would be a second
copy of the guide with the teaching taken out.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import pathlib
import re
import sys
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
CONTENT = HERE / "content"
INTRO = CONTENT / "tutorials.intro.md"
GUIDE = CONTENT / "guide.md"
OUT = CONTENT / "tutorials.md"
STAMP = HERE / "tutorials.json"

REPO = "https://github.com/sfranz2422/kaypy/blob/main/examples"

#: The complete games, in the order they should be read. Each needs a
#: docstring in the file; the first line of it becomes the heading.
FEATURED = ["quiz_door.py", "pet_and_healthbar.py", "stealth_guard.py",
            "asteroids.py"]

#: Files in examples/ that are neither a featured game nor a lesson, and are
#: deliberately not on this page. Named so that a new example added to the
#: repository shows up as an error here rather than being silently dropped.
NOT_A_TUTORIAL = {
    "gen_assets.py": "a fixture generator for the examples, not a game",
}

LESSON_FILE = re.compile(r"^lesson(\d+)_")


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def slug(heading: str) -> str:
    """The anchor python-markdown's toc extension will give this heading.

    Taken from markdown itself rather than guessed, so a link built here and
    the id built at render time cannot disagree about an em dash.
    """
    from markdown.extensions.toc import slugify
    return slugify(heading, "-")


def lesson_titles(guide_md: pathlib.Path) -> dict[int, str]:
    """Lesson number -> its heading in the guide."""
    if not guide_md.is_file():
        sys.exit("content/guide.md is missing — run guide.py first.\n"
                 "  This page links into it, lesson by lesson.")
    out = {}
    for line in guide_md.read_text().splitlines():
        if line.startswith("## "):
            head = line[3:].strip()
            n = re.match(r"(\d+)\s*[—-]", head)
            if n:
                out[int(n.group(1))] = head
    if not out:
        sys.exit("No numbered lessons found in content/guide.md.")
    return out


def described(path: pathlib.Path) -> tuple[str, str]:
    """A featured example's title and the rest of its docstring."""
    doc = ast.get_docstring(ast.parse(path.read_text()))
    if not doc:
        sys.exit("examples/%s has no docstring.\n"
                 "  Its docstring is its description on the tutorials page —\n"
                 "  write one there, next to the code it describes."
                 % path.name)
    title, _, rest = doc.partition("\n")
    # A docstring's first line is a sentence and ends like one. A heading is
    # not a sentence, and a full stop in the contents sidebar looks like a
    # mistake.
    return title.strip().rstrip("."), rest.strip()


def body(kaypy: pathlib.Path) -> str:
    examples = kaypy / "examples"
    if not examples.is_dir():
        sys.exit("No examples/ in %s — pass --from." % kaypy)

    present = {p.name for p in examples.glob("*.py")}
    lessons = {}
    for name in sorted(present):
        m = LESSON_FILE.match(name)
        if m:
            lessons[int(m.group(1))] = name

    accounted = set(FEATURED) | set(NOT_A_TUTORIAL) | set(lessons.values())
    strays = sorted(present - accounted)
    if strays:
        sys.exit("examples/ has files this page does not know about:\n" +
                 "".join("      %s\n" % s for s in strays) +
                 "  Add each to FEATURED (and give it a docstring), or to\n"
                 "  NOT_A_TUTORIAL with a reason. A new example that nobody\n"
                 "  can find is the same as no example.")

    missing = [f for f in FEATURED if f not in present]
    if missing:
        sys.exit("FEATURED names files that are not in examples/: %s"
                 % ", ".join(missing))

    parts = ["## Whole games\n"]
    for name in FEATURED:
        path = examples / name
        title, rest = described(path)
        whole = path.read_text()
        # The docstring is the description above, so it is not also the
        # listing. The line count is of the whole file, though — that is
        # what the reader will see when they open it.
        source = whole[whole.index('"""', whole.index('"""') + 3) + 4:]
        parts.append("### %s\n" % title)
        parts.append("%s\n" % rest)
        parts.append("```python\n%s```\n" % source.lstrip("\n"))
        parts.append("[`examples/%s`](%s/%s) · %d lines\n"
                     % (name, REPO, name, whole.count("\n")))
        parts.append("---\n")

    titles = lesson_titles(GUIDE)
    parts.append("## The lesson programs\n")
    parts.append(
        "Each of these is the finished program from one lesson of the\n"
        "[guide](../guide/), which explains it a piece at a time. Read the\n"
        "lesson; keep the file to run.\n")
    parts.append("| | What it shows | Lines | |\n|---|---|---:|---|")
    for n in sorted(lessons):
        name = lessons[n]
        head = titles.get(n)
        if head is None:
            sys.exit("examples/%s has no lesson %d in the guide.\n"
                     "  Either the lesson was renumbered or the file was."
                     % (name, n))
        # "3 — Collision handling" -> "Collision handling"
        what = re.sub(r"^\d+\s*[—-]\s*", "", head)
        lines = (examples / name).read_text().count("\n")
        parts.append("| **%d** | [%s](../guide/#%s) | %d | [source](%s/%s) |"
                     % (n, what, slug(head), lines, REPO, name))
    parts.append("")

    parts.append("""---

## Coming next

**Coin Collector**, a thirteen-step platform game built from nothing — the
one to work through once the guide's lessons make sense. It exists as a
classroom walkthrough written for a different engine, and is being rewritten
for KayPy rather than translated, because the two think about a game in
genuinely different ways and a line-by-line translation would teach the seams
instead of the game.

If you are teaching with this and want it sooner, or want something else
first, say so on the [Discord](https://discord.gg/sVXnsDZNm).
""")
    return "\n".join(parts)


HEADER = """<!-- Built by tutorials.py. Do not edit.

  The listings are read out of examples/ in the kaypy repository, so the code
  here is the code that repository tests. The part above them is
  content/tutorials.intro.md, which IS edited by hand.

      python3 tutorials.py --from ~/kaypy      rebuild
      python3 tutorials.py --check             has anything moved on?
-->
"""


def compose(kaypy: pathlib.Path) -> str:
    if not INTRO.is_file():
        sys.exit("content/tutorials.intro.md is missing.")
    return HEADER + "\n" + INTRO.read_text().rstrip("\n") + "\n\n" + body(kaypy)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", default=os.path.expanduser("~/kaypy"))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    kaypy = pathlib.Path(args.src).expanduser().resolve()
    page = compose(kaypy)

    if args.check:
        if not OUT.is_file() or not STAMP.is_file():
            print("  no content/tutorials.md — run: python3 tutorials.py")
            return 1
        here = OUT.read_text()
        if here == page:
            print("  content/tutorials.md is current with examples/")
            return 0
        if digest(here) != json.loads(STAMP.read_text()).get("page_sha256"):
            print("  content/tutorials.md has been edited by hand")
            print("    (edit content/tutorials.intro.md, or the examples)")
        else:
            print("  the examples have changed since this was built")
        print("\n  run: python3 tutorials.py")
        return 1

    OUT.write_text(page)
    STAMP.write_text(json.dumps({
        "from": str(kaypy / "examples"),
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "featured": FEATURED,
        "page_sha256": digest(page),
    }, indent=1) + "\n")

    print("content/tutorials.md — %d whole games, %d lesson programs"
          % (len(FEATURED), page.count("\n| **")))
    print("  intro from content/tutorials.intro.md (written here)")
    print("  listings read from %s" % (kaypy / "examples"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
