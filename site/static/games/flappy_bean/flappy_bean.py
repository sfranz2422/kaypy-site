"""Flappy Bean -- flap through the gaps, and don't touch anything.

    space, up or click   flap

Bean is always falling, and every flap pushes it back up. Fly through the
gap between each pair of pipes for a point. The more points you have, the
faster the pipes come and the smaller the gaps get. Touch a pipe or the
grass, or fly off the top, and it is game over. Your best score is
remembered.

HOW THIS FILE IS PUT TOGETHER

    1. the window and the picture
    2. the settings
    3. how hard the game is
    4. the game scene: Bean, the grass, the pipes, points, dying
    5. start the game

The pipes are plain rectangles, so there is no art to find, and every number
that shapes the game is in the settings, ready to be argued about.
"""

from kaypy import *

# ----------------------------------------------------------------- 1. setup

kaypy(width=800, height=600, background=[121, 189, 220])

# How hard Bean falls. Lower it and Bean floats; raise it and Bean drops
# like a stone.
setGravity(1600)

loadSprite("bean", "images/bean.png")


# -------------------------------------------------------------- 2. settings
#
# Everything you would want to change is here. Change one at a time and
# play it -- that is the whole point of having them in one place.

FLAP = 520            # how hard a flap pushes Bean up
GROUND = 60           # how tall the strip of grass is

PIPE_WIDTH = 70
MARGIN = 90           # how close to the top or the grass a gap may be

GAP_START = 210       # the hole between the pipes, to begin with
GAP_SMALLEST = 130    # ...the smallest it ever gets
GAP_SHRINK = 6        # ...and how much smaller each point makes it

SPEED_START = 190     # how fast the pipes slide, in pixels per second
SPEED_FASTEST = 420   # ...the fastest they ever go
SPEED_GAIN = 9        # ...and how much faster each point makes them

WAIT_START = 1.55     # seconds between pipes, to begin with
WAIT_SHORTEST = 0.95  # ...the shortest wait there ever is
WAIT_DROP = 0.02      # ...and how much shorter each point makes it

# The name the best score is saved under. Every game on a website shares
# the same storage, so the game's own name goes in it -- a plain "best"
# would be overwritten by the next game that saved one.
BEST_KEY = "flappy_best"


# -------------------------------------------------- 3. how hard the game is
#
# Each of these works out a number from the score. They all get harder as
# the score goes up, and they all stop somewhere, so the game ends up hard
# but never impossible. Without the stops, nobody could get past about
# thirty points.

score = 0


def gap_size():
    gap = GAP_START - score * GAP_SHRINK
    if gap < GAP_SMALLEST:
        gap = GAP_SMALLEST
    return gap


def pipe_speed():
    speed = SPEED_START + score * SPEED_GAIN
    if speed > SPEED_FASTEST:
        speed = SPEED_FASTEST
    return speed


def pipe_wait():
    seconds = WAIT_START - score * WAIT_DROP
    if seconds < WAIT_SHORTEST:
        seconds = WAIT_SHORTEST
    return seconds


# ------------------------------------------------------- 4. the game scene
#
# These change while you play. A function that CHANGES one has to say
# `global` first, which means "the one up here, not a new one of my own".

alive = True
next_pipe = 0       # seconds until the next pair of pipes
last_y = 0          # where Bean was last frame, for the tilt


@scene("game")
def game():
    global score, alive, next_pipe, last_y

    # A new game, so everything starts again.
    score = 0
    alive = True
    next_pipe = pipe_wait()
    best = getData(BEST_KEY, 0)

    # rotate(0) lets Bean tilt. It starts level. z(5) draws Bean in front
    # of the pipes, which are added later and would otherwise cover it.
    bean = add([sprite("bean"), pos(180, 240), anchor("center"), rotate(0),
                area(), body(), z(5)])
    last_y = bean.pos.y

    # The grass. It is solid, so Bean lands on it -- and landing on it is
    # losing.
    add([rect(width(), GROUND), pos(0, height() - GROUND),
         color(96, 156, 76), area(), body(isStatic=True), "ground"])

    score_label = add([text("0", size=48), pos(width() / 2, 40),
                       anchor("center"), z(10)])
    best_label = add([text("best " + str(best), size=18), pos(12, 12),
                      opacity(0.75), z(10)])

    # width=520 wraps a long message onto more than one line.
    message = add([text("Press SPACE to flap", size=26, width=520),
                   pos(width() / 2, height() / 2 + 40), anchor("center"),
                   z(10)])

    # ------------------------------------------------------------ flapping
    #
    # Three ways to flap, all doing the same thing. Once the game is over,
    # a flap starts a new one.

    def flap():
        if alive:
            bean.jump(FLAP)
        else:
            go("game")

    onKeyPress("space", flap)
    onKeyPress("up", flap)
    onClick(flap)

    # --------------------------------------------------------- every frame

    @onUpdate
    def each_frame():
        global next_pipe, last_y

        if not alive:
            return

        # Tilt Bean nose-up while it rises and nose-down while it falls. How
        # far it moved this frame, divided by how long the frame took, is
        # how fast it is going. (dt() is never 0 while the game runs, but
        # dividing by 0 would crash it, so it is checked anyway.)
        if dt() > 0:
            falling_speed = (bean.pos.y - last_y) / dt()
            bean.angle = clamp(falling_speed * 0.06, -28, 75)
        last_y = bean.pos.y

        # Flying off the top is losing too. Without this you could fly
        # above the pipes and score for ever.
        if bean.pos.y < -40:
            die()

        # Time for more pipes? dt() is how long this frame took, so taking
        # it away every frame counts down in real seconds.
        next_pipe = next_pipe - dt()
        if next_pipe <= 0:
            add_pipes()
            next_pipe = pipe_wait()

    # --------------------------------------------------------------- pipes

    def add_pipes():
        gap = gap_size()

        # Where the gap starts, picked at random -- but never so near the
        # top, or the grass, that you could not fly through it.
        top = rand(MARGIN, height() - GROUND - MARGIN - gap)
        bottom = top + gap
        x = width()             # just off the right-hand edge

        # The pipes have area() but NOT body(). Bean flies into them rather
        # than bouncing off, and touching one ends the game.

        # The pipe above the gap, from the top of the window down.
        add([rect(PIPE_WIDTH, top), pos(x, 0), color(76, 145, 65),
             outline(4, (46, 100, 40)), area(), "pipe", "slides"])

        # The pipe below the gap, from the gap down to the grass.
        add([rect(PIPE_WIDTH, height() - GROUND - bottom), pos(x, bottom),
             color(76, 145, 65), outline(4, (46, 100, 40)), area(),
             "pipe", "slides"])

        # An invisible strip across the gap. Touching it is what scores the
        # point. It sits at the BACK of the pipes, so the point only comes
        # once you are through -- not the moment you fly into the gap.
        add([rect(6, gap), pos(x + PIPE_WIDTH - 6, top), opacity(0),
             area(), "point", "slides"])

    # Everything tagged "slides" -- both pipes and the strip -- moves left.
    @onUpdate("slides")
    def slide(thing):
        if not alive:
            return
        thing.move(-pipe_speed(), 0)

        # Gone off the left-hand edge? Throw it away. Otherwise the game
        # keeps every pipe it ever made, and after a few minutes there are
        # hundreds of them out of sight, all still being moved.
        if thing.pos.x < -PIPE_WIDTH - 20:
            thing.destroy()

    # -------------------------------------------------------------- points

    @bean.onCollide("point")
    def scored(strip):
        global score

        if not alive:
            return

        strip.destroy()
        score = score + 1
        score_label.text = str(score)

        if score == 1:
            message.text = ""

        if score == 5 or score == 10 or score == 20:
            message.text = "faster!"

            @wait(0.8)
            def clear_message():
                # Only if you are still flying -- otherwise this would wipe
                # out the game-over message.
                if alive:
                    message.text = ""

    # ------------------------------------------------------------- dying

    @bean.onCollide("pipe")
    def hit_pipe(pipe):
        die()

    @bean.onCollide("ground")
    def hit_ground(ground):
        die()

    def die():
        global alive

        # Hit a pipe and Bean falls onto the grass -- that is a second call
        # to die(), and only the first one should count.
        if not alive:
            return
        alive = False

        shake(10)

        if score > best:
            setData(BEST_KEY, score)
            best_label.text = "best " + str(score)

        if score == 1:
            message.text = "1 point -- press SPACE to try again"
        else:
            message.text = (str(score)
                            + " points -- press SPACE to try again")

        # Nothing else is needed to stop the pipes: slide() does nothing
        # once alive is False. Bean has a body(), so it keeps falling until
        # it lands on the grass.


# ------------------------------------------------------- 5. start the game

go("game")
