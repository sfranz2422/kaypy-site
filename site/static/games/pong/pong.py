"""Pong -- the first video game anyone played at home. You against the
computer.

    up and down arrows      move your paddle
    or hold the mouse (or a finger) where you want the paddle to go

Your paddle is on the left. Hit the ball back past the computer's paddle to
score a point. Every hit makes the ball a little faster, and where it hits
your paddle decides where it goes: the middle sends it straight, the ends
send it off at an angle. First to 7 wins.

HOW THIS FILE IS PUT TOGETHER

    1. the window and the sounds
    2. the settings
    3. the game scene: the paddles, the ball, bouncing, scoring
    4. start the game

There are no pictures at all. The paddles, the ball and the net are
rectangles, and the ball is a game object that carries its own speed.
"""

from kaypy import *

# ----------------------------------------------------------------- 1. setup

kaypy(width=800, height=600, background=[20, 24, 40])

loadSound("hit", "sounds/beep.wav")
loadSound("wall", "sounds/small_beep.wav")
loadSound("point", "sounds/thump.wav")
loadSound("win", "sounds/rising_beep.wav")


# -------------------------------------------------------------- 2. settings
#
# Everything you would want to change is here. Change one at a time and
# play it.

PADDLE_W = 16          # how wide a paddle is
PADDLE_H = 100         # and how tall
PADDLE_GAP = 30        # how far each paddle is from its edge of the window
PADDLE_SPEED = 480     # how fast your paddle moves, in pixels per second

CPU_SPEED = 300        # how fast the computer's paddle can move

BALL_SIZE = 16
BALL_START = 360       # how fast the ball goes at the start of each point
BALL_GAIN = 25         # ...how much faster every hit makes it
BALL_FASTEST = 750     # ...and the fastest it ever goes
BALL_ANGLE = 0.75      # how steeply the ends of a paddle send the ball

WIN_SCORE = 7          # first to this many points wins


# ------------------------------------------------------- 3. the game scene
#
# These change while you play. A function that CHANGES one has to say
# `global` first, which means "the one up here, not a new one of my own".

player_score = 0
cpu_score = 0
playing = True


@scene("game")
def game():
    global player_score, cpu_score, playing

    # A new game, so everything starts again.
    player_score = 0
    cpu_score = 0
    playing = True

    # The net: a dashed line down the middle. It is only a picture.
    for y in range(10, height(), 40):
        add([rect(4, 20), pos(width() / 2 - 2, y), color(90, 100, 130)])

    # anchor("center") means pos() is the middle of the paddle, which makes
    # "is the ball within the paddle?" easy to work out below.
    player = add([rect(PADDLE_W, PADDLE_H), anchor("center"),
                  pos(PADDLE_GAP, height() / 2), color(120, 220, 255)])
    cpu = add([rect(PADDLE_W, PADDLE_H), anchor("center"),
               pos(width() - PADDLE_GAP, height() / 2), color(255, 140, 120)])

    # The ball carries its own speed: dx across and dy down, in pixels per
    # second. A negative dx means it is going left, a negative dy up.
    ball = add([rect(BALL_SIZE, BALL_SIZE), anchor("center"),
                pos(width() / 2, height() / 2)])
    ball.dx = 0
    ball.dy = 0

    player_label = add([text("0", size=56), pos(width() / 2 - 60, 50),
                        anchor("center")])
    cpu_label = add([text("0", size=56), pos(width() / 2 + 60, 50),
                     anchor("center")])

    # width=560 wraps a long message onto more than one line.
    message = add([text("Up and down arrows, or hold the mouse where you "
                        "want your paddle. First to " + str(WIN_SCORE)
                        + " wins!", size=26, width=560),
                   pos(width() / 2, height() - 120), anchor("center"),
                   z(10)])

    # -------------------------------------------------------- your paddle
    #
    # onKeyDown runs its function every frame the key is held, so the
    # paddle keeps moving until you let go.

    @onKeyDown("up")
    def move_up():
        player.move(0, -PADDLE_SPEED)
        keep_on_screen()

    @onKeyDown("down")
    def move_down():
        player.move(0, PADDLE_SPEED)
        keep_on_screen()

    # Holding the mouse down -- or a finger, on a phone -- moves the paddle
    # towards it. Within 10 pixels counts as there, and the paddle stops.
    @onMouseDown
    def move_to_mouse():
        if mousePos().y < player.pos.y - 10:
            player.move(0, -PADDLE_SPEED)
        if mousePos().y > player.pos.y + 10:
            player.move(0, PADDLE_SPEED)
        keep_on_screen()

    def keep_on_screen():
        player.pos.y = clamp(player.pos.y, PADDLE_H / 2,
                             height() - PADDLE_H / 2)

    # ------------------------------------------------- the computer's paddle
    #
    # The computer follows the ball, but only when the ball is coming its
    # way, and never faster than CPU_SPEED. That is what makes it possible
    # to beat: a fast ball at a steep angle gets past it.

    @onUpdate
    def computer():
        if ball.dx > 0:
            target = ball.pos.y
        else:
            target = height() / 2       # drift back to the middle
        if target < cpu.pos.y - 10:
            cpu.move(0, -CPU_SPEED)
        if target > cpu.pos.y + 10:
            cpu.move(0, CPU_SPEED)

    # ------------------------------------------------------------- serving

    def serve(direction):
        # direction is 1 to serve to the right, -1 to the left. The ball
        # starts in the middle and goes off at a random slant.
        ball.pos = vec2(width() / 2, height() / 2)
        ball.dx = BALL_START * direction
        ball.dy = rand(-BALL_START / 2, BALL_START / 2)

    # wait() runs a function later, and it has to be one that needs nothing
    # handed to it. So there is one for each way the ball can be served.
    def serve_left():
        serve(-1)

    def serve_right():
        serve(1)

    # The first serve goes towards you, a second and a half in.
    wait(1.5, serve_left)

    # ------------------------------------------------------------ the ball

    @onUpdate
    def move_ball():
        # Where the ball is before it moves, to see what it crossed.
        old_x = ball.pos.x
        ball.pos.x = ball.pos.x + ball.dx * dt()
        ball.pos.y = ball.pos.y + ball.dy * dt()

        # Off the top or the bottom: turn it round. Putting it back on the
        # edge matters. A slow frame can carry the ball well past it, and if
        # the next frame does not bring it back inside, it is turned round
        # again -- the wrong way -- and leaves the window.
        if ball.pos.y < BALL_SIZE / 2:
            ball.pos.y = BALL_SIZE / 2
            ball.dy = -ball.dy
            play("wall")
        if ball.pos.y > height() - BALL_SIZE / 2:
            ball.pos.y = height() - BALL_SIZE / 2
            ball.dy = -ball.dy
            play("wall")

        # Did it just cross the front of your paddle, going left? "Just
        # crossed" -- it was on one side before it moved and is on the other
        # now -- is what matters. The ball moves 6 to 12 pixels a frame, and
        # more on a slow one, so it is hardly ever exactly AT the front.
        edge = player.pos.x + PADDLE_W / 2 + BALL_SIZE / 2
        if old_x >= edge and ball.pos.x < edge and touching(player):
            ball.pos.x = edge
            bounce(player, 1)

        # The front of the computer's paddle, going right.
        edge = cpu.pos.x - PADDLE_W / 2 - BALL_SIZE / 2
        if old_x <= edge and ball.pos.x > edge and touching(cpu):
            ball.pos.x = edge
            bounce(cpu, -1)

        # Gone off the side: a point to whoever is at the other end.
        if ball.pos.x < -BALL_SIZE:
            point_to("cpu")
        if ball.pos.x > width() + BALL_SIZE:
            point_to("player")

    def touching(paddle):
        # Is the ball level with the paddle? Half the paddle and half the
        # ball, up or down from the paddle's middle.
        return abs(ball.pos.y - paddle.pos.y) < PADDLE_H / 2 + BALL_SIZE / 2

    def bounce(paddle, direction):
        # A little faster each hit, up to BALL_FASTEST.
        speed = abs(ball.dx) + BALL_GAIN
        if speed > BALL_FASTEST:
            speed = BALL_FASTEST
        ball.dx = speed * direction

        # Where on the paddle it hit: -1 is the top end, 0 the middle, 1 the
        # bottom end. That decides how steeply it comes off.
        where = (ball.pos.y - paddle.pos.y) / (PADDLE_H / 2)
        where = clamp(where, -1, 1)
        ball.dy = where * speed * BALL_ANGLE
        play("hit")

    # ------------------------------------------------------------ scoring

    def point_to(who):
        global player_score, cpu_score, playing

        # Park the ball in the middle, standing still, until the next serve.
        ball.pos = vec2(width() / 2, height() / 2)
        ball.dx = 0
        ball.dy = 0
        message.text = ""

        if who == "player":
            player_score = player_score + 1
            player_label.text = str(player_score)
        else:
            cpu_score = cpu_score + 1
            cpu_label.text = str(cpu_score)

        if player_score == WIN_SCORE or cpu_score == WIN_SCORE:
            playing = False
            ball.destroy()
            play("win")
            if player_score == WIN_SCORE:
                message.text = "You win! Press SPACE or click to play again"
            else:
                message.text = ("The computer wins. Press SPACE or click "
                                "to play again")
            return

        play("point")
        # The next serve goes towards whoever just lost the point.
        if who == "player":
            wait(1, serve_right)
        else:
            wait(1, serve_left)

    # Once the game is over, space or a click starts a new one.
    def again():
        if not playing:
            go("game")

    onKeyPress("space", again)
    onClick(again)


# ------------------------------------------------------- 4. start the game

go("game")
