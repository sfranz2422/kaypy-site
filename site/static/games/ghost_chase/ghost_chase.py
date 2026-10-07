"""Ghost Chase -- grab every coin before the ghosts grab you.

    arrow keys      move
    or hold the mouse (or a finger) where you want Bean to go
    SPACE           start again, or click once the game is over

The ghosts never stop coming, but Bean is faster than they are. Get every
coin and you win. Let a ghost touch you and you lose.

HOW THIS FILE IS PUT TOGETHER

    1. the window, the pictures and the sounds
    2. the settings
    3. the game: Bean, the coins, the ghosts, winning and losing
    4. start the game

This is the easiest game on the site. It uses variables, if, a for loop and
a list -- nothing you have to write a function for. The @ lines are recipes:
copy one, change the key or the tag, and it works.
"""

from kaypy import *

# ----------------------------------------------------------------- 1. setup

kaypy(width=800, height=600, background=[40, 44, 70])

loadSprite("bean", "images/bean.png")
loadSprite("coin", "images/coin.png")
loadSprite("ghosty", "images/ghosty.png")
loadSound("beep", "sounds/small_beep.wav")
loadSound("boom", "sounds/small_boom.wav")
loadSound("win", "sounds/rising_beep.wav")


# -------------------------------------------------------------- 2. settings
#
# Change one, press Run, and play it.

BEAN_SPEED = 260       # how fast Bean runs, in pixels per second
GHOST_SPEED = 100      # how fast the ghosts chase -- try 200!
COINS = 20             # how many coins there are to grab


# --------------------------------------------------------------- 3. the game
#
# Everything in the game is inside this scene, so that go("game") at the
# bottom can throw it all away and start again.

@scene("game")
def game():

    # ------------------------------------------------------------- Bean
    #
    # anchor("center") means pos() is the middle of the picture.

    bean = add([sprite("bean"), pos(center()), anchor("center"), area()])

    @onKeyDown("left")
    def move_left():
        bean.move(-BEAN_SPEED, 0)

    @onKeyDown("right")
    def move_right():
        bean.move(BEAN_SPEED, 0)

    @onKeyDown("up")
    def move_up():
        bean.move(0, -BEAN_SPEED)

    @onKeyDown("down")
    def move_down():
        bean.move(0, BEAN_SPEED)

    # Holding the mouse down -- or a finger, on a phone -- runs Bean
    # towards it.
    @onMouseDown
    def move_to_mouse():
        bean.moveTo(mousePos(), BEAN_SPEED)

    # Every frame, put Bean back inside the window if it has gone past an
    # edge. clamp(number, smallest, biggest) keeps a number between two
    # others. 32 is half of Bean's width, and 27 is half its height.
    @onUpdate
    def stay_on_screen():
        bean.pos.x = clamp(bean.pos.x, 32, width() - 32)
        bean.pos.y = clamp(bean.pos.y, 27, height() - 27)

    # ------------------------------------------------------------ coins
    #
    # A for loop puts COINS coins in random places. rand() picks a number
    # between the two you give it. The top 80 pixels are left for the words.

    for i in range(COINS):
        x = rand(40, width() - 40)
        y = rand(100, height() - 40)
        add([sprite("coin"), pos(x, y), anchor("center"), area(), "coin"])

    label = add([text("Coins left: " + str(COINS), size=28),
                 pos(width() / 2, 30), anchor("center"), z(10)])

    # ----------------------------------------------------------- ghosts
    #
    # follow(bean, speed=GHOST_SPEED) is the whole ghost: it moves itself
    # towards Bean, every frame, for ever. No code of ours moves it.

    add([sprite("ghosty"), pos(60, 60), anchor("center"), area(),
         follow(bean, speed=GHOST_SPEED), "ghost"])
    add([sprite("ghosty"), pos(width() - 60, 60), anchor("center"), area(),
         follow(bean, speed=GHOST_SPEED), "ghost"])

    # ---------------------------------------------------- grabbing a coin
    #
    # This runs when Bean touches anything tagged "coin", and the coin it
    # touched is handed in as `coin`.

    @bean.onCollide("coin")
    def grab(coin):
        coin.destroy()
        play("beep")

        # get("coin") is a list of every coin still in the game.
        coins_left = len(get("coin"))
        label.text = "Coins left: " + str(coins_left)

        if coins_left == 0:
            play("win")
            destroyAll("ghost")
            label.text = "You got them all! SPACE or click to play again"

    # -------------------------------------------------------- getting caught

    @bean.onCollide("ghost")
    def caught(ghost):
        play("boom")
        shake(12)
        addKaboom(bean.pos)
        bean.destroy()
        label.text = "Caught! SPACE or click to play again"

    # ------------------------------------------------------- play again
    #
    # go("game") throws everything away and runs the scene from the top.

    @onKeyPress("space")
    def play_again():
        go("game")

    # A click starts again too, but only once the game is over: Bean has
    # been caught (so Bean no longer exists), or there are no coins left.
    # Otherwise a click to move Bean would start a new game.
    @onClick
    def click_to_play_again():
        if not bean.exists() or len(get("coin")) == 0:
            go("game")


# ------------------------------------------------------- 4. start the game

go("game")
