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

So every fenced `python` block in content/learn.md is executed on real
kaypy, and wherever the page shows the output underneath, the two are
compared line for line.

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

HERE = pathlib.Path(__file__).resolve().parent
LESSON = HERE / "content" / "learn.md"
ASSETS = HERE / "dist" / "assets"

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
if not LESSON.is_file():
    sys.exit("No content/learn.md.")
if not (ASSETS / "images" / "coin.png").is_file():
    sys.exit("No sprites in dist/assets — run vendor.py first.")

text = LESSON.read_text()

# ---------------------------------------------------------------- blocks
#
# A `python` block, and the bare block under it if there is one, which is
# what the page claims the program prints.
# Any fence, not just ```python and a bare ```. The first version of this
# could not match a tagged fence like ```text at all, so its CLOSING fence was
# read as an opening one and every pair after it was wrong — on a page with
# one ```text block it silently fell from fourteen programs to three and still
# reported success, because "at least ten programs" was measured on the same
# broken list. A parser that mis-parses quietly is worse than no parser.
BLOCK = re.compile(r"^```([A-Za-z0-9_+-]*)\n(.*?)^```", re.S | re.M)
blocks = [(m.group(1) or "", m.group(2), m.start()) for m in BLOCK.finditer(text)]

programs = []
for i, (lang, body, start) in enumerate(blocks):
    if lang != "python":
        continue
    claimed = None
    if i + 1 < len(blocks) and blocks[i + 1][0] == "":
        between = text[start + len(body):blocks[i + 1][2]]
        # Only if it sits directly underneath, not further down the page.
        if between.count("\n") <= 5:
            claimed = blocks[i + 1][1]
    programs.append((body, claimed))

check("the lesson has programs in it", len(programs) >= 10,
      "%d python blocks" % len(programs))
check("and most of them state their output",
      sum(1 for _, c in programs if c is not None) >= 6,
      "%d of %d show output"
      % (sum(1 for _, c in programs if c is not None), len(programs)))

skipped = [p for p, _ in programs if "# DO NOT" in p]
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

for n, (body, claimed) in enumerate(programs, 1):
    if "# DO NOT" in body:
        continue
    ran += 1
    try:
        proc = subprocess.run(
            [sys.executable, "-c", body],
            cwd=ASSETS, env=env, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        crashed.append("block %d timed out" % n)
        continue

    if proc.returncode != 0:
        last = [ln for ln in proc.stderr.strip().splitlines() if ln.strip()]
        crashed.append("block %d: %s" % (n, last[-1] if last else "failed"))
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
        wrong.append("block %d line %d: page says %r, ran as %r"
                     % (n, first + 1,
                        want[first] if first < len(want) else "(nothing)",
                        got[first] if first < len(got) else "(nothing)"))

check("every program runs without raising", not crashed,
      "; ".join(crashed[:2]) if crashed else "%d programs" % ran)
check("and prints exactly what the page says it prints", not wrong,
      "; ".join(wrong[:2]) if wrong else
      "%d outputs matched" % sum(1 for _, c in programs if c is not None))

# ------------------------------------------------- the page is a lesson
#
# Cheap checks on the things that make it teaching rather than reference,
# each of which has gone missing from a draft at some point.
check("solutions are hidden behind <details>", text.count("<details") >= 3,
      "%d of them" % text.count("<details"))
check("the classwork has a stretch step for fast finishers",
      "**Stretch:**" in text)
check("the page links the playground, so there is somewhere to type",
      "../play/" in text)

done()
