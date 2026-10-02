# kaypy-site

The kaypy website: the guide, the API reference, the tutorials, eight Learn
Python lessons, a games page, and a playground you can write a game in.

**There is no backend.** Not a small one — none. Everything happens in the
visitor's browser: Pyodide brings Python, kaypy is written into its
filesystem, sprites are fetched like any other static asset. It deploys as a
Render **Static Site** with the publish directory set to `site`.

**And there is no build.** `site/` *is* the website — hand-written HTML, CSS
and JavaScript, with Bootstrap 5 and highlight.js from a CDN. The file you
edit is the file Render serves. Nothing generates a page from anything.

That choice has one cost, and it is worth knowing before you change a page:
**shared furniture is duplicated**. The navbar, the head and the footer exist
in every page, so a change to the Learn Python menu is a change to fifteen
files. `test_pages.py` is what keeps them honest.

## Checking it

```
python3 check_site.py                       # links, anchors, page sizes
python3 test_pages.py                       # the shell, the navbar, classes
python3 test_lesson.py  --kaypy ~/kaypy     # runs every lesson program
python3 test_api.py     --kaypy ~/kaypy     # runs every API example
python3 test_playground.py --kaypy ~/kaypy
python3 test_tabstops.py
python3 test_zip.py
```

`test_tabstops.py` and `test_zip.py` need `node` — they run this repo's own
JavaScript rather than describing it. `brew install node` if it is missing.

Nothing above stops on a failure, so read the last line of each rather than
assuming a long green-looking scroll was green.

`--offline` on `test_pages.py` skips the checks that fetch Bootstrap and
highlight.js. The sandbox used to build this could not reach jsDelivr, so
those degrade to a note rather than a failure — which means **they only
really run on a machine with network**, and a green run without it has not
checked them.

**Every check must have been watched to fail.** Sabotage the thing it guards,
confirm it fails, restore. Several checks here were dead when written.

## The two things most likely to bite

**Every code block on a lesson or API page is executed.** `test_lesson.py`
and `test_api.py` pull the blocks out of the built HTML with `pagecode.py`,
run them on real kaypy, and compare the printed output line for line against
what the page claims. A printed output on a teaching page is a *claim*, and a
student who sees it disagree concludes they are wrong, not the page.

Blocks that ask a question carry `data-stdin="Ada|12"` on the `<code>` tag —
the answers a reader types, fed in on stdin, with `input()` wrapped so it
echoes exactly as the browser does. The answers live on the page rather than
in the test file because a table in the test goes stale the moment a block is
inserted above it, and taking them out of the claimed output would be
circular.

**highlight.js publishes two packages and only one works in a browser.** Use
`@highlightjs/cdn-assets`. The plain `highlight.js` package is the Node build:
its `lib/` files are CommonJS, they throw before setting `window.hljs`, and
`site.js` — which asks `if (window.hljs)` first — then silently colours
nothing. The whole site was grey for weeks and nothing said a word. Checking
for the absence of `module.exports` does **not** distinguish them; the browser
build has a UMD tail that contains it. The test asks whether the file defines
a global `hljs`, which is the question that matters.

## Layout

```
site/            the website, served as-is
  learn/         eight lessons, one folder each
  guide/ api/ tutorials/ games/ start/ play/
  static/        site.css, site.js, the exported games
  assets/        sprite packs and the manifest
  static/games/  one folder per game: index.html (built by `kaypy web`)
                 and the program as a .py beside it, which the Games page
                 links on GitHub. Rebuild a game, rewrite its .py --
                 test_pages.py fails if the two differ by a byte
pagecode.py      pulls code blocks and headings out of built HTML
vendor.py        copies the engine and assets in from PyIDE
```

The playground (`site/play/`) is vendored from PyIDE: `runtime.js`,
`game.js`, `export.js`, `sprites.js`, `complete.js` and `style.css` are
copies. `play.js` is this site's own — it has no accounts, no server and no
upload, on purpose.

**`site/play/sprites.js` has deliberately diverged from PyIDE's.** PyIDE's
sprite panel now writes the load line only; the playground still writes the
`add([...])` as well, because a visitor with no lesson around them benefits
from seeing something appear. Do not "resync" it.

## Style

Prose is written for a student who does not yet know enough to tell a typo
from their own mistake. Say what goes wrong and what the error message will
look like. Comments in the HTML and CSS explain the traps — the navbar
collapse needing a matching `data-bs-target` *and* a viewport meta, the two
highlight.js themes chosen by media query so the page never flashes light
before going dark.
