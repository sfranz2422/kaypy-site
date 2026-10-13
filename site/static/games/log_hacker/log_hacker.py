"""Log Hacker -- somewhere in the server's log is a password. Find it.

    click the line that gives a password away

You have broken into a server and you are reading its log: one line for
every time somebody tried to log in, saying when, who, and whether it
worked. People make mistakes. Now and then somebody types their PASSWORD
into the box where their NAME should go, and the server writes it down in
the log, in plain sight.

The people who really have accounts are listed on the right. A failed
login by a name that is NOT on that list is not a name at all -- it is
somebody's password. Click it before the trace reaches 100% and you are
in. Every server is faster than the last.

HOW THIS FILE IS PUT TOGETHER

    1. the window and the sounds
    2. the names and the passwords
    3. the settings
    4. writing the server's files
    5. reading them back
    6. the game scene: the log going past, clicking, the trace
    7. start the game

This is the game for files. A real hacker would find the files already
on the server. This game has to make its own first, with open("users.txt",
"w"), and then it reads them back with open("users.txt", "r") exactly as
it would read any file. It makes new ones for every server, so the log is
never the same twice.
"""

from kaypy import *

# ----------------------------------------------------------------- 1. setup

kaypy(width=800, height=600, background=[8, 14, 10])

loadSound("blip", "sounds/small_beep.wav")
loadSound("granted", "sounds/rising_beep.wav")
loadSound("wrong", "sounds/thump.wav")
loadSound("caught", "sounds/small_boom.wav")


# ------------------------------------------------- 2. names and passwords
#
# The users on each server are picked from NAMES. The passwords somebody
# types by mistake are picked from PASSWORDS -- every one of them a real
# password that thousands of real people use, which is exactly why they
# are easy to guess. A lot of them are names. So a password in the log
# can look just like a user: the only way to tell is to check the list.

NAMES = ["ada", "max", "zoe", "leo", "mia", "raj",
         "olivia", "lucas", "amara", "kenji", "sofia", "mateo"]

PASSWORDS = ["dragon", "qwerty", "letmein", "monkey", "sunshine",
             "football", "shadow", "jordan", "michael", "jessica",
             "charlie", "ashley", "daniel", "thomas", "maggie", "taylor"]


# -------------------------------------------------------------- 3. settings
#
# Everything else you would want to change is here. Change one at a time
# and play it.

USERS_START = 4        # how many users the first server has
LINES_START = 20       # how many lines are in its log
SCROLL_START = 40      # how fast its log goes past, in pixels a second
TRACE_START = 3        # how fast the trace rises, in % a second

# ...and how much more each server after it has.
USERS_MORE = 1
LINES_MORE = 6
SCROLL_MORE = 12
TRACE_MORE = 0.5

WRONG_CLICK = 15       # how much the trace jumps when you click a wrong line
FAIL_CHANCE = 0.3      # how often an ordinary login fails: 0.3 is 3 in 10

ROW = 28               # how tall one line of the log is, in pixels
LOG_TOP = 90           # a line that goes above this has gone
LOG_BOTTOM = 560       # ...and a new one comes in here

GREEN = rgb(90, 230, 120)
DIM = rgb(50, 110, 65)

# The name the best score is saved under. Every game on a website shares
# the same storage, so the game's own name goes in it.
BEST_KEY = "log_hacker_best"


# ------------------------------------------------ 4. writing the server's files
#
# Two files. users.txt has one name on each line:
#
#     ada
#     zoe
#
# and log.txt has one login on each line, its three parts with commas
# between them -- when, who, and whether it worked:
#
#     01:07,zoe,ok
#     01:12,ada,failed
#
# "\n" is the end of a line. write() does not add one for you, so without
# it every name would end up on the same line: adazoemaxsam.

def two_digits(number):
    if number < 10:
        return "0" + str(number)
    return str(number)


def clock(minutes):
    # 75 minutes after midnight is 01:15. // is how many whole hours, and
    # % is the minutes left over.
    hours = minutes // 60 % 24
    return two_digits(hours) + ":" + two_digits(minutes % 60)


def write_files(how_many_users, how_many_lines):
    # Pick the users. A name that is already picked is skipped, so the
    # loop goes round until there are enough different ones.
    users = []
    while len(users) < how_many_users:
        name = choose(NAMES)
        if name not in users:
            users.append(name)

    users_file = open("users.txt", "w")
    for name in users:
        users_file.write(name + "\n")
    users_file.close()

    # The line where somebody slips up. Not one of the first few, so you
    # have read a little of the log before it comes.
    slip = randi(4, how_many_lines - 1)

    log_file = open("log.txt", "w")
    minutes = randi(0, 300)
    for number in range(how_many_lines):
        minutes = minutes + randi(1, 9)
        when = clock(minutes)

        if number == slip:
            # A password where the name should be, which fails -- and then
            # the same person, a moment later, getting it right.
            victim = choose(users)
            log_file.write(when + "," + choose(PASSWORDS) + ",failed\n")
            log_file.write(when + "," + victim + ",ok\n")
        else:
            name = choose(users)
            if chance(FAIL_CHANCE):
                result = "failed"
            else:
                result = "ok"
            log_file.write(when + "," + name + "," + result + "\n")

    log_file.close()


# --------------------------------------------------- 5. reading them back
#
# users.txt is read all at once, with a for loop: each time round, line is
# the next line of the file. Every line ends in its "\n", and strip()
# takes it off -- without that, "ada\n" is not "ada", and nobody would
# ever be on the list.

def read_users():
    users = []
    users_file = open("users.txt", "r")
    for line in users_file:
        users.append(line.strip())
    users_file.close()
    return users


# log.txt is read one line at a time, while you play, with readline().
# The file stays open in between, and remembers where it got to, so each
# readline() hands over the line after the last one. At the end of the
# file there is nothing left to hand over, and readline() gives back "".

log_file = None


# ------------------------------------------------------- 6. the game scene
#
# These change while you play. A function that CHANGES one has to say
# `global` first, which means "the one up here, not a new one of my own".

users = []
trace = 0
playing = True
over = False
told = False


@scene("server")
def server(number):
    global users, log_file, trace, playing, over, told

    # A new server: its own files, written and then read.
    #
    # There are twelve names. Ask write_files for thirteen different
    # ones and its while loop could never find them: it would go round
    # for ever, and the game would freeze. So it stops at twelve.
    how_many_users = USERS_START + (number - 1) * USERS_MORE
    if how_many_users > len(NAMES):
        how_many_users = len(NAMES)
    write_files(how_many_users, LINES_START + (number - 1) * LINES_MORE)
    users = read_users()
    log_file = open("log.txt", "r")

    scroll = SCROLL_START + (number - 1) * SCROLL_MORE
    trace_speed = TRACE_START + (number - 1) * TRACE_MORE

    trace = 0
    playing = True
    over = False
    best = getData(BEST_KEY, 0)

    # ------------------------------------------------------- the screen

    add([text("SERVER " + str(number), size=28), pos(20, 20),
         color(GREEN), z(10)])
    best_label = add([text("best " + str(best), size=18), pos(20, 52),
                      color(DIM), z(10)])

    add([text("TRACE", size=20), pos(470, 28), color(GREEN), z(10)])
    add([rect(200, 18), pos(540, 28), color(20, 40, 26), z(10)])
    trace_bar = add([rect(1, 18), pos(540, 28), color(GREEN), z(11)])
    trace_label = add([text("0%", size=20), pos(750, 28), color(GREEN),
                       z(10)])

    # The users, read from users.txt, down the right-hand side.
    add([text("users.txt", size=20), pos(600, 100), color(DIM), z(10)])
    y = 130
    for name in users:
        add([text(name, size=26), pos(610, y), color(GREEN), z(10)])
        y = y + 32

    add([text("log.txt", size=20), pos(20, 72), color(DIM), z(10)])

    # Two dark bands over the top and bottom of the log, so lines slide
    # in and out of sight behind them rather than over the words above.
    add([rect(800, LOG_TOP), pos(0, 0), color(8, 14, 10), z(5)])
    add([rect(560, 600 - LOG_BOTTOM - ROW), pos(0, LOG_BOTTOM + ROW),
         color(8, 14, 10), z(5)])

    message = add([text("", size=40), pos(280, 300), anchor("center"),
                   color(GREEN), z(20)])

    # ----------------------------------------------- the log going past

    def show(when, name, result):
        # One line of the log: a dark strip at the bottom, which moves up.
        # area() lets it know when the mouse is over it, and the dictionary
        # keeps the name it is showing, to check against the users when it
        # is clicked. The words are its children, so they move with it.
        row = add([rect(540, ROW - 2), pos(10, LOG_BOTTOM), color(8, 14, 10),
                   area(), {"name": name}, "row", "line"])
        row.add([text(when, size=22), pos(10, 4), color(DIM)])
        row.add([text(name, size=22), pos(100, 4), color(GREEN)])
        if result == "failed":
            row.add([text("FAILED", size=22), pos(300, 4), color(RED)])
        else:
            row.add([text("ok", size=22), pos(300, 4), color(GREEN)])

    def next_line():
        global log_file

        if not playing:
            return

        line = log_file.readline()

        # "" means the end of the file. Close it, open it again, and start
        # from the top: the password comes round again -- but the trace
        # has not stopped.
        if line == "":
            log_file.close()
            log_file = open("log.txt", "r")

            # A row of its own to say so. It has no "line" tag, so it
            # moves up with the rest but clicking it does nothing.
            row = add([rect(540, ROW - 2), pos(10, LOG_BOTTOM),
                       color(8, 14, 10), "row"])
            row.add([text("----- end of log.txt, reading it again",
                          size=22), pos(10, 4), color(DIM)])
            wait(ROW / scroll, next_line)
            return

        # "01:07,zoe,ok\n" becomes ["01:07", "zoe", "ok"]: strip() takes
        # the "\n" off the end, and split(",") cuts what is left at
        # every comma.
        parts = line.strip().split(",")
        show(parts[0], parts[1], parts[2])
        play("blip", volume=0.2)

        # The next line once this one has moved up out of its way.
        wait(ROW / scroll, next_line)

    # Every row moves up, and one that has gone past the top is gone.
    @onUpdate("row")
    def move_up(row):
        if not playing:
            return
        row.pos.y = row.pos.y - scroll * dt()
        if row.pos.y < LOG_TOP - ROW:
            row.destroy()

    # A line you can click lights up while the mouse is over it.
    @onUpdate("line")
    def light_up(row):
        if row.isHovering():
            row.color = rgb(25, 50, 32)
        else:
            row.color = rgb(8, 14, 10)

    # ------------------------------------------------------------ clicking
    #
    # onClick runs on every click, wherever it is, and a tap on a phone
    # counts as a click. isHovering() asks whether the mouse is over a
    # line, which needs area() on it.

    @onClick
    def click():
        if not playing:
            return
        for row in get("line"):
            if row.isHovering():
                check(row)
                return

    def check(row):
        global trace

        # A name on the list is only a name. A name that is NOT on the
        # list is somebody's password.
        if row.name in users:
            trace = trace + WRONG_CLICK
            play("wrong")
            shake(6)
            add([text("+" + str(WRONG_CLICK) + "% trace", size=26),
                 pos(mousePos().x, mousePos().y - 30), anchor("center"),
                 color(RED), opacity(1), lifespan(0.6, fade=0.3), z(20)])
        else:
            granted(row.name)

    # --------------------------------------------------------- the trace

    @onUpdate
    def tracing():
        global trace

        if not playing:
            return
        trace = trace + trace_speed * dt()
        if trace >= 100:
            trace = 100
            caught()
        trace_bar.width = trace * 2
        trace_label.text = str(int(trace)) + "%"

    # --------------------------------------------------- in, or caught

    def granted(password):
        global playing

        playing = False
        log_file.close()
        play("granted")
        destroyAll("row")
        message.text = "ACCESS GRANTED"
        add([text("the password was " + password, size=26),
             pos(280, 350), anchor("center"), color(GREEN), z(20)])
        wait(2, next_server)

    def next_server():
        go("server", number + 1)

    def caught():
        global playing

        playing = False
        log_file.close()
        play("caught")
        shake(12)
        destroyAll("row")

        # The servers you got into is one less than the one you were
        # caught on.
        hacked = number - 1
        if hacked > best:
            setData(BEST_KEY, hacked)
            best_label.text = "best " + str(hacked)

        message.text = "TRACED"
        message.color = RED
        add([text("servers hacked: " + str(hacked), size=28),
             pos(280, 360), anchor("center"), color(GREEN), z(20)])

        # A second before you can start again, so a click meant for the
        # log does not skip past what happened.
        wait(1, ready_again)

    def ready_again():
        global over

        over = True
        add([text("press SPACE or click to start again", size=24),
             pos(280, 420), anchor("center"), color(GREEN), z(20)])

    def again():
        if over:
            go("server", 1)

    onKeyPress("space", again)
    onClick(again)

    # The log starts. The first time, how to play comes up first.
    if not told:
        told = True
        say("A password is hiding in this log. Somebody typed it where "
            "their name should go. Click the FAILED line whose name is "
            "not in users.txt -- before the trace reaches 100%.")
    next_line()


# ------------------------------------------------------- 7. start the game

go("server", 1)
