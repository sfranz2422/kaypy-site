"""Bomb Dodge -- bombs fall from the sky. Don't get hit.

    left and right arrows   move
    or hold the mouse (or a finger) where you want Bean to go

Every bomb that lands on the grass instead of on Bean is a point. The more
points you have, the faster the bombs fall and the more of them there are.
One hit and it is game over. Your best score is remembered.

HOW THIS FILE IS PUT TOGETHER

    1. the window, the pictures and the sound
    2. the settings
    3. how hard the game is
    4. the game scene: Bean, the bombs, points, getting hit
    5. start the game

This is the smallest game on the site, and a good one to start from. Swap
the bomb for an apple, make Bean faster, make the bombs bigger -- every
number is in the settings.
"""

from kaypy import *

# ----------------------------------------------------------------- 1. setup

kaypy(width=800, height=600, background=[121, 189, 220])

loadSprite("bean", "images/bean.png")
loadSprite("bomb", "images/bomb.png")
loadSound("boom", "sounds/small_boom.wav")


# -------------------------------------------------------------- 2. settings
#
# Everything you would want to change is here. Change one at a time and
# play it.

GROUND = 60            # how tall the strip of grass is
BEAN_SPEED = 420       # how fast Bean runs, in pixels per second

BOMB_SIZE = 0.5        # how big a bomb is: 1 is the whole picture
HIT_DISTANCE = 42      # how close a bomb has to get to Bean to hit it

FALL_START = 200       # how fast the bombs fall, to begin with
FALL_FASTEST = 520     # ...the fastest they ever fall
FALL_GAIN = 8          # ...and how much faster each point makes them

WAIT_START = 0.9       # seconds between bombs, to begin with
WAIT_SHORTEST = 0.3    # ...the shortest wait there ever is
WAIT_DROP = 0.015      # ...and how much shorter each point makes it

# The name the best score is saved under. Every game on a website shares
# the same storage, so the game's own name goes in it.
BEST_KEY = "bomb_dodge_best"


# -------------------------------------------------- 3. how hard the game is
#
# Each of these works out a number from the score. They get harder as the
# score goes up, and they stop somewhere, so the game ends up hard but never
# impossible.

score = 0


def fall_speed():
    speed = FALL_START + score * FALL_GAIN
    if speed > FALL_FASTEST:
        speed = FALL_FASTEST
    return speed


def bomb_wait():
    seconds = WAIT_START - score * WAIT_DROP
    if seconds < WAIT_SHORTEST:
        seconds = WAIT_SHORTEST
    return seconds


# ------------------------------------------------------- 4. the game scene
#
# These change while you play. A function that CHANGES one has to say
# `global` first, which means "the one up here, not a new one of my own".

alive = True


@scene("game")
def game():
    global score, alive

    # A new game, so everything starts again.
    score = 0
    alive = True
    best = getData(BEST_KEY, 0)

    # The grass. It is only a picture: nothing here uses area() or body(),
    # because the code below works out for itself what is touching what.
    add([rect(width(), GROUND), pos(0, height() - GROUND),
         color(96, 156, 76)])

    # anchor("bot") means pos() is where Bean's feet are, so Bean stands
    # on the grass. z(5) draws Bean in front of the bombs.
    bean = add([sprite("bean"), pos(width() / 2, height() - GROUND),
                anchor("bot"), z(5)])

    score_label = add([text("0", size=48), pos(width() / 2, 40),
                       anchor("center"), z(10)])
    best_label = add([text("best " + str(best), size=18), pos(12, 12),
                      opacity(0.75), z(10)])

    # width=560 wraps a long message onto more than one line.
    message = add([text("Arrow keys to move, or hold the mouse where you "
                        "want to go. Don't get hit!", size=26, width=560),
                   pos(width() / 2, height() / 2), anchor("center"), z(10)])

    # ------------------------------------------------------------ running
    #
    # onKeyDown runs its function every frame the key is held, so Bean
    # keeps running until you let go.

    @onKeyDown("left")
    def run_left():
        bean.move(-BEAN_SPEED, 0)
        keep_on_screen()

    @onKeyDown("right")
    def run_right():
        bean.move(BEAN_SPEED, 0)
        keep_on_screen()

    # Holding the mouse down -- or a finger, on a phone -- runs Bean
    # towards it. Within 10 pixels counts as there, and Bean stops.
    @onMouseDown
    def run_to_mouse():
        if mousePos().x < bean.pos.x - 10:
            bean.move(-BEAN_SPEED, 0)
        if mousePos().x > bean.pos.x + 10:
            bean.move(BEAN_SPEED, 0)
        keep_on_screen()

    def keep_on_screen():
        # 32 is half of Bean's width.
        bean.pos.x = clamp(bean.pos.x, 32, width() - 32)

    # --------------------------------------------------------------- bombs

    def drop_bomb():
        # Game over: no bomb, and no wait() for the next one either, so
        # the bombs stop here.
        if not alive:
            return

        # Somewhere along the top, just above the window so it falls in
        # rather than popping into view. rotate(0) lets it spin.
        x = rand(30, width() - 30)
        add([sprite("bomb"), pos(x, -40), anchor("center"),
             scale(BOMB_SIZE), rotate(0), "bomb"])

        # And the next one, a little later. No brackets after drop_bomb:
        # wait() is handed the function, to run when the time is up.
        wait(bomb_wait(), drop_bomb)

    # The first bomb, a second after the game starts.
    wait(1, drop_bomb)

    # Every bomb runs this, every frame.
    @onUpdate("bomb")
    def fall(bomb):
        global score

        if not alive:
            return

        bomb.move(0, fall_speed())
        bomb.angle = bomb.angle + 90 * dt()

        # Close enough to Bean to hit it? Bean's pos() is its feet, so
        # 27 pixels up -- half its height -- is the middle of Bean.
        middle = vec2(bean.pos.x, bean.pos.y - 27)
        if bomb.pos.dist(middle) < HIT_DISTANCE:
            hit(bomb)
            return

        # Reached the grass without hitting Bean? That is a point.
        if bomb.pos.y > height() - GROUND:
            bomb.destroy()
            score = score + 1
            score_label.text = str(score)
            if score == 1:
                message.text = ""

    # -------------------------------------------------------- getting hit

    def hit(bomb):
        global alive

        alive = False
        play("boom")
        shake(12)
        addKaboom(bomb.pos)

        # Bean goes, and so does every bomb still falling. Left where they
        # are, they hang in the air and cover up the message below.
        bean.destroy()
        destroyAll("bomb")

        if score > best:
            setData(BEST_KEY, score)
            best_label.text = "best " + str(score)

        if score == 1:
            message.text = "1 point -- press SPACE or click to play again"
        else:
            message.text = (str(score)
                            + " points -- press SPACE or click to play again")

    # Once the game is over, space or a click starts a new one.
    def again():
        if not alive:
            go("game")

    onKeyPress("space", again)
    onClick(again)


# ------------------------------------------------------- 5. start the game

go("game")
