"""Block Slide -- slide the blocks, fill the rows, don't reach the top.

    drag a block left or right   (a finger on a phone, the mouse elsewhere)

Every block lies in a row. Drag one sideways, as far as the gaps let it go,
and let go. Blocks with nothing under them fall. A row with no gaps left is
cleared, and everything above it falls too. Then a new row of blocks pushes
up from the bottom -- after every single move. If the blocks are pushed off
the top, the game is over. Your best score is remembered.

HOW THIS FILE IS PUT TOGETHER

    1. the window
    2. the settings
    3. the board: a list of blocks, and questions you can ask it
    4. making a new row
    5. a turn: falling, clearing, rising -- one step at a time
    6. dragging
    7. drawing
    8. start the game

There are no game objects in this game. Every block is a dictionary in a
list, and the board is drawn from that list every frame. Moving a block is
changing a number in its dictionary.
"""

from kaypy import *

# ----------------------------------------------------------------- 1. setup

COLS = 8           # squares across
ROWS = 10          # squares down
CELL = 50          # one square is 50 pixels

BOARD_X = 20       # where the board's top-left corner is in the window
BOARD_Y = 110

# Tall rather than wide, to fit a phone held upright.
kaypy(width=COLS * CELL + 40, height=BOARD_Y + ROWS * CELL + 30,
      background=[30, 30, 50])

loadSound("clear", "sounds/rising_beep.wav")
loadSound("slide", "sounds/swoosh.wav")
loadSound("over", "sounds/small_boom.wav")


# -------------------------------------------------------------- 2. settings
#
# Every number worth changing is here.

START_ROWS = 4        # rows of blocks on the board when a game starts
GAP_CHANCE = 0.3      # how often a new row has a gap where a block could be
STEP_TIME = 0.08      # seconds between one step of falling and the next
CLEAR_TIME = 0.25     # how long a full row flashes before it goes
POINTS_PER_ROW = 10

# A block's colour depends on how long it is.
COLOURS = {
    1: (240, 90, 90),
    2: (250, 180, 60),
    3: (90, 200, 120),
    4: (80, 150, 240),
}

# The name the best score is saved under. Every game on a website shares
# the same storage, so the game's own name goes in it.
BEST_KEY = "block_slide_best"


# ------------------------------------------------------------- 3. the board
#
# Every block is a dictionary:
#
#     {"row": 9, "col": 2, "length": 3, "x": ..., "y": ...}
#
# row 0 is the top and row 9 the bottom; col 0 is the left. A block of
# length 3 at col 2 covers columns 2, 3 and 4. "x" and "y" are where it is
# DRAWN, in pixels -- they glide towards where it really is, so blocks slide
# and fall smoothly instead of jumping.

blocks = []


def cell_x(col):
    return BOARD_X + col * CELL


def cell_y(row):
    return BOARD_Y + row * CELL


def new_block(row, col, length):
    return {"row": row, "col": col, "length": length,
            "x": cell_x(col), "y": cell_y(row)}


def block_at(row, col):
    """The block covering that square, or None if it is empty."""
    for block in blocks:
        if block["row"] == row:
            if block["col"] <= col < block["col"] + block["length"]:
                return block
    return None


def can_fall(block):
    """Is every square directly under this block empty?"""
    below = block["row"] + 1
    if below >= ROWS:
        return False
    for col in range(block["col"], block["col"] + block["length"]):
        if block_at(below, col) is not None:
            return False
    return True


def row_is_full(row):
    for col in range(COLS):
        if block_at(row, col) is None:
            return False
    return True


# -------------------------------------------------------- 4. a new row
#
# Walk along the row from the left. Each time: either leave a gap, or put
# down a block of random length that still fits. A full row would clear
# the moment it arrived, so if the row happens to come out full, the last
# block is taken away again.

def make_row(row):
    made = []
    col = 0
    while col < COLS:
        if chance(GAP_CHANCE):
            col = col + 1
        else:
            length = choose([1, 2, 3, 4])
            if col + length > COLS:
                length = COLS - col
            made.append(new_block(row, col, length))
            col = col + length

    filled = 0
    for block in made:
        filled = filled + block["length"]
    if filled == COLS:
        made.pop()

    return made


# ---------------------------------------------- what the game has to remember
#
# These change while you play. A function that CHANGES one has to say
# `global` first, which means "the one up here, not a new one of my own".

score = 0
best = getData(BEST_KEY, 0)
busy = False          # True while a turn is playing out: no dragging then
flashing = []         # rows that are full and about to go
held = None           # the block being dragged, or None
grab_dx = 0           # where on the block the finger is, in pixels
left_limit = 0        # how far the held block may go, in pixels
right_limit = 0
over = False


# ---------------------------------------------------------- 5. a turn
#
# After a move, the turn plays out one step at a time, with a short wait
# between steps so you can see what happens:
#
#     anything that can fall, falls one row      (again, until nothing can)
#     full rows flash, then go                   (then back to falling)
#     a new row pushes up from the bottom        (then back to falling)
#
# step() does ONE of those and then waits and calls itself again, until
# there is nothing left to do.

risen = False          # has this turn's new row come up yet?


def start_turn():
    global busy, risen
    busy = True
    risen = False
    step()


def step():
    global blocks, busy, risen, flashing, score

    # Falling, one row per step. Going through the rows from the bottom up
    # is what makes it ONE row: a block that has just moved down lands in a
    # row this loop has already been through, so it is not moved again until
    # the next step. Top down, it would be checked again in its new row, and
    # again, and drop to the floor in one go -- and a block resting on it
    # would be left behind.
    moved = False
    for row in range(ROWS - 2, -1, -1):
        for block in blocks:
            if block["row"] == row and can_fall(block):
                block["row"] = row + 1
                moved = True
    if moved:
        wait(STEP_TIME, step)
        return

    # Clearing. Full rows flash first, and go on the next step.
    if len(flashing) > 0:
        for row in flashing:
            keep = []
            for block in blocks:
                if block["row"] != row:
                    keep.append(block)
            blocks = keep
        score = score + POINTS_PER_ROW * len(flashing) * len(flashing)
        flashing = []
        wait(STEP_TIME, step)
        return

    for row in range(ROWS):
        if row_is_full(row):
            flashing.append(row)
    if len(flashing) > 0:
        play("clear")
        wait(CLEAR_TIME, step)
        return

    # Rising. Once a turn, after everything has settled.
    if not risen:
        risen = True
        for block in blocks:
            block["row"] = block["row"] - 1
        for block in make_row(ROWS - 1):
            blocks.append(block)
        for block in blocks:
            if block["row"] < 0:
                game_over()
                return
        wait(STEP_TIME, step)
        return

    busy = False


def game_over():
    global over, best

    over = True
    play("over")
    shake(8)

    # The message pauses the game, which would freeze any block halfway
    # through gliding to its square. Put every block where it really is.
    for block in blocks:
        block["x"] = cell_x(block["col"])
        block["y"] = cell_y(block["row"])
    if score > best:
        best = score
        setData(BEST_KEY, best)
        message = "New best: " + str(score) + "!"
    else:
        message = "Score: " + str(score) + "\nBest: " + str(best)

    @say("Game over!\n\n" + message, button="Play again")
    def again():
        new_game()


def new_game():
    global blocks, score, busy, flashing, held, over

    score = 0
    busy = False
    flashing = []
    held = None
    over = False
    blocks = []
    for row in range(ROWS - START_ROWS, ROWS):
        for block in make_row(row):
            blocks.append(block)


# ---------------------------------------------------------- 6. dragging
#
# A finger on a phone and the mouse on a computer are the same thing to
# kaypy: onMousePress, mousePos() and onMouseRelease answer to both.

@onMousePress
def grab():
    global held, grab_dx, left_limit, right_limit

    if busy or over:
        return

    finger = mousePos()
    col = int((finger.x - BOARD_X) // CELL)
    row = int((finger.y - BOARD_Y) // CELL)
    if col < 0 or col >= COLS or row < 0 or row >= ROWS:
        return

    block = block_at(row, col)
    if block is None:
        return

    held = block
    grab_dx = finger.x - block["x"]

    # How far it can go: walk left from the block until a square is taken
    # or the board ends, then the same to the right.
    left = block["col"]
    while left > 0 and block_at(row, left - 1) is None:
        left = left - 1
    right = block["col"]
    while (right + block["length"] < COLS
           and block_at(row, right + block["length"]) is None):
        right = right + 1

    left_limit = cell_x(left)
    right_limit = cell_x(right)


@onMouseRelease
def let_go():
    global held

    if held is None:
        return

    # Snap to the nearest column.
    col = round((held["x"] - BOARD_X) / CELL)
    moved = col != held["col"]
    held["col"] = col
    held = None

    # A tap that moved nothing is not a move, so no new row for it.
    if moved:
        play("slide")
        start_turn()


# ------------------------------------------------------------ 7. drawing
#
# Every frame: the dragged block follows the finger, every other block
# glides towards where it really is, and then everything is drawn.

@onUpdate
def glide():
    if held is not None:
        held["x"] = clamp(mousePos().x - grab_dx, left_limit, right_limit)

    # Each frame, cover a good part of the distance that is left. Near
    # enough is snapped, so it does not creep for ever.
    amount = clamp(dt() * 18, 0, 1)
    for block in blocks:
        if block is not held:
            block["x"] = lerp(block["x"], cell_x(block["col"]), amount)
        block["y"] = lerp(block["y"], cell_y(block["row"]), amount)


@onDraw
def draw_everything():
    # The board, and a faint square for every empty space.
    drawRect(pos=vec2(BOARD_X - 6, BOARD_Y - 6), width=COLS * CELL + 12,
             height=ROWS * CELL + 12, color=(50, 50, 80), radius=8)
    for row in range(ROWS):
        for col in range(COLS):
            drawRect(pos=vec2(cell_x(col) + 2, cell_y(row) + 2),
                     width=CELL - 4, height=CELL - 4, color=(40, 40, 64),
                     radius=6)

    # The top row is the danger line: anything pushed above it ends the game.
    drawRect(pos=vec2(BOARD_X, BOARD_Y - 4), width=COLS * CELL, height=3,
             color=(240, 90, 90))

    for block in blocks:
        colour = COLOURS[block["length"]]
        if block["row"] in flashing:
            colour = (255, 255, 255)
        drawRect(pos=vec2(block["x"] + 3, block["y"] + 3),
                 width=block["length"] * CELL - 6, height=CELL - 6,
                 color=colour, radius=10)

    drawText(text="Block Slide", pos=vec2(BOARD_X, 18), size=32)
    drawText(text="Score " + str(score), pos=vec2(BOARD_X, 62), size=24)
    drawText(text="Best " + str(best),
             pos=vec2(BOARD_X + 220, 62), size=24)


# ------------------------------------------------------- 8. start the game

new_game()
say("Drag a block left or right to fill a row.\n\n"
    "Every move, a new row comes up from the bottom. "
    "Don't let the blocks reach the top!", button="Play")
