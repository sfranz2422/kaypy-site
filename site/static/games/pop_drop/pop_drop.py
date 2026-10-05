"""Pop Drop -- aim, fire, and pop the pieces before they reach the bottom.

    left / right arrows   turn the launcher
    space                 fire

The pieces hang from the ceiling in a honeycomb. Fire one up at them: it
bounces off the side walls and sticks where it lands. Three or more of the
same kind touching each other pop -- and anything left hanging with nothing
holding it to the ceiling falls off too.

Every shot that pops nothing fills the danger meter. When it is full, the
ceiling comes down a row. If a piece goes past the red line, the game is
over. Clear every piece to move up a level. Steel never pops: the only way
to get rid of it is to cut away whatever it hangs from.

On a phone, the d-pad turns the launcher and the button fires.

HOW THIS FILE IS PUT TOGETHER

    1. the window and the pictures
    2. the settings
    3. the board: a list of rows, and where each spot is on the screen
    4. neighbours, groups, and what is still hanging on
    5. what the game has to remember
    6. levels
    7. aiming and firing
    8. the flying piece, and where it sticks
    9. drawing
   10. start the game

Like Block Slide, the board is not made of game objects. It is a list of
lists of names -- "apple", "steel", or None for an empty spot -- and it is
drawn from that list every frame.
"""

from kaypy import *

# --------------------------------------------------------------- 1. setup

COLS = 8           # spots across the even rows (the odd rows have one less)
CELL = 48          # a piece is 48 pixels across
ROW_H = 42         # rows overlap, like a honeycomb, so they are closer than 48
DANGER_ROWS = 11   # a piece in the 12th row down is past the red line

BOARD_X = 28                 # the left wall
BOARD_Y = 100                # the top of the ceiling
BOARD_W = COLS * CELL
LAUNCH = vec2(BOARD_X + BOARD_W / 2, 630)

# The window is taller than the game. The bottom part is for the d-pad and
# the fire button: joystick=["space"] puts them there, and they press the
# arrow keys and space for you.
kaypy(width=BOARD_W + 2 * BOARD_X, height=940, background=[24, 22, 40],
      joystick=["space"])

loadSprite("apple", "images/apple.png")
loadSprite("bean", "images/bean.png")
loadSprite("coin", "images/coin.png")
loadSprite("egg", "images/egg.png")
loadSprite("ghosty", "images/ghosty.png")
loadSprite("lemon", "images/lemon.png")
loadSprite("mushroom", "images/mushroom.png")
loadSprite("steel", "images/steel.png")

loadSound("fire", "sounds/swoosh.wav")
loadSound("stick", "sounds/thump.wav")
loadSound("pop", "sounds/small_beep.wav")
loadSound("drop", "sounds/small_boom.wav")
loadSound("level", "sounds/rising_beep.wav")
loadSound("over", "sounds/lazer_punch.wav")


# ---------------------------------------------------------- 2. settings

SHOT_SPEED = 900      # pixels per second
TURN_SPEED = 100      # how fast the launcher turns, degrees per second
POINTS_POP = 10       # for each piece that pops
POINTS_DROP = 20      # for each piece that falls off
POINTS_LEVEL = 100    # for clearing a level, times the level number

# Each kind of piece: the colour of the circle behind it, and the size the
# picture is drawn at. The pictures are not all the same shape, so each one
# gets its own width and height -- otherwise the ghost would be squashed.
PIECES = {
    "apple": {"colour": (150, 45, 60), "w": 31, "h": 36},
    "bean": {"colour": (35, 120, 85), "w": 38, "h": 32},
    "coin": {"colour": (190, 110, 30), "w": 26, "h": 32},
    "egg": {"colour": (130, 100, 70), "w": 29, "h": 36},
    "ghosty": {"colour": (50, 80, 170), "w": 29, "h": 36},
    "lemon": {"colour": (130, 140, 30), "w": 26, "h": 36},
    "mushroom": {"colour": (120, 60, 140), "w": 38, "h": 32},
}

# The order new kinds are added in, one more each level.
KINDS = ["apple", "bean", "coin", "egg", "ghosty", "lemon", "mushroom"]

BEST_KEY = "pop_drop_best"


# ----------------------------------------------------------- 3. the board
#
# grid[row][col] is the name of the piece in that spot, or None.
#
# Row 0 is the top. The odd rows are pushed half a piece to the right, so
# they fit into the gaps of the rows above and below -- that is what makes
# it a honeycomb. It also means an odd row has room for one piece fewer.
#
#     row 0:   A B C D E F G H
#     row 1:    a b c d e f g
#     row 2:   A B C D E F G H
#
# There is one more row than can be played in, so a piece that sticks just
# past the red line has somewhere to go -- and then ends the game.

ROWS = DANGER_ROWS + 1
grid = []


def row_length(row):
    if row % 2 == 0:
        return COLS
    return COLS - 1


def in_grid(row, col):
    return 0 <= row < ROWS and 0 <= col < row_length(row)


def empty_grid():
    rows = []
    for row in range(ROWS):
        rows.append([None] * COLS)
    return rows


# The ceiling comes down a row at a time. Everything hangs from it, so the
# whole board is drawn lower by the same amount.

drops = 0            # how many rows the ceiling has come down


def ceiling_y():
    return BOARD_Y + drops * ROW_H


def spot_x(row, col):
    """The middle of a spot, across."""
    x = BOARD_X + CELL / 2 + col * CELL
    if row % 2 == 1:
        x = x + CELL / 2
    return x


def spot_y(row):
    """The middle of a spot, down."""
    return ceiling_y() + CELL / 2 + row * ROW_H


# ------------------------------------- 4. neighbours, groups, hanging on
#
# Every spot touches six others: one each side, two above and two below.
# WHICH two above depends on whether the row is pushed over. Look at "c" in
# the picture above: it sits between "C" and "D". But "C" sits between "b"
# and "c". Hence the shift.

def neighbours(row, col):
    if row % 2 == 0:
        shift = -1
    else:
        shift = 0
    around = [
        (row, col - 1), (row, col + 1),
        (row - 1, col + shift), (row - 1, col + shift + 1),
        (row + 1, col + shift), (row + 1, col + shift + 1),
    ]
    inside = []
    for spot in around:
        if in_grid(spot[0], spot[1]):
            inside.append(spot)
    return inside


def group_of(row, col):
    """Every spot joined to this one by pieces of the same kind.

    A flood fill: start with one spot, keep a list of spots still to look
    around, and add every matching neighbour not already found. When the
    list is empty, the whole group has been found.
    """
    kind = grid[row][col]
    found = [(row, col)]
    to_look = [(row, col)]
    while len(to_look) > 0:
        spot = to_look.pop()
        for near in neighbours(spot[0], spot[1]):
            if grid[near[0]][near[1]] == kind and near not in found:
                found.append(near)
                to_look.append(near)
    return found


def hanging_on():
    """Every spot joined to the ceiling, through pieces of any kind.

    The same flood fill, but it starts from every piece in the top row at
    once, and any piece will do.
    """
    found = []
    for col in range(row_length(0)):
        if grid[0][col] is not None:
            found.append((0, col))
    to_look = list(found)
    while len(to_look) > 0:
        spot = to_look.pop()
        for near in neighbours(spot[0], spot[1]):
            if grid[near[0]][near[1]] is not None and near not in found:
                found.append(near)
                to_look.append(near)
    return found


def kinds_left():
    """The kinds still on the board, not counting steel."""
    left = []
    for row in range(ROWS):
        for col in range(row_length(row)):
            kind = grid[row][col]
            if kind is not None and kind != "steel" and kind not in left:
                left.append(kind)
    return left


# ------------------------------------------- 5. what the game remembers

level = 1
score = 0
best = getData(BEST_KEY, 0)
misses = 0           # shots in a row that popped nothing
aim = -90            # degrees: -90 is straight up, -180 would be left
loaded = "apple"     # the piece in the launcher
next_up = "bean"     # the one after it
shot = None          # the piece in the air: a dictionary, or None
busy = False         # True between levels: no firing then
over = False

# Pieces that have just popped or fallen. They are not on the board any
# more; they are only drawn, until they are gone.
popping = []
falling = []


def misses_allowed():
    """How many misses fill the danger meter. Fewer as the levels go up."""
    return max(4, 8 - level)


# ---------------------------------------------------------- 6. levels
#
# Level 1 has four kinds of piece and four rows. Each level adds one of
# each, up to all seven kinds and seven rows, and from level 2 on, some of
# the pieces are steel.

def start_level():
    global grid, drops, misses, shot, busy, popping, falling

    grid = empty_grid()
    drops = 0
    misses = 0
    shot = None
    busy = False
    popping = []
    falling = []

    kinds = KINDS[:min(3 + level, len(KINDS))]
    rows = min(3 + level, 7)
    for row in range(rows):
        for col in range(row_length(row)):
            grid[row][col] = choose(kinds)

    # Steel goes anywhere below the top row. It may land on steel already
    # put there, so there can be fewer than this -- that is fine.
    for i in range(min(level - 1, 6)):
        row = choose(range(1, rows))
        col = choose(range(row_length(row)))
        grid[row][col] = "steel"

    load_new()
    load_new()


def load_new():
    """Move the next piece into the launcher, and choose a new next one.

    Only kinds still on the board are chosen, so you are never handed a
    piece that cannot match anything.
    """
    global loaded, next_up

    left = kinds_left()
    loaded = next_up
    if loaded not in left and len(left) > 0:
        loaded = choose(left)
    if len(left) > 0:
        next_up = choose(left)


def level_cleared():
    global level, score, busy

    busy = True
    score = score + POINTS_LEVEL * level
    play("level")

    # Any steel still hanging falls away as a bonus.
    for row in range(ROWS):
        for col in range(row_length(row)):
            if grid[row][col] is not None:
                knock_off(row, col)

    level = level + 1

    def show_message():
        @say("Level " + str(level - 1) + " cleared!\n\n"
             "Next: level " + str(level) + ".", button="Go")
        def go_on():
            start_level()

    wait(1.0, show_message)


def game_over():
    global over, best

    over = True
    play("over")
    shake(10)
    if score > best:
        best = score
        setData(BEST_KEY, best)
        message = "New best: " + str(score) + "!"
    else:
        message = "Score: " + str(score) + "\nBest: " + str(best)

    @say("The pieces reached the line!\n\n" + message, button="Play again")
    def again():
        new_game()


def new_game():
    global level, score, over, aim

    level = 1
    score = 0
    over = False
    aim = -90
    start_level()


# ------------------------------------------------- 7. aiming and firing

@onUpdate
def turn():
    global aim

    if isKeyDown("left"):
        aim = aim - TURN_SPEED * dt()
    if isKeyDown("right"):
        aim = aim + TURN_SPEED * dt()
    # Not too flat, or a shot would bounce from wall to wall for ages.
    aim = clamp(aim, -165, -15)


# Only space fires, not up as well. On a phone the d-pad holds two arrows
# at once when a thumb is between them, so a thumb turning left that slid a
# little upwards would fire by accident.
@onKeyPress("space")
def fire():
    global shot

    if shot is not None or busy or over:
        return
    # Vec2.fromAngle turns an angle into a direction: an arrow one pixel
    # long, pointing that way.
    direction = Vec2.fromAngle(aim)
    shot = {"kind": loaded, "pos": LAUNCH, "vel": direction * SHOT_SPEED}
    play("fire")


# ------------------------------- 8. the flying piece, and where it sticks

@onUpdate
def fly():
    if shot is None:
        return

    # A slow frame must not let the piece jump straight through another.
    step = min(dt(), 1 / 30)
    shot["pos"] = shot["pos"] + shot["vel"] * step

    # Bounce off the side walls: put it back inside, and send it the other
    # way across. Its speed up the screen does not change.
    x = shot["pos"].x
    left = BOARD_X + CELL / 2
    right = BOARD_X + BOARD_W - CELL / 2
    if x < left:
        shot["pos"] = vec2(left, shot["pos"].y)
        shot["vel"] = vec2(-shot["vel"].x, shot["vel"].y)
    if x > right:
        shot["pos"] = vec2(right, shot["pos"].y)
        shot["vel"] = vec2(-shot["vel"].x, shot["vel"].y)

    # Stick to the ceiling, or to any piece it comes close enough to touch.
    # "Close enough" is a little less than a whole piece, so a shot can slip
    # through a gap that looks big enough.
    if shot["pos"].y - CELL / 2 <= ceiling_y():
        stick()
        return
    for row in range(ROWS):
        for col in range(row_length(row)):
            if grid[row][col] is not None:
                middle = vec2(spot_x(row, col), spot_y(row))
                if shot["pos"].dist(middle) < CELL * 0.85:
                    stick()
                    return


def stick():
    """Put the flying piece in the nearest empty spot it could hang from."""
    global shot

    best_spot = None
    best_dist = 0
    for row in range(ROWS):
        for col in range(row_length(row)):
            if grid[row][col] is None and can_hang(row, col):
                middle = vec2(spot_x(row, col), spot_y(row))
                distance = shot["pos"].dist(middle)
                if best_spot is None or distance < best_dist:
                    best_spot = (row, col)
                    best_dist = distance

    grid[best_spot[0]][best_spot[1]] = shot["kind"]
    shot = None
    settle(best_spot[0], best_spot[1])


def can_hang(row, col):
    """A spot can be filled if it touches the ceiling or another piece."""
    if row == 0:
        return True
    for near in neighbours(row, col):
        if grid[near[0]][near[1]] is not None:
            return True
    return False


def settle(row, col):
    """After a piece sticks: pop, drop, fill the danger meter, check."""
    global score, misses, drops

    group = group_of(row, col)
    if len(group) >= 3 and grid[row][col] != "steel":
        for spot in group:
            popping.append({"kind": grid[spot[0]][spot[1]],
                            "x": spot_x(spot[0], spot[1]),
                            "y": spot_y(spot[0]), "time": 0})
            grid[spot[0]][spot[1]] = None
        score = score + POINTS_POP * len(group)
        play("pop")

        # Now anything not joined to the ceiling falls.
        held = hanging_on()
        dropped = 0
        for r in range(ROWS):
            for c in range(row_length(r)):
                if grid[r][c] is not None and (r, c) not in held:
                    knock_off(r, c)
                    dropped = dropped + 1
        if dropped > 0:
            score = score + POINTS_DROP * dropped
            play("drop")
        misses = max(0, misses - 1)
    else:
        play("stick")
        misses = misses + 1
        if misses >= misses_allowed():
            misses = 0
            drops = drops + 1
            shake(4)

    if len(kinds_left()) == 0:
        level_cleared()
        return

    # Past the red line? Look at the rows below it.
    for r in range(DANGER_ROWS - drops, ROWS):
        for c in range(row_length(r)):
            if grid[r][c] is not None:
                game_over()
                return

    load_new()


def knock_off(row, col):
    """Take a piece off the board and let it fall."""
    falling.append({"kind": grid[row][col], "x": spot_x(row, col),
                    "y": spot_y(row), "speed": -100})
    grid[row][col] = None


@onUpdate
def move_leftovers():
    global popping, falling

    keep = []
    for piece in popping:
        piece["time"] = piece["time"] + dt()
        if piece["time"] < 0.25:
            keep.append(piece)
    popping = keep

    keep = []
    for piece in falling:
        piece["speed"] = piece["speed"] + 1800 * dt()
        piece["y"] = piece["y"] + piece["speed"] * dt()
        if piece["y"] < height() + CELL:
            keep.append(piece)
    falling = keep


# ------------------------------------------------------------ 9. drawing

def draw_piece(kind, x, y, size=1.0, opacity=1.0):
    if kind == "steel":
        drawSprite(sprite="steel", pos=vec2(x, y), width=(CELL - 4) * size,
                   height=(CELL - 4) * size, anchor="center",
                   opacity=opacity)
        return
    piece = PIECES[kind]
    drawCircle(pos=vec2(x, y), radius=(CELL / 2 - 2) * size,
               color=piece["colour"], opacity=opacity)
    drawSprite(sprite=kind, pos=vec2(x, y), width=piece["w"] * size,
               height=piece["h"] * size, anchor="center", opacity=opacity)


@onDraw
def draw_everything():
    # The well the pieces hang in, and the ceiling that comes down.
    line_y = BOARD_Y + DANGER_ROWS * ROW_H + (CELL - ROW_H)
    drawRect(pos=vec2(BOARD_X, BOARD_Y), width=BOARD_W,
             height=LAUNCH.y + CELL - BOARD_Y, color=(34, 32, 56))
    drawRect(pos=vec2(BOARD_X, BOARD_Y - 8), width=BOARD_W,
             height=ceiling_y() - BOARD_Y + 8, color=(110, 110, 130))
    drawRect(pos=vec2(BOARD_X, line_y), width=BOARD_W, height=3,
             color=(240, 90, 90))

    for row in range(ROWS):
        for col in range(row_length(row)):
            if grid[row][col] is not None:
                draw_piece(grid[row][col], spot_x(row, col), spot_y(row))

    for piece in popping:
        grow = 1 + piece["time"] * 2
        draw_piece(piece["kind"], piece["x"], piece["y"], grow,
                   1 - piece["time"] * 4)
    for piece in falling:
        draw_piece(piece["kind"], piece["x"], piece["y"])

    # The launcher: a line pointing where the shot will go.
    if not busy:
        tip = LAUNCH + Vec2.fromAngle(aim) * 60
        drawLine(p1=LAUNCH, p2=tip, width=6, color=(230, 230, 240))
        if shot is None:
            draw_piece(loaded, LAUNCH.x, LAUNCH.y)
    if shot is not None:
        draw_piece(shot["kind"], shot["pos"].x, shot["pos"].y)

    drawText(text="Next", pos=vec2(BOARD_X + 10, LAUNCH.y - 50), size=18)
    if not busy:
        draw_piece(next_up, BOARD_X + 30, LAUNCH.y, 0.8)

    # The words along the top, and the danger meter: one box per miss.
    drawText(text="Pop Drop", pos=vec2(BOARD_X, 14), size=30)
    drawText(text="Level " + str(level), pos=vec2(BOARD_X + 260, 20),
             size=22)
    drawText(text="Score " + str(score), pos=vec2(BOARD_X, 58), size=20)
    drawText(text="Best " + str(best), pos=vec2(BOARD_X + 150, 58), size=20)

    allowed = misses_allowed()
    for i in range(allowed):
        if i < misses:
            colour = (240, 90, 90)
        else:
            colour = (70, 66, 100)
        drawRect(pos=vec2(BOARD_X + BOARD_W - allowed * 16 + i * 16, 62),
                 width=12, height=16, color=colour, radius=3)


# ------------------------------------------------------- 10. start the game

new_game()
say("Turn the launcher with the left and right arrows. "
    "Fire with space.\n\n"
    "Three of a kind touching pop. Don't let the pieces reach the red line!",
    button="Play")
