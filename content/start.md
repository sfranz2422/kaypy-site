# Get started

Two ways in. The browser needs nothing at all, so start there; move to your
own computer when you want to keep files and share what you made.

## In the browser

Open the [playground](../play/). It runs real Python — the same engine, the
same code — with nothing to install and no account.

Paste this in and press **Run**:

```python
from kaypy import *

kaypy(width=800, height=600, background=[141, 183, 255])

loadSprite("bean", "images/bean.png")
setGravity(2400)

add([rect(width(), 48), pos(0, height() - 48),
     area(), body(isStatic=True), color(90, 150, 70)])

player = add([sprite("bean"), pos(120, 100),
              area(), body(), anchor("bot")])


@onKeyDown("left")
def move_left():
    player.move(-320, 0)


@onKeyDown("right")
def move_right():
    player.move(320, 0)


@onKeyPress("space")
def jump():
    if player.isGrounded():
        player.jump(1000)
```

Arrow keys to move, space to jump.

There is no `run()` at the bottom and no loop to write. The frame loop starts
by itself once your file has been read, which is why the first thing you write
is the part you came for.

The first Run downloads Python itself and takes a few seconds. After that the
browser has it cached and Run is immediate.

## On your computer

kaypy needs **Python 3.10 or newer**. Installing it brings pygame-ce and
nothing else:

```
pip install kaypy
```

Then make a game folder. This is not an empty one — it comes with a working
game and the sprites it uses, so there is something to change rather than
something to start:

```
kaypy new mygame
cd mygame
python game.py
```

A window opens with a character, some ground and a coin. Arrow keys to move,
space to jump. Now open `game.py` and change a number.

`kaypy new` also fetches the lesson sound effects. If the network is blocked
where you are it says so and carries on without them — the game still runs, it
is just silent. When you want them:

```
kaypy sounds mygame
```

## Put it on the web

One command turns a game into one HTML file:

```
kaypy web game.py
```

That writes `web_build/game.html` — about 260 KB for the starter, with the
sprites carried inside it. Double-click it to play, or upload that single file
to itch.io as an HTML project. Nothing else has to go with it.

The first time somebody opens the page it downloads Python, the same as the
playground does. After that it is cached.

## Where to go next

- **[Learn Python](../learn/)** — conditionals, loops and lists, from the
  beginning, for somebody who has not programmed before.
- **[Guide](../guide/)** — thirteen lessons that build on the starter game:
  sprites, collision, gravity, scenes, sound, levels, camera, state.
- **[API](../api/)** — every name in kaypy, with a runnable example each.
- **[Games](../games/)** — things people have made, and how to send in yours.

## If something goes wrong

**`kaypy: command not found`** — the install worked but the script is not on
your PATH. The module does the same thing:

```
python -m kaypy.cli new mygame
```

**The window opens and closes at once** — that is usually an error printed and
gone. Run it from a terminal rather than double-clicking, and the traceback
stays on screen.

**`GameObj has no attribute ...`** — an object is missing the component that
provides it. `player.jump()` needs `body()`; `player.onCollide()` needs
`area()`. The [Guide](../guide/) has a section on this, because it is the
error everybody meets first.
