#!/usr/bin/env python3
"""Every example in the API reference runs, and every name is documented.

    python3 test_api.py [--kaypy ~/kaypy]

An API reference is the one document nobody reads end to end. People arrive at
one entry, copy the example, and expect it to work. So an example that does not
run is worse than no example: it costs a beginner an hour deciding the mistake
is theirs.

Nothing here is checked by eye. Every fenced python block in content/api.md is
run on real kaypy, under SDL's dummy driver, with the sprite packs the
playground serves. The page states a three-line preamble once and the examples
are written as fragments; this prepends that same preamble, so what runs is
what a reader gets by pasting the block into the playground.

FOUR WAYS THIS PAGE CAN BE WRONG, AND ALL FOUR FAIL HERE

  * an example that raises
  * a name kaypy exports that the page never documents
  * a heading for something kaypy does not have (renamed, or never existed)
  * an entry whose example never uses the name it is documenting — which
    reads fine and teaches nothing

The third and fourth are the quiet ones. A reference drifts by documenting a
function that was renamed two releases ago, and nothing about a markdown file
objects.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import sys
from time import perf_counter as _now

HERE = pathlib.Path(__file__).resolve().parent
API = HERE / "content" / "api.md"
ASSETS = HERE / "dist" / "assets"

# Stated once at the top of the page, and prepended to every example here, so
# the two can never disagree about what an example may assume.
PREAMBLE = '''from kaypy import *

kaypy(width=800, height=600, background=[141, 183, 255])
loadSprite("bean", "images/bean.png")
'''

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-52s %s" % ("ok" if ok else "FAIL", label, detail))


def done():
    bad = results.count(False)
    print("\n%s (%d checks, %d failed)"
          % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
    sys.exit(1 if bad else 0)


ap = argparse.ArgumentParser()
ap.add_argument("--kaypy", type=pathlib.Path,
                default=pathlib.Path(os.path.expanduser("~/kaypy")))
args = ap.parse_args()

if not API.is_file():
    print("  no content/api.md yet")
    sys.exit(0)
if not (args.kaypy / "kaypy" / "__init__.py").is_file():
    sys.exit("No kaypy at %s — pass --kaypy." % args.kaypy)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["KAYPY_TEST_MAX_FRAMES"] = "0"
sys.path.insert(0, str(args.kaypy))

import kaypy                                                    # noqa: E402
import kaypy.engine as ke                                       # noqa: E402

text = API.read_text()

# ------------------------------------------------------------- the headings
#
# `### name(...)` or `### .name(...)` — a leading dot marks something you call
# ON an object rather than on its own.
headings = re.findall(r"^#{3,4}\s+`?(\.?)(\w+)\(?", text, re.M)
documented = {name for dot, name in headings if not dot}
methods = {name for dot, name in headings if dot}

exported = set(kaypy.__all__)

# kaplay is the pre-rename alias for kaypy(). It stays in the package so any
# file written before the rename keeps running, but it is deliberately absent
# from this page: nobody has written that line yet, and a reference that
# documents two names for one function invites somebody to type the wrong one.
alias = {n for n in exported if getattr(kaypy, n, None) is kaypy.kaypy} - {"kaypy"}

missing = sorted(exported - documented - alias)
check("every name kaypy exports has an entry", not missing,
      ", ".join(missing[:6]) + (" …" if len(missing) > 6 else ""))

for name in sorted(alias):
    check("the old name %s() is left out on purpose" % name,
          name not in documented)

invented = sorted(n for n in documented if not hasattr(kaypy, n))
check("no entry documents something kaypy does not have", not invented,
      ", ".join(invented[:6]))

# ------------------------------------------------------- the object methods
#
# These come from components at run time, through __getattr__, so they are
# not on the class and cannot be listed by dir(). The check that matters is
# the reverse one: nothing documented here may be imaginary.
KNOWN_METHODS = {
    "move", "moveTo", "jump", "isGrounded", "onGround", "destroy", "exists",
    "has", "is_", "use", "comp", "add", "onCollide", "onCollideEnd",
    "onCollideUpdate", "onUpdate", "onClick", "isHovering", "get_rect",
    "play", "curAnim", "size", "hurt", "heal", "isAlive", "setHP",
    "onHurt", "onHeal", "onDeath", "enterState", "onStateEnter",
    "onStateUpdate", "rotateBy", "rotateTo",
}
unknown = sorted(methods - KNOWN_METHODS)
check("no method entry is imaginary", not unknown, ", ".join(unknown[:6]))

# --------------------------------------------------------- run the examples
#
# Each block gets a fresh engine. Sharing one would let an example depend on
# an object some earlier entry happened to create, and a reader arriving at
# that one entry does not have it.
blocks = re.findall(r"```python\n(.*?)```", text, re.S)
check("the page has examples", len(blocks) > 50, "%d blocks" % len(blocks))


def reset():
    if ke._engine is not None:
        ke._engine._started = True      # stop atexit re-entering the loop
        ke._engine._running = False
        ke._engine = None


here = os.getcwd()
os.chdir(ASSETS)          # so loadSprite("images/bean.png") resolves

# Which entry each block belongs to, so a failure names it.
owners, current = [], "(before the first heading)"
for line in text.splitlines():
    m = re.match(r"^#{3,4}\s+`?(\.?\w+)", line)
    if m:
        current = m.group(1)
    elif line.startswith("```python"):
        owners.append(current)

failed = 0
for i, source in enumerate(blocks):
    owner = owners[i] if i < len(owners) else "?"
    # A block that already starts the engine is a whole program; the rest are
    # fragments that assume the preamble.
    whole = "from kaypy import" in source
    full = source if whole else PREAMBLE + "\n" + source
    reset()
    _t0 = _now()
    try:
        exec(compile(full, "<%s>" % owner, "exec"), {"__name__": "__main__"})
        if os.environ.get("API_TRACE"):
            print("    %6.2fs  %s" % (_now() - _t0, owner), flush=True)
    except Exception as exc:                                    # noqa: BLE001
        failed += 1
        line_no = getattr(exc, "lineno", None)
        offending = ""
        if line_no and 0 < line_no <= len(full.splitlines()):
            offending = full.splitlines()[line_no - 1].strip()
        check("  %s" % owner, False,
              "%s: %s%s" % (type(exc).__name__, str(exc)[:46],
                            "  |  " + offending[:40] if offending else ""))
reset()
os.chdir(here)

check("every example runs on real kaypy", not failed,
      "%d of %d blocks" % (len(blocks) - failed, len(blocks)))

# ------------------------------------------- an example that uses its entry
#
# An entry whose block never mentions the thing it documents is decoration.
# It reads as a worked example and teaches nothing about that name.
silent = []
for i, source in enumerate(blocks):
    owner = owners[i] if i < len(owners) else ""
    bare = owner.lstrip(".")
    if not bare or bare.startswith("("):
        continue
    if not re.search(r"\b%s\b" % re.escape(bare), source):
        silent.append(owner)
check("every example uses the name it documents", not silent,
      ", ".join(sorted(set(silent))[:6]))

done()
