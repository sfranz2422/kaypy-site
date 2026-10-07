"""Paddle Ball -- keep the ball up. Pong, for one.

    left and right arrows   move your paddle
    or hold the mouse (or a finger) where you want the paddle to go

The ball bounces off the top and the sides. Hit it back up with your paddle
and that is a point. Every hit makes the ball a little faster. Miss it and
it is game over. Your best score is remembered.

HOW THIS FILE IS PUT TOGETHER

    1. the window and the sounds
    2. the settings
    3. the game scene: the paddle, the ball, bouncing, points, missing
    4. start the game

There are no pictures at all. The paddle and the ball are rectangles, and
the ball is a game object that carries its own speed: ball.dx is how fast
it is going across, and ball.dy is how fast it is going down. Bouncing is
just making one of them negative. After this, try Pong.
"""

from kaypy import *

# ----------------------------------------------------------------- 1. setup

kaypy(width=800, height=600, background=[20, 24, 40])

loadSound("hit", "sounds/beep.wav")
loadSound("wall", "sounds/small_beep.wav")
loadSound("miss", "sounds/thump.wav")


# -------------------------------------------------------------- 2. settings
#
# Everything you would want to change is here. Change one at a time and
# play it.

PADDLE_W = 120         # how wide the paddle is
PADDLE_H = 16          # and how tall
PADDLE_SPEED = 520     # how fast the paddle moves, in pixels per second

BALL_SIZE = 16
BALL_START = 300       # how fast the ball comes down at the start
BALL_GAIN = 25         # ...how much faster every hit makes it
BALL_FASTEST = 800     # ...and the fastest it ever goes

# The name the best score is saved under. Every game on a website shares
# the same storage, so the game's own name goes in it.
BEST_KEY = "paddle_ball_best"


# ------------------------------------------------------- 3. the game scene
#
# These change while you play. A function that CHANGES one has to say
# `global` first, which means "the one up here, not a new one of my own".

score = 0
alive = True


@scene("game")
def game():
    global score, alive

    # A new game, so everything starts again.
    score = 0
    alive = True
    best = getData(BEST_KEY, 0)

    # anchor("center") means pos() is the middle of the rectangle.
    paddle = add([rect(PADDLE_W, PADDLE_H), anchor("center"),
                  pos(width() / 2, height() - 40), color(120, 220, 255)])

    # The ball starts still. serve() below sets it going.
    ball = add([rect(BALL_SIZE, BALL_SIZE), anchor("center"),
                pos(width() / 2, 100)])
    ball.dx = 0
    ball.dy = 0

    score_label = add([text("0", size=56), pos(width() / 2, 60),
                       anchor("center")])
    best_label = add([text("best " + str(best), size=18), pos(12, 12),
                      opacity(0.75)])

    # width=560 wraps a long message onto more than one line.
    message = add([text("Left and right arrows, or hold the mouse where "
                        "you want your paddle. Keep the ball up!",
                        size=26, width=560),
                   pos(width() / 2, height() / 2), anchor("center"), z(10)])

    # ------------------------------------------------------- the paddle

    @onKeyDown("left")
    def move_left():
        paddle.move(-PADDLE_SPEED, 0)
        keep_on_screen()

    @onKeyDown("right")
    def move_right():
        paddle.move(PADDLE_SPEED, 0)
        keep_on_screen()

    # Holding the mouse down -- or a finger, on a phone -- moves the
    # paddle towards it. Within 10 pixels counts as there.
    @onMouseDown
    def move_to_mouse():
        if mousePos().x < paddle.pos.x - 10:
            paddle.move(-PADDLE_SPEED, 0)
        if mousePos().x > paddle.pos.x + 10:
            paddle.move(PADDLE_SPEED, 0)
        keep_on_screen()

    def keep_on_screen():
        paddle.pos.x = clamp(paddle.pos.x, PADDLE_W / 2,
                             width() - PADDLE_W / 2)

    # --------------------------------------------------------- serving
    #
    # Sideways a random amount, left or right, and always down.

    def serve():
        ball.dx = rand(150, 250)
        if chance(0.5):
            ball.dx = -ball.dx
        ball.dy = BALL_START

    wait(1.5, serve)

    # -------------------------------------------------------- the ball
    #
    # Every frame the ball moves by its own speed, times dt() -- the time
    # since the last frame -- so it goes as fast on a slow computer.

    @onUpdate
    def move_ball():
        if not alive:
            return

        old_y = ball.pos.y
        ball.pos.x = ball.pos.x + ball.dx * dt()
        ball.pos.y = ball.pos.y + ball.dy * dt()

        # The side walls: put it back inside, and turn it round.
        if ball.pos.x < BALL_SIZE / 2:
            ball.pos.x = BALL_SIZE / 2
            ball.dx = -ball.dx
            play("wall")
        if ball.pos.x > width() - BALL_SIZE / 2:
            ball.pos.x = width() - BALL_SIZE / 2
            ball.dx = -ball.dx
            play("wall")

        # The top.
        if ball.pos.y < BALL_SIZE / 2:
            ball.pos.y = BALL_SIZE / 2
            ball.dy = -ball.dy
            play("wall")

        # The paddle. `top` is where the middle of the ball is when it
        # sits on the paddle, and `reach` is how far from the middle of the
        # paddle it can be and still touch it. Did the ball go past `top`
        # THIS frame, coming down, within reach? Checking where it was a
        # frame ago as well as where it is now means a fast ball can't
        # jump straight through.
        top = paddle.pos.y - PADDLE_H / 2 - BALL_SIZE / 2
        across = abs(ball.pos.x - paddle.pos.x)
        reach = PADDLE_W / 2 + BALL_SIZE / 2
        if old_y <= top and ball.pos.y > top and across < reach:
            ball.pos.y = top
            hit()

        # Gone past the bottom?
        if ball.pos.y > height() + BALL_SIZE:
            missed()

    # ------------------------------------------------------- hitting it

    def hit():
        global score

        # A little faster than it came down, but never faster than
        # BALL_FASTEST. Then make it negative, which sends it back up.
        # Only the up-and-down speed grows: if the sideways speed grew too,
        # the ball would soon cross the window faster than the paddle can.
        speed = ball.dy + BALL_GAIN
        if speed > BALL_FASTEST:
            speed = BALL_FASTEST
        ball.dy = -speed
        play("hit")

        score = score + 1
        score_label.text = str(score)
        message.text = ""

    # -------------------------------------------------------- missing it

    def missed():
        global alive

        alive = False
        play("miss")
        shake(8)
        ball.destroy()

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


# ------------------------------------------------------- 4. start the game

go("game")
