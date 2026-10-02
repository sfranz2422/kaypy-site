"""Coin Rush -- grab every coin before the clock runs out.

    arrow keys   run

Bean has 30 seconds to collect every coin on the level. Get them all and the
next level starts, with more in the way: first walls, then spikes, then
ghosts, then a gazer that comes after you. Touch a spike or a ghost and you
lose 3 seconds and go back to where you started.

Every coin counts towards your score, and the score carries on from level to
level. Finish all five and they start again with less time on the clock, so
the game only ends when the clock beats you. Your best score is remembered.

HOW THIS FILE IS PUT TOGETHER

    1. the window, the pictures and the sounds
    2. the settings
    3. the levels
    4. what each letter turns into
    5. the level scene: Bean, the keys, the clock, the coins
    6. start the game

The levels are pictures made of letters. Move an 'o' and you have moved a
coin -- you never have to touch the code to change a level.
"""

from kaypy import *

# ----------------------------------------------------------------- 1. setup

TILE = 64          # one tile is 64 pixels square
ACROSS = 15        # tiles across
DOWN = 10          # tiles down
TOP = 56           # a strip at the top for the score and the clock

kaypy(width=TILE * ACROSS, height=TOP + TILE * DOWN,
      background=[118, 186, 120])

# We look down on Bean from above, so nothing falls. 0 is already the
# setting when a game starts, so this line changes nothing -- it is here to
# say what kind of game this is. A platform game sets it to about 2400.
setGravity(0)

loadSprite("bean", "images/bean.png")
loadSprite("coin", "images/coin.png")
loadSprite("steel", "images/steel.png")
loadSprite("spike", "images/spike.png")
loadSprite("ghosty", "images/ghosty.png")
loadSprite("gazer", "images/gazer.png")

loadSound("coin", "sounds/small_beep.wav")
loadSound("ouch", "sounds/thump.wav")
loadSound("done", "sounds/rising_beep.wav")


# -------------------------------------------------------------- 2. settings
#
# Every number worth changing is here.

SPEED = 300           # how fast Bean runs, in pixels per second
TIME_LIMIT = 30       # seconds on the clock for each level
FASTER_EACH_LAP = 5   # seconds fewer each time round all five levels
SHORTEST = 10         # ...but never fewer than this
PENALTY = 3           # seconds lost for touching a spike, ghost or gazer
GHOST_SPEED = 100     # how fast a ghost floats
CHASE_SPEED = 60      # how fast the gazer follows you

# The name the best score is saved under. Every game on a website shares
# the same storage, so the game's own name goes in it -- a plain "best"
# would be overwritten by the next game that saved one.
BEST_KEY = "coin_rush_best"


# ---------------------------------------------------------------- 3. levels
#
# One letter is one tile.
#
#   #  wall       o  coin       P  Bean starts here
#   ^  spike      h  ghost that floats side to side
#                 v  ghost that floats up and down
#                 G  gazer, which chases you straight through walls
#
# A space is empty floor. Every row has to be 15 letters long.

LEVEL_1 = [
    "###############",
    "#             #",
    "#  o       o  #",
    "#      o      #",
    "#             #",
    "#   o     o   #",
    "#      P      #",
    "#  o       o  #",
    "#      o      #",
    "###############",
]

LEVEL_2 = [
    "###############",
    "#o    #      o#",
    "#     #   o   #",
    "#  o  #       #",
    "#     ### ### #",
    "#  o    P    o#",
    "### ###   #   #",
    "#       o #   #",
    "#o        #  o#",
    "###############",
]

LEVEL_3 = [
    "###############",
    "#o   ^   ^   o#",
    "# ##   o   ## #",
    "#  #  ^ ^  #  #",
    "#o    #P#    o#",
    "#  ^  # #  ^  #",
    "# ### # # ### #",
    "#  o  ^ ^  o  #",
    "#o           o#",
    "###############",
]

LEVEL_4 = [
    "###############",
    "#o   h       o#",
    "#  ###   ###  #",
    "#  #o  ^  o#  #",
    "#v #   P   # v#",
    "#  #o     o#  #",
    "#  ###   ###  #",
    "#o     h     o#",
    "#      ^      #",
    "###############",
]

LEVEL_5 = [
    "###############",
    "#o   #   #   o#",
    "# ## # ^ # ## #",
    "#  o   h     o#",
    "#v ##  P  ## v#",
    "#     ^ ^     #",
    "# ##o## ##o## #",
    "#o    h      o#",
    "#  ^       ^ G#",
    "###############",
]

LEVELS = [LEVEL_1, LEVEL_2, LEVEL_3, LEVEL_4, LEVEL_5]

# What to tell the player before each level.
TIPS = [
    "Grab every coin before the clock runs out!",
    "Walls! Find a way round them.",
    "Spikes! Touch one and you lose 3 seconds.",
    "Ghosts! Watch how they float, then slip past.",
    "The gazer follows you, even through walls. Keep moving!",
]


# ----------------------------------------------- 4. what each letter becomes
#
# addLevel() reads the picture. Each time it finds a letter it looks it up
# here and builds an object from the list. The `lambda:` means "build a new
# one every time you find this letter", so every coin is its own coin.
#
# Everything that hurts Bean is tagged "danger". The ghosts and the gazer
# have a second tag too -- "across", "updown" or "chaser" -- which is what
# makes each of them move the way it does. A spike is only "danger".

TILES = {
    "#": lambda: [sprite("steel"), area(), body(isStatic=True), "wall"],
    "o": lambda: [sprite("coin"), area(), "coin"],
    "^": lambda: [sprite("spike"), area(), "danger"],
    "h": lambda: [sprite("ghosty"), scale(0.6), area(), z(10),
                  "danger", "across"],
    "v": lambda: [sprite("ghosty"), scale(0.6), area(), z(10),
                  "danger", "updown"],
    "G": lambda: [sprite("gazer"), scale(0.4), area(), z(10),
                  "danger", "chaser"],

    # Bean is a tile like everything else, so moving the 'P' moves where you
    # start. scale(0.7) because the picture is a whole tile wide, and a Bean
    # that fills a tile gets stuck in every gap.
    "P": lambda: [sprite("bean"), scale(0.7), area(), body(), z(20),
                  "player"],
}


# -------------------------------------------- what the game has to remember
#
# These change while you play. A function that CHANGES one has to say
# `global` first, which means "the one up here, not a new one of my own".

going_left = False
going_right = False
going_up = False
going_down = False

time_left = 0          # seconds left on the clock
coins = 0              # coins collected on this level
level_over = False


# ------------------------------------------------------- 5. the level scene
#
# The scene is CALLED "level". The function is NOT called play(), because
# kaypy already has a play() for sounds -- name your function play() and
# every play("coin") would start a level instead of making a noise.
#
# number is which level (0 is the first), score is the coins from earlier
# levels, and lap is how many times you have been through all five.

@scene("level")
def build_level(number, score, lap):
    global going_left, going_right, going_up, going_down
    global time_left, coins, level_over

    addLevel(LEVELS[number], {
        "tileWidth": TILE,
        "tileHeight": TILE,
        "pos": vec2(0, TOP),
        "tiles": TILES,
    })

    bean = get("player")[0]
    start = vec2(bean.pos.x, bean.pos.y)
    total = len(get("coin"))

    # A new level, so everything starts again.
    going_left = False
    going_right = False
    going_up = False
    going_down = False
    coins = 0
    level_over = False

    time_left = TIME_LIMIT - lap * FASTER_EACH_LAP
    if time_left < SHORTEST:
        time_left = SHORTEST

    # -------------------------------------------------------------- the keys
    #
    # WHY NOT JUST onKeyDown?
    #
    # onKeyDown asks "is the key down right now?" every frame. But a message
    # on the screen pauses the game, and if you let go of an arrow while it
    # is up, the let-go can be missed. Then the game thinks the arrow is
    # still held, and on the next level Bean runs off by itself.
    #
    # So the game keeps its own note: True when a key is pressed, False when
    # it is let go, and all four go back to False at the start of a level.

    @onKeyPress("left")
    def press_left():
        global going_left
        going_left = True

    @onKeyRelease("left")
    def release_left():
        global going_left
        going_left = False

    @onKeyPress("right")
    def press_right():
        global going_right
        going_right = True

    @onKeyRelease("right")
    def release_right():
        global going_right
        going_right = False

    @onKeyPress("up")
    def press_up():
        global going_up
        going_up = True

    @onKeyRelease("up")
    def release_up():
        global going_up
        going_up = False

    @onKeyPress("down")
    def press_down():
        global going_down
        going_down = True

    @onKeyRelease("down")
    def release_down():
        global going_down
        going_down = False

    # ------------------------------------------------- the words at the top

    label = add([text("", size=26), pos(16, 14), fixed(), z(100)])
    clock = add([text("", size=26), pos(width() - 130, 14), fixed(), z(100)])

    def show_score():
        label.text = ("Level " + str(number + 1)
                      + "     Coins " + str(coins) + " / " + str(total)
                      + "     Score " + str(score + coins))
        # int() drops the part after the decimal point: 7.8 becomes 7.
        clock.text = "Time " + str(int(time_left))

    # ------------------------------------------------------- every frame

    @onUpdate
    def each_frame():
        global time_left

        if level_over:
            return

        if going_left:
            bean.move(-SPEED, 0)
            bean.flipX = True
        if going_right:
            bean.move(SPEED, 0)
            bean.flipX = False
        if going_up:
            bean.move(0, -SPEED)
        if going_down:
            bean.move(0, SPEED)

        # The clock. dt() is how long this frame took, so taking it away
        # every frame counts down in real seconds.
        time_left = time_left - dt()
        if time_left <= 0:
            time_left = 0
            times_up()

        show_score()

    # ----------------------------------------------------------- the coins

    @bean.onCollide("coin")
    def got_coin(coin):
        global coins, level_over

        coin.destroy()
        coins = coins + 1
        play("coin")
        show_score()

        if coins == total:
            level_over = True
            play("done")
            new_score = score + coins

            if number + 1 < len(LEVELS):
                @say("Level " + str(number + 1) + " done!\n\n"
                     + "Score: " + str(new_score))
                def next_level():
                    go("level", number + 1, new_score, lap)
            else:
                # Back to level 1, one lap further on, less time.
                @say("You beat all five levels!\n\n"
                     + "Score: " + str(new_score) + "\n\n"
                     + "Again -- with less time!")
                def next_lap():
                    go("level", 0, new_score, lap + 1)

    # -------------------------------------------------- spikes and ghosts

    @bean.onCollide("danger")
    def ouch(thing):
        global time_left

        if level_over:
            return
        time_left = time_left - PENALTY
        bean.pos = vec2(start.x, start.y)
        shake(10)
        play("ouch")

    # wave() swings between two numbers for ever. Used as a SPEED, it makes
    # a ghost float one way, slow down, and float back again.
    @onUpdate("across")
    def float_across(ghost):
        ghost.move(wave(-GHOST_SPEED, GHOST_SPEED, time() * 1.5), 0)

    @onUpdate("updown")
    def float_updown(ghost):
        ghost.move(0, wave(-GHOST_SPEED, GHOST_SPEED, time() * 1.5))

    # moveTo() heads towards a point. The gazer has no body(), so walls do
    # not stop it.
    @onUpdate("chaser")
    def chase(gazer):
        gazer.moveTo(bean.pos, CHASE_SPEED)

    # ------------------------------------------------------------ time's up

    def times_up():
        global level_over

        level_over = True
        final = score + coins
        best = getData(BEST_KEY, 0)

        if final > best:
            setData(BEST_KEY, final)
            message = "New best score: " + str(final) + "!"
        else:
            message = "Score: " + str(final) + "\nBest: " + str(best)

        shake(8)
        play("ouch")

        @say("Time's up!\n\n" + message, button="Play again")
        def play_again():
            go("level", 0, 0, 0)

    # The message pauses the game, so the clock does not start until you
    # close it.
    show_score()
    say("Level " + str(number + 1) + "\n\n" + TIPS[number], button="Go!")


# ------------------------------------------------------- 6. start the game

go("level", 0, 0, 0)
