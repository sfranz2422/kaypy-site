"""Spike Runner -- the cube runs by itself. You just jump.

    space, up or click   jump (hold it to keep jumping)

The cube never stops running. Jump over the spikes, onto the blocks and
across the gaps. In mid-air, a yellow orb gives you a second jump: hold
jump as you go through it. Touch a spike, run into the side of a
block or fall into a gap, and you start again from the beginning. The bar
at the top shows how far you got, and your best is remembered.

HOW THIS FILE IS PUT TOGETHER

    1. the window, the pictures and the sounds
    2. the settings
    3. the level, in sections
    4. what each letter turns into
    5. the run: the cube, jumping, crashing, the camera, the progress bar
    6. start the game

The level is a row of short sections, each a picture made of letters. Add
a section, swap two round, or draw a new one -- you never have to touch the
code to change the level.
"""

from kaypy import *

# ----------------------------------------------------------------- 1. setup

TILE = 40          # one tile is 40 pixels square

kaypy(width=960, height=560, background=[40, 90, 200])

# Strong gravity and a hard jump make short, snappy hops.
setGravity(5000)

loadSprite("spike", "images/triangle.png")

loadSound("crash", "sounds/small_boom.wav")
loadSound("win", "sounds/rising_beep.wav")

# Music is switched off, because the track is 2.4 MB and would make the
# game slow to load. To switch it on: take the # off the line below, and set
# MUSIC = True in the settings.
# loadSound("music", "sounds/background.wav")


# -------------------------------------------------------------- 2. settings
#
# Every number worth changing is here.

SPEED = 420           # how fast the cube runs, in pixels per second
JUMP = 1000           # how hard a jump is: two and a half tiles high
ORB_JUMP = 1150       # how hard an orb throws you, a little more
SPIN = 520            # how fast the cube turns in the air, degrees a second
SPIKE_REACH = 22      # how close to a spike's middle counts as touching it
MUSIC = False         # True plays music -- see the loadSound line above

# The name the best score is saved under. Every game on a website shares
# the same storage, so the game's own name goes in it.
BEST_KEY = "spike_runner_best"


# --------------------------------------------------------- 3. the level
#
# One letter is one tile.
#
#   #  block        ^  spike        o  jump orb
#   @  the cube starts here
#
# A space is empty. The bottom row is the floor: leave a gap in it and the
# cube can fall through.
#
# The level is a row of SECTIONS, joined end to end. Every section has to
# have the same number of rows -- 9 -- but each can be as wide as you like.

START = [
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "  @       ",
    "##########",
]

ONE_SPIKE = [
    "              ",
    "              ",
    "              ",
    "              ",
    "              ",
    "              ",
    "              ",
    "      ^       ",
    "##############",
]

TWO_SPIKES = [
    "              ",
    "              ",
    "              ",
    "              ",
    "              ",
    "              ",
    "              ",
    "      ^^      ",
    "##############",
]

STEPS = [
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                 ##     ",
    "            ##   ##     ",
    "       ##   ##   ##^^^  ",
    "########################",
]

GAP = [
    "              ",
    "              ",
    "              ",
    "              ",
    "              ",
    "              ",
    "              ",
    "              ",
    "#####   ######",
]

THREE_SPIKES = [
    "                ",
    "                ",
    "                ",
    "                ",
    "                ",
    "                ",
    "                ",
    "       ^^^      ",
    "################",
]

PLATFORMS = [
    "                              ",
    "                              ",
    "                              ",
    "                              ",
    "              ####            ",
    "                              ",
    "         ###                  ",
    "    ^          ^^^^^^^        ",
    "##############################",
]

ORB_GAP = [
    "                    ",
    "                    ",
    "                    ",
    "                    ",
    "                    ",
    "       o            ",
    "                    ",
    "                    ",
    "#####       ########",
]

TUNNEL = [
    "                          ",
    "                          ",
    "                          ",
    "                          ",
    "      ##############      ",
    "                          ",
    "                          ",
    "          ^    ^          ",
    "##########################",
]

STAIRS_UP = [
    "                          ",
    "                          ",
    "                          ",
    "                     ##   ",
    "                ##   ##   ",
    "           ##   ##   ##   ",
    "      ##   ##   ##   ##   ",
    "      ##^^^##^^^##^^^##^^^",
    "##########################",
]

ORB_CHAIN = [
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "       o   o            ",
    "                        ",
    "                        ",
    "#####          #########",
]

FINISH = [
    "                    ",
    "                    ",
    "                    ",
    "                    ",
    "                    ",
    "                    ",
    "                    ",
    "                    ",
    "####################",
]

SECTIONS = [
    START, ONE_SPIKE, ONE_SPIKE, TWO_SPIKES, STEPS, GAP, THREE_SPIKES,
    PLATFORMS, ORB_GAP, TWO_SPIKES, TUNNEL, GAP, STAIRS_UP, ORB_CHAIN,
    THREE_SPIKES, PLATFORMS, ORB_GAP, STEPS, FINISH,
]


def join_sections(sections):
    """Glue the sections together, side by side, into one long level.

    Row 0 of the level is row 0 of every section, one after another, and
    the same for every other row.
    """
    # Every row of a section has to be the same width. If one is a letter
    # short, everything after it on that row slides one tile to the left,
    # and nothing says so -- so check, and say which section it is.
    for number in range(len(sections)):
        section = sections[number]
        for line in section:
            if len(line) != len(section[0]):
                print("Section", number + 1, "in SECTIONS has rows of",
                      "different widths. Count the letters on each row.")

    level = []
    for row in range(len(sections[0])):
        line = ""
        for section in sections:
            line = line + section[row]
        level.append(line)
    return level


LEVEL = join_sections(SECTIONS)
LEVEL_WIDTH = len(LEVEL[0]) * TILE

# The level is 9 rows tall and the window is 14. Starting the level 4 rows
# down leaves sky above it and puts the floor near the bottom.
TOP = TILE * 4


# ----------------------------------------------- 4. what each letter becomes

TILES = {
    "#": lambda: [rect(TILE, TILE), color(20, 30, 70),
                  outline(2, (120, 200, 255)), area(),
                  body(isStatic=True), "block"],

    # The triangle picture is 48 x 39. Scaling it to exactly one tile means
    # it sits on the floor of its square instead of hovering at the top.
    # It has no area(): touching a spike is worked out by distance instead.
    # See crashed_into_spike() below for why.
    "^": lambda: [sprite("spike"), scale(TILE / 48, TILE / 39), "spike"],

    # An orb works once per attempt. "used" says whether it has been.
    "o": lambda: [circle(14), color(255, 220, 60), outline(3, (255, 255, 255)),
                  opacity(1), "orb", {"used": False}],

    # The cube. anchor("center") so that it turns about its middle.
    "@": lambda: [rect(36, 36), color(255, 210, 40), outline(3, (0, 0, 0)),
                  anchor("center"), rotate(0), area(), body(), z(10),
                  "player"],
}


# ---------------------------------------------- what the game has to remember
#
# These change while you play. A function that CHANGES one has to say
# `global` first, which means "the one up here, not a new one of my own".

attempt = 1
crashed = False
finished = False
last_x = 0          # where the cube was last frame
expected = 0        # how far it was told to move last frame
music = None


# ------------------------------------------------------------- 5. the run
#
# The scene is CALLED "run". A new attempt is the same scene built again,
# so everything starts from the beginning. The function is not called
# play(), because kaypy already has a play() for sounds.

@scene("run")
def run(number):
    global attempt, crashed, finished, last_x, expected, music

    attempt = number
    crashed = False
    finished = False
    expected = 0

    addLevel(LEVEL, {
        "tileWidth": TILE,
        "tileHeight": TILE,
        "pos": vec2(0, TOP),
        "tiles": TILES,
    })

    cube = get("player")[0]
    last_x = cube.pos.x
    best = getData(BEST_KEY, 0)

    # Written into the level at the start, so it scrolls away as you go.
    add([text("Attempt " + str(attempt), size=44),
         pos(cube.pos.x + 60, TOP + TILE * 2)])

    # The music starts again with every attempt. The old one is stopped
    # first, or each attempt would add another copy playing on top.
    if music is not None:
        music.paused = True
    if MUSIC:
        music = play("music", loop=True, volume=0.5)

    # --------------------------------------------------------- jumping
    #
    # Holding the key jumps again the moment the cube lands -- that is why
    # this asks every frame rather than waiting for a key press.

    def holding_jump():
        return isKeyDown("space") or isKeyDown("up") or isMouseDown()

    # An orb fires if jump is held while the cube touches it -- held, not
    # just pressed at that moment. The cube is only touching an orb for a
    # tenth of a second, far too short to hit with a fresh press; holding
    # the key as you go in is how it is meant to be played.
    #
    # Each orb fires once, then dims. Without "used", holding the key would
    # fire it again on every frame the cube was touching it.
    def use_orbs():
        for orb in get("orb"):
            # A circle's pos is its top-left corner; its middle is one
            # radius (14) in from there.
            middle = vec2(orb.pos.x + 14, orb.pos.y + 14)
            if not orb.used and cube.pos.dist(middle) < 40:
                orb.used = True
                orb.opacity = 0.3
                cube.jump(ORB_JUMP)

    # A sign over the first orb, because nothing else says what they do.
    orbs = get("orb")
    if len(orbs) > 0:
        first = orbs[0]
        add([text("hold jump through the orb!", size=22),
             pos(first.pos.x - 130, first.pos.y - 60)])

    # ------------------------------------------------------ every frame

    @onUpdate
    def each_frame():
        global last_x, expected

        if crashed or finished:
            return

        # Ran into the side of a block? Then the block stopped the cube, and
        # it got less than half as far as it was told to go last frame. That
        # is "last frame", not this one: frames are not all the same length,
        # and comparing against this frame's would call a long frame after a
        # short one a crash.
        if cube.pos.x - last_x < expected * 0.5:
            crash()
            return
        last_x = cube.pos.x
        expected = SPEED * dt()

        cube.move(SPEED, 0)

        if cube.isGrounded():
            # Land square: turn to the nearest quarter turn.
            cube.angle = round(cube.angle / 90) * 90
            if holding_jump():
                cube.jump(JUMP)
        else:
            cube.angle = cube.angle + SPIN * dt()
            if holding_jump():
                use_orbs()

        if crashed_into_spike():
            crash()
            return

        # Fell into a gap.
        if cube.pos.y > height() + 50:
            crash()
            return

        if cube.pos.x > LEVEL_WIDTH - TILE * 6:
            finish()

        # The camera keeps the cube a quarter of the way across the window,
        # so you can see what is coming.
        setCamPos(vec2(cube.pos.x + width() / 4, height() / 2))

    # A spike is a triangle, but a collision box is a rectangle. A box would
    # kill you for clipping the empty corner beside the point. So instead,
    # measure how far the cube is from the solid middle of the spike, a
    # little below its centre, and only count it if that is close.
    def crashed_into_spike():
        for spike in get("spike"):
            middle = vec2(spike.pos.x + TILE / 2, spike.pos.y + TILE * 0.65)
            if cube.pos.dist(middle) < SPIKE_REACH:
                return True
        return False

    # ------------------------------------------------- the progress bar

    @onDraw
    def progress_bar():
        done = clamp(cube.pos.x / (LEVEL_WIDTH - TILE * 6), 0, 1)
        drawRect(pos=vec2(280, 18), width=400, height=14,
                 color=(20, 30, 70), fixed=True)
        drawRect(pos=vec2(280, 18), width=400 * done, height=14,
                 color=(120, 255, 140), fixed=True)
        drawText(text=str(int(done * 100)) + "%", pos=vec2(692, 12),
                 size=22, fixed=True)
        drawText(text="best " + str(best) + "%", pos=vec2(16, 12),
                 size=20, fixed=True)

    # ------------------------------------------------- crashing, winning

    def percent():
        return int(clamp(cube.pos.x / (LEVEL_WIDTH - TILE * 6), 0, 1) * 100)

    def save_best(score):
        if score > best:
            setData(BEST_KEY, score)

    def crash():
        global crashed

        if crashed:
            return
        crashed = True

        if music is not None:
            music.paused = True
        play("crash")
        shake(10)
        save_best(percent())

        # The cube breaks into pieces that fly off and fade.
        for i in range(12):
            add([rect(10, 10), pos(cube.pos.x, cube.pos.y),
                 color(255, 210, 40), opacity(1),
                 move(vec2(rand(-1, 1), rand(-1, 1)), rand(100, 400)),
                 lifespan(0.6, fade=0.4)])
        cube.destroy()

        @wait(0.7)
        def again():
            go("run", attempt + 1)

    def finish():
        global finished

        finished = True
        if music is not None:
            music.paused = True
        play("win")
        save_best(100)

        if attempt == 1:
            tries = "on your first attempt!"
        else:
            tries = "in " + str(attempt) + " attempts."

        @say("Level complete, " + tries, button="Play again")
        def play_again():
            go("run", 1)


# ------------------------------------------------------- 6. start the game

go("run", 1)
