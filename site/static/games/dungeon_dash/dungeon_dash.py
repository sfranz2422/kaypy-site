"""Dungeon Dash — five levels, five moves, one boss.

Collect every coin on a level and the door opens. Each door gives you a new
move, and the next level has a coin you cannot reach without it.

    arrow keys   run
    space        jump        (press again in the air once you have the
                             double jump, or next to a wall for a wall jump)
    x            dash        (from level 3)

HOW THIS FILE IS PUT TOGETHER

Read it top to bottom. It goes:

    1. the window and the pictures
    2. what each letter in a picture turns into
    3. the player, and the moves
    4. the coins and the door
    5. the enemies
    6. the boss
    7. start the game

The levels are pictures made of letters. Nothing in the game knows where any
particular coin is: it reads the picture and builds whatever it finds. So you
can move a coin by moving an 'o', and you never have to touch the code.
"""

from kaypy import *

# --------------------------------------------------------------- 1. setup

TILE = 48          # a tile is 48 pixels square
ACROSS = 20        # tiles across
DOWN = 13          # tiles down

kaypy(width=TILE * ACROSS, height=TILE * DOWN, background=[22, 20, 30])
setGravity(2400)

# Sprites. Every path is written out in full, on purpose: the editor scans
# this file for the names of the pictures it needs, and it can only see them
# if they are plain text. Build a path with a loop or a % and the scan finds
# nothing, so the game runs with no pictures at all.
IDLE_RUN = {"idle": {"from": 0, "to": 3, "speed": 8, "loop": True},
            "run": {"from": 4, "to": 7, "speed": 10, "loop": True}}
IDLE = {"idle": {"from": 0, "to": 3, "speed": 8, "loop": True}}

loadSprite("knight", "dungeon/knight_m.png", sliceX=9, anims=IDLE_RUN)
loadSprite("goblin", "dungeon/goblin.png", sliceX=8, anims=IDLE_RUN)
loadSprite("chort", "dungeon/chort.png", sliceX=8, anims=IDLE_RUN)
loadSprite("demon", "dungeon/big_demon.png", sliceX=8, anims=IDLE_RUN)
loadSprite("coin", "dungeon/dungeon_coin.png", sliceX=4, anims=IDLE)
loadSprite("wall", "dungeon/wall_mid.png")
loadSprite("door_shut", "dungeon/doors_leaf_closed.png")
loadSprite("door_open", "dungeon/doors_leaf_open.png")
loadSprite("heart_full", "dungeon/ui_heart_full.png")
loadSprite("heart_empty", "dungeon/ui_heart_empty.png")

loadSound("ding", "sounds/small_beep.wav")
loadSound("thump", "sounds/thump.wav")
loadSound("swoosh", "sounds/swing.wav")
loadSound("boom", "sounds/small_boom.wav")
loadSound("open", "sounds/electric_portal_open.wav")
loadSound("screech", "sounds/rising_beep.wav")

# The pictures. One letter is one tile.
#
#   #  wall      o  coin     P  you start here
#   D  door      g  goblin   c  chort      B  boss
#
# A space is empty air. See levels.py for the full note on drawing these.

LEVEL_1 = [
    "####################",
    "#                  #",
    "#                  #",
    "#             o   D#",
    "#            #######",
    "#        o         #",
    "#       #####      #",
    "#     o#           #",
    "#   #              #",
    "#  ###             #",
    "#       #          #",
    "#      P   o   g   #",
    "####################",
]

LEVEL_2 = [
    "####################",
    "#   o              #",
    "#                  #",
    "#  ###       o     #",
    "#      ##    ####  #",
    "#   o       #      #",
    "#  ###             #",
    "#             o   D#",
    "#           ########",
    "#     o            #",
    "#   #####          #",
    "#  P      g    c   #",
    "####################",
]

LEVEL_3 = [
    "####################",
    "#                  #",
    "# o            o  D#",
    "# ##       #########",
    "#                  #",
    "#       # o        #",
    "#        #####     #",
    "#                  #",
    "#    o             #",
    "#   ####           #",
    "#                  #",
    "#  P  g    o   c   #",
    "####################",
]

LEVEL_4 = [
    "####################",
    "#                  #",
    "#  o           o  D#",
    "#  ##          #####",
    "#              #   #",
    "#     o        #   #",
    "#    ###       #   #",
    "#              #   #",
    "#        o     #   #",
    "#      ####    #   #",
    "#              #   #",
    "#  P     g   c #####",
    "####################",
]

LEVEL_5 = [
    "####################",
    "#                  #",
    "#                  #",
    "#   o          o   #",
    "#  ####      ####  #",
    "#                  #",
    "#                  #",
    "#      o    o      #",
    "#    ####  ####    #",
    "#                  #",
    "#                  #",
    "#  P     B         #",
    "####################",
]

LEVELS = [LEVEL_1, LEVEL_2, LEVEL_3, LEVEL_4, LEVEL_5]

# The move each level gives you when you finish it.
ABILITIES = ["jump", "double jump", "dash", "wall jump", "everything"]


# --------------------------------------------------------- 2. the settings

SPEED = 270
JUMP = 850
DASH_SPEED = 900
DASH_TIME = 0.16
WALL_JUMP_GRACE = 0.15  # how long after touching a wall you may still push off

GOBLIN_SPEED = 1.4      # how fast a goblin patrols. This is fed to
                        # wave(), so it is how fast the SWING is, not
                        # pixels per second: bigger is faster, and
                        # about 1.4 is one round trip every 4 seconds.
GOBLIN_RANGE = 2        # how many tiles either side of where it started
CHORT_SPEED = 150       # how fast a chort chases
CHORT_SIGHT = 6         # how many tiles away it notices you
PLATFORM_RANGE = 3      # how many tiles a moving platform slides
PLATFORM_SPEED = 1.2    # how fast it slides

BOSS_HP = 6
BOSS_WALK = 70
BOSS_CHARGE = 420
BOSS_WAIT = 3.0         # seconds between charges
BOSS_TELL = 0.6         # warning before it charges
BOSS_CHARGE_TIME = 0.9


# ------------------------------------------- 3. what each letter turns into
#
# This is the whole join between the picture and the game.
#
# addLevel() walks the picture. Every time it meets a letter it looks it up
# here and builds an object out of the list of parts it finds. A letter that
# is not listed is ignored, which is why a space does nothing.
#
# Add a letter here and you can start drawing it in the levels straight away.
# The `lambda:` in front of each list just means "do not build it yet, build
# one every time you find this letter".

TILES = {
    # The dungeon itself.
    "#": lambda: [sprite("wall"), scale(3), area(), body(isStatic=True),
                  "wall"],

    # A platform that slides. isStatic keeps gravity off it so you can stand
    # on it; it still moves, because nothing stops you changing a static
    # object's position yourself. See slide() further down.
    "-": lambda: [sprite("wall"), scale(3), area(), body(isStatic=True),
                  "wall", "platform"],

    # What you are collecting, and what it opens.
    "o": lambda: [sprite("coin"), scale(3), area(), anchor("center"), "coin"],
    "D": lambda: [sprite("door_shut"), scale(1.5), area(), anchor("bot"),
                  "door"],

    # You. The player is a tile like everything else, so moving the 'P' in a
    # picture is the whole of moving where you start.
    "P": lambda: [sprite("knight"), scale(3), area(), body(jumpForce=JUMP),
                  anchor("bot"), health(3), "player"],

    # The monsters. They share the tag "enemy" so that one piece of code can
    # say what happens when you touch any of them, and each has its own tag
    # as well so that its own behaviour can find it.
    "g": lambda: [sprite("goblin"), scale(3), area(), body(), anchor("bot"),
                  "enemy", "goblin"],
    "c": lambda: [sprite("chort"), scale(3), area(), body(), anchor("bot"),
                  "enemy", "chort"],

    # opacity(1) is on the boss so it can fade in and out when it is about to
    # charge. Without the component you can still set boss.opacity and
    # nothing happens -- no error, no fading, just a warning nobody sees.
    "B": lambda: [sprite("demon"), scale(3), area(), body(), anchor("bot"),
                  opacity(1), health(BOSS_HP), "enemy", "boss"],
}


# ------------------------------------------ 4. what the game has to remember
#
# Five things change while you play, so they are variables. Any function that
# CHANGES one has to say `global` first -- that is Python's way of asking
# "the one at the top of the file, not a new one of my own". A function that
# only reads them does not need to say anything.
#
# WHICH WAY THE PLAYER IS FACING IS NOT HERE.
#
# It does not need to be: player.flipX is already true when the sprite is
# facing left, so that IS which way you are facing. Keeping a second copy of
# it would just be one more thing that can disagree with the picture on
# screen.

holding_left = False  # is the left arrow being held down?
holding_right = False # is the right arrow being held down?
jumps_left = 1        # air jumps still available
dash_left = 0         # seconds of dashing still to go
wall_left = 0         # seconds you may still wall jump for
coins_collected = 0
level_over = False

# THESE TWO ARE COUNTDOWNS, NOT DEADLINES.
#
# They used to hold "the time the dash ends", worked out as time() + 0.16,
# and every frame asked whether time() had got there yet. That breaks when
# the level changes, because time() STARTS AGAIN AT ZERO on a new level:
# a dash begun 25 seconds into level 3 left behind a deadline of 25.16,
# the next level's clock started at 0, and the player dashed helplessly
# across the room for the next 25 seconds.
#
# A countdown has nothing to compare against, so it cannot be wrong about
# what time it is. It also reads better: "how much dash is left".


# The scene is CALLED "play", but the function must not be, because kaypy
# already has a play() for sounds. Naming the function play() quietly
# replaced it, so every play("ding") in here called this function instead
# with "ding" as the level number -- and the game died on
#
#     TypeError: list indices must be integers or slices, not str
#
# pointing at the line LEVELS[number], which is nowhere near the mistake.
@scene("play")
def build_level(number):
    picture = LEVELS[number]

    addLevel(picture, {
        "tileWidth": TILE,
        "tileHeight": TILE,
        "pos": vec2(0, 0),
        "tiles": TILES,
    })

    global holding_left, holding_right
    global jumps_left, dash_left, wall_left, coins_collected, level_over

    # addLevel built the player out of the 'P' in the picture, along with
    # everything else. get() finds it again by its tag.
    player = get("player")[0]
    start = vec2(player.pos.x, player.pos.y)

    # Start of a level, so everything the game remembers goes back to the
    # beginning. These are the variables declared at the top of the file.
    # Nothing is held at the start of a level. See the note by the arrow
    # keys below for why this matters.
    holding_left = False
    holding_right = False

    jumps_left = 1
    dash_left = 0
    wall_left = 0
    coins_collected = 0
    level_over = False

    # Which moves you have depends only on which level you are on.
    can_double_jump = number >= 1
    can_dash = number >= 2
    can_wall_jump = number >= 3

    total_coins = len(get("coin"))

    # ------------------------------------------------------- the moves

    # THE ARROW KEYS, REMEMBERED RATHER THAN ASKED ABOUT.
    #
    # The obvious way to do this is onKeyDown, which asks the computer "is
    # the right arrow down right now?" every frame. It was written that way
    # first, and it had a horrible bug.
    #
    # Walking into the door opens a message, and a message pauses the game.
    # Let go of the arrow key while it is paused and the release can be
    # missed -- and then the computer goes on insisting the key is still
    # down. The next level began with the player sprinting right into a wall
    # and no way to stop, because nothing was pressing anything.
    #
    # So the game keeps its own note of which arrow is held, from the moment
    # it is pressed to the moment it is let go, and forgets both at the start
    # of every level. A release that goes missing can no longer follow you
    # into the next one.

    @onKeyPress("left")
    def press_left():
        global holding_left
        holding_left = True

    @onKeyRelease("left")
    def let_go_left():
        global holding_left
        holding_left = False

    @onKeyPress("right")
    def press_right():
        global holding_right
        holding_right = True

    @onKeyRelease("right")
    def let_go_right():
        global holding_right
        holding_right = False

    @onKeyPress("space")
    def jump():
        global jumps_left, wall_left

        if level_over:
            return

        # On the ground: an ordinary jump, and your air jump comes back.
        if player.isGrounded():
            player.jump(JUMP)
            jumps_left = 1
            return

        # Next to a wall: push off it, away from the way you are facing,
        # and turn round. The little bit of time in wall_left is
        # deliberate -- without it you would have to press space on the
        # exact frame you touch the wall, which nobody can do.
        if can_wall_jump and wall_left > 0:
            player.jump(JUMP)
            if player.flipX:
                player.move(SPEED * 2, 0)
            else:
                player.move(-SPEED * 2, 0)
            player.flipX = not player.flipX
            wall_left = 0
            play("swoosh")
            return

        # In the air with a jump left: the double jump.
        if can_double_jump and jumps_left > 0:
            player.jump(JUMP)
            jumps_left = jumps_left - 1

    @onKeyPress("x")
    def dash():
        global dash_left

        if level_over or not can_dash:
            return
        if dash_left > 0:          # already dashing
            return
        dash_left = DASH_TIME
        play("swoosh")

    @onUpdate
    def each_frame():
        global jumps_left, dash_left, wall_left

        if level_over:
            return

        # Count both timers down. dt() is how long this frame took, so
        # subtracting it each frame counts real seconds.
        if dash_left > 0:
            dash_left = dash_left - dt()
        if wall_left > 0:
            wall_left = wall_left - dt()

        # Walking. Both at once cancel out, which is what a real keyboard
        # does anyway.
        if holding_left:
            player.move(-SPEED, 0)
            player.flipX = True
        if holding_right:
            player.move(SPEED, 0)
            player.flipX = False

        # A dash is just "move very fast for a moment", the way you face.
        if dash_left > 0:
            if player.flipX:
                player.move(-DASH_SPEED, 0)
            else:
                player.move(DASH_SPEED, 0)

        if player.isGrounded():
            jumps_left = 1

        # Fell off the bottom of the world.
        if player.pos.y > TILE * DOWN + 100:
            hurt_player()

    @player.onCollide("wall")
    def touched_wall(wall):
        # Note down WHEN a wall was last touched, and for a fraction of a
        # second afterwards that still counts. That is what makes a wall
        # jump possible to hit.
        #
        # Which side the wall is on does not need noting: you got there by
        # moving into it, so it is the way you are already facing.
        global wall_left

        if player.isGrounded():
            return
        wall_left = WALL_JUMP_GRACE

    # ------------------------------------------------- coins and the door

    label = add([
        text("0 / " + str(total_coins), size=24),
        pos(16, 14),
        fixed(),
        z(100),
    ])

    @player.onCollide("coin")
    def got_coin(coin):
        global coins_collected

        coin.destroy()
        coins_collected = coins_collected + 1
        label.text = str(coins_collected) + " / " + str(total_coins)
        play("ding")

        if coins_collected >= total_coins:
            for door in get("door"):
                door.use(sprite("door_open"))
            play("open")

    @player.onCollide("door")
    def reached_door(door):
        # The door is there the whole time. It only works once every coin is
        # collected -- that is the whole gate.
        global level_over

        if coins_collected < total_coins:
            return
        level_over = True
        if number + 1 < len(LEVELS):
            say("Level " + str(number + 1) + " done!\n\nYou can now: "
                + ABILITIES[number + 1],
                then=lambda answer: go("play", number + 1))
        else:
            say("You win!", then=lambda answer: go("play", 0))

    # ------------------------------------------------------- getting hurt

    def hurt_player():
        global level_over

        if level_over:
            return
        player.hurt(1)
        shake(10)
        play("thump")
        if player.hp <= 0:
            level_over = True
            say("The dungeon wins this time.",
                then=lambda answer: go("play", number))
        else:
            player.pos = vec2(start.x + TILE / 2, start.y + TILE)

    @player.onCollide("enemy")
    def touched_enemy(enemy):
        # Landing on top of something is a stomp, not a mistake. Anything
        # else hurts.
        if player.pos.y < enemy.pos.y - TILE / 2:
            if enemy.is_("boss"):
                enemy.hurt(1)
                player.jump(JUMP * 0.7)
                play("boom")
                shake(6)
            else:
                enemy.destroy()
                player.jump(JUMP * 0.7)
                play("boom")
        else:
            hurt_player()

    # ------------------------------------------------------- 5. the enemies
    #
    # Each enemy gets its own onUpdate, which runs every frame for that one
    # enemy.
    #
    # NOTHING IS STORED ON THE ENEMY ITSELF.
    #
    # A goblin needs to know where it started, and that is handed to its
    # function as an ordinary argument with a default value -- home=g.pos.x
    # is worked out once, now, and the function keeps it. The same trick as
    # g=goblin on the line above, and for the same reason.

    for goblin in get("goblin"):

        @goblin.onUpdate
        def patrol(g=goblin, home=goblin.pos.x):
            # g=goblin is not a typo. Without it every one of these
            # functions would share the SAME goblin -- whichever one the
            # loop finished on -- and all the others would stand still.
            #
            # wave() swings a number between two values forever, so this one
            # line is the whole patrol. It is the same function the moving
            # platforms use.
            left = home - GOBLIN_RANGE * TILE
            right = home + GOBLIN_RANGE * TILE
            g.pos.x = wave(left, right, time() * GOBLIN_SPEED)

            # Which way to face: work out where it will be in a moment, and
            # if that is further left than it is now, it is walking left.
            soon = wave(left, right, (time() + 0.05) * GOBLIN_SPEED)
            g.flipX = soon < g.pos.x

    for chort in get("chort"):

        @chort.onUpdate
        def chase(c=chort):
            if player.pos.dist(c.pos) > CHORT_SIGHT * TILE:
                c.play("idle")
                return
            c.play("run")
            if player.pos.x > c.pos.x:
                c.move(CHORT_SPEED, 0)
                c.flipX = False
            else:
                c.move(-CHORT_SPEED, 0)
                c.flipX = True

    # ---------------------------------------------- the moving platforms

    for platform in get("platform"):

        @platform.onUpdate
        def slide(p=platform, home=platform.pos.x):
            was = p.pos.x
            p.pos.x = wave(home - PLATFORM_RANGE * TILE / 2,
                           home + PLATFORM_RANGE * TILE / 2,
                           time() * PLATFORM_SPEED)

            # CARRY WHOEVER IS STANDING ON IT.
            #
            # Without these lines the platform slides out from under your
            # feet and you drop off, which feels broken rather than hard.
            # You are "on it" if you are just above it and roughly over it.
            moved = p.pos.x - was
            above = player.pos.y <= p.pos.y + 4
            over = abs(player.pos.x - p.pos.x) < TILE
            if above and over and player.isGrounded():
                player.pos.x = player.pos.x + moved

    # ---------------------------------------------------------- 6. the boss
    #
    # The boss works on a rhythm rather than on remembered timers: the whole
    # fight is "where are we in the current cycle?", which time() answers on
    # its own. A cycle is walk, then a warning flash, then a charge.

    BOSS_CYCLE = BOSS_WAIT + BOSS_TELL + BOSS_CHARGE_TIME

    for boss in get("boss"):

        @boss.onUpdate
        def fight(b=boss):
            # How far through the current cycle we are. % gives the
            # remainder, so this counts 0, 0.1, 0.2 ... up to BOSS_CYCLE and
            # then starts again, forever.
            point = time() % BOSS_CYCLE

            if point < BOSS_WAIT:
                # Walking. This is the only part that chooses a direction,
                # so the charge below simply keeps going the way it ended up
                # facing.
                b.play("run")
                b.opacity = 1
                b.flipX = player.pos.x < b.pos.x
                if b.flipX:
                    b.move(-BOSS_WALK, 0)
                else:
                    b.move(BOSS_WALK, 0)

            elif point < BOSS_WAIT + BOSS_TELL:
                # The warning. It stands still and flashes, so the charge can
                # be learned instead of being a surprise.
                b.play("idle")
                b.opacity = 0.4 + 0.6 * abs(wave(-1, 1, time() * 20))

            else:
                # The charge, straight ahead, fast.
                b.play("run")
                b.opacity = 1
                if b.flipX:
                    b.move(-BOSS_CHARGE, 0)
                else:
                    b.move(BOSS_CHARGE, 0)

        @boss.onDeath
        def boss_died(b=boss):
            global level_over

            addKaboom(b.pos)
            play("boom")
            shake(20)
            b.destroy()
            level_over = True
            say("You beat the dungeon!", then=lambda answer: go("play", 0))

    # ---------------------------------------------------------- the hearts

    @onDraw
    def draw_hearts():
        # drawSprite paints one frame straight onto the screen without making
        # a game object for it. A heart is a mark on the screen, not a thing
        # in the dungeon, so it does not need to be an object.
        heart = 0
        while heart < 3:
            if heart < player.hp:
                name = "heart_full"
            else:
                name = "heart_empty"
            drawSprite(name, pos=vec2(width() - 130 + heart * 40, 18),
                       width=32, height=30, fixed=True)
            heart = heart + 1


go("play", 0)
