/* The playground's shell.
 *
 * PyIDE's app.js is 40 KB and most of it is school: accounts, assignments,
 * turning work in, autosave, multiple files, a notes pane, sharing links. None
 * of that belongs on a public page, and a visitor should not be asked to sign
 * in to try a game engine. So this is a separate shell over the same four
 * modules PyIDE uses — runtime, game, export, sprites — which are vendored
 * from it byte for byte and do all the actual work.
 *
 * WHAT THIS FILE OWNS
 *
 *   the editor, Run, Stop, Download, Start over, the sprite panel's grids,
 *   and one draft kept in this browser
 *
 * WHAT IT DELIBERATELY DOES NOT DO
 *
 *   No accounts, no server, no upload. Nothing a visitor writes here leaves
 *   their machine: there is nowhere for it to go. The draft below is
 *   localStorage, which is per-browser and invisible to us.
 */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };

  var runBtn = $("run");
  var runLabel = $("run-label");
  var stopBtn = $("stop");
  var exportBtn = $("export");
  var resetBtn = $("reset");
  var spritesToggle = $("sprites-toggle");
  var panel = $("sprites");
  var outputEl = $("output");
  var stage = $("stage");
  var statusEl = $("status");

  var DRAFT_KEY = "kaypy-playground-draft";

  /* The program the page opens with, filled in by build.py from
     play/starter.py.

     It lives in a real .py file rather than as a list of JavaScript string
     literals, because that list had to be parsed back out to be tested and
     the parser got it wrong: it matched only the double-quoted lines, so
     every line written with single quotes was dropped, the test ran a
     shorter program than the one that shipped, and it passed. A starter is
     the first thing a visitor presses Run on. It has to be the same text in
     the test and on the page, with nothing in between that can lose a line. */
  var STARTER = {{STARTER}};

  // ----------------------------------------------------------- the editor

  document.body.classList.add("is-game");

  /* Which theme the page has resolved to, counting both an explicit choice
     and the computer's own setting. CodeMirror carries its own theme and does
     NOT follow the page's CSS, so this has to be asked and then applied —
     otherwise a light page gets a dark editor bolted into the middle of it,
     which is what shipped the first time. */
  function isDark() {
    var set = document.documentElement.getAttribute("data-theme");
    if (set === "dark") return true;
    if (set === "light") return false;
    return window.matchMedia
      && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  function cmTheme() { return isDark() ? "material-darker" : "default"; }

  var editor = CodeMirror.fromTextArea($("editor"), {
    mode: "python",
    theme: cmTheme(),
    lineNumbers: true,
    indentUnit: 4,
    tabSize: 4,
    indentWithTabs: false,
    matchBrackets: true,
    autoCloseBrackets: true,
    lineWrapping: false,
    extraKeys: {
      "Ctrl-/": "toggleComment",
      "Cmd-/": "toggleComment",
      "Ctrl-Enter": function () { run(); },
      "Cmd-Enter": function () { run(); },
      Tab: function (cm) {
        if (cm.somethingSelected()) return cm.indentSelection("add");
        cm.replaceSelection("    ");
      }
    }
  });

  /* A draft, in this browser only.
   *
   * Every read and write is wrapped: localStorage throws rather than returning
   * null in a private window and wherever site data is blocked, and a school
   * laptop is exactly where that happens. Losing a draft is a disappointment;
   * a playground that will not open because saving failed is a bug. */
  function loadDraft() {
    try {
      return window.localStorage.getItem(DRAFT_KEY);
    } catch (e) {
      return null;
    }
  }

  function saveDraft(text) {
    try {
      window.localStorage.setItem(DRAFT_KEY, text);
    } catch (e) {
      /* Full, blocked, or private browsing. Nothing to tell the visitor:
         their code is in front of them and still runs. */
    }
  }

  editor.setValue(loadDraft() || STARTER);
  editor.clearHistory();

  var saveTimer = null;
  editor.on("change", function () {
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(function () { saveDraft(editor.getValue()); }, 400);
    if (window.PyIDEComplete && pyodide) {
      window.PyIDEComplete.refresh(editor.getValue());
    }
  });

  resetBtn.addEventListener("click", function () {
    if (!window.confirm("Replace what is in the editor with the starter game?")) {
      return;
    }
    editor.setValue(STARTER);
    editor.focus();
    saveDraft(STARTER);
  });

  // ----------------------------------------------------------- the output

  function write(text, cls) {
    var span = document.createElement("span");
    if (cls) span.className = cls;
    span.textContent = text;
    outputEl.appendChild(span);
    outputEl.scrollTop = outputEl.scrollHeight;
  }

  function clearOutput() { outputEl.textContent = ""; }

  function status(msg) { statusEl.textContent = msg || ""; }

  // ------------------------------------------------------------- Pyodide

  var pyodide = null;
  var running = false;
  var canvas = $("canvas");

  (async function boot() {
    try {
      pyodide = await loadPyodide();
      window.PyIDERuntime.pipeOutput(pyodide, write);
      pyodide.runPython(window.PyIDERuntime.BOOTSTRAP);
      if (window.PyIDEComplete) {
        window.PyIDEComplete.attach(pyodide);
        window.PyIDEComplete.refresh(editor.getValue());
      }
      var version = pyodide.runPython(
        "import sys; '.'.join(str(v) for v in sys.version_info[:3])"
      );
      clearOutput();
      write("Python " + version + " is ready. Press Run.\n", "dim");
      runBtn.disabled = false;
      runLabel.textContent = "Run";
    } catch (e) {
      status("Python could not load.");
      write("Python could not load. Check your connection and refresh.\n" +
            String(e) + "\n", "err");
    }
  })();

  // ------------------------------------------------------------ run/stop

  function setBusy(on) {
    running = on;
    runBtn.hidden = on;
    stopBtn.hidden = !on;
    exportBtn.disabled = on;
    resetBtn.disabled = on;
  }

  async function run() {
    if (running || !pyodide) return;
    var source = editor.getValue();

    if (!window.PyIDEGame.looksLikeGame(source)) {
      clearOutput();
      write("This playground runs kaypy games.\n", "err");
      write('Your program needs `from kaypy import *` at the top.\n', "dim");
      return;
    }

    setBusy(true);
    status("Starting the engine…");
    try {
      /* ensureReady hands back a NEW canvas each time and points SDL at it,
         so the reference here has to be rebound or the key handlers stay on
         an element nobody can see. The source goes along so it can fetch the
         sprites and sounds this particular program names, and only those. */
      canvas = await window.PyIDEGame.ensureReady(pyodide, status, source);
      bindCanvas(canvas);
    } catch (e) {
      status("");
      write("The game engine could not load.\n" + String(e) + "\n", "err");
      setBusy(false);
      return;
    }

    status("");
    clearOutput();
    write("Game running. Click the picture first so the keys reach it.\n", "dim");
    stage.hidden = false;
    canvas.focus();

    try {
      /* Two steps, because they fail differently. The first runs the program
         top to bottom the way `python game.py` does — kaypy() builds the
         engine and everything after it registers handlers. An error there is
         an error in the visitor's setup and stops the run.

         The second awaits the frame loop, a Python coroutine that does not
         return until the game ends or Stop is pressed. */
      var status_ = await pyodide.runPythonAsync(
        "_pyide_run_game(" + JSON.stringify(source) + ")"
      );
      if (status_ === "ok") {
        await pyodide.runPythonAsync("await _pyide_drive_game()");
      }
    } catch (e) {
      write(String(e) + "\n", "err");
    } finally {
      window.PyIDEGame.stop(pyodide);
      setBusy(false);
    }
  }

  function stopRun() {
    if (!running) return;
    /* Ask, don't tear down. Stop clears the engine's running flag; the loop
       notices on its next frame and returns, and the await in run() resolves
       — and ITS finally is what puts the toolbar back. Calling setBusy here
       as well would be a second, earlier answer to the same question, and the
       two would disagree for a frame. */
    window.PyIDEGame.stop(pyodide);
    write("\n— stopped —\n", "dim");
    editor.focus();
  }

  /* Re-bound after every canvas swap, because the listeners belong to the
     element and the element is replaced for each new game. */
  function bindCanvas(el) {
    el.addEventListener("keydown", function (e) {
      if ([" ", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"]
          .indexOf(e.key) >= 0) {
        e.preventDefault();
      }
    });
    el.addEventListener("mousedown", function () { el.focus(); });
  }

  runBtn.addEventListener("click", run);
  stopBtn.addEventListener("click", stopRun);
  $("clear").addEventListener("click", clearOutput);

  /* Light and dark, remembered per browser under this site's own key so a
     choice here does not reach into PyIDE, or the reverse. */
  $("theme").addEventListener("click", function () {
    var next = isDark() ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    editor.setOption("theme", next === "dark" ? "material-darker" : "default");
    try { window.localStorage.setItem("kaypy-theme", next); } catch (e) {}
  });

  /* And follow the computer if the reader has not chosen for themselves. */
  if (window.matchMedia) {
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener
      && window.matchMedia("(prefers-color-scheme: dark)")
           .addEventListener("change", function () {
             if (!document.documentElement.getAttribute("data-theme")) {
               editor.setOption("theme", cmTheme());
             }
           });
  }

  // -------------------------------------------------------------- export

  exportBtn.addEventListener("click", async function () {
    if (running || !pyodide) return;
    var source = editor.getValue();
    if (!window.PyIDEGame.looksLikeGame(source)) {
      write("\nOnly a kaypy game can be packed into a page.\n", "err");
      return;
    }
    var was = exportBtn.textContent;
    exportBtn.disabled = true;
    try {
      var html = await window.PyIDEExport.buildGamePage(
        source, "My kaypy game", function (msg) {
          exportBtn.textContent = msg.length > 14 ? "Packing…" : msg;
        });
      window.PyIDEExport.downloadGamePage("game.html", html);
      write("\nSaved game.html — double-click it to play, or upload that one " +
            "file to itch.io. It needs the internet the first time it runs.\n",
            "dim");
    } catch (e) {
      write("\nCould not pack the game: " + (e.message || e) + "\n", "err");
    } finally {
      exportBtn.textContent = was;
      exportBtn.disabled = running;
    }
  });

  // ------------------------------------------------------- sprites panel

  var spriteGrid = $("sprite-grid");
  var dungeonGrid = $("dungeon-grid");
  var atlasList = $("atlas-list");
  var soundList = $("sound-list");
  var spritesFetched = false;

  var ASSETS = window.PyIDEPaths.assets;

  function insertAtCursor(text) {
    editor.replaceSelection(text);
    editor.focus();
    closeSprites();
  }

  function spriteCell(name, dir, w, h, frames, animNames) {
    var scale = Math.min(1, 48 / Math.max(w, h));
    var cell = document.createElement("button");
    cell.className = "sprite";
    cell.type = "button";
    cell.dataset.name = name + " " + (animNames || "");
    cell.title = name + " — " + w + "×" + h +
                 (frames > 1 ? " — " + frames + " frames: " + animNames : "") +
                 " — click to insert";

    var box = document.createElement("span");
    box.className = "sprite-img";

    var win = document.createElement("span");
    win.className = "sprite-frame";
    win.style.width = Math.round(w * scale) + "px";
    win.style.height = Math.round(h * scale) + "px";

    var img = document.createElement("img");
    img.src = ASSETS + dir + "/" + name + ".png";
    img.alt = "";
    img.loading = "lazy";
    img.style.width = Math.round(w * scale) * frames + "px";

    win.appendChild(img);
    box.appendChild(win);
    cell.appendChild(box);

    if (frames > 1) {
      var mark = document.createElement("span");
      mark.className = "sprite-anim";
      mark.textContent = "▶";
      cell.appendChild(mark);
    }

    var label = document.createElement("span");
    label.className = "sprite-name";
    label.textContent = name;
    cell.appendChild(label);
    return cell;
  }

  async function fillSpritePanel() {
    if (spritesFetched) return;
    spritesFetched = true;
    var manifest;
    try {
      manifest = await fetch(ASSETS + "manifest.json")
        .then(function (r) { return r.json(); });
    } catch (e) {
      spriteGrid.textContent = "Could not load the sprite list.";
      return;
    }

    function addPack(entries, dir, grid) {
      (entries || []).forEach(function (entry) {
        var frames = entry.frames || 1;
        var names = entry.anims ? Object.keys(entry.anims) : [];
        var cell = spriteCell(entry.name, dir, entry.w, entry.h, frames,
                              names.join(", "));
        cell.addEventListener("click", function () {
          insertAtCursor(window.PyIDESprites.insertFor(entry, dir));
        });
        grid.appendChild(cell);
      });
    }

    spriteGrid.textContent = "";
    addPack(manifest.images, "images", spriteGrid);
    addPack(manifest.dungeon, "dungeon", dungeonGrid);
    $("dungeon-section").hidden = !dungeonGrid.children.length;

    /* The atlas: one image holding many sprites, cut out by coordinates. The
       dungeon pack above is that same artwork already cut up — quicker to
       use, but it hides where sprites come from, which is the thing the atlas
       lesson is for. So both are here. */
    (manifest.atlases || []).forEach(function (atlas) {
      var card = document.createElement("button");
      card.className = "atlas-card";
      card.type = "button";
      card.dataset.name = atlas.name + " atlas spritesheet";
      var regions = Object.keys(atlas.regions);
      card.title = atlas.file + " — " + atlas.w + "×" + atlas.h + " — " +
                   regions.join(", ") + " — click to insert";
      var img = document.createElement("img");
      img.src = ASSETS + atlas.file;
      img.alt = "";
      img.loading = "lazy";
      var nameEl = document.createElement("span");
      nameEl.className = "sprite-name";
      nameEl.textContent = atlas.file;
      var note = document.createElement("p");
      note.className = "atlas-note";
      note.textContent = regions.length + " regions cut out by coordinates: " +
                         regions.join(", ");
      card.appendChild(img);
      card.appendChild(nameEl);
      card.appendChild(note);
      card.addEventListener("click", function () {
        insertAtCursor(window.PyIDESprites.insertAtlas(atlas));
      });
      atlasList.appendChild(card);
    });
    $("atlas-section").hidden = !atlasList.children.length;

    var sounds = manifest.sounds || [];
    if (!sounds.length) {
      $("sound-section").hidden = true;
      return;
    }
    soundList.textContent = "";
    sounds.forEach(function (file) {
      var name = file.replace(/\.[^.]+$/, "");
      var b = document.createElement("button");
      b.className = "chip";
      b.type = "button";
      b.textContent = name;
      b.title = 'Insert loadSound("' + name + '", ...) and play("' + name + '")';
      b.addEventListener("click", function () {
        insertAtCursor('loadSound("' + name + '", "sounds/' + file + '")\n' +
                       'play("' + name + '")');
      });
      soundList.appendChild(b);
    });
  }

  function closeSprites() {
    panel.setAttribute("hidden", "");
    spritesToggle.setAttribute("aria-expanded", "false");
  }

  function openSprites() {
    panel.removeAttribute("hidden");
    spritesToggle.setAttribute("aria-expanded", "true");
    fillSpritePanel();
    $("sprite-search").focus();
  }

  spritesToggle.addEventListener("click", function () {
    if (panel.hasAttribute("hidden")) openSprites(); else closeSprites();
  });
  $("sprites-close").addEventListener("click", closeSprites);

  $("sprite-search").addEventListener("input", function (e) {
    var q = e.target.value.trim().toLowerCase();
    var shown = 0;
    var cells = panel.querySelectorAll("[data-name]");
    for (var i = 0; i < cells.length; i++) {
      var hit = !q || cells[i].dataset.name.toLowerCase().indexOf(q) >= 0;
      cells[i].hidden = !hit;
      if (hit) shown++;
    }
    $("sprite-empty").hidden = shown > 0;
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !panel.hasAttribute("hidden")) closeSprites();
  });
})();
