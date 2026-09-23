#!/usr/bin/env python3
"""Look over the built site before it goes out.

    python3 check_site.py

Three kinds of rot, all of which look fine until someone clicks:

  * a template slot that was never filled, so a page says `{{TITLE}}`
  * a link to a page that does not exist
  * a stylesheet, script or image that 404s

A docs site fails quietly. Nothing crashes; a reader just hits a dead end and
assumes the project is abandoned. So this walks every built page, follows
every local href and src, and says what is broken.

It deliberately does NOT check external links. They break for reasons nobody
here controls, and a check that fails because somebody else's server is having
an afternoon is a check people learn to ignore.
"""
from __future__ import annotations

import pathlib
import re
import sys
from urllib.parse import unquote, urlparse

HERE = pathlib.Path(__file__).resolve().parent
DIST = HERE / "dist"

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-52s %s" % ("ok" if ok else "FAIL", label, detail))


if not DIST.is_dir():
    sys.exit("No dist/ — run python3 build.py first.")

pages = sorted(DIST.rglob("*.html"))
check("the site built at all", bool(pages), "%d pages" % len(pages))

# ---------------------------------------------------- unfilled template slots
unfilled = []
for page in pages:
    for slot in set(re.findall(r"\{\{[A-Z_]+\}\}", page.read_text())):
        unfilled.append("%s: %s" % (page.relative_to(DIST), slot))
check("every template slot was filled", not unfilled, ", ".join(unfilled[:3]))

# ------------------------------------------------------------- local links
def resolve(page, target):
    """Where a href from this page points, as a path in dist/."""
    if target.startswith("/"):
        return DIST / target.lstrip("/")
    return (page.parent / target).resolve()


def ids_in(path):
    """Every id= on a page, for checking the #fragment half of a link."""
    try:
        return set(re.findall(r'\bid="([^"]+)"', path.read_text()))
    except OSError:
        return set()


broken, checked = [], 0
dangling, fragments = [], 0
for page in pages:
    text = page.read_text()
    for attr in ("href", "src"):
        for raw in re.findall(r'%s="([^"]+)"' % attr, text):
            url = unquote(raw)
            if urlparse(url).scheme or url.startswith(("//", "mailto:", "data:")):
                continue
            path, _, fragment = url.partition("#")
            path = path.split("?")[0]

            where = page if not path else resolve(page, path)
            if path:
                checked += 1
                if where.is_dir():
                    where = where / "index.html"
                if not where.exists():
                    broken.append("%s -> %s" % (page.relative_to(DIST), raw))
                    continue

            # The half of a link that a plain existence check throws away.
            # A heading that gets reworded does not break the page it is on,
            # it breaks every link that pointed at it — silently, landing the
            # reader at the top of a long page wondering what they missed.
            if fragment:
                fragments += 1
                if fragment not in ids_in(where):
                    dangling.append("%s -> %s" % (page.relative_to(DIST), raw))

check("every local link and asset resolves", not broken,
      "%d checked" % checked if not broken else "; ".join(broken[:3]))
check("every #anchor points at something", not dangling,
      "%d checked" % fragments if not dangling else "; ".join(dangling[:3]))

# --------------------------------------------------------- the nav is whole
home = (DIST / "index.html")
if home.is_file():
    nav = re.search(r'<nav class="top-nav"[^>]*>(.*?)</nav>', home.read_text(), re.S)
    targets = re.findall(r'href="([^"]+)"', nav.group(1)) if nav else []
    missing = [t for t in targets
               if not (DIST / t.lstrip("./") / "index.html").exists()
               and not (DIST / t.lstrip("./")).is_file()
               and t not in ("./", "")]
    check("every page in the nav exists", not missing, ", ".join(missing))

# ------------------------------------------------------- the playground runs
play = DIST / "play" / "index.html"
if play.is_file():
    text = play.read_text()
    engine = DIST / "engine" / "kaypy_bundle.json"
    check("the playground has an engine to run", engine.is_file(),
          "%.0f KB" % (engine.stat().st_size / 1024) if engine.is_file()
          else "run python3 vendor.py")
    check("and sprites to load", (DIST / "assets" / "images").is_dir())
    for gone in ("/login", "signed_in", "autosave", "assignment"):
        if gone in text:
            check("the playground carries no account code: " + gone, False)
else:
    print("  note  no playground yet")

# --------------------------------------------------------------- page size
big = [(p.relative_to(DIST), p.stat().st_size) for p in pages
       if p.stat().st_size > 400_000]
check("no page is absurdly large", not big,
      ", ".join("%s %.0f KB" % (n, s / 1024) for n, s in big[:2]))

bad = results.count(False)
print("\n%s (%d checks, %d failed)"
      % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
sys.exit(1 if bad else 0)
