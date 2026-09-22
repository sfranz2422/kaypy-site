#!/usr/bin/env python3
"""Turn content/ into dist/, which is what Render serves.

    python3 build.py            build
    python3 build.py --serve    build, then serve dist/ at 127.0.0.1:8000
    python3 build.py --check    fail if dist/ is out of date

WHY THE OUTPUT IS COMMITTED

Render is told to run **no build command at all**; it publishes `dist/` as it
finds it. That is not laziness, it is the point. A static site whose deploy
depends on pip resolving two packages on someone else's builder is a static
site that can fail on a morning nobody touched it — during a lesson, for
reasons that have nothing to do with the site. Generating here and committing
the result means the only thing that can go wrong at deploy time is the file
copy.

The cost is that `dist/` has to be regenerated and committed whenever content
changes, and forgetting is easy. `--check` is for that: it rebuilds into a
temporary directory and fails if the result differs from what is committed, so
a pre-push hook or a quick habit catches the omission rather than a visitor
reading last week's page.

SYNTAX HIGHLIGHTING HAPPENS HERE

Not in the browser. Code is highlighted into the HTML at build time, so the
page needs no JavaScript to be readable, there is no flash of unstyled code,
and a reader with a blocked CDN still gets a page. For a site whose whole
audience is beginners reading code, that seemed worth the extra second here.
"""
from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import shutil
import sys

import vendor   # for the list of modules a rebuild must not delete

HERE = pathlib.Path(__file__).resolve().parent
CONTENT = HERE / "content"
TEMPLATES = HERE / "templates"
STATIC = HERE / "static"
PLAY = HERE / "play"
DIST = HERE / "dist"

SITE_NAME = "KayPy"
TAGLINE = ("A game engine for learning Python — build a game out of "
           "components, run it in the browser, share it as one file.")

#: Every page the site can have, in nav order. (slug, title, source or None)
#:
#: A source of None means the page is not built from markdown — Home comes
#: from templates/home.html, the playground from play/.
PAGES = [
    ("", "Home", None),
    ("start", "Get started", "start.md"),
    ("guide", "Guide", "guide.md"),
    ("api", "API", "api.md"),
    ("tutorials", "Tutorials", "tutorials.md"),
    ("play", "Playground", None),
]


def nav_pages():
    """The pages that actually exist, which is what the nav may link to.

    A nav entry for a page with no content is a dead link in the header of
    every page on the site — the most visible possible place for one, and it
    does not fail anywhere: the build succeeds, the deploy succeeds, and a
    reader clicks Guide and gets a 404. So the nav is derived rather than
    declared, and a page joins it by existing. Writing content/guide.md is
    the whole of adding the Guide back.
    """
    return [(slug, title, source) for slug, title, source in PAGES
            if source is None or (CONTENT / source).is_file()]


#: Kept as a module-level name because page_shell() and the playground both
#: read it, and both want the same answer.
NAV = nav_pages()


def need(module, why):
    try:
        return __import__(module)
    except ImportError:
        sys.exit(
            f"build.py needs `{module}` ({why}).\n"
            f"    pip install -r requirements.txt\n"
            f"\nOnly building needs it. Render does not run this script — it\n"
            f"serves the committed dist/ — so a visitor is never affected."
        )


markdown = need("markdown", "to turn the content into HTML")
need("pygments", "to highlight the code samples")


# --------------------------------------------------------------- rendering

def render_markdown(text):
    """Markdown to HTML, with tables, fenced code and highlighting."""
    md = markdown.Markdown(
        extensions=["fenced_code", "codehilite", "tables", "toc", "attr_list"],
        extension_configs={
            "codehilite": {"guess_lang": False, "css_class": "hl"},
            "toc": {"permalink": False},
        },
    )
    body = md.convert(text)
    return body, getattr(md, "toc_tokens", [])


def page_shell(slug, title, body, toc=(), subtitle=None):
    shell = (TEMPLATES / "page.html").read_text()

    depth = "" if slug in ("", ".") else "../"
    nav = []
    for item_slug, item_title, _ in NAV:
        href = (depth or "./") if item_slug == "" else f"{depth}{item_slug}/"
        current = ' class="current"' if item_slug == slug else ""
        nav.append(f'<a href="{href}"{current}>{html.escape(item_title)}</a>')

    sidebar = ""
    if toc:
        links = []
        for entry in toc:
            links.append(
                f'<a href="#{entry["id"]}" class="d{entry["level"]}">'
                f'{html.escape(entry["name"])}</a>')
            for child in entry.get("children", []):
                links.append(
                    f'<a href="#{child["id"]}" class="d{child["level"]}">'
                    f'{html.escape(child["name"])}</a>')
        sidebar = ('<nav class="toc" aria-label="On this page">'
                   '<p class="toc-head">On this page</p>'
                   + "".join(links) + "</nav>")

    # A None title means this page IS the site (the home page), so the
    # <title> is just the site name rather than "kaypy · kaypy".
    full_title = html.escape(title) + " · " + html.escape(SITE_NAME) \
        if title else html.escape(SITE_NAME)

    return (shell
            .replace("{{TITLE}} · {{SITE}}", full_title)
            .replace("{{TITLE}}", html.escape(title or SITE_NAME))
            .replace("{{SITE}}", html.escape(SITE_NAME))
            .replace("{{SUBTITLE}}", html.escape(subtitle or TAGLINE))
            .replace("{{NAV}}", "".join(nav))
            .replace("{{TOC}}", sidebar)
            .replace("{{BODY}}", body)
            .replace("{{ROOT}}", depth or "./")
            .replace("{{CLASS}}", "with-toc" if toc else "plain"))


# ------------------------------------------------------------------ build

def build(into=DIST):
    into = pathlib.Path(into)
    # Everything except what vendor.py owns: the engine, the sprite packs and
    # the modules shared with PyIDE, which must survive a rebuild.
    #
    # The list of those modules is asked of vendor.py rather than repeated
    # here. Written down twice, a module added to one list and not the other
    # gets deleted by every build and restored by every vendor, which looks
    # like the playground working until the day somebody deploys without
    # re-vendoring first.
    vendored = set(vendor.MODULES) | set(vendor.STYLES)
    for item in into.iterdir() if into.exists() else []:
        if item.name in {"engine", "assets"}:
            continue
        if item.name == "play" and (item / "game.js").exists():
            for inner in item.iterdir():
                if inner.name not in vendored:
                    shutil.rmtree(inner) if inner.is_dir() else inner.unlink()
            continue
        shutil.rmtree(item) if item.is_dir() else item.unlink()
    into.mkdir(parents=True, exist_ok=True)

    written = []

    # static files (css, logo, favicons)
    if STATIC.exists():
        shutil.copytree(STATIC, into / "static", dirs_exist_ok=True)
        written += [f"static/{p.name}" for p in STATIC.rglob("*") if p.is_file()]

    # The playground's own shell. Not a content page — it is an application,
    # so it brings its own <head> and layout rather than going through
    # page_shell. But its header must be the site's header, and the nav must
    # be the same nav, so those two slots are filled here. A playground with a
    # nav that has quietly fallen a page behind is how a reader ends up
    # stranded in it.
    (into / "play").mkdir(exist_ok=True)
    for name in ("play.html", "play.js", "play.css"):
        source = PLAY / name
        if not source.exists():
            continue
        text = source.read_text()
        if name == "play.js":
            # The starter program, from the real .py file, as one JSON string.
            # json.dumps is what makes this safe: quotes, backslashes and
            # newlines in Python source are escaped for JavaScript by a
            # library rather than by hand.
            starter = (PLAY / "starter.py").read_text()
            if "{{STARTER}}" not in text:
                sys.exit("play.js has no {{STARTER}} slot — the starter would "
                         "never reach the page.")
            text = text.replace("{{STARTER}}", json.dumps(starter))
        if name == "play.html":
            nav = []
            for item_slug, item_title, _ in NAV:
                href = "../" if item_slug == "" else f"../{item_slug}/"
                current = ' class="current"' if item_slug == "play" else ""
                nav.append(f'<a href="{href}"{current}>'
                           f'{html.escape(item_title)}</a>')
            text = (text.replace("{{NAV}}", "".join(nav))
                        .replace("{{ROOT}}", "../"))
        target = into / "play" / ("index.html" if name == "play.html" else name)
        target.write_text(text)
        written.append(f"play/{target.name}")

    # the content pages
    for slug, title, source in NAV:
        if source is None:
            continue
        md_path = CONTENT / source
        if not md_path.is_file():
            print(f"  note: no content/{source} yet — skipping {title}")
            continue
        body, toc = render_markdown(md_path.read_text())
        out_dir = into if slug == "" else into / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(page_shell(slug, title, body, toc))
        written.append(f"{slug}/index.html" if slug else "index.html")

    # the home page, which is its own template rather than markdown
    home = TEMPLATES / "home.html"
    if home.is_file():
        body = home.read_text()
        (into / "index.html").write_text(
            page_shell("", None, body, subtitle=TAGLINE))
        written.append("index.html")

    # Render serves /404.html for anything missing on a static site.
    missing = CONTENT / "404.md"
    if missing.is_file():
        body, _ = render_markdown(missing.read_text())
        # Root-absolute, not relative. A 404 is served for whatever the
        # reader typed — /guide/oops, /a/b/c — and the browser resolves the
        # page's links against THAT address, not against /404.html. Relative
        # links would point somewhere different on every wrong URL.
        page = page_shell(".", "Not found", body)
        page = page.replace('href="./', 'href="/').replace('src="./', 'src="/')
        (into / "404.html").write_text(page)
        written.append("404.html")

    return written


def check():
    """Is the committed dist/ what build.py would produce right now?"""
    import filecmp
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        fresh = pathlib.Path(tmp) / "dist"
        # Start from the committed one so vendored files are present, then
        # rebuild the generated parts over the top.
        if DIST.exists():
            shutil.copytree(DIST, fresh)
        build(fresh)

        stale = []
        for path in sorted(fresh.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(fresh)
            committed = DIST / rel
            if not committed.is_file():
                stale.append(f"missing from dist/: {rel}")
            elif not filecmp.cmp(path, committed, shallow=False):
                stale.append(f"out of date:       {rel}")

    if stale:
        print("dist/ does not match the source:\n")
        for line in stale:
            print("   ", line)
        print("\n    python3 build.py      # then commit dist/ as well")
        return 1
    print("dist/ is up to date with the source.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--serve", action="store_true",
                    help="serve dist/ after building")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--check", action="store_true",
                    help="fail if dist/ is out of date, and build nothing")
    args = ap.parse_args()

    if args.check:
        return check()

    written = build()
    print(f"built {len(written)} files into dist/")
    for name in written[:12]:
        print("   ", name)
    if len(written) > 12:
        print(f"    ... and {len(written) - 12} more")

    if not (DIST / "engine").exists():
        print("\nnote: no engine yet — the playground will not run.")
        print("      python3 vendor.py")

    if args.serve:
        import http.server
        import socketserver
        import functools

        handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                    directory=str(DIST))
        with socketserver.TCPServer(("127.0.0.1", args.port), handler) as srv:
            print(f"\n  serving dist/ at http://127.0.0.1:{args.port}")
            print("  Ctrl-C to stop\n")
            try:
                srv.serve_forever()
            except KeyboardInterrupt:
                pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
