#!/usr/bin/env python3
"""Read the code and the headings back out of a built page.

WHY THIS EXISTS

The site used to be markdown compiled by build.py, and three test scripts read
that markdown: they pulled every ```python block out of content/api.md and
content/learn.md and RAN it on real kaypy, comparing printed output against
what the page claims. That is the only reason a beginner following the API
reference can trust that the example in front of them works.

The markdown is gone — the pages are hand-written HTML now. The checks are not
worth losing over that, so this module does the same job one step later: it
takes the HTML and hands back the same (language, code, position) tuples the
markdown regex used to produce, so the suites carry on running every example.

TWO THINGS THAT WOULD MAKE THIS LIE, AND ARE GUARDED

  * &amp;lt; and friends. Code inside <pre><code> is HTML-escaped, so a page
    showing `if x < 3:` holds `if x &lt; 3:`. Run unescaped, that is a syntax
    error in a program the page is right about. html.unescape fixes it, and
    `blocks` is where it must happen — not in each caller.

  * A block with no language. Markdown's ``` with no word after it became
    <pre><code> with no class, and those are the OUTPUT blocks the lessons
    print underneath a program. They must come back as language "", in
    document order, or every program is compared against the wrong output.
"""
from __future__ import annotations

import html
import re

#: <pre> then <code>, with the language class on the code element where
#: highlight.js wants it. The class is optional: a block without one is an
#: output block, and has to be reported as such rather than skipped.
_BLOCK = re.compile(
    r"<pre[^>]*>\s*<code(?P<attrs>[^>]*)>(?P<code>.*?)</code>\s*</pre>",
    re.S)

_LANG = re.compile(r'class="[^"]*\blanguage-([A-Za-z0-9_+-]+)')

_HEADING = re.compile(r"<(h[1-6])\b[^>]*>(?P<text>.*?)</\1>", re.S)

_TAG = re.compile(r"<[^>]+>")


def blocks(page: str):
    """Every code block, as (language, code, start, end) in document order.

    `language` is "" for a block that does not say what it is. `code` is
    unescaped and ends with a newline, exactly as the markdown fence did.
    `start` and `end` are offsets into `page`, so a caller can ask what sits
    between two blocks — which is how the lessons decide whether an output
    block belongs to the program above it.
    """
    out = []
    for match in _BLOCK.finditer(page):
        lang = _LANG.search(match.group("attrs"))
        code = html.unescape(_TAG.sub("", match.group("code")))
        if not code.endswith("\n"):
            code += "\n"
        out.append((lang.group(1) if lang else "", code,
                    match.start(), match.end()))
    return out


def headings(page: str):
    """Every heading, as (level, text, position) — level being 1..6.

    The text is the heading's words with markup removed and entities undone,
    so `<h3 id="onkeydown"><code>onKeyDown()</code></h3>` reads as
    "onKeyDown()" — which is what a check on a documented name needs. The
    position lets a caller work out which heading a code block sits under.
    """
    out = []
    for match in _HEADING.finditer(page):
        text = html.unescape(_TAG.sub("", match.group("text")))
        out.append((int(match.group(1)[1]), " ".join(text.split()),
                    match.start()))
    return out


def text_only(page: str) -> str:
    """The page with its code blocks, script, style and markup removed.

    For checks that read the prose. Code is dropped first: a check looking for
    a command the page recommends should not match a comment inside an example
    that says not to use it.
    """
    body = re.sub(r"<(script|style)\b.*?</\1>", " ", page, flags=re.S)
    body = _BLOCK.sub(" ", body)
    return html.unescape(_TAG.sub(" ", body))


if __name__ == "__main__":
    import pathlib
    import sys

    for name in sys.argv[1:]:
        page = pathlib.Path(name).read_text()
        found = blocks(page)
        langs = {}
        for lang, _code, _start, _end in found:
            langs[lang or "(none)"] = langs.get(lang or "(none)", 0) + 1
        print("%s: %d blocks %s, %d headings"
              % (name, len(found), langs, len(headings(page))))
