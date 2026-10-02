"""Dark Blue -- jump, collect the coins, and avoid the red stuff.

    left / right   run
    up             jump (hold it to jump higher)
    escape         back to the menu

Collect every coin on a level to go on to the next. Touch anything red --
lava or a moving red block -- or fall off the bottom, and the level starts
again. There are five levels. The game counts how many times you died, and
remembers your fewest.

Based on "Dark Blue" by Thomas Palef (lessmilk.com).

HOW THIS FILE IS PUT TOGETHER

    1. the window, the pictures and the sounds
    2. the settings
    3. the levels
    4. what each letter turns into
    5. the menu
    6. the level scene: Bean, the camera, the coins, the red stuff
    7. the end
    8. start the game

The levels are pictures made of letters. Move a '$' and you have moved a
coin -- you never have to touch the code to change a level.
"""

from kaypy import *

# ----------------------------------------------------------------- 1. setup

TILE = 30          # one tile is 30 pixels square

# 30 tiles across and 20 down fit in the window. A level is wider than that,
# so the camera follows Bean from side to side.
kaypy(width=TILE * 30, height=TILE * 20, background=[67, 117, 210])
setGravity(1350)

loadSprite("bean", "images/bean.png")
loadSprite("coin", "images/coin.png")
loadSprite("steel", "images/steel.png")

loadSound("coin", "sounds/small_beep.wav")
loadSound("ouch", "sounds/thump.wav")
loadSound("done", "sounds/rising_beep.wav")


# -------------------------------------------------------------- 2. settings
#
# Every number worth changing is here.

RUN_SPEED = 375       # how fast Bean runs on the ground, pixels per second
AIR_SPEED = 300       # ...and in the air, a little slower
JUMP = 712            # how hard Bean jumps
JUMP_HOLD = 0.2       # how long holding up keeps pushing Bean higher
ENEMY_SPEED = 150     # how fast the red blocks move

# The name the fewest deaths is saved under. Every game on a website shares
# the same storage, so the game's own name goes in it.
BEST_KEY = "dark_blue_fewest_deaths"


# ---------------------------------------------------------------- 3. levels
#
# One letter is one tile.
#
#   #  ground           $  coin           @  Bean starts here
#   =  lava             >  red block that moves side to side
#                       v  red block that moves up and down
#
# A space is empty.

LEVEL_1 = [
    "                                                                                                #",
    "                                                                                                #",
    "####                                                                                            #",
    "   #                                                                                            #",
    "   #                                                                                            #",
    "   #                                                                                            #",
    "   #            $                                                                               #",
    "   #                                                                                            #",
    "   #           ####                                                                             #",
    "   #           #  #            $        $$                                                      #",
    "   #           #  #                                                                             #",
    "   #           #  #          ####     #####     ####                                            #",
    "   ####  $$    #  #          #  #               #  #                                         ####",
    "      #        #  #   $$     #  #               #  #                                         #   ",
    "      #    @   #  #          #  #               #  #   $                                     #   ",
    "      ##########  ############  #################  ##########           ######################   ",
    "                                                            #===========#                        ",
    "                                                            #############                        ",
]

LEVEL_2 = [
    "   #                           #      #                                                             ",
    "   #                           #      #                                                             ",
    "   #                           #      #                                                             ",
    "   #                           #      #                                                         ####",
    "   #        #  >  #            #      #                                                         #   ",
    "   #                           #      #                                                         #   ",
    "   #                           #======#                                                         #   ",
    "   #                           #======#              ####                                       #   ",
    "   #                           #======#              #  #       $                               #   ",
    "   #                           ########            ###  #                                       #   ",
    "   #        @                                      #    #      ###                              #   ",
    "   #                                             ###    #                                    $  #   ",
    "   #                            v    v           #      #                                       #   ",
    "   #         $ $ $                             ###      #                    #  $   $  #        #   ",
    "   #                                           #        #                    #  >      #        #   ",
    "   #############################################        #               #########################   ",
    "                                                        #===============#                           ",
    "                                                        #################                           ",
    "                                                                                                    ",
    "                                                                                                    ",
]

LEVEL_3 = [
    "                                                  #                 #                 #         #   ",
    "                                                  #                 #                 #         #   ",
    "                                                  #                 #                 #         #   ",
    "   ######                                         #                                   #    #    #   ",
    "   #    #                                         #                                   #    #    #   ",
    "   # ## #                              $ $ $      #                                   #    # $$ #   ",
    "   # #  #                                         #                                   ##   #    #   ",
    "   # ####                     ####    #######     #                                   #    #    #   ",
    "   #                          #  #          #     #                                   #    #    #   ",
    "   #                          #  #          #   > #                                   #   ## $$ #   ",
    "   #        @           ####  #  #          #   > #      $          v          $      #    #    #   ",
    "   #                    #  #  #  #          #     #                                   #    #    #   ",
    "   #                    #  #  #  #          #     #      $                     $      ##   #    #   ",
    "   #              ####  #  #  #  #          #                                              #====#   ",
    "   #              #  #  #  #  #  #          #           ###         #         ###          #====#   ",
    "   #              #  #==#  #==#  #=======   #           # #===================# #          #====#   ",
    "   ################  ####  ####  #######=   ############# ##################### #################   ",
    "                                        =                                                           ",
    "                                        =                                                           ",
    "                                        =                                                           ",
]

LEVEL_4 = [
    "                                        #                         #                         #       ",
    "#########                               ###########################                         ####### ",
    "        #                                  =         =                                            # ",
    "        #                                                                                         # ",
    "        #                                                                                         # ",
    "   ######                                       =         =                                       # ",
    "   #                                    ###########################                         ###   # ",
    "   #                         #####      #                         #>                        # #   # ",
    "   #                         #   #      ########################  #        >                # #   # ",
    "   #                         #   #                   v         #  #                >        # # $ # ",
    "   #  @                      #   #                     $ $ $   #  #                        ># #   # ",
    "   # $ $                   ###   ###             v             #  ########################### ##### ",
    "   #                         #   #                     $ $ $   #                                    ",
    "   ######       #####        #   #           v                 #                                    ",
    "        #=======#   #        #   #                     $ $ $   #                                    ",
    "        #=======#   #        #   #       v                     #                                    ",
    "        #########   ##########   ###############################                                    ",
    "                                                                                                    ",
    "                                                                                                    ",
    "                                                                                                    ",
]

LEVEL_5 = [
    "  # = #                   #                     #               #                                #  ",
    "  # = #                   #                     #               #                                #  ",
    "  # = #                   #######################               #                               >#  ",
    "  # = #                                                  $ $ $  #                 >              #  ",
    "  # = #                                                         #>                               #  ",
    "  # = #     @                                          ##########                                #  ",
    "  # = #                 ##     #     #     #     ##                                              #  ",
    "  # = #                  #=======================#                 #        #        #        #  #  ",
    "  # = #                  #=======================#                 #========#========#========#  #  ",
    "  # = #########################################################################################  #  ",
    "  # =                                                                                            #  ",
    "  # =     $                                                      $ $ $ $ $         ###   ###     #  ",
    "  # =               v                                          v           v       # #   # #     #  ",
    "  # =     $                 v                        ###         $ $ $ $ $                       #  ",
    "  # =                                                # #    #        >        #                  #  ",
    "  #===    $    ###  v  ###  v  ###  v  ###     ###   # #    ###################    vvv   vvv     #  ",
    "  #=====                                             # #                                         #  ",
    "  #=================#=======#=======#================# #                                         #  ",
    "  ##################################################=# ###########################################  ",
    "                                                    =                                               ",
]
LEVELS = [LEVEL_1, LEVEL_2, LEVEL_3, LEVEL_4, LEVEL_5]
LEVEL_NAMES = ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5"]

# The words written into each level, as [column, row, words]. Columns and
# rows are counted in tiles, from 0, the same as the letters above.
SIGNS = [
    [[12, 3, "use the arrow keys to move"],
     [40, 17, "coins are awesome, take them"],
     [66, 3, "red things = bad things"],
     [87, 17, "collect all coins to finish the level"]],
    [[15, 1, "right, left, right... this looks boring"],
     [59, 1, "use the up arrow key to jump"],
     [59, 3, "but you probably already know that"]],
    [],
    [[79, 14, "there are so many red things"],
     [79, 16, "stop reading this!"]],
    [[15, 1, "this is the last level"],
     [15, 3, "you can't beat it"]],
]


# ----------------------------------------------- 4. what each letter becomes
#
# addLevel() reads the picture. Each time it finds a letter it looks it up
# here and builds an object from the list. The `lambda:` means "build a new
# one every time you find this letter", so every coin is its own coin.
#
# The red blocks have no body(), so gravity leaves them alone and they
# float. Each one carries its own direction: "across" is 1 for side to side
# and 0 for up and down, and "way" is 1 or -1 for which way it is going.

TILES = {
    "#": lambda: [sprite("steel"), scale(TILE / 64), area(),
                  body(isStatic=True), "ground"],
    "=": lambda: [rect(TILE, TILE), color(220, 50, 50), area(), "danger"],
    "$": lambda: [sprite("coin"), scale(0.5), area(), "coin",
                  {"home_y": 0}],
    ">": lambda: [rect(TILE, TILE), color(255, 100, 100), area(),
                  "danger", "enemy", {"across": 1, "way": 1}],
    "v": lambda: [rect(TILE, TILE), color(255, 100, 100), area(),
                  "danger", "enemy", {"across": 0, "way": 1}],

    # Bean is a tile too, so moving the '@' moves where you start.
    # scale(0.4) makes Bean a little smaller than a tile, so it fits
    # through a gap one tile wide.
    "@": lambda: [sprite("bean"), scale(0.4), area(), body(), rotate(0),
                  z(10), "player"],
}


# ---------------------------------------------- what the game has to remember
#
# These change while you play. A function that CHANGES one has to say
# `global` first, which means "the one up here, not a new one of my own".

deaths = 0            # how many times you have died, this game
coins = 0             # coins collected on this level
hold = 0              # seconds of jump-holding left
level_over = False


# -------------------------------------------------------------- 5. the menu

@scene("menu")
def menu():
    add([text("Dark Blue", size=80), pos(width() / 2, 170),
         anchor("center")])
    add([text("Jump, collect coins, avoid the red stuff", size=26),
         pos(width() / 2, 250), anchor("center")])

    start = add([text("press UP to start, or DOWN to choose a level", size=28),
                 pos(width() / 2, height() - 120), anchor("center"),
                 rotate(0)])

    best = getData(BEST_KEY, None)
    if best is not None:
        add([text("fewest deaths: " + str(best), size=22),
             pos(width() / 2, 330), anchor("center")])

    add([text('based on "Dark Blue" by Thomas Palef (lessmilk.com)', size=16),
         pos(width() / 2, height() - 30), anchor("center"),
         color(200, 200, 220)])

    # wave() swings between two numbers for ever, so the words rock from
    # side to side.
    @onUpdate
    def rock():
        start.angle = wave(-1.5, 1.5, time() * 3)

    @onKeyPress("up")
    def play_from_the_start():
        go("level", 0, 0)

    @onKeyPress("down")
    def choose():
        # ask() lists the levels. Click one, or press its number, and
        # picked() is handed the words you chose -- "Level 3", say. The loop
        # finds which one that was, and starts that level.
        @ask("Which level?", LEVEL_NAMES)
        def picked(choice):
            for i in range(len(LEVEL_NAMES)):
                if LEVEL_NAMES[i] == choice:
                    go("level", i, 0)


# ------------------------------------------------------ 6. the level scene
#
# number is which level (0 is the first), and so_far is how many times you
# have died already. Dying starts the same level again with so_far + 1,
# which puts every coin back where it was.
#
# The scene is CALLED "level". The function is NOT called play(), because
# kaypy already has a play() for sounds -- name your function play() and
# every play("coin") would start a level instead of making a noise.

@scene("level")
def build_level(number, so_far):
    global deaths, coins, hold, level_over

    deaths = so_far
    coins = 0
    hold = 0
    level_over = False

    level = LEVELS[number]
    level_width = len(level[0]) * TILE

    addLevel(level, {
        "tileWidth": TILE,
        "tileHeight": TILE,
        "tiles": TILES,
    })

    bean = get("player")[0]
    total = len(get("coin"))

    # Each coin bobs up and down around where the level put it, so it has
    # to remember where that was.
    for coin in get("coin"):
        coin.home_y = coin.pos.y

    for sign in SIGNS[number]:
        add([text(sign[2], size=22), pos(sign[0] * TILE, sign[1] * TILE)])

    label = add([text("", size=24), pos(16, 12), fixed(), z(100)])

    def show_score():
        label.text = ("Level " + str(number + 1)
                      + "     Coins " + str(coins) + " / " + str(total)
                      + "     Deaths " + str(deaths))

    show_score()

    @onKeyPress("escape")
    def back_to_menu():
        go("menu")

    # ------------------------------------------------------- every frame

    @onUpdate
    def each_frame():
        global hold

        if level_over:
            return

        # Running. A little slower in the air, so a jump is easier to aim.
        speed = AIR_SPEED
        if bean.isGrounded():
            speed = RUN_SPEED

        if isKeyDown("left"):
            bean.move(-speed, 0)
        if isKeyDown("right"):
            bean.move(speed, 0)

        # Jumping. A tap is a small jump. Keep holding up and Bean keeps
        # being pushed upward for JUMP_HOLD seconds, so it goes higher.
        if isKeyDown("up"):
            if bean.isGrounded():
                bean.jump(JUMP)
                hold = JUMP_HOLD
            elif hold > 0:
                hold = hold - dt()
                bean.jump(JUMP)
        else:
            # Let go, and the push is over until Bean lands again.
            hold = 0

        # Fell off the bottom.
        if bean.pos.y > height() + 100:
            die()

        # The camera follows Bean from side to side, but stops at the ends
        # of the level so you never see past them. It never moves up or
        # down: the whole level is exactly one window tall.
        x = clamp(bean.pos.x, width() / 2, level_width - width() / 2)
        setCamPos(vec2(x, height() / 2))

    # ------------------------------------------------------------- coins

    @onUpdate("coin")
    def bob(coin):
        coin.pos.y = coin.home_y + wave(-3, 3, time() * 5)

    @bean.onCollide("coin")
    def got_coin(coin):
        global coins

        if level_over:
            return

        coin.destroy()
        coins = coins + 1
        play("coin")
        show_score()

        if coins == total:
            finish()

    # ------------------------------------------------------ the red stuff

    @onUpdate("enemy")
    def patrol(enemy):
        if enemy.across == 1:
            enemy.move(enemy.way * ENEMY_SPEED, 0)
        else:
            enemy.move(0, enemy.way * ENEMY_SPEED)

    # A red block that touches the ground turns away from it. "Away" rather
    # than just "the other way": a block can touch two tiles of a wall at
    # the same moment, and turning round twice would leave it going the
    # same way, into the wall.
    @onCollide("enemy", "ground")
    def turn_round(enemy, tile):
        if enemy.across == 1:
            if tile.pos.x > enemy.pos.x:
                enemy.way = -1
            else:
                enemy.way = 1
        else:
            if tile.pos.y > enemy.pos.y:
                enemy.way = -1
            else:
                enemy.way = 1

    @bean.onCollide("danger")
    def ouch(thing):
        die()

    def die():
        global level_over

        # Bean can touch lava and a red block at the same moment, which
        # would otherwise be two deaths.
        if level_over:
            return
        level_over = True

        play("ouch")
        shake(8)

        # The same level again, one more death on the count. go() builds
        # it from scratch, so every coin is back.
        @wait(0.4)
        def again():
            go("level", number, deaths + 1)

    # ------------------------------------------------------- level done

    def finish():
        global level_over

        level_over = True
        play("done")

        # Spin Bean round once, then go on.
        def spin(angle):
            bean.angle = angle

        tween(0, 360, 0.6, spin)

        @wait(0.7)
        def next_level():
            if number + 1 < len(LEVELS):
                go("level", number + 1, deaths)
            else:
                go("end", deaths)


# ---------------------------------------------------------------- 7. the end

@scene("end")
def the_end(total_deaths):
    best = getData(BEST_KEY, None)
    if best is None or total_deaths < best:
        setData(BEST_KEY, total_deaths)
        best_line = "That's your best yet!"
    else:
        best_line = "Your best is " + str(best) + "."

    if total_deaths == 1:
        died = "You died 1 time."
    else:
        died = "You died " + str(total_deaths) + " times."

    add([text("You beat Dark Blue!", size=60), pos(width() / 2, 180),
         anchor("center")])
    add([text(died + "\n" + best_line, size=30), pos(width() / 2, 300),
         anchor("center")])

    again = add([text("press UP to play again", size=28),
                 pos(width() / 2, height() - 120), anchor("center"),
                 rotate(0)])

    @onUpdate
    def rock():
        again.angle = wave(-1.5, 1.5, time() * 3)

    @onKeyPress("up")
    def play_again():
        go("menu")


# --------------------------------------------------------- 8. start the game

go("menu")
