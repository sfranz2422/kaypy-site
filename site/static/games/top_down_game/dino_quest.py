"""Dino Quest — a top-down adventure where the villagers ask the questions.

    Arrows or WASD   walk
    Z                swing the sword
    SPACE            talk to a villager you are standing next to
    ESCAPE           pause

Two villages, Oakhollow in the north-west and Stonebrook in the south-east,
a road between them, and monsters in the woods on either side. Every
villager has something to say and a question to ask. Answer it right and it
never comes back; answer it wrong and they will ask you again next time.

------------------------------------------------------------------ THE QUIZ

Paste your npoint URL into QUESTION_BANK_URL below.

The game opens by asking for a quiz code. LEAVE THE BOX EMPTY and it plays
the practice questions at the bottom of this settings block — so it is
playable right now, before any URL is set, and it still starts if the
network is down or somebody mistypes their code. Setting QUIZ_CODE skips
that question, which is what to do when a whole class gets the same quiz.

The bank is the same shape as the quiz script:

    {"98563": [["SA", "What is your name?"],
               ["MC", "Which keyword starts a loop", ["if","for","def"], 1]]}

    ["SA", question]                 typed answer, not marked — anything goes
    ["SA", question, answer]         typed answer, marked against `answer`
    ["MC", question, choices, n]     multiple choice, `n` counts from 0

--------------------------------------------------------- WHY IT IS BUILT SO

Two things in here are not obvious and are worth reading before changing:

  * ask() does NOT wait. It puts a panel up and calls you back later, so
    anything that should happen after an answer goes INSIDE the handler.
    Code written below an ask() runs immediately, while the question is
    still on screen.

  * Panels queue. Calling say(flavour) and then ask(question) in the same
    breath shows the flavour text first and the question after it, which is
    exactly the conversation we want and is why they are in that order.
    Marking a question works the same way: say("Correct.") from inside the
    handler puts that message up as soon as the question closes.

Runs in PyIDE, the kaypy playground, or next to an images/ and dungeon/
folder on the desktop.
"""
from kaypy import *
import json

# ============================================================== SETTINGS
#
# Everything worth arguing about is in this block.

QUESTION_BANK_URL = "https://api.npoint.io/fd7c9521c3cda98fa90a"     # <-- your npoint URL goes here
QUIZ_CODE = ""             # set one to skip the question and go straight in

PLAYER_SPEED = 260         # pixels per second
PLAYER_HEARTS = 5
SWORD_REACH = 34           # how far in front of you the blade appears
SWORD_TIME = 0.16          # how long it stays there
HURT_COOLDOWN = 0.9        # seconds of mercy after taking a hit

ENEMY_SIGHT = 300          # how close before a monster notices you
TALK_RANGE = 78            # how close before SPACE will talk to a villager

TILE = 48                  # the art is 16px, drawn at 3x

# Used when QUESTION_BANK_URL is blank, or the fetch fails. Same shape as
# the bank, so a lesson works before anybody has set a URL up.
PRACTICE_QUESTIONS = [
    ["SA", "Traveller! What do they call you?"],
    ["MC", "Which keyword starts a loop in Python?",
     ["if", "for", "def"], 1],
    ["MC", "What does len([3, 5, 7]) give you?", ["2", "3", "7"], 1],
    ["SA", "What symbol starts a comment in Python?", "#"],
    ["MC", "Which one is a list?",
     ["(1, 2, 3)", "[1, 2, 3]", "{1, 2, 3}"], 1],
    ["MC", "How many times does 'for i in range(4)' repeat?",
     ["3", "4", "5"], 1],
]

# ============================================================== THE ENGINE

kaypy(width=960, height=640, background=[58, 104, 62])   # grass green
setGravity(0)                                            # top-down: no down

# ---------------------------------------------------------------- the art
#
# The dino is nine separate files rather than one strip, so it is loaded as a
# list of frames. The layout matches the dungeon characters: 0-3 standing
# about, 4-7 walking, 8 the hurt pose.
# EVERY PATH IS WRITTEN OUT IN FULL, ON PURPOSE.
#
# In the browser there is no folder to read. PyIDE and the playground scan
# your source for things that look like asset paths and fetch just those into
# the runtime's filesystem before the program starts — 200 sprites is about
# 5MB and nobody's game uses all of them.
#
# That scan reads STRING LITERALS. The first version of this file built the
# paths instead:
#
#     loadSprite("dino", ["images/dino_%d.png" % i for i in range(9)])
#     loadSprite(name, "dungeon/%s.png" % name)
#
# which is nicer Python and fetched exactly nothing: the literal in the file
# is "images/dino_%d.png", and no such picture exists. It ran perfectly on a
# desktop, where the folder is really there, and died in the editor on the
# first sprite. So loops are fine, but the paths inside them have to be
# whole.
IDLE = {"idle": {"from": 0, "to": 3, "speed": 8, "loop": True}}
IDLE_RUN = {"idle": {"from": 0, "to": 3, "speed": 8, "loop": True},
            "run": {"from": 4, "to": 7, "speed": 10, "loop": True}}

loadSprite("dino", ["images/dino_0.png", "images/dino_1.png",
                    "images/dino_2.png", "images/dino_3.png",
                    "images/dino_4.png", "images/dino_5.png",
                    "images/dino_6.png", "images/dino_7.png",
                    "images/dino_8.png"], anims={
    "idle": {"from": 0, "to": 3, "speed": 8, "loop": True},
    "run": {"from": 4, "to": 7, "speed": 10, "loop": True},
    "hit": {"from": 8, "to": 8, "speed": 1, "loop": False},
})

# Villagers: nine frames each, except the necromancer, who only stands.
loadSprite("dwarf_m", "dungeon/dwarf_m.png", sliceX=9, anims=IDLE_RUN)
loadSprite("elf_f", "dungeon/elf_f.png", sliceX=9, anims=IDLE_RUN)
loadSprite("knight_f", "dungeon/knight_f.png", sliceX=9, anims=IDLE_RUN)
loadSprite("necromancer", "dungeon/necromancer.png", sliceX=4, anims=IDLE)

# Monsters. The slug has an idle and nothing else — see ENEMY_KINDS.
loadSprite("skelet", "dungeon/skelet.png", sliceX=8, anims=IDLE_RUN)
loadSprite("goblin", "dungeon/goblin.png", sliceX=8, anims=IDLE_RUN)
loadSprite("imp", "dungeon/imp.png", sliceX=8, anims=IDLE_RUN)
loadSprite("slug", "dungeon/slug.png", sliceX=4, anims=IDLE)

# Scenery and the HUD.
loadSprite("floor_1", "dungeon/floor_1.png")
loadSprite("floor_2", "dungeon/floor_2.png")
loadSprite("wall_mid", "dungeon/wall_mid.png")
loadSprite("column", "dungeon/column.png")
loadSprite("crate", "dungeon/crate.png")
loadSprite("doors_leaf_closed", "dungeon/doors_leaf_closed.png")
loadSprite("wall_fountain_mid_blue", "dungeon/wall_fountain_mid_blue.png")
loadSprite("ui_heart_full", "dungeon/ui_heart_full.png")
loadSprite("ui_heart_empty", "dungeon/ui_heart_empty.png")
loadSprite("weapon_regular_sword", "dungeon/weapon_regular_sword.png")

# ================================================================ THE MAP
#
# One character per tile. Drawn once at startup and then never touched.
#
#   '#' wall   '.' village floor   ',' road   ' ' grass   'C' crate
#
#   'T' standing stone — the dungeon pack has no trees, so the woods are
#       made of old pillars. They look like what they are, which is better
#       than calling a column an oak and hoping nobody looks.
#
#   'D' door, 'F' fountain — and the lower-case 'd' and 'f' beside them are
#       the rest of the same picture. A door is two tiles wide and a
#       fountain three, so the map has to give them the room; see PROP.
LAYOUT = [
    "############################################",
    "#                                          #",
    "#                                          #",
    "#  ##############                       T  #",
    "#  #......T.....#                T         #",
    "#  #.####..####.#                   T      #",
    "#  #.#Dd#..#Dd#.#         T                #",
    "#  #............,,,,,,,,,                  #",
    "#  #............#       ,,,,,,,,,,         #",
    "#  #.Fff........#       ,       ,,     T   #",
    "#  #............#       ,       ,,         #",
    "#  #..C.........#       ,    T  ,,         #",
    "#  ######,,######       ,       ,,         #",
    "#                       ,       ,,   T     #",
    "#                       ,       ,,         #",
    "#                       ,       ,,         #",
    "#           T           ,       ,,         #",
    "#     T            T    , ######,,#######  #",
    "#                       , #.............#  #",
    "#        T              , #.####.....T..#  #",
    "#  T                    , #.#Dd#........#T #",
    "#             T         ,,,.............#  #",
    "#                         #........####.#  #",
    "#       T                 #........#Dd#.#  #",
    "#                T        #.............#  #",
    "#          T          T   #.Fff...C.....#  #",
    "#    T              T     ###############  #",
    "#                                          #",
    "#                                          #",
    "############################################",
]

SOLID = "#TFfCDd"                    # characters you cannot walk through
WORLD_W = len(LAYOUT[0]) * TILE
WORLD_H = len(LAYOUT) * TILE

# ---- the picture -------------------------------------------------------
#
# Scenery only: no area(), no body(). Collision is handled separately, by
# the blocks built below, because every object with an area() is checked
# against every other one every frame. Six hundred wall tiles would be a
# hundred and eighty thousand checks a frame, and the game would crawl.
GROUND = {".": "floor_1", ",": "floor_2"}

# NOT EVERY PICTURE IS ONE TILE.
#
# The art is 16px and a tile is 16px at 3x, so most of it drops straight in.
# Four of these do not, and putting them in a one-tile slot was wrong in two
# different ways at once:
#
#   doors_leaf_closed  32x32 -> 2 tiles wide and 2 tall
#   wall_fountain      48x16 -> 3 tiles wide
#   column             16x48 -> 3 tiles TALL
#   crate              16x24 -> one and a half tiles tall
#
# The door was the visible one: drawn from its tile's top-left it covered
# the tile to its right, and that wall tile — added afterwards, at the same
# z — painted straight back over the door's top-right quarter. It looked
# like a corner of the door was missing. It was not missing; it was
# underneath. Two fountains written side by side were worse: six tiles of
# water in two tiles of map, the second drawn over the first.
#
# So a prop declares how many tiles it takes, the map gives it that many,
# and anything taller than its tile is anchored at the BOTTOM so it rises
# out of its square the way a pillar or a doorway does — rather than
# hanging down over the ground in front of it.
#
#   (sprite, tiles wide, tiles tall)
PROP = {
    "#": ("wall_mid", 1, 1),
    "T": ("column", 1, 3),
    "C": ("crate", 1, 1.5),
    "D": ("doors_leaf_closed", 2, 2),
    "F": ("wall_fountain_mid_blue", 3, 1),
}
# The tiles a multi-tile prop spills onto. They are solid, and they draw
# nothing — the prop itself already covers them.
COVERED = "df"

ground_tiles = {}
for ch, art in GROUND.items():
    ground_tiles[ch] = (lambda a: (lambda: [sprite(a), scale(3), z(0)]))(art)

addLevel(LAYOUT, {"tileWidth": TILE, "tileHeight": TILE,
                  "tiles": ground_tiles})

# The props are placed here rather than through addLevel, because they need
# a pos() of their own and addLevel supplies one — a second pos() in the
# component list REPLACES the level's, which would stack every prop in the
# game at the same spot.
for row, line in enumerate(LAYOUT):
    for col, ch in enumerate(line):
        if ch == "#":
            # The backdrop everything else stands against, so it goes under.
            add([sprite("wall_mid"), pos(col * TILE, row * TILE),
                 scale(3), z(1)])
        elif ch in PROP:
            art, wide, tall = PROP[ch]
            # anchor("bot") makes the sprite's pos its own bottom-centre, so
            # this puts that at the bottom-centre of the prop's footprint. A
            # three-tall column stands in its tile and rises two above it.
            add([sprite(art),
                 pos(col * TILE + wide * TILE / 2, (row + 1) * TILE),
                 anchor("bot"), scale(3), z(2)])
        # COVERED characters draw nothing: the prop beside them already did.


# ---- the walls you actually bump into -----------------------------------

def solid_blocks(layout):
    """The solid tiles, gathered into as few rectangles as possible.

    Greedy: take the first solid tile nobody has claimed, run right while
    the row stays solid, then run down while that whole width stays solid,
    and claim the lot. A village wall turns into a handful of long blocks
    instead of ninety separate ones.

    This matters more than it looks. Collision is checked pair by pair
    between everything that has an area(), so the cost is the SQUARE of how
    many there are. Ninety wall tiles and ten monsters is not ten per cent
    worse than nine walls and ten monsters, it is about seventeen times
    worse, and it shows up as a game that is fine on a laptop and unplayable
    on a school Chromebook.
    """
    rows, cols = len(layout), len(layout[0])
    taken = [[False] * cols for _ in range(rows)]
    blocks = []

    for r in range(rows):
        for c in range(cols):
            if taken[r][c] or layout[r][c] not in SOLID:
                continue

            wide = 0
            while (c + wide < cols
                   and not taken[r][c + wide]
                   and layout[r][c + wide] in SOLID):
                wide += 1

            tall = 1
            while r + tall < rows:
                row = layout[r + tall]
                if all(row[c + i] in SOLID and not taken[r + tall][c + i]
                       for i in range(wide)):
                    tall += 1
                else:
                    break

            for rr in range(r, r + tall):
                for cc in range(c, c + wide):
                    taken[rr][cc] = True
            blocks.append((c, r, wide, tall))

    return blocks


for bx, by, bw, bh in solid_blocks(LAYOUT):
    add([rect(bw * TILE, bh * TILE), pos(bx * TILE, by * TILE),
         opacity(0), area(), body(isStatic=True), "wall"])


def tile_pos(col, row):
    """The middle of a tile, which is where a character stands."""
    return vec2(col * TILE + TILE / 2, row * TILE + TILE / 2)




# ============================================================== THE PLAYER
#
# The thing that moves and collides is a plain 34x34 box; the dino is a
# CHILD of it, drawn on top. Giving the sprite the area() instead would make
# the collider 48x78 — the dino is tall — and a character nearly two tiles
# high catches on doorways it is plainly walking through.
player = add([rect(34, 34), pos(tile_pos(9, 10)), anchor("center"),
              opacity(0), area(), body(), health(PLAYER_HEARTS), z(5),
              "player"])
dino = player.add([sprite("dino", anim="idle"), pos(0, 8), anchor("bot"),
                   scale(3)])

player.facing_value = vec2(0, 1)     # which way the sword will go
player.hurt_at_value = -99.0
player.answered_value = 0


def face_of(dx, dy):
    if dx or dy:
        return vec2(dx, dy).unit()
    return player.facing_value


@onUpdate
def walk():
    # No isShowing() check here, and none in the monster below.
    #
    # A panel pauses the engine, and onUpdate handlers do not run while it
    # is paused — so the world already stops on its own. A guard here reads
    # as the thing holding the game still, and it is not; deleting it
    # changes nothing at all, which is how it was found.
    #
    # KEY handlers are the opposite: those still fire while paused, on
    # purpose, so that a pause menu can hear the key that closes it. That
    # is why swing() and talk() DO check isShowing(), and why they must.
    if over[0]:
        return

    dx = dy = 0
    if isKeyDown("left") or isKeyDown("a"):
        dx -= 1
    if isKeyDown("right") or isKeyDown("d"):
        dx += 1
    if isKeyDown("up") or isKeyDown("w"):
        dy -= 1
    if isKeyDown("down") or isKeyDown("s"):
        dy += 1

    if dx or dy:
        step = vec2(dx, dy).unit() * PLAYER_SPEED   # diagonals are not faster
        player.move(step.x, step.y)
        player.facing_value = face_of(dx, dy)
        if dx:
            dino.flipX = dx < 0
        if dino.curAnim() != "run":
            dino.play("run")
    elif dino.curAnim() != "idle":
        dino.play("idle")


# ---- the camera ---------------------------------------------------------
#
# CAM_SCALE zooms in: at 1.5 the art is half again as big and you see less
# of the world at once, which suits 16px pixel art on a projector.
#
# The function is setCamScale, not setCameraScale — there is no
# setCameraScale, and calling it is a NameError before the first frame.
CAM_SCALE = 1.5
setCamScale(CAM_SCALE)


@onUpdate
def follow_player():
    # HOW MUCH WORLD FITS ON SCREEN CHANGES WITH THE ZOOM.
    #
    # The clamp stops the camera before it shows past the edge of the map,
    # and what it has to clamp to is half the VISIBLE world, not half the
    # window. Zoomed to 1.5 the window shows 960/1.5 = 640 world pixels
    # across, so the margin is 320 and not 480. Using the window's own half
    # width holds the camera 160px too far in: the player can walk into a
    # strip along each edge that the camera refuses to follow them into, and
    # eventually off the side of the screen entirely.
    half_w = width() / (2 * CAM_SCALE)
    half_h = height() / (2 * CAM_SCALE)
    setCamPos(vec2(clamp(player.pos.x, half_w, WORLD_W - half_w),
                   clamp(player.pos.y, half_h, WORLD_H - half_h)))


# ================================================================ THE SWORD

@onKeyPress("z")
def swing():
    if isShowing() or get("blade"):
        return

    d = player.facing_value
    # The sword art points up, so the angle is measured from there.
    angle = {(0, -1): 0, (1, 0): 90, (0, 1): 180, (-1, 0): 270}.get(
        (round(d.x), round(d.y)), 0)

    add([sprite("weapon_regular_sword"),
         pos(player.pos + d * SWORD_REACH), anchor("center"),
         scale(2.5), rotate(angle), area(), lifespan(SWORD_TIME),
         z(6), "blade"])


@onCollide("blade", "enemy")
def sword_hits(blade, enemy):
    enemy.hurt(1)
    shake(4)
    # A shove away from the player, so a monster cannot stand inside you
    # while you both take turns doing damage.
    away = (enemy.pos - player.pos).unit()
    enemy.pos = enemy.pos + away * 18
    flash(enemy.pos, "!", YELLOW)


# ============================================================== THE MONSTERS

ENEMY_KINDS = [
    # sprite      hp  speed  scale  has a walking animation?
    ("slug",       2,   55,   2.5,  False),   # slugs only have an idle
    ("skelet",     3,  105,   2.5,  True),
    ("goblin",     2,  120,   2.5,  True),
    ("imp",        3,  135,   2.5,  True),
]

# Spawn points, in tiles: the woods on either side of the road.
ENEMY_SPOTS = [(7, 18), (10, 21), (14, 24), (19, 26), (8, 26),
               (30, 5), (35, 8), (38, 12), (27, 9), (40, 16),
               (21, 15), (28, 24)]


def spawn_enemy(col, row, kind):
    art, hp, speed, size, can_run = kind
    e = add([sprite(art, anim="idle"), pos(tile_pos(col, row)),
             anchor("center"), scale(size), area(), health(hp), z(4),
             "enemy"])
    e.speed_value = speed
    e.home_value = tile_pos(col, row)
    # Asked for an animation it has not got, play() raises a KeyError from a
    # line that looks perfectly reasonable — and only once a slug happens to
    # see you, which in a big map can be minutes in.
    e.can_run_value = can_run

    @e.onDeath
    def died():
        flash(e.pos, "+1", GREEN)
        e.destroy()

    return e


for i, (col, row) in enumerate(ENEMY_SPOTS):
    spawn_enemy(col, row, ENEMY_KINDS[i % len(ENEMY_KINDS)])


@onUpdate("enemy")
def monster_thinks(e):
    to_player = player.pos - e.pos
    if to_player.len() < ENEMY_SIGHT:
        step = to_player.unit() * e.speed_value
        e.move(step.x, step.y)
        if e.can_run_value and e.curAnim() != "run":
            e.play("run")
        e.flipX = step.x < 0
    else:
        # Drift home, so a monster chased across the map comes back.
        home = e.home_value - e.pos
        if home.len() > 12:
            step = home.unit() * (e.speed_value * 0.35)
            e.move(step.x, step.y)
        elif e.can_run_value and e.curAnim() != "idle":
            e.play("idle")


@onCollide("player", "enemy")
def monster_hits(p, e):
    take_a_hit()


@player.onCollideUpdate("enemy")
def monster_keeps_hitting(e):
    take_a_hit()


def take_a_hit():
    if isShowing() or time() - player.hurt_at_value < HURT_COOLDOWN:
        return
    player.hurt_at_value = time()
    player.hurt(1)
    shake(8)
    dino.play("hit")
    wait(0.35, lambda: dino.play("idle") if player.exists() else None)


over = [False]


@player.onDeath
def died():
    # NOT pause(). It used to be say(...) followed by wait(0.1, pause) — and
    # a paused game has dt of zero, so the timer only ran once the message
    # was dismissed and the game resumed. A tenth of a second later it
    # paused again, with nothing on screen, and the game simply stopped
    # answering the keyboard. "It froze and I could not move" is the only
    # thing a player can say about that, and it is the hardest possible
    # thing to tell apart from a bug in the map.
    #
    # So death is a flag the rest of the game reads, and the screen says so.
    over[0] = True
    say("The dino falls. Press Run to try again.")


# ============================================================== THE QUESTIONS
#
# `pool` is what is left to ask. A right answer takes a question OUT of it,
# so it never comes round again; a wrong answer leaves it in, so it does.

pool = []
asked_now = [None]     # the question on screen, if any


def load_questions():
    """The first thing the game does: ask which quiz to play.

    Leave the box empty and it plays the practice questions, so the game
    always starts — no URL, no code, no internet, still a game. Setting
    QUIZ_CODE above skips this question, which is what to do when handing
    the same quiz to a whole class.
    """
    if QUIZ_CODE:
        use_code(QUIZ_CODE)
        return
    ask_for_code()


def ask_for_code():
    @ask("Quiz code? Leave it empty for the practice questions.",
         placeholder="")
    def got(code):
        use_code((code or "").strip())


def use_code(code):
    """Start the quiz with that code, or fall back and say why.

    Every way this can go wrong ends in a playable game with a line of
    explanation, never in a stopped one. A class of thirty will produce a
    typo, a blocked network and an empty box within the first minute, and
    none of those is a reason for somebody to sit looking at nothing.
    """
    if not code:
        use_practice()
        return

    if not QUESTION_BANK_URL:
        use_practice("There is no question bank set up in this file — put "
                     "your npoint URL in QUESTION_BANK_URL at the top. "
                     "These are the practice questions.")
        return

    bank = fetch_bank()
    if bank is None:
        use_practice("Could not reach the question bank, so these are the "
                     "practice questions.")
        return

    found = bank.get(code)
    if found:
        pool.extend(found)
        begin()
    else:
        # Queued behind the message, so they read it and then get another go.
        say("No quiz has the code %s. Have another try, or leave it empty "
            "for the practice questions." % code)
        ask_for_code()


def fresh_url(url):
    """The same address with something different on the end each time.

    NPOINT IS CACHED, AND THE CACHE IS NOT IN YOUR BROWSER.

    Add questions to a bin, save it, and the plain URL keeps serving the old
    copy for a while — proved on this very bin, at one moment, two requests
    apart:

        .../fd7c9521c3cda98fa90a              ->  2 questions
        .../fd7c9521c3cda98fa90a?nocache=123  -> 10 questions

    So a hard refresh does nothing: the stale copy is upstream, not in the
    page. A parameter nobody reads makes it a different address to the
    cache, and the bin itself ignores it.

    This matters for a lesson more than it looks. A teacher adds questions
    during first period, the class gets yesterday's quiz, and everything on
    both ends is working perfectly.
    """
    joiner = "&" if "?" in url else "?"
    return "%s%sfresh=%d" % (url, joiner, randi(1, 2000000000))


def read_url(url):
    """The text at that address, in a browser or on a desktop.

    NOT `requests`. This used to be requests.get(...), which worked
    perfectly in PyIDE and died the moment the game was exported to a page
    of its own:

        ModuleNotFoundError: No module named 'requests'

    PyIDE installs requests itself, from wheels it keeps for the purpose.
    An exported game is one HTML file and whatever Pyodide brings with it,
    and requests is not in that — Pyodide can fetch it, but only with an
    `await`, and there is nowhere to await inside an answer handler.

    `pyodide.http.open_url` is already there, needs no install, and is
    synchronous, which is the part that matters. Checked in the deployed
    page's own Pyodide (314.0.6), where it fetched the real bank.

    On a desktop there is no pyodide, and urllib is in the standard
    library. Between the two there is nothing left to install anywhere,
    which also means PyIDE no longer downloads the requests wheels to run
    this game at all.
    """
    try:
        from pyodide.http import open_url        # a browser
    except ImportError:
        from urllib.request import urlopen       # a desktop
        with urlopen(url, timeout=10) as page:
            return page.read().decode("utf-8")
    return open_url(url).read()


def fetch_bank():
    """The bank as a dict, or None if it could not be had.

    Never raises. A school network that blocks npoint, a URL with a typo in
    it and a bank that is valid JSON but not a dict all arrive here, and all
    three mean the same thing to the game: play the practice questions.
    """
    try:
        bank = json.loads(read_url(fresh_url(QUESTION_BANK_URL)))
    except Exception:                                      # noqa: BLE001
        return None
    return bank if isinstance(bank, dict) else None


def use_practice(note=""):
    pool.extend(PRACTICE_QUESTIONS)
    if note:
        say(note)
    begin()


def begin():
    say("Two villages, and everyone has a question. Arrows to walk, Z for "
        "your sword, SPACE to talk.")


def pick_question():
    """One of the questions still unanswered, or None when they are done."""
    if not pool:
        return None
    return choose(pool)


def put_question(q, villager):
    """Ask it, and deal with the answer when it arrives — INSIDE the
    handler, because ask() has already returned by the time it is answered.
    """
    kind = q[0]

    if kind == "SA" and len(q) < 3:
        # No answer given in the bank, so there is nothing to mark. Asking
        # somebody their name is still worth doing.
        @ask(q[1])
        def told(reply):
            asked_now[0] = None
            pool.remove(q) if q in pool else None
            flash(player.pos, "Well met, %s!" % (reply or "traveller"), WHITE)
        return

    if kind == "SA":
        @ask(q[1], answer=q[2])
        def typed(correct):
            grade(q, correct, villager)
        return

    @ask(q[1], q[2], answer=q[3])
    def picked(correct):
        grade(q, correct, villager)


def grade(q, correct, villager):
    asked_now[0] = None

    if correct:
        if q in pool:
            pool.remove(q)
        player.answered_value += 1
        player.heal(1)
        # A panel rather than a floating word: being marked is the point of
        # the exercise, and it should stop the game the way the question
        # did. This is queued behind nothing — finish() has already closed
        # the question — so it comes straight up.
        say("Correct. %s looks pleased." % villager.who_value)
        if not pool:
            say("That was the last question either village had. "
                "Go and enjoy the quiet.")
    else:
        say("Not quite. %s will ask you that one again."
            % villager.who_value)
        villager.repeat_value = q      # this one comes back


# ============================================================== THE VILLAGERS

# (tile col, row, sprite, name, the lines they work through)
PEOPLE = [
    (6, 7, "dwarf_m", "Bran the Smith", [
        "Oakhollow has stood here four hundred years, and the well has "
        "never once run dry.",
        "The road east is safe by day. By night, less so.",
        "My father forged that sword you carry. Mind the edge.",
    ]),
    (13, 10, "elf_f", "Ysolde", [
        "You came up the south road? Then you saw the stones. They were "
        "a road, once.",
        "Stonebrook and Oakhollow have not spoken in a year. Nobody "
        "remembers why.",
        "Take the east gate. The fountain marks the turning.",
    ]),
    (31, 21, "knight_f", "Captain Mira", [
        "Stonebrook keeps its gate shut and its questions sharp.",
        "Four of my guard went up among the stones. Two came back.",
        "Answer enough of these and I will call you one of ours.",
    ]),
    (37, 24, "necromancer", "Old Pell", [
        "They call me a necromancer. I keep bees.",
        "Every answer you get right is one the road will not ask you again.",
        "The monsters are not from here. Something let them in.",
    ]),
]

for col, row, art, name, lines in PEOPLE:
    npc = add([sprite(art, anim="idle"), pos(tile_pos(col, row)),
               anchor("center"), scale(2.5), z(4), "villager"])
    npc.who_value = name
    npc.lines_value = list(lines)
    npc.repeat_value = None


def nearest_villager():
    best, best_d = None, TALK_RANGE
    for npc in get("villager"):
        d = (npc.pos - player.pos).len()
        if d < best_d:
            best, best_d = npc, d
    return best


@onKeyPress("space")
def talk():
    if isShowing():
        return
    npc = nearest_villager()
    if npc is None:
        return

    # The line first, then the question. Both go on the queue, so the
    # villager speaks and the question follows once you have read it.
    if npc.lines_value:
        say("%s: %s" % (npc.who_value, npc.lines_value.pop(0)))
    else:
        say("%s has nothing new to say." % npc.who_value)

    q = npc.repeat_value or pick_question()
    npc.repeat_value = None
    if q is None:
        say("And no more questions for you.")
        return

    asked_now[0] = q
    put_question(q, npc)


# ==================================================================== THE HUD

hearts = []
for i in range(PLAYER_HEARTS):
    hearts.append(add([sprite("ui_heart_full"), pos(16 + i * 40, 16),
                       scale(2.5), fixed(), z(50)]))

tally = add([text("", size=22), pos(16, 56), fixed(), z(50)])
hint = add([text("", size=20), pos(16, height() - 34), fixed(), z(50)])


@onUpdate
def paint_hud():
    for i, h in enumerate(hearts):
        h.use(sprite("ui_heart_full" if i < player.hp else "ui_heart_empty"))

    tally.text = "Answered: %d      Left: %d" % (
        player.answered_value, len(pool))

    npc = nearest_villager()
    hint.text = ("SPACE — talk to %s" % npc.who_value) if npc else ""


def flash(where, message, colour):
    """A word that appears in the world and fades, for things that do not
    deserve a panel — a hit landing, an answer marked."""
    add([text(message, size=22), pos(where.x, where.y - 46),
         anchor("center"), color(colour), lifespan(1.0), z(60)])


@onKeyPress("escape")
def toggle_pause():
    if isShowing():
        return
    resume() if isPaused() else pause()


# ------------------------------------------------- say why nothing is moving
#
# A PAUSED GAME AND A BROKEN ONE LOOK EXACTLY THE SAME.
#
# Both sit there and ignore the keyboard. That is a miserable thing to hand a
# class: the only report anybody can make is "it froze", which is also what
# an actual bug looks like, so every pause gets debugged as a crash.
#
# onDraw handlers run while the game is paused — that is how the panel gets
# drawn — so this is the one thing that can still speak up. Three states, and
# the screen now names which one it is in.
@onDraw
def why_nothing_moves():
    if isShowing():
        return                      # the panel is its own explanation

    if over[0]:
        drawText("The dino has fallen. Press Run to start again.",
                 pos=vec2(width() / 2, height() / 2), size=28,
                 color=RED, anchor="center", fixed=True)
    elif isPaused():
        drawText("Paused — press Escape to carry on",
                 pos=vec2(width() / 2, height() / 2), size=28,
                 color=WHITE, anchor="center", fixed=True)


load_questions()
