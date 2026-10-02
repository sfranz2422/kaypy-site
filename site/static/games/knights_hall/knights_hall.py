"""Knight's Hall -- hold the hall against wave after wave of monsters.

    d-pad / arrow keys   walk, in eight directions
    S button / space     swing your sword the way you are facing
    Z button / z         dash -- you cannot be hurt while you dash

Made for a phone held upright, like a handheld game: the hall at the top,
the d-pad and the two buttons underneath it, where your thumbs are. On a
computer the arrow keys, space and z do exactly the same thing.

HOW THE BUTTONS GET ON THE SCREEN

One word, on the first line of the program:

    kaypy(width=576, height=864, joystick=True)

joystick=True draws a d-pad and two buttons, and they PRETEND TO BE KEYS.
Holding the left of the d-pad is the left arrow being held down; the two
buttons are space and z. So nothing else in this file knows about the
buttons at all. It asks isKeyDown("left") and onKeyPress("space"), the same
as any game, and a thumb answers.

HOW THIS FILE IS PUT TOGETHER

    1. the window and the pictures
    2. the settings
    3. the hall, drawn as a picture made of letters
    4. what the game has to remember
    5. the knight: walking, the sword, the dash, getting hurt
    6. the monsters, and the waves they come in
    7. the score, the hearts and the button labels
    8. start the game
"""

from kaypy import *

# --------------------------------------------------------------- 1. setup

TILE = 48          # a tile is 48 pixels square: the 16-pixel art, times 3

# The hall is 12 tiles square, and the window is taller than that. The
# extra 6 tiles at the bottom are where the d-pad and the buttons go, so a
# thumb on the controls never covers a monster.
kaypy(width=TILE * 12, height=TILE * 18, background=[20, 17, 26],
      joystick=True)

# Sprites. Every path is written out in full, on purpose: the playground
# reads this file for the names of the pictures it needs, and it only finds
# them if they are plain text.
IDLE_RUN = {"idle": {"from": 0, "to": 3, "speed": 8, "loop": True},
            "run": {"from": 4, "to": 7, "speed": 10, "loop": True}}

loadSprite("knight", "dungeon/knight_m.png", sliceX=9, anims=IDLE_RUN)
loadSprite("goblin", "dungeon/goblin.png", sliceX=8, anims=IDLE_RUN)
loadSprite("imp", "dungeon/imp.png", sliceX=8, anims=IDLE_RUN)
loadSprite("orc", "dungeon/orc_warrior.png", sliceX=8, anims=IDLE_RUN)
loadSprite("sword", "dungeon/weapon_regular_sword.png")
loadSprite("flask", "dungeon/flask_red.png")
loadSprite("heart_full", "dungeon/ui_heart_full.png")
loadSprite("heart_empty", "dungeon/ui_heart_empty.png")

loadSprite("floor_1", "dungeon/floor_1.png")
loadSprite("floor_2", "dungeon/floor_2.png")
loadSprite("floor_3", "dungeon/floor_3.png")
loadSprite("wall_top", "dungeon/wall_top_mid.png")
loadSprite("wall", "dungeon/wall_mid.png")
loadSprite("banner", "dungeon/wall_banner_red.png")
loadSprite("door", "dungeon/doors_leaf_open.png")

loadSound("swing", "sounds/swing.wav")
loadSound("hit", "sounds/thump.wav")
loadSound("dash", "sounds/swoosh.wav")
loadSound("hurt", "sounds/lazer_punch.wav")
loadSound("drink", "sounds/small_beep.wav")
loadSound("wave", "sounds/rising_beep.wav")
loadSound("boom", "sounds/small_boom.wav")


# --------------------------------------------------------- 2. the settings

SPEED = 220             # how fast the knight walks, pixels per second
HEARTS = 3

SWORD_REACH = 42        # how far in front of the knight the blade appears
SWORD_TIME = 0.15       # how long a swing lasts, in seconds
KNOCKBACK = 40          # how far a monster is shoved when the sword hits it

DASH_SPEED = 900
DASH_TIME = 0.18        # how long a dash lasts
DASH_RECHARGE = 1.0     # how long until you can dash again
HURT_TIME = 1.2         # after a hit, how long before you can be hurt again

SPAWN_GAP = 0.8         # seconds between monsters coming through a door
WAVE_PAUSE = 2.0        # seconds of quiet between waves
FLASK_CHANCE = 0.1      # how likely a monster is to drop a healing flask

# The three kinds of monster. Each one is a dictionary, so adding a fourth
# is one more line here (and a loadSprite above).
MONSTERS = {
    "goblin": {"hp": 1, "speed": 80},
    "imp": {"hp": 1, "speed": 140},
    "orc": {"hp": 3, "speed": 60},
}

BEST_KEY = "knights_hall_best"


# ----------------------------------------------------------- 3. the hall
#
# One letter is one tile.
#
#   ^  top of the wall     #  wall      B  wall with a banner
#   D  a doorway, two tiles wide and two tall. The 'd's beside and under
#      it are the rest of the same door, so they draw nothing.
#   .  ,  :  three kinds of floor, so it does not look like wallpaper
#
# The monsters come in through the doors, so a door can be moved by moving
# its letters -- nothing in the code knows where they are.

HALL = [
    "^D^^^D^^^D^^",
    "#dd#BddB#dd#",
    "#..,....:..#",
    "#.:...,....#",
    "#....,...,.#",
    "#,.:.......#",
    "#.....:..,.#",
    "#..,.......#",
    "#.....,.:..#",
    "#.:.,......#",
    "#.......,..#",
    "############",
]

# A door is drawn from the top-left of its tile, and the picture is two
# tiles wide and two tall, so it covers three more tiles than its own. Those
# are the 'd's. Put a '#' there instead and that wall gets drawn over a
# corner of the door.

TILES = {
    "^": lambda: [sprite("wall_top"), scale(3)],
    "#": lambda: [sprite("wall"), scale(3)],
    "B": lambda: [sprite("banner"), scale(3)],
    "D": lambda: [sprite("door"), scale(3)],
    ".": lambda: [sprite("floor_1"), scale(3)],
    ",": lambda: [sprite("floor_2"), scale(3)],
    ":": lambda: [sprite("floor_3"), scale(3)],
}

# The floor, in pixels: everything inside the walls. Nothing that walks may
# leave it. There are no walls to bump into -- each frame the knight and the
# monsters are simply put back inside this box with clamp().
LEFT = TILE * 1
RIGHT = TILE * 11
TOP = TILE * 2
BOTTOM = TILE * 11

# Where the monsters appear: just inside each door. Worked out from the
# picture, so they move with the doors.
DOORS = []
for col in range(len(HALL[0])):
    if HALL[0][col] == "D":
        DOORS.append(vec2(col * TILE + TILE, TOP + 10))


# --------------------------------------------- 4. what the game remembers
#
# These change while you play, so any function that CHANGES one has to say
# `global` first. They all go back to the start in the scene below.

facing = (0, 1)     # which way the knight faces, as (x, y): (0, 1) is down
dash_left = 0       # seconds of dash still to go
dash_wait = 0       # seconds until the next dash is allowed
hurt_left = 0       # seconds of safety left after being hit
wave_number = 0     # not called `wave`: that would hide kaypy's wave()
score = 0
queue = []          # the monsters still to come in this wave
spawn_wait = 0      # seconds until the next one comes through a door
game_over = False

best = getData(BEST_KEY, 0)

# The way the sword points for each of the eight ways the knight can face.
# The picture of the sword points straight up, so up is 0 degrees and the
# rest go round clockwise.
SWORD_ANGLE = {
    (0, -1): 0, (1, -1): 45, (1, 0): 90, (1, 1): 135,
    (0, 1): 180, (-1, 1): 225, (-1, 0): 270, (-1, -1): 315,
}


@scene("hall")
def hall():
    global facing, dash_left, dash_wait, hurt_left
    global wave_number, score, queue, spawn_wait, game_over

    facing = (0, 1)
    dash_left = 0
    dash_wait = 0
    hurt_left = 0
    wave_number = 0
    score = 0
    queue = []
    spawn_wait = WAVE_PAUSE
    game_over = False

    addLevel(HALL, {"tileWidth": TILE, "tileHeight": TILE,
                    "pos": vec2(0, 0), "tiles": TILES})

    # ------------------------------------------------------- 5. the knight

    knight = add([
        sprite("knight", anim="idle"),
        pos((LEFT + RIGHT) / 2, (TOP + BOTTOM) / 2),
        anchor("center"),
        scale(2.5),
        area(),
        opacity(1),
        health(HEARTS),
        z(10),
        "knight",
    ])

    @onUpdate
    def walk():
        global facing, dash_left, dash_wait, hurt_left

        if game_over:
            return

        # Count the timers down. dt() is how long this frame took, so
        # taking it off every frame counts real seconds.
        if dash_left > 0:
            dash_left = dash_left - dt()
        if dash_wait > 0:
            dash_wait = dash_wait - dt()
        if hurt_left > 0:
            hurt_left = hurt_left - dt()

        # Which arrows are held. The d-pad holds these too, and a thumb
        # between two arrows holds both -- that is a diagonal.
        dx = 0
        dy = 0
        if isKeyDown("left"):
            dx = dx - 1
        if isKeyDown("right"):
            dx = dx + 1
        if isKeyDown("up"):
            dy = dy - 1
        if isKeyDown("down"):
            dy = dy + 1

        if dash_left > 0:
            # A dash goes the way you were facing when it started, fast,
            # whatever you do with the d-pad meanwhile.
            way = vec2(facing[0], facing[1]).unit()
            knight.move(way.x * DASH_SPEED, way.y * DASH_SPEED)
        elif dx != 0 or dy != 0:
            facing = (dx, dy)
            # unit() makes the arrow one long whichever way it points.
            # Without it, (1, 1) is about 1.4 long and the knight would
            # walk faster diagonally than straight.
            way = vec2(dx, dy).unit()
            knight.move(way.x * SPEED, way.y * SPEED)
            if dx != 0:
                knight.flipX = dx < 0
            if knight.curAnim() != "run":
                knight.play("run")
        elif knight.curAnim() != "idle":
            knight.play("idle")

        # Stay on the floor.
        knight.pos.x = clamp(knight.pos.x, LEFT + 20, RIGHT - 20)
        knight.pos.y = clamp(knight.pos.y, TOP, BOTTOM - 35)

        # See-through while dashing, flickering while safe after a hit, and
        # solid the rest of the time.
        if dash_left > 0:
            knight.opacity = 0.4
        elif hurt_left > 0:
            knight.opacity = wave(0.2, 1, time() * 20)
        else:
            knight.opacity = 1

    # ---- the sword

    @onKeyPress("space")
    def swing():
        if game_over or isShowing():
            return
        # One swing at a time. get() gives back a list, and an empty list
        # counts as False, so this asks "is a sword out already?"
        if get("sword"):
            return
        add([
            sprite("sword"),
            pos(sword_spot()),
            anchor("center"),
            scale(2.5),
            rotate(SWORD_ANGLE[facing]),
            area(),
            lifespan(SWORD_TIME),
            z(11),
            "sword",
        ])
        play("swing")

    def sword_spot():
        way = vec2(facing[0], facing[1]).unit()
        return knight.pos + way * SWORD_REACH

    @onUpdate("sword")
    def follow_knight(sword):
        # The sword stays in the knight's hand as the knight moves.
        sword.pos = sword_spot()

    @onCollide("sword", "enemy")
    def sword_hits(sword, enemy):
        enemy.hurt(1)
        play("hit")
        # Shove it away from the knight, so one monster cannot stand on you.
        away = (enemy.pos - knight.pos).unit()
        enemy.pos = enemy.pos + away * KNOCKBACK

    # ---- the dash

    @onKeyPress("z")
    def dash():
        global dash_left, dash_wait

        if game_over or isShowing():
            return
        if dash_wait > 0:
            return
        dash_left = DASH_TIME
        dash_wait = DASH_RECHARGE
        play("dash")

    # ---- getting hurt

    # onCollideUpdate, not onCollide: onCollide only happens at the moment
    # two things START touching. A goblin that walks into you while you are
    # safe after a hit, and then just stays there, would never hurt you
    # again. This one asks every frame they are touching.
    @knight.onCollideUpdate("enemy")
    def touched(enemy):
        global hurt_left

        if game_over or dash_left > 0 or hurt_left > 0:
            return
        knight.hurt(1)
        hurt_left = HURT_TIME
        shake(8)
        play("hurt")

    @knight.onDeath
    def knight_died():
        global game_over, best

        game_over = True
        play("boom")
        addKaboom(knight.pos)
        knight.destroy()

        if score > best:
            best = score
            setData(BEST_KEY, best)

        @say("The hall has fallen.\n\nYou reached wave "
             + str(wave_number) + " and beat " + str(score) + " monsters.",
             button="Play again")
        def again():
            go("hall")

    @knight.onCollide("flask")
    def drink(flask):
        flask.destroy()
        knight.heal(1)
        play("drink")

    # ------------------------------------------------------ 6. the monsters

    def add_monster(kind):
        details = MONSTERS[kind]
        door = choose(DOORS)
        monster = add([
            sprite(kind, anim="run"),
            pos(door.x, door.y),
            anchor("center"),
            scale(2.5),
            area(),
            health(details["hp"]),
            z(5),
            "enemy",
        ])

        # Not quite all the same speed, so they spread out instead of
        # walking in one lump.
        speed = details["speed"] * rand(0.85, 1.15)

        # Every monster gets its own chase(), made fresh inside this call of
        # add_monster(). So `monster` and `speed` in it mean THIS monster and
        # THIS speed, even when there are ten of them.
        @monster.onUpdate
        def chase():
            if game_over:
                return
            toward = (knight.pos - monster.pos).unit()
            monster.move(toward.x * speed, toward.y * speed)
            monster.flipX = toward.x < 0
            monster.pos.x = clamp(monster.pos.x, LEFT + 16, RIGHT - 16)
            monster.pos.y = clamp(monster.pos.y, TOP, BOTTOM - 20)

        @monster.onDeath
        def beaten():
            global score
            score = score + 1
            addKaboom(monster.pos, scale=0.5)
            if chance(FLASK_CHANCE):
                # opacity(1) is what lets lifespan() fade it out. Without
                # it kaypy prints a note and the flask just vanishes.
                add([sprite("flask"), pos(monster.pos), anchor("center"),
                     scale(2.5), area(), opacity(1), lifespan(8, fade=1),
                     z(4), "flask"])
            monster.destroy()

    def next_wave():
        global wave_number, queue

        wave_number = wave_number + 1
        # More goblins every wave, imps from wave 2, an orc every third.
        queue = []
        for i in range(wave_number + 2):
            queue.append("goblin")
        for i in range(wave_number - 1):
            queue.append("imp")
        for i in range(wave_number // 3):
            queue.append("orc")
        play("wave")

    @onUpdate
    def waves():
        global spawn_wait

        if game_over:
            return
        spawn_wait = spawn_wait - dt()
        if spawn_wait > 0:
            return

        if len(queue) > 0:
            # Let the next one in, chosen at random from those left.
            kind = choose(queue)
            queue.remove(kind)
            add_monster(kind)
            spawn_wait = SPAWN_GAP
        elif len(get("enemy")) == 0:
            # Everyone beaten and nobody waiting: the next wave.
            next_wave()
            spawn_wait = WAVE_PAUSE

    # ----------------------------------------- 7. the score, hearts, labels
    #
    # The bottom of the window, under the hall, is the control panel. The
    # d-pad and buttons are drawn there by kaypy, on top of everything; all
    # this draws is the writing around them.

    PANEL = TILE * 12

    @onDraw
    def panel():
        # Everything is on the right, above the buttons. The d-pad takes up
        # the whole of the left.
        drawText(text="WAVE " + str(wave_number), pos=vec2(310, PANEL + 10),
                 size=24, color=(240, 220, 160))
        drawText(text="SCORE " + str(score) + "   BEST " + str(best),
                 pos=vec2(310, PANEL + 54), size=16, color=(200, 200, 210))

        # A full heart for every hit you can still take.
        hp = 0
        if knight.exists():
            hp = knight.hp
        i = 0
        while i < HEARTS:
            if i < hp:
                name = "heart_full"
            else:
                name = "heart_empty"
            drawSprite(sprite=name, pos=vec2(width() - 150 + i * 46,
                                             PANEL + 8),
                       width=39, height=36)
            i = i + 1

        # What the two buttons do. kaypy labels them with their keys, S and
        # Z, so the game says what they are FOR.
        drawText(text="SWORD", pos=vec2(width() - 130, PANEL + 242),
                 size=16, color=(200, 200, 210))
        if dash_wait > 0:
            dash_colour = (110, 110, 120)
        else:
            dash_colour = (200, 200, 210)
        drawText(text="DASH", pos=vec2(width() - 243, PANEL + 186),
                 size=16, color=dash_colour)

        # A note about the next wave, while it is waiting to start.
        if len(queue) == 0 and len(get("enemy")) == 0 and not game_over:
            drawText(text="Wave " + str(wave_number + 1) + " is coming...",
                     pos=vec2(width() / 2 - 120, TOP + 190), size=24,
                     color=(255, 255, 255))


# ------------------------------------------------------- 8. start the game

go("hall")

say("Monsters are coming through the doors.\n\n"
    "Walk with the d-pad. S swings your sword the way you are facing. "
    "Z dashes, and you can't be hurt while you dash.\n\n"
    "On a computer: arrow keys, space and z.", button="Play")
