"""Log Hacker -- guess the server's password. Every guess tells you how close.

    click a word to try it as the password

You have broken into a server. One of the words on the left is its
password, and you have four tries. Every wrong guess goes in the log on
the right, with how many of its letters are the right letter in the
right place. Use that to rule words out: the password has to match every
line in the log. Get it, and the next server's password is longer.

There is no clock. Take as long as you like.

HOW THIS FILE IS PUT TOGETHER

    1. the window and the sounds
    2. the words
    3. the settings
    4. writing the server's files
    5. reading them back
    6. how close a guess is
    7. the game scene: the words, guessing, the log
    8. start the game

This is the game for files. A real hacker would find the files already on
the server. This game has to make its own first, and then it reads them
back exactly as it would read any file. There are three:

    words.txt       the words it could be, one on each line
    password.txt    the one it is
    log.txt         every guess so far, and how close it was

Every file is opened with `with`, which closes it again by itself at the
end of the indented lines underneath.
"""

from kaypy import *

# ----------------------------------------------------------------- 1. setup

kaypy(width=800, height=600, background=[8, 14, 10])

loadSound("blip", "sounds/small_beep.wav")
loadSound("granted", "sounds/rising_beep.wav")
loadSound("wrong", "sounds/thump.wav")
loadSound("locked", "sounds/small_boom.wav")


# --------------------------------------------------------------- 2. the words
#
# Every password is one of these. A server only uses words of one length,
# so they are mixed together here and picked out by length later. A lot of
# them look alike -- crash, crack, track -- which is what makes how close a
# guess was worth knowing.

WORDS = ["admin", "login", "guest", "pixel", "cyber", "virus", "token",
         "cache", "patch", "debug", "shell", "stack", "crash", "crack",
         "track", "trace", "trick", "brick", "block", "clock", "click",
         "flash", "stash", "slash",
         "server", "binary", "cookie", "kernel", "packet", "router",
         "script", "secret", "socket", "pocket", "rocket", "locket",
         "system", "matrix", "shadow", "access", "backup", "buffer",
         "hacker", "logger", "loader", "locker", "master", "poster",
         "account", "browser", "network", "malware", "monitor", "program",
         "console", "hacking", "decrypt", "encrypt", "virtual", "digital",
         "gateway", "storage", "process", "compile", "install", "payload",
         "cracker", "tracker", "packets", "sockets", "rockets", "pockets"]


# -------------------------------------------------------------- 3. settings
#
# Everything else you would want to change is here. Change one at a time
# and play it.

TRIES = 4              # how many guesses you get on each server

WORDS_START = 8        # how many words the first server has
WORDS_MORE = 1         # ...one more on each server after it
WORDS_MOST = 14        # ...and never more than this, or they run off the screen

LENGTH_START = 5       # how long the first server's password is
LENGTH_MOST = 7        # every two servers it is one longer, up to this

GREEN = rgb(90, 230, 120)
DIM = rgb(50, 110, 65)
BRIGHT = rgb(200, 255, 210)

# The name the best score is saved under. Every game on a website shares
# the same storage, so the game's own name goes in it.
BEST_KEY = "log_hacker_best"


# --------------------------------------------- 4. writing the server's files
#
# with open("words.txt", "w") as words_file: opens the file, and calls it
# words_file for the indented lines underneath. When they end, the file is
# closed by itself. "w" means write: it makes the file, or empties it if
# it is already there.
#
# "\n" is the end of a line. write() does not add one for you, so without
# it every word would end up on the same line: crashcracktrack.

def write_files(length, how_many):
    # Every word in WORDS that is the right length.
    fits = []
    for word in WORDS:
        if len(word) == length:
            fits.append(word)

    # The while loop below picks different words until it has enough. Ask
    # it for more than there are and it could never finish: it would go
    # round for ever, and the game would freeze. So never ask for more.
    if how_many > len(fits):
        how_many = len(fits)

    words = []
    while len(words) < how_many:
        word = choose(fits)
        if word not in words:
            words.append(word)

    with open("words.txt", "w") as words_file:
        for word in words:
            words_file.write(word + "\n")

    # One of them is the password.
    with open("password.txt", "w") as password_file:
        password_file.write(choose(words) + "\n")

    # A new log, with nothing in it yet. "w" empties it.
    with open("log.txt", "w") as log_file:
        log_file.write("")


# --------------------------------------------------- 5. reading them back
#
# "r" means read. A for loop over a file goes round once for each line,
# and line is the line, "\n" and all. strip() takes the "\n" off --
# without it, "crash\n" is not "crash", and no guess would ever be right.

def read_words():
    words = []
    with open("words.txt", "r") as words_file:
        for line in words_file:
            words.append(line.strip())
    return words


def read_password():
    # read() is the whole file, as one string.
    with open("password.txt", "r") as password_file:
        password = password_file.read().strip()
    return password


def read_log():
    # Each line of the log is a guess and how many letters it got right,
    # with a comma between: crash,2
    guesses = []
    with open("log.txt", "r") as log_file:
        for line in log_file:
            guesses.append(line.strip())
    return guesses


# ------------------------------------------------- 6. how close a guess is
#
# How many letters of the guess are the right letter in the right place.
# crash and crack share c, r, a in the same places, so that is 3.

def letters_right(guess, password):
    right = 0
    for i in range(len(password)):
        if guess[i] == password[i]:
            right = right + 1
    return right


# ------------------------------------------------------- 7. the game scene
#
# These change while you play. A function that CHANGES one has to say
# `global` first, which means "the one up here, not a new one of my own".

tries_left = TRIES
playing = True
over = False
told = False


@scene("server")
def server(number):
    global tries_left, playing, over, told

    # A new server: its own files, written and then read. The password is
    # one letter longer every two servers.
    length = LENGTH_START + (number - 1) // 2
    if length > LENGTH_MOST:
        length = LENGTH_MOST
    how_many = WORDS_START + (number - 1) * WORDS_MORE
    if how_many > WORDS_MOST:
        how_many = WORDS_MOST
    write_files(length, how_many)
    words = read_words()

    tries_left = TRIES
    playing = True
    over = False
    best = getData(BEST_KEY, 0)

    # ------------------------------------------------------- the screen

    add([text("SERVER " + str(number), size=28), pos(20, 20), color(GREEN)])
    best_label = add([text("best " + str(best), size=18), pos(20, 52),
                      color(DIM)])
    tries_label = add([text("TRIES LEFT " + str(TRIES), size=24),
                       pos(780, 24), anchor("topright"), color(GREEN)])

    add([text("words.txt", size=20), pos(40, 100), color(DIM)])
    add([text("log.txt", size=20), pos(330, 100), color(DIM)])

    # The words, read from words.txt. Each one is something to click:
    # area() lets it know when the mouse is over it, and the dictionary
    # gives it two values of its own -- the word, and whether it has been
    # tried yet.
    y = 130
    for word in words:
        add([text(word, size=26), pos(50, y), color(GREEN), area(),
             {"word": word, "tried": False}, "word"])
        y = y + 32

    message = add([text("", size=36), pos(560, 450), anchor("center"),
                   color(GREEN), z(10)])
    under = add([text("", size=22), pos(560, 495), anchor("center"),
                 color(GREEN), z(10)])

    # ------------------------------------------------------------ the log
    #
    # Read log.txt and put every line of it on the screen. The old lines
    # are taken away first, so each guess is shown once.

    def show_log():
        destroyAll("entry")
        y = 130
        for guess in read_log():
            # "crash,2" becomes ["crash", "2"]: split(",") cuts it up at
            # the comma.
            parts = guess.split(",")
            add([text("> " + parts[0], size=24), pos(340, y), color(GREEN),
                 "entry"])
            add([text(parts[1] + "/" + str(length) + " right", size=24),
                 pos(500, y), color(DIM), "entry"])
            y = y + 32

    # ------------------------------------------------------------ guessing

    # A word lights up while the mouse is over it, unless it has been tried.
    @onUpdate("word")
    def light_up(row):
        if row.tried:
            row.color = DIM
        elif row.isHovering() and playing:
            row.color = BRIGHT
        else:
            row.color = GREEN

    # onClick runs on every click, wherever it is, and a tap on a phone
    # counts as a click. isHovering() asks whether the mouse is over a word,
    # which needs area() on it.
    @onClick
    def click():
        if not playing:
            return
        for row in get("word"):
            if row.isHovering() and not row.tried:
                guess(row)
                return

    def guess(row):
        global tries_left

        row.tried = True
        password = read_password()
        right = letters_right(row.word, password)

        # The guess goes on the end of the log. "a" means add: it keeps
        # what is there and writes after it, where "w" would empty it.
        with open("log.txt", "a") as log_file:
            log_file.write(row.word + "," + str(right) + "\n")
        show_log()

        if row.word == password:
            granted(password)
            return

        tries_left = tries_left - 1
        tries_label.text = "TRIES LEFT " + str(tries_left)
        play("wrong")
        shake(4)
        if tries_left == 0:
            locked_out(password)

    # --------------------------------------------------- in, or locked out

    def granted(password):
        global playing

        playing = False
        play("granted")
        message.text = "ACCESS GRANTED"
        under.text = "the password was " + password
        wait(2, next_server)

    def next_server():
        go("server", number + 1)

    def locked_out(password):
        global playing

        playing = False
        play("locked")
        shake(12)

        # The servers you got into is one less than the one you were
        # locked out of.
        hacked = number - 1
        if hacked > best:
            setData(BEST_KEY, hacked)
            best_label.text = "best " + str(hacked)

        message.text = "LOCKED OUT"
        message.color = RED
        under.text = "it was " + password + " -- servers hacked: " + str(hacked)

        # A second before you can start again, so a click meant for a word
        # does not skip past what happened.
        wait(1, ready_again)

    def ready_again():
        global over

        over = True
        add([text("press SPACE or click to start again", size=22),
             pos(560, 540), anchor("center"), color(GREEN)])

    def again():
        if over:
            go("server", 1)

    onKeyPress("space", again)
    onClick(again)

    # The first time, how to play comes up first.
    if not told:
        told = True
        say("One of these words is the server's password, and you have "
            "four tries. Click a word to guess it. The log tells you how "
            "many of its letters are in the right place -- the password "
            "has to match every line of it. There is no clock.")


# ------------------------------------------------------- 8. start the game

go("server", 1)
