# The guide

Thirteen lessons, from an empty file to an enemy with a state machine. Every
one is a game you can run, and each adds one idea to the one before it.

You need to know what a variable and a function are. Everything else — game
loops, collision, animation, scenes — is explained here as it comes up.

> **Reading straight through takes about an hour.** Typing it in takes a few
> evenings, and is the point. Every lesson ends with something to change, and
> the changing is where the learning is.

---

## Getting started

Every game in this guide is an ordinary Python file that begins:

```python
from kaypy import *
```

That one line brings in every name you will use. Everything else follows from
it.

There are two ways to run what you write, and **the lessons are identical in
both** — same code, same results. Use whichever suits you.

### In the playground, with nothing installed

Open the [playground](../play/). It runs Python in your browser, the sprites
are already there, and it starts with the import line above.

Press **Run** to play, and **click the picture once** so the keys reach the
game. Press **Stop** when you want the keyboard back for typing.

Nothing is saved on a server, because there is no server — so when you have
something you want to keep, use **Download**. You get a zip holding your `.py`
file and a single self-contained `.html` you can double-click to play, or send
to somebody, or upload to itch.io.

### On your own machine

Install once, then make yourself a game to work in:

```bash
pip install kaypy
kaypy new mygame
cd mygame
```

That folder has a small working game in `game.py`, and all the sprites and
sounds these lessons use. Run it:

```bash
python game.py
```

A window opens and the game is already running. Close it to stop.

To turn the same file into a web page instead:

```bash
kaypy web game.py
```

That gives you one HTML file. Double-click it and the game plays — no server,
nothing to install.

**There is no `run()` call anywhere in this guide**, either way. The loop starts
on its own once your file has finished being read, so the first thing you write
is the part you came for.

### Where the pictures and sounds live

Paths look the same wherever you run:

```python
loadSprite("bean", "images/bean.png")       # the cartoon pack
loadSprite("elf_m", "dungeon/elf_m.png")    # the dungeon pack — pixel art
loadSound("ding", "sounds/ding.wav")        # sounds
```

In the playground, the **Sprites** button opens every sprite and sound there is;
click one and it inserts the lines you need, so you never type a path by hand.
The search box covers both packs at once, and a ▶ in the corner of a cell means
that sprite animates.

On your own machine, `kaypy new` put those same three folders next to your
`game.py`, so the paths line up already.

Either way, **the two sprite packs are separate folders**, and that matters: a
dungeon sprite is not in `images/`. There is also `dungeon.png`, the dungeon
artwork as one uncut image — that is a sprite atlas, and Lesson 12 is about
cutting one up yourself.

### If you want to look something up

The [API reference](../api/) lists every name there is, each with a small
example you can run. This guide teaches; that page answers.

---

## Reading JavaScript examples

*Skip this section if you have never seen JavaScript — nothing later depends on
it.*

KayPy's function names follow [KAPLAY](https://kaplayjs.com), a JavaScript game
engine. You never have to write or read any JavaScript. It matters for one
reason only: when you search the web for how to do something, the examples you
find are usually theirs, and they translate almost line for line.

Here is the whole translation.

| JavaScript | Python |
|---|---|
| `kaplay({ width: 800 })` | `kaypy(width=800)` |
| `body({ jumpForce: 800 })` | `body(jumpForce=800)` |
| `const SPEED = 300;` | `SPEED = 300` |
| `function jump() { ... }` | `def jump(): ...` |
| `if (a && !b) { ... }` | `if a and not b: ...` |
| `true` / `false` / `null` | `True` / `False` / `None` |
| `// a comment` | `# a comment` |
| `{ ... }` blocks | indentation |
| `;` at the end of a line | nothing |

Two rules worth stating plainly:

**Options in curly braces become keyword arguments.** Anywhere the JavaScript
shows `{ speed: 10, loop: true }`, you write `speed=10, loop=True`.

**Callbacks can ignore arguments they don't want.** An event handler that takes
no arguments works even when the engine has something to hand it. If you do want
it, give your function a parameter and you will get it.

### Event handlers

This is the one place where the Python is shaped differently, and it is an
improvement. JavaScript writes an event like this:

```javascript
onKeyPress("space", () => {
    if (player.isGrounded()) player.jump(800)
})
```

In Python you put the event **above** the function it should run:

```python
@onKeyPress("space")
def jump():
    if player.isGrounded():
        player.jump(800)
```

The `@` line reads as a label: *when space is pressed, run this*. The function
underneath is an ordinary function — as many lines as you like, `if` statements,
variables, anything.

Every event in this guide works that way. You can also hand an event a function
directly:

```python
onKeyPress("space", jump)
```

Both do exactly the same thing. Use whichever is clearer. Where a JavaScript
example uses a one-line arrow function, Python's equivalent is a `lambda`:

```javascript
onKeyDown("left", () => player.move(-300, 0))   // JavaScript
```
```python
onKeyDown("left", lambda: player.move(-300, 0))  # Python, same thing
```

You never have to write one. This guide uses the `@` form throughout, because a
`lambda` can only hold a single expression — the moment a handler needs an `if`,
or to change a variable, a `lambda` can't do it and you need a real function
anyway.

---
