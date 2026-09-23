#!/usr/bin/env python3
"""Build content/guide.md out of kaypy's GUIDE.md.

    python3 guide.py                     # from ~/kaypy
    python3 guide.py --from ~/kaypy
    python3 guide.py --check             # verify, change nothing

WHY THE GUIDE IS NOT SIMPLY COPIED

The thirteen lessons are the same wherever you read them, and they are copied
here verbatim. What cannot be copied is everything around them. GUIDE.md opens
by telling you to press **+ Game** in PyIDE or to `pip install kaypy`, because
those are the two places its readers are. A reader of this page is already in
a browser, three clicks from a playground, and has not installed anything.

So the front matter is written for this site and lives in
`content/guide.intro.md`, a plain file you can edit like any other page. The
lessons are pasted on after it, unchanged.

WHY THE FEW EDITS INSIDE THE LESSONS ARE SPELLED OUT IN FULL

Five sentences inside the lessons name PyIDE, because that is the editor the
original reader had. On this site the same thing is the playground.

The tempting way to fix that is `text.replace("PyIDE", "the playground")`. The
trouble with a blind replacement is not that it is wrong today — it is that it
reports nothing when it stops matching. Reword one of those sentences in
kaypy, and this script goes on succeeding while quietly shipping a page that
tells a reader to press a button that is not there.

So each edit is written out below as the exact sentence before and after, and
every one of them must be found. If a sentence has moved on, the build stops
and names it, which is a minute's work — as against a wrong sentence on a
public page that nobody will notice for months.

WHAT --check IS FOR

The same question vendor.py answers about the engine: has the source moved on
without this copy? `guide.json` records a hash of the lessons as they were
taken, so `--check` can tell "the guide is current" apart from "the guide was
edited here by hand", which are very different problems.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
CONTENT = HERE / "content"
INTRO = CONTENT / "guide.intro.md"
OUT = CONTENT / "guide.md"
STAMP = HERE / "guide.json"

#: Where the lessons begin in GUIDE.md. Everything above it is front matter
#: written for a reader of the repository, and is replaced; everything from
#: here down is copied.
FIRST_LESSON = "## 1 — Adding a game object"

#: Exact replacements, applied to the copied half. Each is (before, after,
#: how many times it must appear) — and a count that does not match stops the
#: build rather than being silently absorbed.
EDITS = [
    ("Run it — **Run** in PyIDE, or `python game.py` on your machine.",
     "Run it — **Run** in the playground, or `python game.py` on your machine.",
     1),
    ("You don't have to type any of that. In PyIDE, click the elf in the **Sprites**\npanel",
     "You don't have to type any of that. In the playground, click the elf in the\n**Sprites** panel",
     1),
    ("**Sprites** panel under *Sprite atlas*, and in `examples/` on disk. Clicking it\nin PyIDE inserts all of this:",
     "**Sprites** panel under *Sprite atlas*, and next to your `game.py` on disk.\nClicking it in the playground inserts all of this:",
     1),
    ("In PyIDE it must be a file the\nSprites panel lists;",
     "In the playground it must be a file the\nSprites panel lists;",
     1),
    ("**The keys do nothing** — click the picture once. In PyIDE, and in a web build,",
     "**The keys do nothing** — click the picture once. In the playground, and in a\nweb build,",
     1),
    # American spelling throughout the site.
    ("Play with the position, colour and scale.",
     "Play with the position, color and scale.",
     1),
]

HEADER = """<!-- Built by guide.py. Do not edit.

  The lessons come from GUIDE.md in the kaypy repository. The part above them
  is content/guide.intro.md, which IS edited by hand.

      python3 guide.py --from ~/kaypy      rebuild
      python3 guide.py --check             has the source moved on?
-->
"""


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def fenced(text: str) -> list[str]:
    """Every fenced code block, in order."""
    return re.findall(r"^```[a-z]*\n(.*?)^```", text, re.S | re.M)


def lessons_from(guide: pathlib.Path) -> str:
    text = guide.read_text()
    if FIRST_LESSON not in text:
        sys.exit("GUIDE.md has no %r — the lessons may have been renamed.\n"
                 "  Nothing was written. Fix FIRST_LESSON in guide.py."
                 % FIRST_LESSON)
    body = text[text.index(FIRST_LESSON):]
    before_code = fenced(body)

    missed = []
    for before, after, times in EDITS:
        found = body.count(before)
        if found != times:
            missed.append((before, times, found))
            continue
        body = body.replace(before, after)

    if missed:
        print("These sentences in GUIDE.md are not what guide.py expects:\n")
        for before, want, got in missed:
            first = before.split("\n")[0]
            print("  expected %d, found %d:" % (want, got))
            print("      %s" % (first[:72] + ("…" if len(first) > 72 else "")))
        sys.exit("\nNothing was written. Update EDITS in guide.py to match.")

    # An edit is allowed to change what the guide SAYS. It is not allowed to
    # change what the guide RUNS. Every code block here is a program somebody
    # will copy, and one the kaypy repository executes in its own tests — so
    # a replacement that reached inside a fence would put code on this site
    # that nothing anywhere tests, which is the one thing a tutorial page
    # must never do.
    if fenced(body) != before_code:
        sys.exit("An entry in EDITS changed the inside of a code block.\n"
                 "  The code here is tested in the kaypy repository and must\n"
                 "  stay identical to it. Reword the prose, not the program.")

    left = body.count("PyIDE")
    if left:
        sys.exit("%d mention%s of PyIDE left in the lessons after editing.\n"
                 "  This page is read by people who have never heard of it.\n"
                 "  Add the sentence to EDITS in guide.py."
                 % (left, "" if left == 1 else "s"))

    return body


def compose(guide: pathlib.Path) -> tuple[str, str]:
    """The finished page, and a hash of the lessons it was built from."""
    if not INTRO.is_file():
        sys.exit("content/guide.intro.md is missing — that is the front matter "
                 "this site writes for itself.")
    body = lessons_from(guide)
    page = HEADER + "\n" + INTRO.read_text().rstrip("\n") + "\n\n" + body
    return page, digest(body)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", default=os.path.expanduser("~/kaypy"),
                    help="the kaypy checkout to take the lessons from")
    ap.add_argument("--check", action="store_true",
                    help="compare what is here against the source; write nothing")
    args = ap.parse_args()

    kaypy = pathlib.Path(args.src).expanduser().resolve()
    guide = kaypy / "GUIDE.md"
    if not guide.is_file():
        sys.exit("No GUIDE.md at %s — pass --from." % kaypy)

    page, lesson_hash = compose(guide)

    if args.check:
        return check(page, lesson_hash)

    OUT.write_text(page)
    STAMP.write_text(json.dumps({
        "from": str(guide),
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lessons_sha256": lesson_hash,
        "page_sha256": digest(page),
        "lessons": page.count("\n## ") and sum(
            1 for line in page.splitlines()
            if line.startswith("## ") and line[3].isdigit()),
    }, indent=1) + "\n")

    count = sum(1 for line in page.splitlines()
                if line.startswith("## ") and line[3:4].isdigit())
    print("content/guide.md — %d lessons, %d lines, %.0f KB"
          % (count, page.count("\n") + 1, len(page) / 1024))
    print("  intro from content/guide.intro.md (written here)")
    print("  lessons from %s (copied, %d edits)" % (guide, len(EDITS)))
    return 0


def check(page: str, lesson_hash: str) -> int:
    if not OUT.is_file():
        print("  no content/guide.md — run: python3 guide.py")
        return 1
    if not STAMP.is_file():
        print("  no guide.json — run: python3 guide.py")
        return 1

    recorded = json.loads(STAMP.read_text())
    here = OUT.read_text()

    if here == page:
        print("  content/guide.md is current with GUIDE.md")
        return 0

    # Which half moved decides what the fix is, so say which.
    if recorded.get("lessons_sha256") != lesson_hash:
        print("  the lessons in GUIDE.md have changed since this was built")
    if digest(here) != recorded.get("page_sha256"):
        print("  content/guide.md has been edited by hand since it was built")
        print("    (edit content/guide.intro.md, or GUIDE.md, not the output)")
    print("\n  run: python3 guide.py")
    return 1


if __name__ == "__main__":
    sys.exit(main())
