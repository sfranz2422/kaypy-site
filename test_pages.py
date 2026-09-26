#!/usr/bin/env python3
"""The pages say things that are true, and the header links what it should.

    python3 test_pages.py --kaypy ~/kaypy

check_site.py already follows every link and catches dead ones. This is the
other half: a page can link perfectly and still be wrong.

WHAT GOES WRONG HERE, AND LOOKS FINE

  * Get started prints a command that no longer exists. `kaypy new` is not
    checked by anything — the page is HTML, the CLI is Python, and the only
    thing joining them is that somebody typed both. A reader follows the page,
    gets "invalid choice", and concludes the project is broken.

  * The Games page links a game that is not a kaypy game. There are five
    folders under site/static/games/ and three of them are JavaScript Kaplay,
    which look identical from the outside and would be a lie on a page headed
    "written in Python with kaypy".

  * The submission form's address is set to something that is not a form. An
    iframe with a wrong address renders BLANK — no error, no broken-image
    icon, nothing — and is found by somebody failing to send you a game.

  * A page uses a class with no rule anywhere. Since the move to Bootstrap
    this is the easiest mistake on the site to make and the hardest to see:
    `btn-outline-kaypy` is one of ours and `btn-outline-primary` is
    Bootstrap's, and a typo in either renders as an unstyled rectangle that
    still says the right words.

  * The navbar falls a page behind. It is written into all eleven pages now
    rather than generated into them once, so the header is eleven copies of
    itself and a new page reaches ten of them.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

import pagecode

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE / "site"

BOOTSTRAP_CSS = ("https://cdn.jsdelivr.net/npm/bootstrap@5.3.3"
                 "/dist/css/bootstrap.min.css")

#: Every page, as the path under site/ that a reader reaches. Written down
#: rather than globbed: a glob cannot tell a page that should exist from one
#: that does, so a page deleted by accident would simply stop being checked.
PAGES = [
    "index.html",
    "start/index.html",
    "learn/index.html",
    "learn/conditionals/index.html",
    "learn/loops/index.html",
    "learn/lists/index.html",
    "guide/index.html",
    "api/index.html",
    "tutorials/index.html",
    "games/index.html",
    "play/index.html",
    "404.html",
]

#: What the header must offer, as the tail of each link. The playground has its
#: own bar rather than the site navbar, so it is checked separately below.
NAV_TAILS = ["start/", "learn/", "guide/", "api/", "tutorials/", "games/",
             "play/"]

results = []


def check(label, ok, detail=""):
    """Detail is printed only on a FAILURE.

    Printed on a pass it reads as evidence for the opposite: "ok — flappy is
    really a kaypy game — no mention of pyodide" says two contradictory things
    on one line, and the eye believes the second.
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
ap.add_argument("--offline", action="store_true",
                help="skip the check that needs Bootstrap's stylesheet")
args = ap.parse_args()

# =============================================================== every page is there
pages = {}
for rel in PAGES:
    path = SITE / rel
    check("%s exists" % rel, path.is_file())
    if path.is_file():
        pages[rel] = path.read_text()

if not pages:
    done()

# ====================================================== no unfilled template slots
#
# There is no build any more, so nothing fills a {{SLOT}} — which makes one
# left in a page permanent. It renders as literal text, which is the one kind
# of rot a reader sees immediately and nobody editing locally ever does.
leftover = []
for rel, page in pages.items():
    for slot in re.findall(r"\{\{[A-Z_]+\}\}", page):
        leftover.append("%s in %s" % (slot, rel))
for extra in SITE.rglob("*.js"):
    for slot in re.findall(r"\{\{[A-Z_]+\}\}", extra.read_text(errors="ignore")):
        leftover.append("%s in %s" % (slot, extra.relative_to(SITE)))
check("no {{SLOT}} survives anywhere in the site", not leftover,
      "; ".join(leftover[:3]))

# ============================================================= the navbar, everywhere
#
# Eleven hand-written copies of the same header. This is the cost of dropping
# the build, and it is paid here rather than by a reader.
for rel, page in pages.items():
    if rel == "play/index.html":
        continue
    depth = rel.count("/")
    root = "./" if depth == 0 else "../" * depth
    missing = [t for t in NAV_TAILS if 'href="%s%s"' % (root, t) not in page]
    if rel == "404.html":
        # Root-absolute: a 404 is served for whatever the reader typed, and
        # relative links would resolve against THAT address.
        missing = [t for t in NAV_TAILS if 'href="/%s"' % t not in page]
    check("%s links every page in the header" % rel, not missing,
          "missing: %s" % missing)

# The playground has its own bar, and its own copy of the same links.
play = pages.get("play/index.html", "")
missing = [t for t in NAV_TAILS if 'href="../%s"' % t not in play]
check("the playground's bar links every page", not missing,
      "missing: %s" % missing)

# ================================================== the navbar collapses on a phone
#
# This is the whole reason the site moved to Bootstrap. Three parts, and
# missing any one of them leaves a header that is broken in a different way:
# no toggler and the menu is simply gone on a phone; no matching id and the
# button is dead; no `collapse` class and the menu is permanently open and
# overflowing, which is the state it was in before.
for rel, page in pages.items():
    if rel == "play/index.html":
        continue
    target = re.search(r'data-bs-target="#([\w-]+)"', page)
    ok = bool(target) and 'id="%s"' % target.group(1) in page
    check("%s has a toggler wired to its menu" % rel, ok,
          "no data-bs-target" if not target
          else "nothing has id=%s" % target.group(1))
    check("  and the menu is a collapse",
          'class="collapse navbar-collapse"' in page)
    check("  and the navbar is told to expand at lg",
          "navbar-expand-lg" in page)
    check("  and Bootstrap's JavaScript is loaded to work the toggler",
          "bootstrap.bundle.min.js" in page)
    # WITHOUT THIS META TAG NONE OF THE ABOVE DOES ANYTHING ON A PHONE.
    # A mobile browser with no viewport tag lays the page out at ~980px and
    # then zooms the whole thing out, so every Bootstrap breakpoint reports
    # "desktop", the navbar never collapses, and the page looks exactly like
    # the broken one it replaced — just smaller. This is the single tag the
    # entire mobile header depends on.
    check("  and a viewport tag, or the breakpoints never fire on a phone",
          re.search(r'<meta\s+name="viewport"[^>]*width=device-width', page)
          is not None)
    check("  and Bootstrap's stylesheet, not just its JavaScript",
          "bootstrap@5.3.3/dist/css/bootstrap.min.css" in page)

# ================================================ code is coloured, and readable dark
#
# Three separate silent failures, none of which raises:
#
#   * the language class on the <pre> instead of the <code>. highlight.js reads
#     it off the code element; on the pre it is ignored and the block renders in
#     flat grey.
#   * highlight.js loaded without the python grammar. core.min.js alone knows
#     no languages, so highlightElement throws per block and every one stays
#     grey.
#   * one highlight.js theme instead of two. github.min.css on its own gives a
#     reader in dark mode near-black text on a near-black background.
for rel, page in pages.items():
    if rel == "play/index.html":
        continue        # CodeMirror, not highlight.js
    if "<pre" not in page:
        continue
    check("%s puts the language on the <code>, not the <pre>" % rel,
          '<pre class="language-' not in page
          and '<pre><code class="language-' in page)
    check("  and loads the python grammar, not just highlight.js's core",
          "languages/python.min.js" in page)
    check("  and a dark code theme as well as a light one",
          "github-dark.min.css" in page and "github.min.css" in page)
    check("  chosen by media attribute, not by a script after first paint",
          page.count('media="(prefers-color-scheme:') >= 2)
    check("  and tells Bootstrap's own components about dark, in the head",
          'setAttribute("data-bs-theme", "dark")' in page)

# ======================================================= the old shell is gone
#
# The hand-rolled header this replaced had its own markup. A page that kept any
# of it would render with an unstyled duplicate header above the real one: the
# rules are deleted from site.css, so the markup is invisible rather than wrong.
GONE = ['class="top"', 'class="top-nav"', 'class="gh"', 'class="brand"',
        'class="cta ', 'class="cards"', "{{TOC}}"]
for rel, page in pages.items():
    if rel == "play/index.html":
        continue        # its bar legitimately uses class="brand"
    left = [g for g in GONE if g in page]
    check("%s has none of the old header left in it" % rel, not left, str(left))

# ===================================================== Learn Python is split up
#
# The single Learn page had a twelve-hundred-line sidebar down its right, which
# is what prompted the split. These check the split actually happened rather
# than that three files exist.
hub = pages["learn/index.html"]
for slug in ("conditionals", "loops", "lists"):
    check("the hub links the %s lesson" % slug,
          'href="%s/"' % slug in hub)
    lesson = pages["learn/%s/index.html" % slug]
    check("  and %s is one lesson, not all three" % slug,
          len(re.findall(r"<h1[^>]*>", lesson)) == 1
          and lesson.count("Classwork") <= 4,
          "%d h1, %d mentions of Classwork"
          % (len(re.findall(r"<h1[^>]*>", lesson)), lesson.count("Classwork")))
    check("  and the dropdown in its own header reaches the other two",
          all('href="../../learn/%s/"' % other in lesson
              for other in ("conditionals", "loops", "lists")),
          "the header dropdown is incomplete")

check("the hub is not still carrying the lessons itself",
      hub.count("Classwork") <= 1, "%d mentions" % hub.count("Classwork"))

# ================================================== the games are kaypy games
games = pages["games/index.html"]
linked = re.findall(r'href="\.\./static/games/([A-Za-z0-9_\-]+)/"', games)
check("the Games page links some games", len(linked) >= 2, str(linked))

for name in linked:
    index = SITE / "static" / "games" / name / "index.html"
    if not index.is_file():
        check("  %s exists" % name, False, "no index.html")
        continue
    text = index.read_text(errors="ignore")
    # A kaypy export runs Python: it loads Pyodide. The JavaScript Kaplay games
    # in the same folder do not, and are indistinguishable from the outside —
    # same folder, same index.html, same canvas.
    check("  %s really is a kaypy game (it loads Python)" % name,
          "pyodide" in text.lower(), "no mention of pyodide")

all_games = sorted(p.name for p in (SITE / "static" / "games").iterdir()
                   if p.is_dir())
js_only = [g for g in all_games if g not in linked]
print("      (not linked, and correctly so — these are JavaScript Kaplay: %s)"
      % ", ".join(js_only))
for name in js_only:
    index = SITE / "static" / "games" / name / "index.html"
    if index.is_file():
        check("  %s is NOT claimed as kaypy" % name,
              "pyodide" not in index.read_text(errors="ignore").lower(),
              "it loads Pyodide — it may belong on the page after all")

# ================================================== the submission form
form = re.search(r'<iframe\b[^>]*?\bsrc="([^"]+)"[^>]*>', games)
check("the Games page embeds the submission form", form is not None)
if form:
    url = form.group(1)
    # A Google Form embeds from /viewform?embedded=true. The edit link, or the
    # short forms.gle link, renders an empty white box instead.
    check("  from a real Google Forms embed address",
          url.startswith("https://docs.google.com/forms/")
          and "/viewform" in url and "embedded=true" in url, url)
    check("  not the EDIT link, which only you can open", "/edit" not in url, url)
    check("  and the iframe is given a height, or it collapses to nothing",
          re.search(r'height="[1-9]\d{2,}"', form.group(0)) is not None,
          form.group(0)[:90])

# ============================================ every class has a rule somewhere
#
# Ours are in site/static/site.css; Bootstrap's are in the CDN file the pages
# load. A class in neither is a typo, and a typo in a class name is invisible:
# the element renders, unstyled, saying the right words.
ours = set(re.findall(r"\.(-?[A-Za-z_][\w-]*)",
                      (SITE / "static" / "site.css").read_text()))

theirs = set()
if args.offline:
    print("      (--offline: Bootstrap's own classes were not fetched)")
else:
    try:
        with urllib.request.urlopen(BOOTSTRAP_CSS, timeout=15) as res:
            theirs = set(re.findall(r"\.(-?[A-Za-z_][\w-]*)",
                                    res.read().decode("utf-8", "replace")))
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        print("      (could not fetch Bootstrap's CSS: %s — pass --offline "
              "to skip this on purpose)" % err)

if theirs:
    check("  Bootstrap's stylesheet was really read",
          len(theirs) > 500 and "container" in theirs, "%d classes" % len(theirs))
    known = ours | theirs
    unstyled = {}
    for rel, page in pages.items():
        if rel == "play/index.html":
            continue     # its own stylesheet, checked by test_playground.py
        # Code blocks first: highlight.js puts its own token classes on every
        # span inside them at RUN time, and those are in its stylesheet, not
        # in either of these two.
        body = pagecode._BLOCK.sub(" ", page)
        for value in re.findall(r'class="([^"]+)"', body):
            for name in value.split():
                if name not in known:
                    unstyled.setdefault(name, rel)
    check("every class the pages use has a rule somewhere", not unstyled,
          "; ".join("%s (%s)" % (k, v) for k, v in sorted(unstyled.items())[:4]))

# ====================================== Get started names real commands
start = pages["start/index.html"]
# ONLY FROM CODE BLOCKS. Scanning the whole page pulled in the sentence
# "kaypy needs Python 3.10 or newer" and then went looking for a subcommand
# called `needs`. A command is a thing in a code block; prose is prose.
fenced = "\n".join(code for _lang, code, _s, _e in pagecode.blocks(start))
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

    module_calls = re.findall(r"python -m (kaypy\S*)", fenced)
    bad_module = [m for m in module_calls
                  if not (root / m.replace(".", "/")).with_suffix(".py").is_file()]
    check("  a `python -m ...` line points at a module that exists",
          not bad_module, str(bad_module))
else:
    print("      (no --kaypy given, so the commands were not run)")

done()
