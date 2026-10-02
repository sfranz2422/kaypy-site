"""Flappy Bean — space (or click) to flap, don't touch anything.

Put this next to your images/ folder and run it:

    python game.py

The pipes are plain rectangles, so there is no art to find and every number
that shapes the game is right here in the settings block, ready to be argued
about.
"""
from kaypy import *

kaypy(width=800, height=600, background=[121, 189, 220])

loadSprite("bean", "images/bean.png")
setGravity(1600)

# ---------------------------------------------------------------- settings
#
# Everything you would want to change is here. Change one at a time and play
# it — that is the whole point of having them in one place.

FLAP = 520          # how hard a flap pushes upward
GRAVITY = 1600      # set above, in setGravity()
GROUND = 60         # the height of the grass strip

GAP_START = 210     # the hole between pipes, to begin with
GAP_MIN = 130       # and the smallest it ever gets
GAP_SHRINK = 6      # how much narrower each point makes it

SPEED_START = 190   # how fast the world slides past, in pixels per second
SPEED_MAX = 420
SPEED_GAIN = 9      # added per point

SPACING = 1.55      # seconds between pipes at the start
SPACING_MIN = 0.95

PIPE_W = 70
MARGIN = 90         # how close to the top or bottom a gap may sit


# ---------------------------------------------------------------- the state
#
# One dict rather than a pile of globals, so the handlers below can change
# it without every one of them needing a `global` line. A student can read
# `state["score"]` and know exactly what it is.
state = {
    "score": 0,
    "alive": True,
    "best": getData("flappy_best", 0),
    # Which game this is. See next_pipe() — it is the whole reason restarting
    # does not slowly turn the game into a pipe machine gun.
    "run": 0,
}


def difficulty():
    """How hard the game is right now, from the score.

    Both numbers move together and both are clamped, so the game gets
    harder for a while and then settles into something a person can
    actually play. Without the clamp it becomes impossible at about
    thirty points, which is a worse game than one that plateaus.
    """
    n = state["score"]
    gap = max(GAP_MIN, GAP_START - n * GAP_SHRINK)
    speed = min(SPEED_MAX, SPEED_START + n * SPEED_GAIN)
    spacing = max(SPACING_MIN, SPACING - n * 0.02)
    return gap, speed, spacing


# ------------------------------------------------------------------ the bird
bird = add([
    sprite("bean"),
    pos(180, 240),
    area(),
    body(),
    anchor("center"),
    rotate(0),
    "bird",
])

# The ground. It is solid, so landing on it is a collision like any other.
add([
    rect(width(), GROUND),
    pos(0, height() - GROUND),
    area(),
    body(isStatic=True),
    color(96, 156, 76),
    "ground",
])


# ------------------------------------------------------------------- the HUD
score_label = add([text("0", size=48), pos(width() / 2, 40),
                   anchor("center"), color(255, 255, 255), fixed(), z(10)])

best_label = add([text("best %d" % state["best"], size=18), pos(12, 12),
                  color(255, 255, 255), opacity(0.75), fixed(), z(10)])

message = add([text("", size=26, width=520), pos(width() / 2, height() / 2 + 40),
               anchor("center"), color(255, 255, 255), fixed(), z(10)])

message.text = "Press SPACE to flap"


# -------------------------------------------------------------------- pipes
def spawn_pipe():
    """One pair of rectangles with a hole between them.

    They carry area() but NOT body(), so they are triggers rather than
    walls: the bird passes through them and the collision handler ends the
    game. A body() here would shove the bird sideways instead, which looks
    like the game is broken rather than like you lost.
    """
    if not state["alive"]:
        return

    gap, speed, _ = difficulty()
    top = rand(MARGIN, height() - GROUND - MARGIN - gap)
    x = width() + PIPE_W              # just off the right-hand edge

    for y, h in [(0, top), (top + gap, height() - GROUND - top - gap)]:
        add([
            rect(PIPE_W, h),
            pos(x, y),
            area(),
            color(76, 145, 65),
            outline(4, rgb(46, 100, 40)),
            move(vec2(-1, 0), speed),
            "pipe",
        ])

    # An invisible strip in the gap. Touching it is the point being scored,
    # which is simpler and more reliable than watching a pipe's x go past
    # the bird — a destroyed pipe cannot be asked where it is.
    #
    # It sits at the pipe's BACK edge, not its front. Put it at the front and
    # the point lands the moment you enter the gap, so you can score and then
    # clip the pipe on your way through — which reads as the game cheating
    # you. A point should mean "got past that one".
    add([
        rect(6, gap),
        pos(x + PIPE_W - 6, top),
        area(),
        opacity(0),
        move(vec2(-1, 0), speed),
        "point",
    ])


def next_pipe():
    """Schedule the next pipe, at the spacing the current score asks for.

    Each pipe schedules the one after it, so this is a chain rather than a
    loop — that is what lets the spacing change as you score.

    THE TICKET

    A chain that schedules itself has to be able to stop, and "stop" is not
    just "am I alive". When you die there is almost always a wait() already
    counting down. It fires a moment later, sees a living game again because
    you have pressed space by then, and starts a SECOND chain — so the next
    game gets pipes twice as fast, the one after that three times, and the
    difficulty ramp appears to be broken.

    So each chain carries the run number it was born in and stops the moment
    that stops being the current one. Restart bumps the number, and every
    chain from the previous game quietly retires.
    """
    if not state["alive"]:
        return
    mine = state["run"]
    _, _, spacing = difficulty()

    def tick():
        if mine != state["run"] or not state["alive"]:
            return
        spawn_pipe()
        next_pipe()

    wait(spacing, tick)


# ------------------------------------------------------------------- playing
def flap():
    if state["alive"]:
        bird.jump(FLAP)
    else:
        restart()


onKeyPress("space", flap)
onKeyPress("up", flap)
onClick(flap)


@onUpdate
def tilt():
    """Point the bird where it is going.

    Not decoration: it is the only feedback telling a player whether they
    are still rising or already falling, which is most of what makes the
    game readable.
    """
    if not state["alive"]:
        return
    speed = bird.comp("body").vel.y
    bird.angle = max(-28, min(75, speed * 0.06))


@onUpdate
def tidy_up():
    """Throw away pipes that have gone past the left edge.

    Without this the game keeps every pipe it has ever made, and after a
    few minutes there are hundreds of rectangles being moved and tested
    for collision off-screen where nobody can see them.

    (kaypy has an `offscreen(destroy=True)` component for exactly this,
    but in 0.13.0 it raises `TypeError: 'bool' object is not callable` the
    moment it fires — the destroy flag shadows the component's own destroy
    method. Four lines here instead.)
    """
    for junk in get("pipe") + get("point"):
        if junk.pos.x < -PIPE_W - 20:
            junk.destroy()


@onUpdate
def check_bounds():
    # Flying off the top is losing too. Without this you can park above the
    # pipes and score for ever.
    if state["alive"] and bird.pos.y < -40:
        die()


@bird.onCollide("pipe")
def hit_pipe(pipe):
    die()


@bird.onCollide("ground")
def hit_ground(ground):
    die()


@bird.onCollide("point")
def scored(marker):
    if not state["alive"]:
        return
    marker.destroy()
    state["score"] += 1
    score_label.text = str(state["score"])

    gap, speed, _ = difficulty()
    if state["score"] in (5, 10, 20):
        message.text = "faster!"
        wait(0.8, lambda: setattr(message, "text", ""))


def die():
    if not state["alive"]:
        return
    state["alive"] = False
    shake(10)

    if state["score"] > state["best"]:
        state["best"] = state["score"]
        setData("flappy_best", state["best"])
        best_label.text = "best %d" % state["best"]

    message.text = "%d point%s — press SPACE to try again" % (
        state["score"], "" if state["score"] == 1 else "s")

    # Freeze the world. The pipes stop because their move() speed is zeroed;
    # the bird keeps falling, which is what the original does and reads as
    # losing rather than as the game hanging.
    for pipe in get("pipe") + get("point"):
        pipe.comp("move").speed = 0


def restart():
    for junk in get("pipe") + get("point"):
        junk.destroy()

    state["score"] = 0
    state["alive"] = True
    state["run"] += 1            # retires every pipe chain from last game
    score_label.text = "0"
    message.text = ""

    bird.pos = vec2(180, 240)
    bird.comp("body").vel.y = 0
    bird.angle = 0

    next_pipe()


next_pipe()
