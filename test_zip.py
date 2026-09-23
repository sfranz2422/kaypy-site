#!/usr/bin/env python3
"""The playground's download really is a zip, with the code in it.

    python3 test_zip.py

The playground has no accounts and no server, so the download IS the save
button. If it produces a file that will not open, a visitor loses everything
they wrote — and a zip that is subtly malformed opens fine in one tool and
not in another, which is the worst way to find out.

So this does not check that the code calls a zip function. It runs the real
zip writer under node, takes the bytes it produces, and opens them with
Python's own zipfile — a completely different implementation. Anything the
two disagree about is a bug.

WHY BOTH FILES

game.html is the game and cannot be edited: the program is inside it, but so
is the whole engine, base64'd. Without game.py beside it, somebody who closes
the tab has a game they can play and can never change again.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
DIST = HERE / "dist"
PLAY = HERE / "play"

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-52s %s" % ("ok" if ok else "FAIL", label, detail))


def done():
    bad = results.count(False)
    print("\n%s (%d checks, %d failed)"
          % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
    sys.exit(1 if bad else 0)


page = (PLAY / "play.html").read_text()
script = (PLAY / "play.js").read_text()

check("the page loads the zip writer", './zip.js"' in page)
check("and it is vendored", (DIST / "play" / "zip.js").is_file())
check("the download builds a zip", "PyIDEZip.download(" in script)

for name in ("game.html", "game.py"):
    check("  and puts %s in it" % name, '"%s"' % name in script)

# The source that goes in has to be what is in the editor, not what the
# program was when the page loaded. An export that saved the starter instead
# of the visitor's work would look completely normal.
check("  the .py is the editor's current contents",
      'name: "game.py", data: source' in script)

zip_js = DIST / "play" / "zip.js"
if not zip_js.is_file():
    done()

# ------------------------------------------------- run the real zip writer
work = pathlib.Path(tempfile.mkdtemp())
out = work / "out.zip"

driver = """
import { readFileSync, writeFileSync } from "fs";
globalThis.window = {};
globalThis.document = { createElement: () => ({ style: {}, click() {} }),
                        body: { appendChild() {}, removeChild() {} } };
globalThis.URL = { createObjectURL: () => "blob:x", revokeObjectURL() {} };
globalThis.Blob = class { constructor(parts) { this.parts = parts; } };

new Function("window", "document", "URL", "Blob",
  readFileSync(%s, "utf8"))
  (globalThis.window, globalThis.document, globalThis.URL, globalThis.Blob);

const Z = globalThis.window.PyIDEZip;
const bytes = Z.build([
  { name: "game.html", data: "<!doctype html><title>x</title>" },
  { name: "game.py",   data: "from kaypy import *\\nkaypy(width=800)\\n" }
]);
writeFileSync(%s, Buffer.from(bytes));
""" % (json.dumps(str(zip_js)), json.dumps(str(out)))

(work / "run.mjs").write_text(driver)
proc = subprocess.run(["node", str(work / "run.mjs")], capture_output=True, text=True)
check("the zip writer runs", proc.returncode == 0,
      proc.stderr.strip().splitlines()[-1][:60] if proc.returncode else "")

if proc.returncode == 0 and out.is_file():
    # Python's zipfile, not the writer's own idea of whether it worked.
    try:
        with zipfile.ZipFile(out) as z:
            bad = z.testzip()
            names = z.namelist()
            html = z.read("game.html").decode()
            code = z.read("game.py").decode()
        check("Python's zipfile opens what it wrote", True,
              "%d bytes" % out.stat().st_size)
        check("  with no corrupt entry", bad is None, str(bad))
        check("  holding both files", sorted(names) == ["game.html", "game.py"],
              ", ".join(names))
        check("  the page comes back whole", html.startswith("<!doctype html>"))
        check("  and the code comes back byte for byte",
              code == "from kaypy import *\nkaypy(width=800)\n", repr(code[:40]))
    except Exception as exc:                                    # noqa: BLE001
        check("Python's zipfile opens what it wrote", False,
              "%s: %s" % (type(exc).__name__, exc))

import shutil                                                   # noqa: E402
shutil.rmtree(work, ignore_errors=True)
done()
