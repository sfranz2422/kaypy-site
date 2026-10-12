"""Spiral Storm -- the Gazer fills the sky with bullets. Don't get hit.

    arrow keys              move
    or hold the mouse (or a finger) where you want Bean to go

Every second you last is a point. The longer you last, the more the Gazer
throws at you: first shots aimed straight at Bean, then rings of bullets,
then a spiral that never stops turning. One hit and it is game over. Your
best score is remembered.

HOW THIS FILE IS PUT TOGETHER

    1. the window, the pictures and the sounds
    2. the settings
    3. how hard the game is
    4. the game scene: zooming out, Bean, the Gazer, the bullets
    5. start the game

Every bullet is a game object with move() on it, which sends it off in a
straight line by itself. All the Gazer has to do is say which way.
Vec2.fromAngle(angle) turns an angle into a direction: 0 is right, 90 is
down, 180 is left, 270 is up. A ring is a for loop over the angles, and a
spiral is one angle that keeps turning. After this, try Pong.
"""

from kaypy import *

# ----------------------------------------------------------------- 1. setup

kaypy(width=800, height=600, background=[24, 18, 40])

loadSprite("bean", "images/bean.png")
loadSprite("gazer", "images/gazer.png")
loadSound("shoot", "sounds/small_beep.wav")
loadSound("boom", "sounds/small_boom.wav")


# -------------------------------------------------------------- 2. settings
#
# Everything you would want to change is here. Change one at a time and
# play it.

# How far the camera is zoomed out. 1 is normal; 0.7 shows more of the
# world, so everything looks smaller and there is more room to dodge.
ZOOM = 0.7

BEAN_SPEED = 360       # how fast Bean moves, in pixels per second

# How close a bullet's middle has to get to Bean's middle to hit. Bean is
# 64 pixels wide, so this is a lot smaller than Bean, on purpose: a bullet
# that only clips the edge of Bean misses, and you can squeeze through gaps
# that look too small.
HIT_DISTANCE = 16

BULLET_SIZE = 9        # how big a bullet is (its radius)
SPEED_START = 130      # how fast bullets fly, to begin with
SPEED_FASTEST = 200    # ...the fastest they ever fly
SPEED_GAIN = 1         # ...and how much faster each point makes them

AIM_WAIT = 0.7         # seconds between shots aimed straight at Bean

RING_FROM = 8          # the score the rings start at
RING_GAP = 15          # degrees between the bullets in a ring
RING_WAIT_START = 2.5  # seconds between rings, to begin with
RING_WAIT_SHORTEST = 2 # ...the shortest wait there ever is
RING_WAIT_DROP = 0.02  # ...and how much shorter each point makes it

SPIRAL_FROM = 20       # the score the spiral starts at
SPIRAL_ARMS = 4        # how many arms the spiral has
SPIRAL_WAIT = 0.25     # seconds between one turn of the spiral and the next
SPIRAL_TURN = 11       # how many degrees it turns each time

# The name the best score is saved under. Every game on a website shares
# the same storage, so the game's own name goes in it.
BEST_KEY = "spiral_storm_best"


# -------------------------------------------------- 3. how hard the game is
#
# Each of these works out a number from the score. They get harder as the
# score goes up, and they stop somewhere, so the game ends up hard but never
# impossible.

score = 0


def bullet_speed():
    speed = SPEED_START + score * SPEED_GAIN
    if speed > SPEED_FASTEST:
        speed = SPEED_FASTEST
    return speed


def ring_wait():
    seconds = RING_WAIT_START - score * RING_WAIT_DROP
    if seconds < RING_WAIT_SHORTEST:
        seconds = RING_WAIT_SHORTEST
    return seconds


# ------------------------------------------------------- 4. the game scene
#
# These change while you play. A function that CHANGES one has to say
# `global` first, which means "the one up here, not a new one of my own".

alive = True
spiral_angle = 0


@scene("game")
def game():
    global score, alive, spiral_angle

    # A new game, so everything starts again.
    score = 0
    alive = True
    spiral_angle = 0
    best = getData(BEST_KEY, 0)

    # ----------------------------------------------------- zooming out
    #
    # The camera shows the world at ZOOM times its size, so the window
    # now holds a bigger piece of the world: arena_w by arena_h, which is
    # 1143 by 857 when ZOOM is 0.7. Point the camera at the middle of that
    # and the arena runs from (0, 0) to (arena_w, arena_h), the way the
    # window did before. go() puts the camera back to normal, which is why
    # this is in the scene.
    arena_w = width() / ZOOM
    arena_h = height() / ZOOM
    setCamScale(ZOOM)
    setCamPos(vec2(arena_w / 2, arena_h / 2))

    # The Gazer, along the top. anchor("center") means pos() is the middle.
    gazer = add([sprite("gazer"), pos(arena_w / 2, 110), anchor("center"),
                 z(5)])

    bean = add([sprite("bean"), pos(arena_w / 2, arena_h - 100),
                anchor("center"), z(5)])

    # fixed() keeps the writing where it is on the screen, at its normal
    # size, whatever the camera does. So these positions are in the window,
    # not the arena.
    score_label = add([text("0", size=48), pos(width() / 2, 40),
                       anchor("center"), fixed(), z(10)])
    best_label = add([text("best " + str(best), size=18), pos(12, 12),
                      opacity(0.75), fixed(), z(10)])

    # width=560 wraps a long message onto more than one line.
    message = add([text("Arrow keys to move, or hold the mouse where you "
                        "want to go. Don't get hit!", size=26, width=560),
                   pos(width() / 2, height() / 2), anchor("center"),
                   fixed(), z(10)])

    # ------------------------------------------------------------ moving

    @onKeyDown("left")
    def go_left():
        bean.move(-BEAN_SPEED, 0)
        keep_on_screen()

    @onKeyDown("right")
    def go_right():
        bean.move(BEAN_SPEED, 0)
        keep_on_screen()

    @onKeyDown("up")
    def go_up():
        bean.move(0, -BEAN_SPEED)
        keep_on_screen()

    @onKeyDown("down")
    def go_down():
        bean.move(0, BEAN_SPEED)
        keep_on_screen()

    # Holding the mouse down -- or a finger, on a phone -- moves Bean
    # towards it. mousePos() is where the mouse is in the WINDOW; with the
    # camera zoomed out, toWorld() turns that into where it is in the arena.
    @onMouseDown
    def go_to_mouse():
        bean.moveTo(toWorld(mousePos()), BEAN_SPEED)
        keep_on_screen()

    def keep_on_screen():
        # 32 and 27 are half of Bean's width and height.
        bean.pos.x = clamp(bean.pos.x, 32, arena_w - 32)
        bean.pos.y = clamp(bean.pos.y, 27, arena_h - 27)

    # ------------------------------------------------------------- the Gazer
    #
    # It swings from side to side. wave() goes smoothly back and forth
    # between the two numbers as time() goes up.

    @onUpdate
    def swing():
        if alive:
            gazer.pos.x = wave(150, arena_w - 150, time() * 0.6)

    # ------------------------------------------------------------ bullets
    #
    # One bullet, from the Gazer, flying in `direction`. move() keeps it
    # going by itself; it only needs to be told which way and how fast.
    # Each kind of shot has its own colour, so you can tell them apart.

    def shoot(direction, colour):
        add([circle(BULLET_SIZE), color(colour), pos(gazer.pos),
             anchor("center"), move(direction, bullet_speed()), "bullet"])

    # A shot aimed straight at Bean. Bean's position take away the Gazer's
    # is the way from the Gazer to Bean.
    def aim():
        if not alive:
            return
        shoot(bean.pos - gazer.pos, YELLOW)
        wait(AIM_WAIT, aim)

    # A ring: one bullet every RING_GAP degrees, all the way round.
    def ring():
        if not alive:
            return
        if score >= RING_FROM:
            for angle in range(0, 360, RING_GAP):
                shoot(Vec2.fromAngle(angle), MAGENTA)
            play("shoot")
        wait(ring_wait(), ring)

    # A spiral: a bullet for each arm, spread evenly round, at an angle
    # that turns a little further every time.
    def spiral():
        global spiral_angle
        if not alive:
            return
        if score >= SPIRAL_FROM:
            for arm in range(0, 360, 360 // SPIRAL_ARMS):
                shoot(Vec2.fromAngle(spiral_angle + arm), CYAN)
            spiral_angle = spiral_angle + SPIRAL_TURN
        wait(SPIRAL_WAIT, spiral)

    wait(1, aim)
    wait(1, ring)
    wait(1, spiral)

    # Every bullet runs this, every frame.
    @onUpdate("bullet")
    def check(bullet):
        if not alive:
            return

        if bullet.pos.dist(bean.pos) < HIT_DISTANCE:
            hit(bullet)
            return

        # Gone out of the arena? Then it is finished with. Left alone, it
        # would fly on for ever, and thousands of them would slow the game
        # down to a crawl.
        x = bullet.pos.x
        y = bullet.pos.y
        if x < -20 or x > arena_w + 20 or y < -20 or y > arena_h + 20:
            bullet.destroy()

    # ------------------------------------------------------------- points
    #
    # A point for every second you are still here.

    def tick():
        global score
        if not alive:
            return
        score = score + 1
        score_label.text = str(score)
        if score == 1:
            message.text = ""
        wait(1, tick)

    wait(1, tick)

    # -------------------------------------------------------- getting hit

    def hit(bullet):
        global alive

        alive = False
        play("boom")
        shake(12)
        addKaboom(bean.pos)

        # Bean goes, and so does every bullet. move() would keep them
        # flying, over the top of the message below.
        bean.destroy()
        destroyAll("bullet")

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
