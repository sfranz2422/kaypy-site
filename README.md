# kaypy-site

The kaypy website: the guide, the API reference, the tutorials, and a
playground you can write a game in.

**There is no backend.** Not "a small one" — none. Everything the playground
does happens in the visitor's browser: Pyodide brings Python, kaypy is written
into its filesystem as files, and the sprite packs are fetched like any other
static asset. So this deploys as a Render **Static Site**, costs nothing to
run, and has nothing that can be down.

**And there is no build.** `site/` is the website: hand-written HTML, CSS and
JavaScript, with Bootstrap 5 and highlight.js from a CDN. The file you edit is
the file Render serves. Nothing generates a page from anything, so there is no
step to forget, no output to commit alongside a source, and nothing to install
before you can change a sentence.

## Deploying

Render → New → Static Site → this repo.

| | |
|---|---|
| Build command | *leave it empty* |
| Publish directory | `site` |

> **If you are looking at an older deploy, the publish directory used to be
> `dist`.** That folder is now called `site`, and Render will 404 the whole
> site until the setting is changed. It is one dropdown: Settings → Build &
> Deploy → Publish Directory.

`SKIP_INSTALL_DEPS` is no longer needed. It was there because Render detected
`requirements.txt` and pip-installed markdown and pygments on every deploy;
there is no `requirements.txt` any more, because nothing here needs a package
to run. (Leaving the variable set does no harm.)

**Render serves `site/404.html` for a missing path on its own.** Verified on
the live site; no rewrite rule needed. (Their docs do not say so, hence the
note.) Its links are root-absolute — `/guide/`, not `../guide/` — because a
404 is served for whatever the reader typed, and the browser resolves relative
links against *that* address.

**A `.app` domain is HSTS-preloaded**, so browsers refuse it over plain HTTP,
always. While DNS propagates and before the certificate is issued you get a
TLS error page rather than the usual "site can't be reached" — expected, and
not a sign the DNS is wrong. GoDaddy has no ANAME/ALIAS, so the apex is an
`A` record to Render's load balancer and `www` is a `CNAME`.

## Working on it

Edit the HTML. To see it:

```bash
python3 -m http.server -d site 8000     # then http://127.0.0.1:8000
```

A file:// URL mostly works too, but not for the playground: it fetches
`starter.py`, and a `fetch()` from `file://` is blocked. Use the server.

### Adding a page

Copy the nearest existing page and edit it. The parts to change are the
`<title>`, the `<meta name="description">`, and the `active` class in the
navbar — and then **the navbar in every other page**, because the header is
now eleven hand-written copies of itself rather than one template. That is the
price of having no build, and `test_pages.py` collects it: it checks every
page links every other, so a half-added page fails there rather than stranding
a reader.

`../` depth matters. A page at `site/guide/index.html` reaches the root with
`../`; a lesson at `site/learn/loops/index.html` needs `../../`. Getting this
wrong produces a link to `/learn/guide/`, which is a 404 that renders
perfectly. `check_site.py` follows every link and catches it.

### Code blocks

```html
<pre><code class="language-python">player = add([sprite("bean")])
</code></pre>
```

**The class goes on the `<code>`, not the `<pre>`.** highlight.js reads it off
the code element; on the pre it is ignored, the block renders in flat grey, and
nothing errors. A block with no class at all is deliberate — the lessons use
those for the output a program prints, and `test_lesson.py` pairs each one with
the program directly above it.

### Checking it

Nothing here needs a package, and all of it is worth running before a deploy:

```bash
python3 check_site.py                   # every link, anchor and asset
python3 test_pages.py --kaypy ~/kaypy   # the header, the nav, the classes,
                                        #   the form, the commands it names
python3 test_api.py --kaypy ~/kaypy     # RUNS all 141 examples on real kaypy
python3 test_lesson.py --kaypy ~/kaypy  # RUNS all 45 lesson programs and
                                        #   compares the printed output
python3 test_playground.py --kaypy ~/kaypy
python3 test_tabstops.py
python3 test_zip.py
```

The two that run code are the ones that matter most. An API reference is read
by somebody who copies one example and expects it to work, and a lesson's
printed output is a claim a student will believe over their own eyes. Both used
to read the markdown; the markdown is gone, so `pagecode.py` lifts the same
blocks back out of the HTML and they carry on running.

`test_pages.py` fetches Bootstrap's stylesheet to check that every class on
every page has a rule *somewhere* — ours in `site/static/site.css`, theirs in
the CDN file. A class in neither is a typo, and a typo in a class name renders
as an unstyled rectangle saying the right words. Pass `--offline` to skip that
one check on a network that will not allow it.

## What was lost when the build went, and what to do about it

Worth knowing, because it is the one real cost:

**The Guide no longer tracks `kaypy/GUIDE.md`.** `guide.py` used to paste those
thirteen lessons in, checking that an edit changed what the guide *said* and
never what it *ran*. When GUIDE.md changes, `site/guide/index.html` now has to
be updated by hand. The same goes for `site/tutorials/index.html` and
`kaypy/examples/`.

The safety net under both is `test_api.py`: the API page's examples are still
executed on real kaypy, so a page that drifts into describing an engine that
does not exist fails there.

## Where things come from

Most of this repo is written here. The engine and the sprites are not — they
already exist in PyIDE, and two copies drifting apart is the failure that costs
a lesson:

```bash
python3 vendor.py           # from ~/pyide
python3 vendor.py --check   # compare only, change nothing
```

| vendored | from | why |
|---|---|---|
| `site/engine/kaypy_bundle.json` | `pyide/static/py/` | the engine the playground runs |
| `site/assets/` | `pyide/static/assets/` | the sprite packs and sounds |
| `site/play/game.js`, `runtime.js`, `export.js`, `sprites.js`, `complete.js`, `zip.js` | `pyide/static/` | the parts of the editor that are not UI |
| `site/play/style.css` | `pyide/static/` | PyIDE's chrome, so the playground does not imitate a look and drift from it |

`vendor.py` writes `site/engine/stamp.json` saying which kaypy version and
which PyIDE commit it took them from, so a bug in a built game can be traced to
a source tree rather than guessed at.

What is **not** vendored is the editor shell itself — Run, Stop, the Sprites
panel, Export. PyIDE's is wound through accounts, autosave, assignments, tabs
and console mode, none of which exist here. The playground's shell is its own,
and small.

**The playground does not load `site.css`.** It loads PyIDE's `style.css`,
which carries its own complete palette; both define `--bg` and `--line`, and
loading the two together makes a mess of one of them.

## Layout

```
site/                     the website. What Render publishes, and what you edit.
  index.html              the front page
  start/  guide/  api/  tutorials/  games/
  learn/                  the hub, then one folder per lesson
    conditionals/  loops/  lists/
  play/                   the playground
    index.html            its page — its own bar, not the site navbar
    play.js  play.css     its shell, written here
    starter.py            the program it opens with. A REAL .py file: the page
                          fetches it, so you can run and edit it like any other
    game.js  runtime.js  export.js  sprites.js  complete.js  zip.js  style.css
                          vendored from PyIDE — do not edit, re-vendor
  static/
    site.css              the palette and the few components Bootstrap lacks
    site.js              highlights code, marks your place in the sidebar
    games/                the example games the Games page links
  engine/  assets/        vendored: the engine and the sprite packs
  404.html

pagecode.py               reads the code and headings back out of a built page
vendor.py                 pyide -> site   (engine, sprites, editor modules)
check_site.py             every link, anchor and asset in site/
test_pages.py             the header, the nav, the classes, the form, the CLI
test_api.py               runs every example on the API page
test_lesson.py            runs every lesson program and checks its output
test_playground.py        the playground's wiring and its starter
test_tabstops.py          the editor's Tab and Backspace behaviour
test_zip.py               the one-file download
```
