#!/usr/bin/env python3
"""The playground page is wired up, and its starter program actually runs.

    python3 test_playground.py [--kaypy ~/kaypy]

A visitor's whole impression of kaypy is the first press of Run. If the
starter program throws, the engine looks broken — and nothing about a
playground fails loudly on the way out: the page builds, the files copy, the
site deploys, and the error appears in somebody else's browser.

So the starter is not eyeballed. It is lifted out of play.js, parsed, and RUN
on real kaypy with SDL on its dummy driver, which is the same way kaypy's own
lessons are tested. Every sprite it names must exist in the vendored assets,
and every handler it registers must be reachable.

WHAT THIS CANNOT TELL YOU

Whether it looks right. Pyodide, CodeMirror and the canvas are a browser's
job, and SDL's dummy driver draws nothing. Only opening the page does that:

    python3 -m http.server -d site
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE / "site"
PLAY = SITE / "play"          # the playground IS these files now; nothing
DIST = SITE                   # is generated, so source and built are one

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

page = (PLAY / "index.html").read_text()
script = (PLAY / "play.js").read_text()

# Comments stripped, for the same reason play.js's are below: this page
# explains in a comment which stylesheet it deliberately does NOT load, and a
# substring search read that explanation as the thing it was warning about.
# That is twice now. A scan for "is X absent?" has to look at code only.
page_code = re.sub(r"<!--.*?-->", " ", page, flags=re.S)

# ------------------------------------------------ the page loads what it needs
for name in ("runtime.js", "export.js", "game.js", "sprites.js", "complete.js",
             "style.css", "play.js", "play.css"):
    check("the playground loads %s" % name, './%s"' % name in page)

check("and every vendored one is in site/play/",
      all((DIST / "play" / n).is_file()
          for n in ("runtime.js", "export.js", "game.js", "sprites.js",
                    "complete.js", "style.css")))

# site.css must NOT be here. Both stylesheets define --bg, --line and --green
# from different palettes, and whichever loaded second would win — which is
# not a crash, it is a page with one theme's background and another's text.
check("and does NOT also load site.css", "site.css" not in page_code,
      "both define --bg; the second to load would win")

# Every element play.js reaches for has to exist. getElementById returns null
# for a typo, and the failure is a TypeError deep in an event handler that
# nobody sees until they click the thing.
wanted = set(re.findall(r'\$\("([a-z-]+)"\)', script))
absent = sorted(w for w in wanted if ('id="%s"' % w) not in page)
check("every id play.js looks up exists in the page", not absent,
      ", ".join(absent) if absent else "%d ids" % len(wanted))

# The sprite grid is styled by PyIDE's stylesheet, which names these classes.
# An invented name is not an error — it is an unstyled column of buttons.
style = (DIST / "play" / "style.css").read_text() if (DIST / "play" / "style.css").is_file() else ""
if style:
    used = set(re.findall(r'className = "([a-z-]+)"', script))
    unknown = sorted(c for c in used if ("." + c) not in style)
    check("every class play.js sets is one style.css styles", not unknown,
          ", ".join(unknown) if unknown else " ".join(sorted(used)))

# export.js has to come before game.js: an export carries runtime.js's Python
# bootstrap inside it, and the order is PyIDE's for that reason.
check("export.js is loaded before game.js",
      page.index('./export.js"') < page.index('./game.js"'))

# ------------------------------------------------------- the paths it overrides
paths = re.search(r"window\.PyIDEPaths\s*=\s*\{(.*?)\}", page, re.S)
check("the page sets window.PyIDEPaths", bool(paths))
if paths:
    body = paths.group(1)
    bundle = re.search(r'bundle:\s*"([^"]+)"', body)
    assets = re.search(r'assets:\s*"([^"]+)"', body)
    check("  it points at the vendored bundle",
          bundle and (DIST / "play" / bundle.group(1)).resolve().is_file(),
          bundle.group(1) if bundle else "not set")
    check("  and at the vendored assets",
          assets and (DIST / "play" / assets.group(1)).resolve().is_dir(),
          assets.group(1) if assets else "not set")
    # Relative, so the site works from a subdirectory and from a local build.
    check("  both are relative, not rooted at /",
          bundle and assets and not bundle.group(1).startswith("/")
          and not assets.group(1).startswith("/"))

# ------------------------------------------- the same Pyodide PyIDE was tested on
site_py = re.search(r"pyodide/v([\d.]+)/full/pyodide\.js", page)
pyide_index = args.kaypy.parent / "pyide" / "templates" / "index.html"
if pyide_index.is_file():
    theirs = re.search(r"pyodide/v([\d.]+)/full/pyodide\.js",
                       pyide_index.read_text())
    check("the same Pyodide version PyIDE runs",
          site_py and theirs and site_py.group(1) == theirs.group(1),
          "site %s | pyide %s" % (site_py.group(1) if site_py else "?",
                                  theirs.group(1) if theirs else "?"))
else:
    print("  skip  no PyIDE checkout to compare the Pyodide version against")

# --------------------------------------------------------- no school in here
#
# The point of this page is that a visitor is never asked to sign in. These
# are the names PyIDE's account, assignment and autosave code uses; none of
# them should have followed the modules across.
#
# Comments are stripped first. play.js opens by explaining that it does NOT do
# assignments or autosave, and a substring search cannot tell an explanation
# from an implementation — the first version of this check failed on its own
# documentation, which is a false alarm, and a test that cries wolf gets
# muted.
code_only = re.sub(r"/\*.*?\*/", " ", script, flags=re.S)
code_only = re.sub(r"^\s*//.*$", " ", code_only, flags=re.M)

for gone in ("/login", "signed_in", "assignment", "autosave", "/api/",
             "csrf", "fetch(\"/", "XMLHttpRequest"):
    check("the playground has no %r in its code" % gone,
          gone.lower() not in code_only.lower(),
          "found in play.js" if gone.lower() in code_only.lower() else "")

# The only network calls it may make are to the vendored assets, the CDNs the
# page names, and Pyodide's own. Nothing may be posted anywhere: there is no
# server, and a visitor's code must not leave their machine.
check("and posts nothing anywhere",
      not re.search(r'method:\s*["\']POST', code_only, re.I))

# ----------------------------------------------------------- the starter
#
# Read from site/play/starter.py, which IS the file the page fetches.
# into play.js with json.dumps. There is no parsing step here to get wrong.
#
# An earlier version kept the starter as a list of JavaScript string literals
# and pulled it back out with a regex. The regex matched only double-quoted
# lines, so every line written with single quotes vanished — the test ran a
# shorter program than the page shipped, and reported ok. Hence starter.py.
starter_file = PLAY / "starter.py"
check("there is a starter program", starter_file.is_file())
if not starter_file.is_file():
    done()
starter = starter_file.read_text()
check("  it is a real program", len(starter.splitlines()) > 20,
      "%d lines" % len(starter.splitlines()))
check("  that imports kaypy", "from kaypy import *" in starter)
check("  and starts the engine",
      re.search(r"^kaypy\(", starter, re.M) is not None)

# HOW THE STARTER REACHES THE PAGE
#
# It used to be inlined into play.js by build.py. There is no build now, so
# play.js fetches starter.py at run time — which means three new ways for the
# starter to silently not arrive, and all three are checked here.
#
# The worst of them is the second: the editor is built before the fetch lands,
# so anything reading STARTER in that window sees an empty string. If the
# fetch were dropped and nothing replaced it, the page would open with an
# empty editor and no error anywhere.
check("  and play.js fetches it rather than carrying a copy",
      'fetch("starter.py"' in script,
      "nothing fetches starter.py")
check("  with no stale inlined copy left beside the fetch",
      "var STARTER = \"from kaypy" not in script)
check("  it sits next to play.js, so the relative fetch resolves",
      (PLAY / "starter.py").is_file())
check("  the fetched text is put into the editor",
      re.search(r"fetchStarter\(\)\s*\.then", script) is not None)
check("  a saved draft is not overwritten when it lands",
      re.search(r"if \(draft\) return", script) is not None,
      "a late fetch would replace what the visitor had written")
check("  and Start over refuses while it is still empty",
      re.search(r"if \(!STARTER\)", script) is not None,
      "pressing it early would blank the editor")

# ------------------------------------------- every sprite and sound it names
named = re.findall(r'load(?:Sprite|Sound)\("[^"]+",\s*"([^"]+)"\)', starter)
missing = [p for p in named if not (DIST / "assets" / p).is_file()]
check("every asset the starter names is vendored", not missing,
      ", ".join(missing) if missing else " ".join(named))

# ------------------------------------------------------------- run it for real
#
# THIS USED TO CALL done() WHEN THERE WAS NO KAYPY TO RUN AGAINST.
#
# done() prints the tally and exits, so without --kaypy the suite stopped
# here and every check written below it simply never ran — while still
# reporting ALL PASSED, because the checks that did run all passed. A
# skipped section and a passing one looked identical from the outside, and
# three checks added underneath it sat there doing nothing until the total
# failed to go up by three.
#
# So the skip is a branch now, not an exit.
if not (args.kaypy / "kaypy" / "__init__.py").is_file():
    print("  skip  no kaypy checkout at %s — pass --kaypy to run the starter"
          % args.kaypy)
else:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ["KAYPY_TEST_MAX_FRAMES"] = "0"
    sys.path.insert(0, str(args.kaypy))

    os.chdir(DIST / "assets")      # so loadSprite("images/bean.png") resolves

    import kaypy                                                    # noqa: E402
    import kaypy.engine as ke                                       # noqa: E402

    namespace = {"__name__": "__main__"}
    try:
        exec(compile(starter, "starter.py", "exec"), namespace)
        engine = ke._engine
        ran = engine is not None
    except Exception as exc:                                        # noqa: BLE001
        engine, ran = None, False
        check("the starter runs on real kaypy", False,
              "%s: %s" % (type(exc).__name__, exc))

    if ran:
        check("the starter runs on real kaypy", True,
              "%d objects" % len(engine._objs))
        # A starter that builds objects but wires nothing is a starter where
        # pressing an arrow key does nothing, which reads as a broken engine to
        # somebody who has never seen a working one.
        handlers = (len(engine.events.key_down_handlers)
                    + len(engine.events.key_press_handlers))
        check("  its keys are wired up", handlers >= 3, "%d handlers" % handlers)
        check("  and it puts something on the screen", len(engine._objs) >= 4)

        engine._started = True
        engine._running = False
        ke._engine = None

os.chdir(HERE)
# ------------------------------------------------- find and replace is wired
#
# Same four files as the three editors. The one that ships broken quietly is
# dialog.min.css: without it find and replace WORK, and the bar asking for
# the search term is an unstyled input floating over the code.
play_html = page
for addon in ("addon/dialog/dialog.min.js",
              "addon/search/searchcursor.min.js",
              "addon/search/search.min.js",
              "addon/dialog/dialog.min.css"):
    check("the playground loads %s" % addon.split("/")[-1],
          addon in play_html)
check("  and searchcursor comes before search",
      play_html.find("searchcursor.min.js")
      < play_html.find("addon/search/search.min.js"))
# The addons must load before play.js builds the editor: search.js sets the
# `search` option through defineOption, which only reaches editors made
# after it runs, and then reads cm.options.search.bottom unguarded.
check("  and the addons load before play.js builds the editor",
      play_html.find("addon/search/search.min.js") < play_html.find("play.js"))

check("  and the search bar is given a usable width",
      ".CodeMirror-dialog input" in (PLAY / "play.css").read_text())

done()
