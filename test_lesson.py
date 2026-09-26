#!/usr/bin/env python3
"""Every program in the lessons runs, and prints exactly what the page says.

    python3 test_lesson.py [--kaypy ~/kaypy]

A lesson page is read by somebody who does not yet know enough to tell a
typo from their own mistake. When the page says a program prints

    Boss down in 6 hits

and it actually prints 7, the student does not conclude that the page is
wrong. They conclude that they are. That is the whole reason this file
exists: a printed output on a teaching page is a claim, and claims get
checked.

So every Python block on every lesson page is executed on real kaypy, and
wherever the page shows the output underneath, the two are compared line for
line.

The blocks are read out of the built HTML by pagecode.py. They used to be read
out of content/learn.md, which no longer exists: the site is hand-written HTML
now, and there is no markdown to read. Nothing else about this file changed —
the same programs run, on the same engine, against the same claims.

THE ONE BLOCK THAT MUST NOT RUN

The lesson teaches that writing your own `while True:` in a kaypy program
hangs it — the engine's loop is already running, and yours never gives it a
turn. That is worth showing, and the demonstration is a program that never
returns. Running it here would hang this test and, worse, hang CI, where a
job with no output is a job somebody cancels twenty minutes later.

Blocks marked with a `# DO NOT` comment are skipped, and the count of them
is pinned below. A skip nobody notices is how a whole section stops being
checked, so adding one has to be deliberate.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys

import pagecode

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE / "site"
ASSETS = SITE / "assets"

#: The lessons, in order. Named rather than globbed: a glob over site/learn/
#: would silently pick up nothing at all if the folder were renamed, and
#: "0 programs found" is a pass in a suite that only counts failures.
LESSONS = ["conditionals", "loops", "lists"]

#: How many blocks are allowed to carry `# DO NOT` and be skipped. Pinned so
#: that a second one cannot appear without this number being changed.
EXPECTED_SKIPS = 1

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-54s %s" % ("ok" if ok else "FAIL", label, detail))


def done():
    bad = results.count(False)
    print("\n%s (%d checks, %d failed)"
          % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
    sys.exit(1 if bad else 0)


ap = argparse.ArgumentParser()
ap.add_argument("--kaypy", type=pathlib.Path,
                default=pathlib.Path(os.path.expanduser("~/kaypy")))
args = ap.parse_args()

kaypy_root = args.kaypy.expanduser().resolve()
if not (kaypy_root / "kaypy" / "__init__.py").is_file():
    sys.exit("No kaypy at %s — pass --kaypy." % kaypy_root)
pages = [(name, SITE / "learn" / name / "index.html") for name in LESSONS]
absent = [str(p.relative_to(HERE)) for _n, p in pages if not p.is_file()]
if absent:
    sys.exit("Missing lesson pages: %s" % ", ".join(absent))
if not (ASSETS / "images" / "coin.png").is_file():
    sys.exit("No sprites in site/assets — run vendor.py first.")

# ---------------------------------------------------------------- blocks
#
# A Python block, and the block with no language under it if there is one,
# which is what the page claims the program prints.
#
# "Directly underneath" is strict here: nothing but whitespace between the two.
# In the markdown this used to allow a short paragraph in the gap, because a
# fence pair is five lines of text apart even when adjacent; in the HTML an
# adjacent pair is separated by a single newline, so anything more is a
# different block and pairing them would compare a program against output that
# belongs to another one.
programs = []
for name, path in pages:
    page = path.read_text()
    blocks = pagecode.blocks(page)
    found = 0
    for i, (lang, body, _start, end) in enumerate(blocks):
        if lang != "python":
            continue
        claimed = None
        if i + 1 < len(blocks) and blocks[i + 1][0] == "":
            if not pagecode.text_only(page[end:blocks[i + 1][2]]).strip():
                claimed = blocks[i + 1][1]
        programs.append((name, body, claimed))
        found += 1
    # Per page, not just in total: a lesson that lost all its code would
    # otherwise hide behind the other two.
    check("%s has programs in it" % name, found >= 4, "%d python blocks" % found)

check("the lessons have programs in them", len(programs) >= 10,
      "%d python blocks" % len(programs))
check("and most of them state their output",
      sum(1 for _, _, c in programs if c is not None) >= 6,
      "%d of %d show output"
      % (sum(1 for _, _, c in programs if c is not None), len(programs)))

skipped = [b for _n, b, _c in programs if "# DO NOT" in b]
check("exactly the expected number of blocks are skipped",
      len(skipped) == EXPECTED_SKIPS,
      "%d skipped, expected %d" % (len(skipped), EXPECTED_SKIPS))
check("  and the skipped one is the hanging loop",
      all("while True" in p for p in skipped))

# ------------------------------------------------------------- run them
env = dict(os.environ)
env["SDL_VIDEODRIVER"] = "dummy"
env["SDL_AUDIODRIVER"] = "dummy"
env["KAYPY_TEST_MAX_FRAMES"] = "3"
env["PYTHONPATH"] = str(kaypy_root)

crashed, wrong = [], []
ran = 0

for n, (name, body, claimed) in enumerate(programs, 1):
    if "# DO NOT" in body:
        continue
    ran += 1
    try:
        proc = subprocess.run(
            [sys.executable, "-c", body],
            cwd=ASSETS, env=env, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        crashed.append("%s block %d timed out" % (name, n))
        continue

    if proc.returncode != 0:
        last = [ln for ln in proc.stderr.strip().splitlines() if ln.strip()]
        crashed.append("%s block %d: %s" % (name, n, last[-1] if last else "failed"))
        continue

    if claimed is None:
        continue

    # pygame prints a banner on import; it is not part of what the page
    # claims, and the page would be silly to include it.
    got = [ln.rstrip() for ln in proc.stdout.splitlines()
           if not ln.startswith("pygame-ce") and "Hello from the pygame" not in ln]
    want = [ln.rstrip() for ln in claimed.splitlines()]
    while got and not got[-1]:
        got.pop()
    while want and not want[-1]:
        want.pop()

    if got != want:
        first = next((i for i in range(max(len(got), len(want)))
                      if got[i:i + 1] != want[i:i + 1]), 0)
        wrong.append("%s block %d line %d: page says %r, ran as %r"
                     % (name, n, first + 1,
                        want[first] if first < len(want) else "(nothing)",
                        got[first] if first < len(got) else "(nothing)"))

check("every program runs without raising", not crashed,
      "; ".join(crashed[:2]) if crashed else "%d programs" % ran)
check("and prints exactly what the page says it prints", not wrong,
      "; ".join(wrong[:2]) if wrong else
      "%d outputs matched" % sum(1 for _, _, c in programs if c is not None))

# ------------------------------------------------- the page is a lesson
#
# Cheap checks on the things that make it teaching rather than reference,
# each of which has gone missing from a draft at some point.
# Per page. Written as one loop over all three rather than against a single
# concatenated blob, because a check on the union passes when one lesson has
# all of it and another has none — which is exactly the state a newly split
# page arrives in.
#: Solutions folded away, counted across all three lessons. It is a total and
#: not a per-page floor because the lessons are not the same shape: loops has
#: three foldaways, conditionals and lists one each. A per-page floor of three
#: fails honest pages, and a floor of one passes a page that lost two.
EXPECTED_DETAILS = 5

details = 0
for name, path in pages:
    page = path.read_text()
    details += page.count("<details")
    check("%s hides at least one solution behind <details>" % name,
          page.count("<details") >= 1, "%d of them" % page.count("<details"))
    # Markdown's `**Stretch:**` is <strong>Stretch:</strong> now.
    check("  and has a stretch step for fast finishers",
          re.search(r"<strong>\s*Stretch:", page) is not None)
    # THE DEPTH. A lesson page lives at /learn/<name>/, so the playground is
    # two levels up, not one. `../play/` here would resolve to /learn/play/ —
    # a 404 that renders perfectly and is only found by clicking it.
    found_play = '"../../play/"' in page
    check("  and links the playground, so there is somewhere to type",
          found_play,
          "" if found_play else
          ("found ../play/, which resolves to /learn/play/"
           if '"../play/"' in page else "no link to the playground at all"))

check("the three lessons fold away %d solutions between them" % EXPECTED_DETAILS,
      details == EXPECTED_DETAILS, "%d, expected %d" % (details, EXPECTED_DETAILS))

done()
