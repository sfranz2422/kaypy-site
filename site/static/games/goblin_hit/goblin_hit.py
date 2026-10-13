"""Goblin Hit -- monsters pop out of holes. Hit them before they duck.

    click a monster (or tap it) to hit it

Nine holes, thirty seconds. Every kind of monster is worth something
different, and the quick ones are worth the most. Don't hit the angel.
When the time is up you see what you hit, and your best score is
remembered.

HOW THIS FILE IS PUT TOGETHER

    1. the window, the pictures and the sounds
    2. the monsters: what each one is worth, and how long it stays up
    3. the settings
    4. how hard the game is
    5. the game scene: the holes, popping up, hitting, time up
    6. start the game

This is the game for after dictionaries. Every monster has a name, and the
name is the key that looks up everything else about it: its picture, its
points, how long it stays up, and how many of it you hit. Add a monster
of your own and you will see -- it is one new line in each dictionary.
"""

from kaypy import *

# ----------------------------------------------------------------- 1. setup

kaypy(width=800, height=600, background=[72, 62, 78])

# Each monster's picture is eight little pictures in a row. sliceX=8 cuts it
# into eight, and the game only ever shows the first one.
loadSprite("goblin", "dungeon/goblin.png", sliceX=8)
loadSprite("skeleton", "dungeon/skelet.png", sliceX=8)
loadSprite("imp", "dungeon/imp.png", sliceX=8)
loadSprite("chort", "dungeon/chort.png", sliceX=8)
loadSprite("angel", "dungeon/angel.png", sliceX=8)

loadSound("hit", "sounds/thump.wav")
loadSound("ouch", "sounds/small_boom.wav")


# ------------------------------------------------------------ 2. the monsters
#
# Two dictionaries, with the same keys. A key is a monster's name -- the
# same name its picture was loaded under above -- and the value is one fact
# about it. POINTS["imp"] is how many points an imp is worth; STAY["imp"] is
# how long an imp stays up.

POINTS = {
    "goblin": 1,
    "skeleton": 2,
    "imp": 3,
    "chort": 5,
    "angel": -5,
}

STAY = {
    "goblin": 1.4,
    "skeleton": 1.2,
    "imp": 0.9,
    "chort": 0.7,
    "angel": 1.4,
}

# Which monster comes up next is picked from this list. The more times a
# name is in it, the more often that monster comes up.
PICK_FROM = ["goblin", "goblin", "goblin", "goblin",
             "skeleton", "skeleton", "skeleton",
             "imp", "imp", "chort", "angel", "angel"]


# -------------------------------------------------------------- 3. settings
#
# Everything else you would want to change is here. Change one at a time
# and play it.

ROUND = 30             # how long a game lasts, in seconds

MONSTER_SIZE = 5       # how big a monster is: the pictures are 16 pixels

WAIT_START = 0.7       # seconds between monsters, to begin with
WAIT_SHORTEST = 0.3    # ...the shortest wait there ever is
WAIT_DROP = 0.015      # ...and how much shorter each second makes it

# The name the best score is saved under. Every game on a website shares
# the same storage, so the game's own name goes in it.
BEST_KEY = "goblin_hit_best"


# -------------------------------------------------- 4. how hard the game is
#
# The longer the game has gone on, the less time between monsters. It
# stops somewhere, so the game ends up hard but never impossible.

time_left = ROUND


def pop_wait():
    seconds = WAIT_START - (ROUND - time_left) * WAIT_DROP
    if seconds < WAIT_SHORTEST:
        seconds = WAIT_SHORTEST
    return seconds


# ------------------------------------------------------- 5. the game scene
#
# These change while you play. A function that CHANGES one has to say
# `global` first, which means "the one up here, not a new one of my own".

score = 0
playing = True
over = False

# How many of each monster you hit. It starts empty, and a monster's
# name goes in the first time you hit one.
hits = {}


@scene("game")
def game():
    global score, time_left, playing, over, hits

    # A new game, so everything starts again.
    score = 0
    time_left = ROUND
    playing = True
    over = False
    hits = {}
    best = getData(BEST_KEY, 0)

    # The nine holes, in three rows of three. A hole is a dark rectangle
    # with round ends: radius=20 rounds its corners.
    #
    # The dictionary at the end, {"busy": False}, gives each hole a value
    # of its own: hole.busy is True while a monster is in it, so two never
    # come up in the same hole.
    for row in range(3):
        for column in range(3):
            x = 220 + column * 180
            y = 230 + row * 150
            add([rect(120, 40, radius=20), pos(x, y), anchor("center"),
                 color(20, 14, 24), {"busy": False}, "hole"])

    score_label = add([text("0", size=48), pos(width() / 2, 40),
                       anchor("center"), z(10)])
    best_label = add([text("best " + str(best), size=18), pos(12, 12),
                      opacity(0.75), z(10)])
    time_label = add([text(str(ROUND), size=28), pos(width() - 12, 12),
                      anchor("topright"), z(10)])

    message = add([text("Click the monsters! Not the angel.", size=26),
                   pos(width() / 2, 100), anchor("center"), z(10)])

    # --------------------------------------------------------- popping up

    def pop_up():
        # Time is up: no monster, and no wait() for the next one either.
        if not playing:
            return

        # A hole at random. If a monster is already in it, there is no new
        # one this time -- the wait() below still comes round again.
        hole = choose(get("hole"))
        if not hole.busy:
            kind = choose(PICK_FROM)
            hole.busy = True

            # anchor("bot") puts the monster's feet in the hole. The
            # dictionary gives it three values of its own: what kind it is,
            # which hole it is in, and how long it has left before it ducks.
            add([sprite(kind), pos(hole.pos.x, hole.pos.y + 8),
                 anchor("bot"), scale(MONSTER_SIZE), area(), z(5),
                 {"kind": kind, "hole": hole, "stay": STAY[kind]},
                 "monster"])

        wait(pop_wait(), pop_up)

    # The first monster, half a second after the game starts.
    wait(0.5, pop_up)

    # Every monster runs this, every frame: its time runs down, and when
    # there is none left it goes back down its hole.
    @onUpdate("monster")
    def stay_up(monster):
        monster.stay = monster.stay - dt()
        if monster.stay <= 0:
            monster.hole.busy = False
            monster.destroy()

    # ------------------------------------------------------------ hitting
    #
    # onClick runs on every click, wherever it is, and a tap on a phone
    # counts as a click. isHovering() asks whether the mouse is over a
    # monster, which needs area() on it.

    @onClick
    def click():
        if not playing:
            return
        for monster in get("monster"):
            if monster.isHovering():
                hit(monster)
                return

    def hit(monster):
        global score

        kind = monster.kind
        points = POINTS[kind]
        score = score + points
        score_label.text = str(score)
        message.text = ""

        # One more of this kind. hits.get(kind, 0) is how many there
        # were, or 0 if this is the first.
        hits[kind] = hits.get(kind, 0) + 1

        # How many points it was, just where the monster was.
        if points > 0:
            play("hit")
            words = "+" + str(points)
            colour = YELLOW
        else:
            play("ouch")
            shake(10)
            words = str(points)
            colour = RED
        add([text(words, size=32), pos(monster.pos.x, monster.pos.y - 80),
             anchor("center"), color(colour), opacity(1),
             lifespan(0.5, fade=0.3), z(10)])

        monster.hole.busy = False
        monster.destroy()

    # ------------------------------------------------------------- the clock

    def tick():
        global time_left

        if not playing:
            return
        time_left = time_left - 1
        time_label.text = str(time_left)
        if time_left == 0:
            time_up()

    loop(1, tick)

    # -------------------------------------------------------------- time up

    def time_up():
        global playing

        playing = False
        destroyAll("monster")
        destroyAll("hole")

        if score > best:
            setData(BEST_KEY, score)
            best_label.text = "best " + str(score)

        message.text = "Time! " + str(score) + " points"

        # One line for each kind you hit: its picture, how many, and
        # what they came to. .items() hands over each key with its value.
        y = 180
        for kind, count in hits.items():
            add([sprite(kind), pos(300, y), anchor("center"), scale(3)])
            add([text("x " + str(count) + " = " + str(count * POINTS[kind]),
                      size=28), pos(350, y), anchor("left")])
            y = y + 60

        # A second before you can start again, so a click meant for the
        # last monster does not skip past your score.
        wait(1, ready_again)

    def ready_again():
        global over

        over = True
        add([text("press SPACE or click to play again", size=24),
             pos(width() / 2, height() - 40), anchor("center")])

    def again():
        if over:
            go("game")

    onKeyPress("space", again)
    onClick(again)


# ------------------------------------------------------- 6. start the game

go("game")
