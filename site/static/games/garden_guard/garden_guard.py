"""Garden Guard -- plant a garden, and hold off the zombies.

    click or tap a plant card, then a square of lawn, to plant it
    click or tap a sun to collect it

Zombies walk in from the right, one row at a time, and eat any plant in
their way. Plants cost sun. Sun falls from the sky, and pineapples make more
of it, so plant pineapples first, then beans to shoot the zombies. Each row
has a lawnmower that clears the row the first time a zombie gets through --
but only the first time. If a zombie reaches the house, the level is lost.

Every level brings a new plant and a new kind of zombie. The level you
reached is remembered.

THE PLANTS

    pineapple   makes sun
    bean        shoots peas down its row
    brock       a wall: takes a long time to eat
    bomb        blows up every zombie in the squares around it
    onion       shoots icy peas that slow zombies down

HOW THIS FILE IS PUT TOGETHER

    1. the window and the pictures
    2. the settings: plants, zombies and levels
    3. the lawn
    4. what the game has to remember
    5. levels: starting, winning, losing
    6. sun
    7. planting: the cards and the lawn
    8. what plants do
    9. zombies, and peas hitting them
   10. the lawnmowers
   11. the waves
   12. drawing the top bar
   13. start the game

Plants, zombies, peas and suns are game objects. Each one carries a few
values of its own as well -- a zombie knows its row and how fast it walks,
a plant knows how long until it next shoots.
"""

from kaypy import *

# --------------------------------------------------------------- 1. setup

COLS = 9           # squares across the lawn
ROWS = 5           # rows of lawn
CELL = 80          # a square is 80 pixels wide
ROW_H = 90         # and 90 tall

LAWN_X = 90        # the lawn starts here; left of it is the house
LAWN_Y = 120       # and here, under the top bar

kaypy(width=LAWN_X + COLS * CELL + 50, height=LAWN_Y + ROWS * ROW_H + 20,
      background=[60, 45, 35])

loadSprite("sun", "images/sun.png")
loadSprite("pineapple", "images/pineapple.png")
loadSprite("bean", "images/bean.png")
loadSprite("brock", "images/brock.png")
loadSprite("bomb", "images/bomb.png")
loadSprite("onion", "images/onion.png")

# The zombies are strips of tiny pictures, one frame after another.
loadSprite("zombie", "dungeon/zombie.png", sliceX=4, anims={
    "walk": {"from": 0, "to": 3, "speed": 6, "loop": True},
})
loadSprite("tiny_zombie", "dungeon/tiny_zombie.png", sliceX=8, anims={
    "walk": {"from": 4, "to": 7, "speed": 10, "loop": True},
})
loadSprite("big_zombie", "dungeon/big_zombie.png", sliceX=8, anims={
    "walk": {"from": 4, "to": 7, "speed": 6, "loop": True},
})

loadSound("collect", "sounds/small_beep.wav")
loadSound("plant", "sounds/thump.wav")
loadSound("boom", "sounds/small_boom.wav")
loadSound("mower", "sounds/swoosh.wav")
loadSound("win", "sounds/rising_beep.wav")
loadSound("lose", "sounds/lazer_punch.wav")


# ----------------------------------------------------------- 2. settings

START_SUN = 50          # sun at the start of a level
SUN_VALUE = 25          # what one sun is worth
SKY_SUN_EVERY = 9       # seconds between suns falling from the sky
SUN_LIFE = 12           # seconds a sun stays before it fades away

PEA_SPEED = 320         # pixels per second
SLOW_TIME = 3           # how long an icy pea slows a zombie, in seconds
BITE_TIME = 0.6         # seconds between a zombie's bites

FIRST_WAVE = 20         # seconds before the first zombies come
WAVE_GAP = 16           # seconds between waves
SPAWN_GAP = 2.5         # seconds between zombies in the same wave

# Each plant: what it costs, how long before you can plant another, how
# many bites it takes to eat, and how often it does its job, in seconds.
# "scale" shrinks the picture to fit a square; "w" and "h" are the size of
# the picture file itself, which the cards need to draw it.
PLANTS = {
    "pineapple": {"cost": 50, "wait": 5, "hp": 6, "every": 12,
                  "scale": 0.75, "w": 64, "h": 80},
    "bean": {"cost": 100, "wait": 5, "hp": 6, "every": 1.4,
             "scale": 0.9, "w": 64, "h": 54},
    "brock": {"cost": 50, "wait": 20, "hp": 60, "every": 0,
              "scale": 0.55, "w": 128, "h": 102},
    "bomb": {"cost": 150, "wait": 30, "hp": 100, "every": 0.8,
             "scale": 0.65, "w": 82, "h": 92},
    "onion": {"cost": 175, "wait": 5, "hp": 6, "every": 1.4,
              "scale": 0.6, "w": 77, "h": 101},
}

# Each zombie: how many peas it takes, and how fast it walks.
ZOMBIES = {
    "zombie": {"hp": 10, "speed": 16, "scale": 4},
    "tiny_zombie": {"hp": 5, "speed": 32, "scale": 3},
    "big_zombie": {"hp": 30, "speed": 10, "scale": 2.2},
}

# Each level: the plants you can use, and the waves of zombies. A wave is
# a list of the zombies in it; they come one after another, in random rows.
# The last wave of every level is the big one.
LEVELS = [
    {"plants": ["pineapple", "bean"],
     "waves": [["zombie"], ["zombie"], ["zombie", "zombie"], ["zombie"],
               ["zombie", "zombie"],
               ["zombie", "zombie", "zombie", "zombie"]]},
    {"plants": ["pineapple", "bean", "brock"],
     "waves": [["zombie"], ["tiny_zombie"], ["zombie", "zombie"],
               ["tiny_zombie", "zombie"],
               ["zombie", "tiny_zombie", "zombie"],
               ["zombie", "zombie", "tiny_zombie", "tiny_zombie",
                "zombie"]]},
    {"plants": ["pineapple", "bean", "brock", "bomb"],
     "waves": [["zombie"], ["zombie", "tiny_zombie"], ["big_zombie"],
               ["zombie", "zombie", "tiny_zombie"],
               ["big_zombie", "zombie"],
               ["zombie", "tiny_zombie", "zombie", "tiny_zombie"],
               ["big_zombie", "big_zombie", "zombie", "zombie",
                "tiny_zombie", "tiny_zombie"]]},
    {"plants": ["pineapple", "bean", "brock", "bomb", "onion"],
     "waves": [["zombie", "zombie"], ["tiny_zombie", "tiny_zombie"],
               ["big_zombie", "zombie"],
               ["zombie", "zombie", "tiny_zombie", "zombie"],
               ["big_zombie", "big_zombie"],
               ["tiny_zombie", "tiny_zombie", "tiny_zombie", "zombie",
                "zombie"],
               ["big_zombie", "zombie", "zombie", "big_zombie"],
               ["big_zombie", "big_zombie", "big_zombie", "zombie",
                "zombie", "zombie", "tiny_zombie", "tiny_zombie",
                "tiny_zombie"]]},
]

LEVEL_KEY = "garden_guard_level"


# -------------------------------------------------------------- 3. the lawn
#
# The lawn is made of rectangles that are game objects, not drawn in
# onDraw. onDraw draws on top of every object, so a lawn drawn there would
# cover the plants and the zombies. z(-10) puts these behind everything.

for row in range(ROWS):
    for col in range(COLS):
        if (row + col) % 2 == 0:
            green = (90, 170, 70)
        else:
            green = (80, 155, 62)
        add([rect(CELL, ROW_H), pos(LAWN_X + col * CELL, LAWN_Y + row * ROW_H),
             color(green[0], green[1], green[2]), z(-10)])


def square_x(col):
    """The middle of a square, across."""
    return LAWN_X + col * CELL + CELL / 2


def row_y(row):
    """The middle of a row, down."""
    return LAWN_Y + row * ROW_H + ROW_H / 2


# ------------------------------------------- 4. what the game remembers

level = getData(LEVEL_KEY, 0)   # 0 is the first level in LEVELS
sun = START_SUN
selected = None      # the name of the plant card picked, or None
ready_at = {}        # plant name -> the time() its card is ready again
over = False         # True once the zombies are in, or a level is won

# grid[row][col] is the plant in that square, or None.
grid = []

# One lawnmower per row: where it is, and whether it is waiting, going, or
# gone for good.
mowers = []

wave_number = 0      # how many waves have come so far this level
wave_wait = 0        # seconds until the next wave
queue = []           # zombies of this wave still to come
spawn_wait = 0       # seconds until the next one of them
banner = ""          # big words across the lawn, for a moment
banner_time = 0


# ------------------------------------------------------------- 5. levels

def start_level():
    global sun, selected, ready_at, over, grid, mowers
    global wave_number, wave_wait, queue, spawn_wait, banner, banner_time

    destroyAll("plant")
    destroyAll("zombie")
    destroyAll("pea")
    destroyAll("sun")

    sun = START_SUN
    selected = None
    ready_at = {}
    over = False
    grid = []
    mowers = []
    for row in range(ROWS):
        grid.append([None] * COLS)
        mowers.append({"x": LAWN_X - 40, "state": "waiting"})

    wave_number = 0
    wave_wait = FIRST_WAVE
    queue = []
    spawn_wait = 0
    banner = "Level " + str(level + 1)
    banner_time = 2


def level_won():
    global over, level

    over = True
    play("win")
    if level + 1 < len(LEVELS):
        new_plant = LEVELS[level + 1]["plants"][-1]
        level = level + 1
        setData(LEVEL_KEY, level)

        @say("Level " + str(level) + " cleared!\n\n"
             "You have a new plant: the " + new_plant + ".",
             button="Next level")
        def next_level():
            start_level()
    else:
        level = 0
        setData(LEVEL_KEY, level)

        @say("You saved the garden!\n\nEvery level cleared.",
             button="Play again")
        def again():
            start_level()


def level_lost():
    global over

    over = True
    play("lose")
    shake(10)

    @say("The zombies got into the house!", button="Try again")
    def try_again():
        start_level()


# ------------------------------------------------------------------ 6. sun

def make_sun(x, start_y, land_y):
    """A sun that drifts down to land_y, waits, and fades away."""
    s = add([sprite("sun"), pos(x, start_y), anchor("center"), scale(0.8),
             opacity(1), lifespan(SUN_LIFE, fade=2), z(20), "sun"])
    s.land_y = land_y


@onUpdate("sun")
def drift(s):
    if s.pos.y < s.land_y:
        s.pos.y += 60 * dt()


@loop(SKY_SUN_EVERY)
def sun_from_the_sky():
    # It starts under the top bar, so it seems to come out from behind it.
    x = rand(LAWN_X + 30, LAWN_X + COLS * CELL - 30)
    make_sun(x, LAWN_Y - 40, rand(LAWN_Y + 40, LAWN_Y + ROWS * ROW_H - 40))


# ------------------------------------- 7. planting: the cards and the lawn
#
# One handler for every click or tap. It asks, in order: was that a sun?
# a card? the lawn? A sun comes first because suns float over the lawn,
# and a tap on one should collect it, not plant something under it.

CARD_X = 95
CARD_W = 78
CARD_GAP = 6


def card_x(i):
    return CARD_X + i * (CARD_W + CARD_GAP)


def card_ready(name):
    return time() >= ready_at.get(name, 0)


@onMousePress
def click():
    global sun, selected

    if over:
        return
    m = mousePos()

    for s in get("sun"):
        if m.dist(s.pos) < 35:
            sun = sun + SUN_VALUE
            s.destroy()
            play("collect")
            return

    plants = LEVELS[level]["plants"]
    if m.y < LAWN_Y:
        for i in range(len(plants)):
            if card_x(i) <= m.x < card_x(i) + CARD_W:
                name = plants[i]
                if selected == name:
                    selected = None            # tap again to put it back
                elif card_ready(name) and sun >= PLANTS[name]["cost"]:
                    selected = name
        return

    col = int((m.x - LAWN_X) // CELL)
    row = int((m.y - LAWN_Y) // ROW_H)
    if selected is None or col < 0 or col >= COLS or row < 0 or row >= ROWS:
        return
    if grid[row][col] is not None:
        return

    put_plant(selected, row, col)
    sun = sun - PLANTS[selected]["cost"]
    ready_at[selected] = time() + PLANTS[selected]["wait"]
    selected = None
    play("plant")


def put_plant(name, row, col):
    info = PLANTS[name]
    plant = add([sprite(name), pos(square_x(col), row_y(row)),
                 anchor("center"), scale(info["scale"]), health(info["hp"]),
                 z(1), "plant"])
    plant.kind = name
    plant.row = row
    plant.col = col
    plant.timer = info["every"]
    if name == "pineapple":
        plant.timer = 5          # the first sun comes sooner
    grid[row][col] = plant


def remove_plant(plant):
    grid[plant.row][plant.col] = None
    plant.destroy()


# --------------------------------------------------- 8. what plants do

@onUpdate("plant")
def plant_work(plant):
    if over:
        return
    plant.timer -= dt()
    if plant.timer > 0:
        return

    if plant.kind == "pineapple":
        make_sun(plant.pos.x + 15, plant.pos.y - 10, plant.pos.y + 20)
        plant.timer = PLANTS["pineapple"]["every"]

    if plant.kind == "bean" or plant.kind == "onion":
        if zombie_ahead(plant):
            shoot(plant)
            plant.timer = PLANTS[plant.kind]["every"]

    if plant.kind == "bomb":
        explode(plant)


def zombie_ahead(plant):
    """Is there a zombie on the lawn in this plant's row, in front of it?"""
    for zombie in get("zombie"):
        if zombie.row == plant.row and zombie.pos.x > plant.pos.x - 10:
            if zombie.pos.x < LAWN_X + COLS * CELL + 10:
                return True
    return False


def shoot(plant):
    if plant.kind == "onion":
        colour = (160, 220, 255)
    else:
        colour = (120, 220, 80)
    pea = add([circle(9), pos(plant.pos.x + 25, row_y(plant.row) - 6),
               anchor("center"), color(colour[0], colour[1], colour[2]),
               area(), move(vec2(1, 0), PEA_SPEED), z(15), "pea"])
    pea.row = plant.row
    pea.icy = plant.kind == "onion"


@onUpdate("pea")
def pea_gone(pea):
    # Past the end of the lawn, a pea can never hit anything. Take it away,
    # or the game slowly fills up with peas nobody can see.
    if pea.pos.x > width() + 20:
        pea.destroy()


def explode(bomb):
    addKaboom(bomb.pos, scale=1.5)
    play("boom")
    shake(6)
    for zombie in get("zombie"):
        if abs(zombie.row - bomb.row) <= 1:
            if abs(zombie.pos.x - bomb.pos.x) < CELL * 1.5:
                zombie.destroy()
    remove_plant(bomb)


# ------------------------------------- 9. zombies, and peas hitting them

def spawn(kind):
    info = ZOMBIES[kind]
    row = choose(range(ROWS))
    # anchor("bot") means pos is where its feet are.
    zombie = add([sprite(kind, anim="walk"),
                  pos(width() + 30, row_y(row) + ROW_H / 2 - 8),
                  anchor("bot"), scale(info["scale"]), area(),
                  health(info["hp"]), z(3 + row), "zombie"])
    zombie.flipX = True      # the pictures face right; zombies walk left
    zombie.kind = kind
    zombie.row = row
    zombie.walk_speed = info["speed"] * rand(0.9, 1.1)
    zombie.slow_left = 0
    zombie.bite_wait = 0


def plant_in_front(zombie):
    """The plant in the square the zombie's face is in, or None."""
    col = int((zombie.pos.x - 20 - LAWN_X) // CELL)
    if col < 0 or col >= COLS:
        return None
    return grid[zombie.row][col]


@onUpdate("zombie")
def walk(zombie):
    if over:
        return

    speed = zombie.walk_speed
    if zombie.slow_left > 0:
        zombie.slow_left -= dt()
        speed = speed / 2

    plant = plant_in_front(zombie)
    if plant is not None:
        # Stop and eat.
        zombie.bite_wait -= dt()
        if zombie.bite_wait <= 0:
            plant.hurt(1)
            zombie.bite_wait = BITE_TIME
            if not plant.isAlive():
                remove_plant(plant)
    else:
        zombie.pos.x -= speed * dt()

    # At the edge of the lawn: the mower, if it is still there. Past the
    # mower: the house.
    mower = mowers[zombie.row]
    if zombie.pos.x < LAWN_X - 10 and mower["state"] == "waiting":
        mower["state"] = "going"
        play("mower")
    if zombie.pos.x < 20:
        level_lost()


@onCollide("pea", "zombie")
def hit(pea, zombie):
    # A pea only hits zombies in its own row, and only once.
    if pea.row != zombie.row or not pea.exists():
        return
    pea.destroy()
    zombie.hurt(1)
    if pea.icy:
        zombie.slow_left = SLOW_TIME
    if not zombie.isAlive():
        zombie.destroy()


# --------------------------------------------------------- 10. lawnmowers

@onUpdate
def mow():
    if over:
        return
    for row in range(ROWS):
        mower = mowers[row]
        if mower["state"] == "going":
            mower["x"] += 500 * dt()
            for zombie in get("zombie"):
                if zombie.row == row and abs(zombie.pos.x - mower["x"]) < 40:
                    zombie.destroy()
            if mower["x"] > width() + 40:
                mower["state"] = "gone"


# -------------------------------------------------------------- 11. waves

@onUpdate
def run_waves():
    global wave_number, wave_wait, queue, spawn_wait, banner, banner_time

    banner_time -= dt()
    if over:
        return
    waves = LEVELS[level]["waves"]

    if len(queue) > 0:
        spawn_wait -= dt()
        if spawn_wait <= 0:
            spawn(queue.pop(0))
            spawn_wait = SPAWN_GAP
    elif wave_number < len(waves):
        wave_wait -= dt()
        if wave_wait <= 0:
            queue = list(waves[wave_number])
            wave_number = wave_number + 1
            wave_wait = WAVE_GAP
            spawn_wait = 0
            if wave_number == len(waves):
                banner = "A big wave is coming!"
                banner_time = 3
    elif len(get("zombie")) == 0:
        level_won()


# ------------------------------------------------------ 12. the top bar

def draw_mower(x, y):
    drawRect(pos=vec2(x - 22, y - 14), width=44, height=22,
             color=(200, 50, 50), radius=5)
    drawRect(pos=vec2(x - 18, y - 30), width=6, height=18,
             color=(90, 90, 90))
    drawCircle(pos=vec2(x - 13, y + 10), radius=7, color=(30, 30, 30))
    drawCircle(pos=vec2(x + 13, y + 10), radius=7, color=(30, 30, 30))


@onDraw
def draw_everything():
    for row in range(ROWS):
        if mowers[row]["state"] != "gone":
            draw_mower(mowers[row]["x"], row_y(row) + 10)

    # Slowed zombies get a blue glow.
    for zombie in get("zombie"):
        if zombie.slow_left > 0:
            drawCircle(pos=vec2(zombie.pos.x, zombie.pos.y - 30), radius=30,
                       color=(120, 190, 255), opacity=0.35)

    # The plant you are holding, over the square under the mouse.
    m = mousePos()
    if selected is not None and m.y > LAWN_Y and m.x > LAWN_X:
        col = int((m.x - LAWN_X) // CELL)
        row = int((m.y - LAWN_Y) // ROW_H)
        if col < COLS and row < ROWS:
            info = PLANTS[selected]
            drawSprite(sprite=selected, pos=vec2(square_x(col), row_y(row)),
                       width=info["w"] * info["scale"],
                       height=info["h"] * info["scale"],
                       anchor="center", opacity=0.5)

    # The top bar: how much sun, then a card for each plant.
    drawRect(pos=vec2(0, 0), width=width(), height=LAWN_Y - 8,
             color=(110, 75, 45))
    drawRect(pos=vec2(8, 8), width=78, height=96, color=(80, 55, 35),
             radius=8)
    drawSprite(sprite="sun", pos=vec2(47, 42), width=50, height=50,
               anchor="center")
    drawText(text=str(sun), pos=vec2(47, 88), size=22, anchor="center")

    plants = LEVELS[level]["plants"]
    for i in range(len(plants)):
        name = plants[i]
        info = PLANTS[name]
        x = card_x(i)
        drawRect(pos=vec2(x, 8), width=CARD_W, height=96,
                 color=(235, 220, 170), radius=8)
        if selected == name:
            drawRect(pos=vec2(x, 8), width=CARD_W, height=96,
                     color=(255, 240, 60), radius=8, outline=4)
        drawSprite(sprite=name, pos=vec2(x + CARD_W / 2, 46),
                   width=info["w"] * info["scale"] * 0.75,
                   height=info["h"] * info["scale"] * 0.75, anchor="center")
        drawText(text=str(info["cost"]), pos=vec2(x + CARD_W / 2, 90),
                 size=18, color=(60, 40, 20), anchor="center")

        # Grey while it is waiting to be ready, shrinking as it gets
        # nearer; dim if you cannot afford it.
        if not card_ready(name):
            left = (ready_at[name] - time()) / info["wait"]
            drawRect(pos=vec2(x, 8), width=CARD_W, height=96 * left,
                     color=(40, 40, 40), opacity=0.6, radius=8)
        elif sun < info["cost"]:
            drawRect(pos=vec2(x, 8), width=CARD_W, height=96,
                     color=(40, 40, 40), opacity=0.4, radius=8)

    waves = LEVELS[level]["waves"]
    drawText(text="Level " + str(level + 1), pos=vec2(width() - 20, 22),
             size=26, anchor="topright")
    if wave_number == 0:
        progress = "Get ready!"
    else:
        progress = "Wave " + str(wave_number) + " of " + str(len(waves))
    drawText(text=progress, pos=vec2(width() - 20, 62), size=20,
             anchor="topright")

    if banner_time > 0:
        drawText(text=banner, pos=vec2(LAWN_X + COLS * CELL / 2,
                                       LAWN_Y + ROWS * ROW_H / 2),
                 size=44, anchor="center")


# ------------------------------------------------------- 13. start the game

start_level()
say("Zombies are coming for the garden!\n\n"
    "Tap a plant card, then a square of lawn, to plant it. Plants cost sun: "
    "tap the suns to collect them. Pineapples make more sun, and beans "
    "shoot the zombies.", button="Play")
