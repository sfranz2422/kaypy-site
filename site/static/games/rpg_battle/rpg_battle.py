"""A turn-based battle — the hero on the right, the monsters on the left.

    up / down     move the cursor
    space         choose
    x             go back

Attack, Magic, Item, Run. Everyone takes a turn in speed order, fastest
first, and the round repeats until one side is finished.

HOW THIS FILE IS PUT TOGETHER

Read it top to bottom. It goes:

    1. the window and the pictures
    2. the fighters, as data
    3. whose turn it is
    4. what the menu is showing
    5. doing something on your turn
    6. the monsters' turn
    7. drawing the screen

NOBODY HERE IS A GAME OBJECT.

A platform game needs game objects: things with a position that fall, collide
and get destroyed. A battle needs none of that. Nothing moves, nothing falls,
and nothing bumps into anything -- so the hero and the monsters are plain
dictionaries, and the screen is drawn from them every frame. That is the whole
design, and it is why there is no add() anywhere in this file.
"""

from kaypy import *

# --------------------------------------------------------------- 1. setup

WIDE = 960
TALL = 640

kaypy(width=WIDE, height=TALL, background=[18, 16, 24])

IDLE_RUN = {"idle": {"from": 0, "to": 3, "speed": 8, "loop": True},
            "run": {"from": 4, "to": 7, "speed": 10, "loop": True}}

loadSprite("knight", "dungeon/knight_m.png", sliceX=9, anims=IDLE_RUN)
loadSprite("goblin", "dungeon/goblin.png", sliceX=8, anims=IDLE_RUN)
loadSprite("skeleton", "dungeon/skelet.png", sliceX=8, anims=IDLE_RUN)
loadSprite("chort", "dungeon/chort.png", sliceX=8, anims=IDLE_RUN)

loadSound("hit", "sounds/thump.wav")
loadSound("magic", "sounds/rising_beep.wav")
loadSound("drink", "sounds/small_beep.wav")
loadSound("down", "sounds/small_boom.wav")


# ------------------------------------------------------- 2. the fighters
#
# Everything about a fighter is in one dictionary. To make the knight tougher,
# change a number here. To add a fourth monster, copy a block and change the
# name, the picture and where it stands.

hero = {
    "name": "Knight",
    "hp": 40, "max_hp": 40,
    "mp": 12, "max_mp": 12,
    "attack": 10,
    "defence": 4,
    "speed": 9,
    "picture": "knight",
    "x": 740, "y": 330,
    "friend": True,
}

monsters = [
    {"name": "Goblin",   "hp": 18, "max_hp": 18, "attack": 3, "defence": 2,
     "speed": 8, "picture": "goblin",   "x": 150, "y": 330, "friend": False},
    {"name": "Skeleton", "hp": 24, "max_hp": 24, "attack": 4, "defence": 3,
     "speed": 5, "picture": "skeleton", "x": 290, "y": 330, "friend": False},
    {"name": "Chort",    "hp": 30, "max_hp": 30, "attack": 6, "defence": 4,
     "speed": 3, "picture": "chort",    "x": 430, "y": 330, "friend": False},
]

# Spells cost MP. "damage" ones hurt a monster, "heal" ones mend the hero.
spells = [
    {"name": "Fire",  "cost": 4, "power": 14, "kind": "damage"},
    {"name": "Spark", "cost": 2, "power": 8,  "kind": "damage"},
    {"name": "Mend",  "cost": 3, "power": 16, "kind": "heal"},
]

# A bag. Using one takes it out of the bag, so the list gets shorter.
items = [
    {"name": "Potion", "power": 18, "kind": "heal"},
    {"name": "Potion", "power": 18, "kind": "heal"},
    {"name": "Ether",  "power": 8,  "kind": "mana"},
]

COMMANDS = ["Attack", "Magic", "Item", "Run"]


# ------------------------------------------------------ 3. whose turn it is
#
# One list, sorted so the fastest goes first. When it runs out, the round is
# over and a new one is built -- which is also how a monster that has just
# been defeated stops getting turns.

order = []
turn = 0

# What the game is doing right now. "choosing" waits for you; "watching"
# is showing a message before moving on; "over" is the end.
doing = "choosing"

# Which menu is open, where the cursor is, and what we are about to do.
menu = "main"
cursor = 0
chosen_spell = None
chosen_item = None

message = ""
pause_left = 0.0

# Has the player pressed anything yet? Until they have, the screen says how
# to play. In a browser the game only hears the keyboard once the picture has
# been clicked, and a battle that ignores every key looks broken rather than
# unfocused -- so the game says so itself instead of leaving it to a note in
# the output pane that nobody reads.
pressed_anything = False

# Set when a message is only an explanation -- "not enough MP" -- rather than
# something that happened. When the message clears, the turn comes straight
# back to you instead of passing on.
keep_turn = False


def living_monsters():
    """The monsters still standing."""
    alive = []
    for monster in monsters:
        if monster["hp"] > 0:
            alive.append(monster)
    return alive


def build_order():
    """Everyone still standing, fastest first."""
    global order, turn

    fighters = []
    if hero["hp"] > 0:
        fighters.append(hero)
    for monster in living_monsters():
        fighters.append(monster)

    # Sort by speed, highest first. sorted() leaves the original list alone
    # and hands back a new one in the order we asked for.
    order = sorted(fighters, key=speed_of, reverse=True)
    turn = 0


def speed_of(fighter):
    return fighter["speed"]


def whose_turn():
    if turn < len(order):
        return order[turn]
    return None


def say_and_wait(words, seconds=0.9, yours_again=False, ends_it=False):
    """Put a line on the message bar and hold there for a moment.

    yours_again=True means the message did not use up a turn -- it was a
    refusal, like trying to cast a spell you cannot afford.

    ends_it=True means this is the last thing that will happen.

    THE ORDER MATTERS HERE. This used to be called AFTER the caller had set
    doing = "over", and then quietly set doing = "watching" itself, so the
    battle never actually reached its end state. It still looked finished,
    because the message sat there for ninety-nine seconds -- which is exactly
    the kind of bug that survives being played.
    """
    global message, pause_left, doing, keep_turn

    message = words
    pause_left = seconds
    doing = "over" if ends_it else "watching"
    keep_turn = yours_again


def next_turn():
    """Hand the turn on, and start a new round when this one runs out."""
    global turn, doing, menu, cursor

    if battle_finished():
        return

    turn = turn + 1
    while turn < len(order) and order[turn]["hp"] <= 0:
        turn = turn + 1        # skip anyone defeated mid-round

    if turn >= len(order):
        build_order()

    fighter = whose_turn()
    if fighter is None:
        return

    if fighter["friend"]:
        doing = "choosing"
        menu = "main"
        cursor = 0
    else:
        monster_turn(fighter)


def battle_finished():
    """True if either side is done, and says so."""
    if hero["hp"] <= 0:
        say_and_wait("The knight falls...", 99, ends_it=True)
        return True
    if not living_monsters():
        say_and_wait("You win!", 99, ends_it=True)
        return True
    return False


# --------------------------------------------------- 4. what the menu shows

def menu_lines():
    """The rows the menu box is currently showing."""
    if menu == "main":
        return COMMANDS
    if menu == "magic":
        rows = []
        for spell in spells:
            rows.append(spell["name"] + "  " + str(spell["cost"]) + " MP")
        return rows
    if menu == "item":
        if not items:
            return ["(the bag is empty)"]
        rows = []
        for item in items:
            rows.append(item["name"])
        return rows
    if menu == "target":
        rows = []
        for monster in living_monsters():
            rows.append(monster["name"])
        return rows
    return []


@onKeyPress("up")
def move_up():
    global cursor, pressed_anything
    pressed_anything = True
    if doing != "choosing":
        return
    cursor = cursor - 1
    if cursor < 0:
        cursor = len(menu_lines()) - 1


@onKeyPress("down")
def move_down():
    global cursor, pressed_anything
    pressed_anything = True
    if doing != "choosing":
        return
    cursor = cursor + 1
    if cursor > len(menu_lines()) - 1:
        cursor = 0


@onKeyPress("x")
def go_back():
    """Back out to the main menu. There is nowhere to go back to from there."""
    global menu, cursor, chosen_spell, chosen_item, pressed_anything

    pressed_anything = True

    if doing != "choosing" or menu == "main":
        return
    menu = "main"
    cursor = 0
    chosen_spell = None
    chosen_item = None


@onKeyPress("space")
def choose():
    global menu, cursor, chosen_spell, chosen_item, pressed_anything

    pressed_anything = True
    if doing != "choosing":
        return

    if menu == "main":
        command = COMMANDS[cursor]
        if command == "Attack":
            chosen_spell = None
            menu = "target"
            cursor = 0
        elif command == "Magic":
            menu = "magic"
            cursor = 0
        elif command == "Item":
            menu = "item"
            cursor = 0
        elif command == "Run":
            run_away()
        return

    if menu == "magic":
        spell = spells[cursor]
        if spell["cost"] > hero["mp"]:
            # A refusal is not a turn. Without yours_again the knight would
            # stand there and lose its go for asking.
            say_and_wait("Not enough MP.", 0.7, yours_again=True)
            return
        chosen_spell = spell
        if spell["kind"] == "heal":
            cast_on_hero(spell)
        else:
            menu = "target"
            cursor = 0
        return

    if menu == "item":
        if not items:
            return
        chosen_item = items[cursor]
        use_item(chosen_item)
        return

    if menu == "target":
        alive = living_monsters()
        if not alive:
            return
        target = alive[cursor]
        if chosen_spell is None:
            swing_at(target)
        else:
            cast_at(chosen_spell, target)


# ------------------------------------------------ 5. doing something on your turn

def damage_from(attacker, defender):
    """Attack minus defence, give or take a little, never less than one."""
    rough = attacker["attack"] + randi(0, 3) - defender["defence"]
    if rough < 1:
        rough = 1
    return rough


def swing_at(target):
    global menu, cursor

    harm = damage_from(hero, target)
    target["hp"] = target["hp"] - harm
    play("hit")
    shake(6)
    menu = "main"
    cursor = 0

    if target["hp"] <= 0:
        target["hp"] = 0
        play("down")
        say_and_wait("The " + target["name"] + " takes " + str(harm)
                     + " and falls!")
    else:
        say_and_wait("The " + target["name"] + " takes " + str(harm) + ".")


def cast_at(spell, target):
    global menu, cursor, chosen_spell

    hero["mp"] = hero["mp"] - spell["cost"]
    harm = spell["power"] + randi(0, 3)
    target["hp"] = target["hp"] - harm
    play("magic")
    shake(4)
    menu = "main"
    cursor = 0
    chosen_spell = None

    if target["hp"] <= 0:
        target["hp"] = 0
        play("down")
        say_and_wait(spell["name"] + " burns the " + target["name"]
                     + " away!")
    else:
        say_and_wait(spell["name"] + " hits the " + target["name"]
                     + " for " + str(harm) + ".")


def cast_on_hero(spell):
    global menu, cursor, chosen_spell

    hero["mp"] = hero["mp"] - spell["cost"]
    mended = heal(hero, spell["power"])
    play("magic")
    menu = "main"
    cursor = 0
    chosen_spell = None
    say_and_wait(spell["name"] + " mends " + str(mended) + " HP.")


def heal(who, amount):
    """Heal, but never above the maximum. Returns how much it really was."""
    before = who["hp"]
    who["hp"] = who["hp"] + amount
    if who["hp"] > who["max_hp"]:
        who["hp"] = who["max_hp"]
    return who["hp"] - before


def use_item(item):
    global menu, cursor, chosen_item

    items.remove(item)          # out of the bag for good
    menu = "main"
    cursor = 0
    chosen_item = None
    play("drink")

    if item["kind"] == "heal":
        mended = heal(hero, item["power"])
        say_and_wait("The " + item["name"] + " mends " + str(mended) + " HP.")
    else:
        hero["mp"] = hero["mp"] + item["power"]
        if hero["mp"] > hero["max_mp"]:
            hero["mp"] = hero["max_mp"]
        say_and_wait("The " + item["name"] + " restores some MP.")


def run_away():
    if chance(0.5):
        say_and_wait("You got away!", 99, ends_it=True)
    else:
        say_and_wait("You could not get away!")


# ----------------------------------------------------- 6. the monsters' turn

def monster_turn(monster):
    harm = damage_from(monster, hero)
    hero["hp"] = hero["hp"] - harm
    if hero["hp"] < 0:
        hero["hp"] = 0
    play("hit")
    shake(8)
    say_and_wait("The " + monster["name"] + " hits you for " + str(harm) + ".")


@onUpdate
def each_frame():
    """The only thing that happens over time: waiting on a message."""
    global pause_left, doing, keep_turn

    if doing != "watching":
        return

    pause_left = pause_left - dt()
    if pause_left > 0:
        return

    # The message has had its moment.
    if battle_finished():
        return
    if keep_turn:
        doing = "choosing"      # it was only an explanation
        return
    next_turn()


# -------------------------------------------------------- 7. drawing it all

PANEL = 430          # where the bottom panel starts
INK = rgb(235, 235, 245)
DIM = rgb(150, 150, 170)
GOLD = rgb(240, 200, 90)
BOX = rgb(28, 26, 38)
EDGE = rgb(90, 88, 110)


def draw_box(x, y, w, h):
    drawRect(pos=vec2(x, y), width=w, height=h, color=BOX, radius=8,
             outline=2)
    drawRect(pos=vec2(x, y), width=w, height=h, color=EDGE, radius=8,
             outline=2, opacity=0.9)


def draw_bar(x, y, w, h, part, whole, shade):
    drawRect(pos=vec2(x, y), width=w, height=h, color=rgb(50, 48, 62),
             radius=3)
    if whole > 0 and part > 0:
        drawRect(pos=vec2(x, y), width=w * part / whole, height=h,
                 color=shade, radius=3)


@onDraw
def draw_everything():
    # The monsters, on the left.
    alive = living_monsters()
    for monster in monsters:
        if monster["hp"] <= 0:
            continue
        picked = (doing == "choosing" and menu == "target"
                  and cursor < len(alive) and alive[cursor] is monster)
        if picked:
            drawText(text=">", pos=vec2(monster["x"] - 34, monster["y"] - 40),
                     size=28, color=GOLD)
        drawSprite(sprite=monster["picture"], pos=vec2(monster["x"],
                                                       monster["y"]),
                   width=64, height=64, anchor="bot")
        drawText(text=monster["name"], pos=vec2(monster["x"], monster["y"] + 8),
                 size=16, color=DIM, anchor="top")
        draw_bar(monster["x"] - 32, monster["y"] + 30, 64, 6,
                 monster["hp"], monster["max_hp"], rgb(200, 70, 70))

    # The hero, on the right.
    drawSprite(sprite="knight", pos=vec2(hero["x"], hero["y"]),
               width=64, height=112, anchor="bot")

    # The bottom panel: a message line, the menu, and how you are doing.
    draw_box(20, PANEL, WIDE - 40, 54)
    drawText(text=message, pos=vec2(40, PANEL + 16), size=20, color=INK)

    draw_box(20, PANEL + 66, 380, 130)
    rows = menu_lines()
    row = 0
    while row < len(rows):
        picked = (doing == "choosing" and row == cursor)
        if picked:
            # A filled bar behind the row, not just a small arrow. At the size
            # this runs in a browser pane an arrow is a few pixels and easy to
            # miss -- which reads as "you cannot select anything".
            drawRect(pos=vec2(34, PANEL + 76 + row * 28), width=352,
                     height=26, color=rgb(64, 58, 32), radius=4)
            drawText(text=">", pos=vec2(42, PANEL + 80 + row * 28), size=20,
                     color=GOLD)
        drawText(text=rows[row], pos=vec2(66, PANEL + 80 + row * 28), size=20,
                 color=GOLD if picked else INK)
        row = row + 1

    # How to play, until the player has pressed something.
    if not pressed_anything:
        drawRect(pos=vec2(WIDE / 2, 150), width=540, height=46,
                 color=rgb(42, 38, 56), radius=8, anchor="center")
        drawText(text="Click this picture, then use  UP  DOWN  SPACE",
                 pos=vec2(WIDE / 2, 150), size=20, color=GOLD,
                 anchor="center")

    draw_box(WIDE - 320, PANEL + 66, 300, 130)
    drawText(text=hero["name"], pos=vec2(WIDE - 300, PANEL + 82), size=20,
             color=INK)
    drawText(text="HP  " + str(hero["hp"]) + " / " + str(hero["max_hp"]),
             pos=vec2(WIDE - 300, PANEL + 112), size=18, color=DIM)
    draw_bar(WIDE - 300, PANEL + 134, 260, 8, hero["hp"], hero["max_hp"],
             rgb(90, 200, 110))
    drawText(text="MP  " + str(hero["mp"]) + " / " + str(hero["max_mp"]),
             pos=vec2(WIDE - 300, PANEL + 150), size=18, color=DIM)
    draw_bar(WIDE - 300, PANEL + 172, 260, 8, hero["mp"], hero["max_mp"],
             rgb(90, 140, 220))


# ------------------------------------------------------------ 8. begin

build_order()
first = whose_turn()
if first is not None and not first["friend"]:
    monster_turn(first)
else:
    message = "A goblin, a skeleton and a chort block your way!"
