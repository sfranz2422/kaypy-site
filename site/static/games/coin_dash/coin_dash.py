"""Coin Dash -- grab the coin, dodge the red blocks, don't fall in the hole.

    left / right   run
    up or space    jump

One coin at a time. Grab it and it pops up somewhere else, worth 5 points.
Red blocks drop in through the gap in the ceiling and run about, and the
higher your score, the faster they come. Touch one, or fall through the gap
in the floor, and it is game over. Your best score is remembered.

HOW THIS FILE IS PUT TOGETHER

    1. the window, the pictures and the sounds
    2. the settings
    3. the level
    4. the menu scene
    5. the game scene: Bean, the coin, the red blocks, dying
    6. start the game

The level is a picture made of letters. Change a '#' and you have moved a
wall -- you never have to touch the code to change the level.
"""

from kaypy import *

# ----------------------------------------------------------------- 1. setup

TILE = 40          # one tile is 40 pixels square
ACROSS = 25        # tiles across
DOWN = 17          # tiles down

kaypy(width=TILE * ACROSS, height=TILE * DOWN, background=[52, 152, 219])

# A platform game, so things fall. Without this line nothing would.
setGravity(1000)

# Every picture and sound here comes with the playground, so you can paste
# this whole file in and press Run. The red blocks are not pictures at all
# -- they are plain rectangles, made with rect().
loadSprite("bean", "images/bean.png")
loadSprite("coin", "images/coin.png")

# The name before the comma is the name the game uses. The file after it is
# the one that gets played -- swap it for any sound in the playground.
loadSound("jump", "sounds/swoosh.wav")
loadSound("coin", "sounds/small_beep.wav")
loadSound("dead", "sounds/small_boom.wav")


# -------------------------------------------------------------- 2. settings
#
# Every number worth changing is here.

BEAN_SIZE = 0.6       # Bean's picture is bigger than a tile, so shrink it
COIN_SIZE = 0.7       # ...and the coin a little less
RUN_SPEED = 400       # how fast you run, in pixels per second
JUMP = 640            # how hard you jump
ENEMY_SPEED = 200     # how fast a red block runs once it gets going
POINTS = 5            # points for each coin

# A new red block every 5 seconds to begin with. The more points you have,
# the shorter the wait, until at 50 points there is one every half second.
SLOWEST = 5
FASTEST = 0.5
HARDEST_AT = 50

# Where the coin can be. Each time you grab it, it moves to one of these --
# never the one it was just at.
COIN_SPOTS = [
    vec2(120, 300),
    vec2(840, 300),
    vec2(800, 160),
    vec2(200, 160),
    vec2(140, 600),
    vec2(900, 600),
    vec2(230, 490),
    vec2(760, 490),
]

# The name the best score is saved under. Every game on a website shares
# the same storage, so the game's own name goes in it -- a plain "best"
# would be overwritten by the next game that saved one.
BEST_KEY = "coin_dash_best"


# ----------------------------------------------------------------- 3. level
#
# One letter is one tile.
#
#   #  wall
#   =  the red gaps, top and bottom. Red blocks drop in through the top
#      one, and you can fall out through the bottom one.
#
# A space is empty. Every row has to be 25 letters long.

LEVEL = [
    "##########=====##########",
    "#                       #",
    "#                       #",
    "#         #   #         #",
    "#                       #",
    "#  ######       ######  #",
    "#                       #",
    "#                       #",
    "#                       #",
    "#####   #########   #####",
    "#       #       #       #",
    "#       #       #       #",
    "#      ##       ##      #",
    "#    ###         ###    #",
    "#                       #",
    "#                       #",
    "##########=====##########",
]

# What each letter turns into. A wall has body(isStatic=True), so things
# stand on it and bump into it. A gap has no area(), so nothing touches it
# -- it is only there to be looked at.
TILES = {
    "#": lambda: [rect(TILE, TILE), color(52, 73, 94), area(),
                  body(isStatic=True), "wall"],
    "=": lambda: [rect(TILE, TILE), color(231, 76, 60)],
}


# ------------------------------------------------------------ 4. the menu
#
# last_score is what you got last time. The very first time, there is no
# last time, so it starts at 0.

@scene("menu")
def menu(last_score):
    best = getData(BEST_KEY, 0)
    if last_score > best:
        best = last_score
        setData(BEST_KEY, best)

    # The title starts above the top of the window and drops in, bouncing.
    # tween() changes a number smoothly from -100 to 160 over one second,
    # and calls drop_title with each new number along the way.
    title = add([text("Coin Dash", size=120), pos(width() / 2, -100),
                 anchor("center")])

    def drop_title(y):
        title.pos.y = y

    tween(-100, 160, 1, drop_title, easings.easeOutBounce)

    start = add([text("Press Up to Start", size=60), pos(center()),
                 anchor("center"), rotate(0)])

    add([text("Score: " + str(last_score) + "\nBest Score: " + str(best),
              size=44),
         pos(width() / 2, 520), anchor("center")])

    # wave() swings between two numbers for ever, so the words rock from
    # side to side.
    @onUpdate
    def rock():
        start.angle = wave(-2, 2, time() * 3)

    @onKeyPress("up")
    def start_game():
        go("game")

    @onKeyPress("space")
    def start_game_too():
        go("game")

    @onClick
    def clicked():
        go("game")


# ------------------------------------------------------- 5. the game scene
#
# The scene is CALLED "game". The function is NOT called play(), because
# kaypy already has a play() for sounds -- name your function play() and
# every play("coin") would start a game instead of making a noise.
#
# These change while you play. A function that CHANGES one has to say
# `global` first, which means "the one up here, not a new one of my own".

score = 0
next_enemy = 0      # seconds until the next red block drops in
dead = False


@scene("game")
def game():
    global score, next_enemy, dead

    score = 0
    next_enemy = 0
    dead = False

    addLevel(LEVEL, {
        "tileWidth": TILE,
        "tileHeight": TILE,
        "tiles": TILES,
    })

    bean = add([sprite("bean"), scale(BEAN_SIZE), pos(500, 340),
                anchor("center"), area(), body(), z(10), "player"])

    coin = add([sprite("coin"), scale(COIN_SIZE), pos(COIN_SPOTS[0]),
                anchor("center"), area(), opacity(1), "coin"])

    label = add([text("Score: 0", size=36), pos(60, 50), z(100)])

    # ------------------------------------------------------- every frame

    @onUpdate
    def each_frame():
        global next_enemy

        if dead:
            return

        # Running. flipX turns the picture round, so Bean faces the way
        # it is going.
        if isKeyDown("left"):
            bean.move(-RUN_SPEED, 0)
            bean.flipX = True
        if isKeyDown("right"):
            bean.move(RUN_SPEED, 0)
            bean.flipX = False

        # Jumping. Only from the ground, or you could fly by tapping.
        if isKeyDown("up") or isKeyDown("space"):
            if bean.isGrounded():
                bean.jump(JUMP)
                play("jump")

        # Out through the gap in the floor, or the one in the ceiling.
        if bean.pos.y > height() or bean.pos.y < 0:
            die()

        # Time for another red block? dt() is how long this frame took, so
        # taking it away every frame counts down in real seconds.
        next_enemy = next_enemy - dt()
        if next_enemy <= 0:
            add_enemy()
            next_enemy = enemy_wait()

    # -------------------------------------------------------------- coins

    @bean.onCollide("coin")
    def got_coin(c):
        global score

        if dead:
            return

        score = score + POINTS
        label.text = "Score: " + str(score)
        play("coin")
        move_coin()

    def move_coin():
        # Every spot except the one the coin is at now.
        spots = []
        for spot in COIN_SPOTS:
            if spot.x != coin.pos.x or spot.y != coin.pos.y:
                spots.append(spot)

        coin.pos = choose(spots)

        # Fade in at the new spot, so you can see where it went.
        tween(0, 1, 0.3, fade_coin)

    def fade_coin(amount):
        coin.opacity = amount

    # -------------------------------------------------------- red blocks

    # The longer you survive, the less time between red blocks.
    def enemy_wait():
        progress = score / HARDEST_AT
        if progress > 1:
            progress = 1
        return SLOWEST - (SLOWEST - FASTEST) * progress

    def add_enemy():
        # In through the gap in the ceiling. lifespan(15) clears it away
        # after 15 seconds, so they never pile up.
        enemy = add([rect(40, 40), color(231, 76, 60), pos(500, -20),
                     anchor("center"), area(), body(), lifespan(15),
                     "enemy",
                     {"speed": choose([-200, 200, 60, -60]), "last_x": 0}])

        # After two seconds it stops dawdling and picks a direction.
        @wait(2)
        def get_going():
            enemy.speed = choose([-ENEMY_SPEED, ENEMY_SPEED])

    @onUpdate("enemy")
    def run_about(enemy):
        # If it got nowhere since last frame, a wall is in the way -- so
        # turn round. abs() is the size of a number without its sign, so
        # this asks "did it move less than a tenth of a pixel either way?"
        # (last_x starts at 0, far from where a block starts, so a brand
        # new block does not turn round before it has had a chance to move.)
        if abs(enemy.pos.x - enemy.last_x) < 0.1:
            enemy.speed = -enemy.speed
        enemy.last_x = enemy.pos.x
        enemy.move(enemy.speed, 0)

    @bean.onCollide("enemy")
    def hit(enemy):
        die()

    # ------------------------------------------------------------ dying

    def die():
        global dead

        # Touching two red blocks at once would otherwise die twice.
        if dead:
            return
        dead = True

        play("dead")
        shake(12)

        # A red flash over the whole window, gone in a third of a second.
        add([rect(width(), height()), color(255, 50, 35), opacity(0.6),
             lifespan(0.3, fade=0.3), z(200)])

        # Bean bursts into little white squares, each flying off in
        # its own direction and fading away.
        for i in range(40):
            direction = vec2(rand(-1, 1), rand(-1, 1))
            add([rect(8, 8), pos(bean.pos), color(255, 255, 255),
                 opacity(1), move(direction, rand(50, 300)),
                 lifespan(1, fade=0.5),
                 z(150)])

        bean.destroy()

        @wait(1)
        def back_to_menu():
            go("menu", score)


# ------------------------------------------------------- 6. start the game

go("menu", 0)
