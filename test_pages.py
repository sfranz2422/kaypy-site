#!/usr/bin/env python3
"""The Get started and Games pages say things that are true.

    python3 test_pages.py --kaypy ~/kaypy

check_site.py already follows every link and catches dead ones. This is the
other half: a page can link perfectly and still be wrong.

WHAT GOES WRONG HERE, AND LOOKS FINE

  * Get started prints a command that no longer exists. `kaypy new` is not
    checked by anything — the page is markdown, the CLI is Python, and the
    only thing joining them is that somebody typed both. A reader follows
    the page, gets "invalid choice", and concludes the project is broken.

  * The Games page links a game that is not a kaypy game. There are five
    folders under static/games/ and three of them are JavaScript Kaplay,
    which look identical from the outside and would be a lie on a page
    headed "written in Python with kaypy".

  * The {{SUBMIT_FORM}} marker survives into the built page, so a reader
    sees {{SUBMIT_FORM}} where the form should be. Template slots that are
    never filled are the oldest rot on a static site.

  * The form URL is set to something that is not a form. An iframe with a
    wrong address renders BLANK — no error, no broken-image icon, nothing —
    and is found by somebody failing to send you a game.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
DIST = HERE / "dist"
CONTENT = HERE / "content"

results = []


def check(label, ok, detail=""):
    """Detail is printed only on a FAILURE.

    Printed on a pass it reads as evidence for the opposite: "ok — flappy is
    really a kaypy game — no mention of pyodide" says two contradictory
    things on one line, and the eye believes the second.
    """
    results.append(bool(ok))
    print("  %-4s %-58s %s" % ("ok" if ok else "FAIL", label,
                               "" if ok else detail))


def done():
    bad = results.count(False)
    print("\n%s (%d checks, %d failed)"
          % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
    sys.exit(1 if bad else 0)


ap = argparse.ArgumentParser()
ap.add_argument("--kaypy", default=None,
                help="a kaypy checkout, to check the commands against")
args = ap.parse_args()

import build                                                   # noqa: E402

# ============================================ the pages are in the header
slugs = [slug for slug, _title, _src in build.NAV]
check("Get started is in the nav", "start" in slugs, str(slugs))
check("Games is in the nav", "games" in slugs, str(slugs))

for slug in ("start", "games"):
    page = DIST / slug / "index.html"
    check("  and /%s/ was built" % slug, page.is_file())

home = (DIST / "index.html").read_text() if (DIST / "index.html").is_file() else ""
check("the header links to both", 'href="start/"' in home
      and 'href="games/"' in home)

# ================================================= no unfilled template slots
#
# A {{...}} left in a built page is the one kind of rot a reader sees
# immediately and nobody testing locally ever does, because it renders as
# text rather than raising.
leftover = []
for page in DIST.rglob("*.html"):
    for slot in re.findall(r"\{\{[A-Z_]+\}\}", page.read_text()):
        leftover.append("%s in %s" % (slot, page.relative_to(DIST)))
check("no {{SLOT}} survived into a built page", not leftover,
      "; ".join(leftover[:3]))

# ================================================== the games are kaypy games
games_md = (CONTENT / "games.md").read_text()
linked = re.findall(r"\(\.\./static/games/([A-Za-z0-9_\-]+)/\)", games_md)
check("the Games page links some games", len(linked) >= 2, str(linked))

for name in linked:
    index = HERE / "static" / "games" / name / "index.html"
    if not index.is_file():
        check("  %s exists" % name, False, "no index.html")
        continue
    text = index.read_text(errors="ignore")
    # A kaypy export runs Python: it loads Pyodide. The JavaScript Kaplay
    # games in the same folder do not, and are indistinguishable from the
    # outside — same folder, same index.html, same canvas.
    check("  %s really is a kaypy game (it loads Python)" % name,
          "pyodide" in text.lower(), "no mention of pyodide")

all_games = sorted(p.name for p in (HERE / "static" / "games").iterdir()
                   if p.is_dir())
js_only = [g for g in all_games if g not in linked]
print("      (not linked, and correctly so — these are JavaScript Kaplay: %s)"
      % ", ".join(js_only))
for name in js_only:
    index = HERE / "static" / "games" / name / "index.html"
    if index.is_file():
        check("  %s is NOT claimed as kaypy" % name,
              "pyodide" not in index.read_text(errors="ignore").lower(),
              "it loads Pyodide — it may belong on the page after all")

# ================================================== the submission form slot
check("the Games page has a place for the form",
      "{{SUBMIT_FORM}}" in games_md)

# Guarded: if the page is not there the nav checks above have already
# failed, and this should report that too rather than dying with a
# FileNotFoundError and taking the rest of the suite's results with it.
_games_page = DIST / "games" / "index.html"
built = _games_page.read_text() if _games_page.is_file() else ""
if build.GAMES_FORM_URL:
    check("  and the form is embedded",
          "<iframe" in built and build.GAMES_FORM_URL in built)
    # A Google Form embeds from /viewform?embedded=true. The edit link, or
    # the short forms.gle link, renders an empty white box instead.
    check("  from a real Google Forms embed address",
          build.GAMES_FORM_URL.startswith("https://docs.google.com/forms/")
          and "/viewform" in build.GAMES_FORM_URL
          and "embedded=true" in build.GAMES_FORM_URL,
          build.GAMES_FORM_URL)
    check("  not the EDIT link, which only you can open",
          "/edit" not in build.GAMES_FORM_URL, build.GAMES_FORM_URL)
else:
    check("  with an honest substitute until it is set",
          "not up yet" in built and "<iframe" not in built)
    print("      (GAMES_FORM_URL is empty in build.py — paste the embed "
          "address there and rebuild)")

# ============================================ the classes the pages apply
css = (HERE / "static" / "site.css").read_text()
styled = set(re.findall(r"\.([A-Za-z][\w-]*)", css))
applied = set()
for page in (DIST / "games" / "index.html", DIST / "start" / "index.html"):
    if not page.is_file():
        continue
    # Code blocks are stripped first. The highlighter puts Pygments token
    # classes on every span inside them — k, n, kc, nn, w — and those
    # inherit from the block rather than each having a rule of their own.
    # Counting them reported six "unstyled" classes that are nothing to do
    # with the page's own layout.
    text = re.sub(r"<pre.*?</pre>", "", page.read_text(), flags=re.S)
    for value in re.findall(r'class="([^"]+)"', text):
        applied |= set(value.split())
unstyled = sorted(c for c in applied if c not in styled)
check("every class these pages use has a CSS rule", not unstyled,
      str(unstyled))

# ====================================== Get started names real commands
start_md = (CONTENT / "start.md").read_text()
# ONLY FROM FENCED BLOCKS. Scanning the whole page pulled in the sentence
# "kaypy needs Python 3.10 or newer" and then went looking for a subcommand
# called `needs`. A command is a thing in a code block; prose is prose.
fenced = "\n".join(re.findall(r"```(?:[a-z]*)\n(.*?)```", start_md, re.S))
commands = re.findall(r"^(kaypy [a-z]+|pip install kaypy|python game\.py"
                      r"|python -m kaypy\S*)", fenced, re.M)
check("Get started actually shows commands", len(commands) >= 4,
      str(sorted(set(commands))))

if args.kaypy:
    root = pathlib.Path(args.kaypy).expanduser()
    helped = subprocess.run(
        [sys.executable, "-m", "kaypy.cli", "--help"],
        capture_output=True, text=True, cwd=str(root),
        env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(root),
             "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"})
    usage = helped.stdout
    check("  the CLI was found", "usage: kaypy" in usage,
          (helped.stderr or usage)[:60])

    # Every `kaypy <word>` the page prints must be a real subcommand. This is
    # the check that would have caught `python -m kaypy`, which the page
    # recommended and which does not work: kaypy has no __main__.py.
    wanted = sorted({c.split()[1] for c in commands if c.startswith("kaypy ")})
    unknown = [w for w in wanted if w not in usage]
    check("  and every command the page names exists", not unknown,
          "not in --help: %s" % unknown)
    check("    (and the page names several)", len(wanted) >= 3, str(wanted))

    module_calls = re.findall(r"python -m (kaypy\S*)", start_md)
    bad_module = [m for m in module_calls
                  if not (root / m.replace(".", "/")).with_suffix(".py").is_file()]
    check("  a `python -m ...` line points at a module that exists",
          not bad_module, str(bad_module))
else:
    print("      (no --kaypy given, so the commands were not run)")

done()
