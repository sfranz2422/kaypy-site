<!-- Built by tutorials.py. Do not edit.

  The listings are read out of examples/ in the kaypy repository, so the code
  here is the code that repository tests. The part above them is
  content/tutorials.intro.md, which IS edited by hand.

      python3 tutorials.py --from ~/kaypy      rebuild
      python3 tutorials.py --check             has anything moved on?
-->

# Tutorials

Whole games, short enough to read in one sitting.

The [guide](../guide/) teaches one idea at a time and builds up. This page is
the other half of that: finished programs you can copy into the
[playground](../play/), press Run, and then take apart. Nothing here is a
fragment — every listing is a complete file that runs as it stands.

> **How to use one.** Copy it, run it, then break something on purpose. Change
> a number and see what moves. That tells you more about what a line does than
> reading it does.

## Whole games

### A door that asks a question — what ask(), say() and pause() are for

python3 quiz_door.py

Arrows to move, space to jump, escape to pause. Walk into the door and the
game stops and asks you something; get it right and the door opens.

Not one of the thirteen lessons: it is the smallest complete example of the
one thing a teacher asks for that a game engine usually cannot do. Three
names here appear nowhere in the lessons:

    ask(question, choices, answer=n)   stop and ask, then run a callback
    say(text)                          stop and show a line of text
    pause() / resume() / isPaused()    freeze the game where it stands

The question is a callback rather than a return value because a browser
cannot block: nothing can wait for an answer without stopping the frame that
would draw the question. So `ask` puts the panel up and hands you the answer
when there is one, and the game is paused in between.

```python
from kaypy import *

kaypy(width=800, height=600, background=[141, 183, 255])

loadSprite("bean", "images/bean.png")
setGravity(2400)

add([rect(width(), 48), pos(0, height() - 48), area(), body(isStatic=True),
     color(90, 150, 70)])

player = add([sprite("bean"), pos(80, 100), area(), body(), anchor("bot")])
door = add([rect(40, 90), pos(650, height() - 138), area(), color(140, 90, 40),
            "door"])

score = 0
label = add([text("Score: 0", size=26), pos(12, 12), fixed()])


@onKeyDown("left")
def left():
    player.move(-320, 0)


@onKeyDown("right")
def right():
    player.move(320, 0)


@onKeyPress("space")
def jump():
    if player.isGrounded():
        player.jump(1000)


@player.onCollide("door")
def at_the_door(d):
    @ask("Which keyword starts a loop in Python?", ["if", "for", "def"], answer=1)
    def checked(correct):
        global score
        if correct:
            score += 1
            label.text = "Score: %d" % score
            d.destroy()
            say("The door swings open.")
        else:
            say("Not that one. Have another go.")


@onKeyPress("escape")
def toggle_pause():
    resume() if isPaused() else pause()
```

[`examples/quiz_door.py`](https://github.com/sfranz2422/kaypy/blob/main/examples/quiz_door.py) · 71 lines

---

### A pet that trails you and a health bar that never does — what follow() is for

python3 pet_and_healthbar.py

Arrows to move, space to jump, F to hurt the enemy. The ghost chases you and
falls behind when you run; the red bar over the enemy is welded to it and
never falls behind at all.

Both of those are one component. The difference between them is the word
`speed`:

    follow(target)              be exactly where it is
    follow(target, speed=180)   move toward it at 180 pixels a second

The bar is the interesting half. It is pinned to an object that gravity
moves, that collision shoves out of the floor, and that a keypress teleports
— and it stays put through all three, because follow() runs after the engine
has finished deciding where everything actually ended up, rather than before
like every other component. Without that it would sit correctly while the
enemy stands still and slide off it the moment the enemy moved, which looks
like a drawing bug and is not one.

```python
from kaypy import *

kaypy(width=800, height=600, background=[141, 183, 255])

loadSprite("bean", "images/bean.png")
loadSprite("ghosty", "images/ghosty.png")
setGravity(1600)

add([rect(width(), 48), pos(0, height() - 48), area(),
     body(isStatic=True), color(90, 150, 70)])

player = add([sprite("bean"), pos(120, 300), area(), body()])

# Locked on: no speed, so it is simply where the player is, plus an offset.
add([text("you", size=18), pos(0, 0), color(30, 40, 60),
     follow(player, offset=vec2(4, -28))])

# Chasing: with a speed, it heads for the player and arrives when it arrives.
add([sprite("ghosty"), pos(600, 200), follow(player, speed=180)])

enemy = add([sprite("ghosty"), pos(560, 400), area(), body(), health(5)])

# A health bar over something gravity is pulling down and the floor is
# pushing back up. This is the case that shows whether follow() runs early
# or late.
BAR = 48
backing = add([rect(BAR, 6), pos(0, 0), color(40, 20, 20),
               follow(enemy, offset=vec2(0, -14))])
bar = add([rect(BAR, 6), pos(0, 0), color(220, 60, 60),
           follow(enemy, offset=vec2(0, -14))])


@onKeyDown("left")
def go_left():
    player.move(-320, 0)


@onKeyDown("right")
def go_right():
    player.move(320, 0)


@onKeyPress("space")
def jump():
    if player.isGrounded():
        player.jump(760)


@onKeyPress("f")
def hurt():
    if enemy.exists():
        enemy.hurt(1)
        bar.width = BAR * max(0, enemy.hp) / 5


@enemy.onDeath
def gone():
    # A follower whose target is destroyed stops where it stands and goes on
    # existing — which is right for a pet and wrong for a health bar, so the
    # bars are destroyed here, next to the thing they belonged to.
    enemy.destroy()
    backing.destroy()
    bar.destroy()


add([text("arrows move · space jumps · F hurts the ghost", size=20),
     pos(12, 12), color(20, 30, 50), fixed()])
```

[`examples/pet_and_healthbar.py`](https://github.com/sfranz2422/kaypy/blob/main/examples/pet_and_healthbar.py) · 89 lines

---

### Asteroids — what rotate() is for

python3 asteroids.py

Left and right turn the ship, up thrusts in the direction it is facing,
space fires. Rocks drift, split when hit, and wrap around the screen.

Not one of the thirteen lessons: it is the game the lessons build towards,
and the one that cannot be written at all without a ship that turns. Three
things here appear nowhere in the lessons and are the whole point of it:

    rotate(angle)            the ship turns
    Vec2.fromAngle(angle)    which way "forward" is, once it has turned
    a velocity of its own     momentum, so letting go of thrust coasts

```python
from kaypy import *

kaypy(width=800, height=600, background=[8, 8, 20])

TURN = 200          # degrees per second
THRUST = 320        # pixels per second per second
MAX_SPEED = 420
BULLET_SPEED = 560

score = 0

ship = add([
    rect(26, 18),
    pos(center()),
    anchor("center"),
    color(200, 230, 255),
    rotate(0),
    area(),
    "ship",
])
ship.vel = vec2(0, 0)

label = add([text("0", size=22), pos(12, 10), fixed()])


def wrap(obj):
    """Off one edge, on at the other — the rule that makes it Asteroids."""
    p = obj.pos
    if p.x < 0:
        obj.pos = vec2(width(), p.y)
    elif p.x > width():
        obj.pos = vec2(0, p.y)
    p = obj.pos
    if p.y < 0:
        obj.pos = vec2(p.x, height())
    elif p.y > height():
        obj.pos = vec2(p.x, 0)


def spawn_rock(at=None, chunks=3):
    r = add([
        circle(chunks * 11),
        pos(at or vec2(rand(0, width()), rand(0, 60))),
        anchor("center"),
        color(150, 140, 130),
        outline(2, (90, 85, 80)),
        area(),
        rotate(rand(0, 360)),
        "rock",
    ])
    r.vel = Vec2.fromAngle(rand(0, 360)) * rand(40, 110)
    r.spin = rand(-90, 90)
    r.chunks = chunks   # 3, 2, 1 — splits down to nothing
    return r


for _ in range(4):
    spawn_rock()


@onKeyDown("left")
def turn_left():
    ship.rotateBy(-TURN * dt())


@onKeyDown("right")
def turn_right():
    ship.rotateBy(TURN * dt())


@onKeyDown("up")
def thrust():
    ship.vel = ship.vel + Vec2.fromAngle(ship.angle) * THRUST * dt()
    if ship.vel.len() > MAX_SPEED:
        ship.vel = ship.vel.unit() * MAX_SPEED


@onKeyPress("space")
def fire():
    b = add([
        circle(3),
        pos(ship.pos),
        anchor("center"),
        color(255, 240, 160),
        area(),
        "bullet",
    ])
    b.vel = Vec2.fromAngle(ship.angle) * BULLET_SPEED
    wait(1.2, lambda: b.destroy() if b.exists() else None)


@onUpdate
def fly():
    ship.pos = ship.pos + ship.vel * dt()
    wrap(ship)
    for r in get("rock"):
        r.pos = r.pos + r.vel * dt()
        r.rotateBy(r.spin * dt())
        wrap(r)
    for b in get("bullet"):
        b.pos = b.pos + b.vel * dt()
        wrap(b)


@onUpdate
def shooting():
    global score
    for b in get("bullet"):
        for r in get("rock"):
            if not (b.exists() and r.exists()):
                continue
            if b.pos.dist(r.pos) < r.chunks * 11:
                b.destroy()
                r.destroy()
                score += 10 * r.chunks
                label.text = str(score)
                shake(6)
                if r.chunks > 1:
                    for _ in range(2):
                        spawn_rock(r.pos, r.chunks - 1)
                break
```

[`examples/asteroids.py`](https://github.com/sfranz2422/kaypy/blob/main/examples/asteroids.py) · 136 lines

---

## The lesson programs

Each of these is the finished program from one lesson of the
[guide](../guide/), which explains it a piece at a time. Read the
lesson; keep the file to run.

| | What it shows | Lines | |
|---|---|---:|---|
| **1** | [Adding a game object](../guide/#1-adding-a-game-object) | 12 | [source](https://github.com/sfranz2422/kaypy/blob/main/examples/lesson1_adding_object.py) |
| **2** | [Player movement](../guide/#2-player-movement) | 25 | [source](https://github.com/sfranz2422/kaypy/blob/main/examples/lesson2_player_movement.py) |
| **3** | [Collision handling](../guide/#3-collision-handling) | 48 | [source](https://github.com/sfranz2422/kaypy/blob/main/examples/lesson3_collision.py) |
| **5** | [Gravity](../guide/#5-gravity) | 39 | [source](https://github.com/sfranz2422/kaypy/blob/main/examples/lesson5_gravity.py) |
| **6** | [Sprite animation](../guide/#6-sprite-animation) | 67 | [source](https://github.com/sfranz2422/kaypy/blob/main/examples/lesson6_sprite_animation.py) |
| **7** | [Scenes](../guide/#7-scenes) | 91 | [source](https://github.com/sfranz2422/kaypy/blob/main/examples/lesson7_scenes.py) |
| **8** | [Audio and buttons](../guide/#8-audio-and-buttons) | 38 | [source](https://github.com/sfranz2422/kaypy/blob/main/examples/lesson8_audio_buttons.py) |
| **9** | [Timer and loop](../guide/#9-timer-and-loop) | 17 | [source](https://github.com/sfranz2422/kaypy/blob/main/examples/lesson9_timer_loop.py) |
| **10** | [Levels](../guide/#10-levels) | 43 | [source](https://github.com/sfranz2422/kaypy/blob/main/examples/lesson10_levels.py) |
| **11** | [Camera](../guide/#11-camera) | 58 | [source](https://github.com/sfranz2422/kaypy/blob/main/examples/lesson11_camera.py) |
| **12** | [Sprite atlas](../guide/#12-sprite-atlas) | 100 | [source](https://github.com/sfranz2422/kaypy/blob/main/examples/lesson12_sprite_atlas.py) |
| **13** | [Using state to handle AI](../guide/#13-using-state-to-handle-ai) | 61 | [source](https://github.com/sfranz2422/kaypy/blob/main/examples/lesson13_state_ai.py) |

---

## Coming next

**Coin Collector**, a thirteen-step platform game built from nothing — the
one to work through once the guide's lessons make sense. It exists as a
classroom walkthrough written for a different engine, and is being rewritten
for KayPy rather than translated, because the two think about a game in
genuinely different ways and a line-by-line translation would teach the seams
instead of the game.

If you are teaching with this and want it sooner, or want something else
first, say so on the [Discord](https://discord.gg/sVXnsDZNm).
