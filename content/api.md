# API reference

Every function KayPy gives you, with a working example for each one.

**Every example below assumes these lines at the top:**

```python
from kaypy import *

kaypy(width=800, height=600, background=[141, 183, 255])
loadSprite("bean", "images/bean.png")
```

That is what the [playground](../play/) starts with, so you can paste any
example straight in and press Run. Examples are fragments — they make whatever
else they need.

The names follow [KAPLAY](https://kaplayjs.com)'s, so its documentation and
examples describe these functions too. Where Python makes a difference, this
page says so.

---

## Starting a game

### kaypy(width, height, background, joystick)

Starts the engine. It must come first — before loading anything, before adding
anything. There is no `run()` to call afterwards: the loop starts by itself
once your file has been read.

```python
kaypy(width=1024, height=768, background=[20, 20, 40])
```

`joystick=True` puts a d-pad and two buttons on the screen, for playing with
a thumb. They hold the arrow keys and send `space` and `z`, so a game written
for the keyboard works on a phone without changing a line:

```python
from kaypy import *

kaypy(width=800, height=600, joystick=True)
loadSprite("bean", "images/bean.png")

player = add([sprite("bean"), pos(100, 100)])

# The d-pad drives this. Nothing here knows it is not a keyboard.
@onKeyDown("left")
def go_left():
    player.move(-320, 0)
```

Pass a list to choose what the two buttons send:

```python
kaypy(width=800, height=600, joystick=["space", "x"])
```

It works with a mouse too, so you can try it without picking up a phone.

### width()

How wide the window is, in pixels. Use it instead of typing the number twice.

```python
add([rect(width(), 20), pos(0, 0), color(90, 150, 70)])
```

### height()

How tall the window is.

```python
# A floor along the bottom, whatever size the window is.
add([rect(width(), 48), pos(0, height() - 48), area(), body(isStatic=True)])
```

### center()

The middle of the window, as a `vec2`.

```python
add([sprite("bean"), pos(center()), anchor("center")])
```

### dt()

How many seconds the last frame took. Multiply by `dt()` to move at the same
speed on a fast computer and a slow one.

```python
player = add([sprite("bean"), pos(100, 100)])

@onUpdate
def drift():
    player.pos.x += 60 * dt()      # 60 pixels a second, not 60 a frame
```

### raycast(origin, direction, exclude, max_distance, ignore)

The first `area()` a straight line runs into, as a hit with `.obj`, `.point`,
`.distance` and `.normal` — or `None`. `exclude` skips tags, `ignore` skips
particular objects, which is what you want when casting from an object's own
position, since the ray starts inside its own box.

```python
player = add([sprite("bean"), pos(100, 300), area()])
add([rect(20, 200), pos(400, 200), area(), "wall"])

hit = raycast(player.pos, vec2(1, 0), ignore=[player])
if hit:
    print("wall at", hit.distance, "px")
```

---

### time()

Seconds since `kaypy()` started.

```python
label = add([text("0"), pos(10, 10), fixed()])

@onUpdate
def tick():
    label.text = str(round(time(), 1))
```

### setGravity(n)

How hard things with a `body()` fall. Off by default — a top-down game wants no
gravity at all.

```python
setGravity(2400)
```

### setBackground(r, g, b)

Change the background color after the game has started.

```python
setBackground(40, 10, 60)
```

---

## Loading pictures and sounds

Loading and using are separate steps. Forgetting the load is the commonest
reason a sprite does not appear.

### loadSprite(name, path, sliceX, sliceY, anims)

Make a picture available under a name. `sliceX` and `sliceY` cut a strip of
frames out of one image, and `anims` names runs of those frames.

```python
loadSprite("coin", "images/coin.png")

# A strip of 8 frames across, with two named animations cut out of it.
loadSprite("angel", "dungeon/angel.png", sliceX=8, anims={
    "idle": {"from": 0, "to": 3, "speed": 8, "loop": True},
    "run": {"from": 4, "to": 7, "speed": 10, "loop": True},
})
```

### loadSpriteAtlas(path, atlas)

One image holding many sprites, cut up by coordinates. More work than separate
files, and it is how most real sprite sheets arrive.

```python
loadSpriteAtlas("dungeon.png", {
    "wall": {"x": 16, "y": 16, "width": 16, "height": 16},
    "hero": {"x": 128, "y": 196, "width": 144, "height": 28, "sliceX": 9},
})

add([sprite("hero"), pos(100, 100)])
```

### loadSound(name, path)

Make a sound available under a name.

```python
loadSound("ding", "sounds/ding.wav")
```

---

## Making things

### add(components)

Build a game object out of a list of components, and put it in the world.
Returns the object, so you can keep it in a variable.

```python
player = add([
    sprite("bean"),
    pos(120, 80),
    area(),
    body(),
    "player",                    # a plain string is a tag
    {"hits": 0, "dir": 1},       # a dict is your own values
])

player.hits += 1
```

A **tag** says what something is: `get("enemy")` finds every object carrying
one, and `onCollide("enemy")` works off it. A **dict** is that object's own
state — `hits`, `dir`, `cooldown` — set as ordinary attributes you can read and
change.

A key that a component already owns is refused rather than quietly shadowing
it, and so is a key that is not a valid Python name.

### get(tag)

Every object carrying a tag, as a list.

```python
add([sprite("bean"), pos(100, 100), "enemy"])
add([sprite("bean"), pos(200, 100), "enemy"])

for e in get("enemy"):
    e.pos.x += 10
```

### destroy(obj)

Remove one object. `obj.destroy()` does the same thing.

```python
coin = add([sprite("bean"), pos(300, 300), area(), "coin"])
destroy(coin)
```

### destroyAll(tag)

Remove every object carrying a tag. Returns how many went.

```python
add([sprite("bean"), pos(10, 10), "bullet"])
add([sprite("bean"), pos(40, 10), "bullet"])

gone = destroyAll("bullet")      # 2
```

### addLevel(layout, config)

Build a level out of a picture made of characters. Each character maps to a
list of components; a space is nothing.

```python
addLevel([
    "                    ",
    "         @          ",
    "  ====        ===   ",
    "====================",
], {
    "tileWidth": 32,
    "tileHeight": 32,
    "tiles": {
        "=": lambda: [rect(32, 32), area(), body(isStatic=True), color(90, 150, 70)],
        "@": lambda: [sprite("bean"), area(), body(), "player"],
    },
})
```

### addKaboom(position, scale)

The explosion from KAPLAY, at a point. Cleans itself up.

```python
addKaboom(vec2(400, 300), scale=2.0)
```

---

## Components

A component is one thing an object *has*. Add one, get one behavior; delete
one, lose exactly that. Most give the object some attributes and methods of
its own, which are listed with each.

### pos(x, y)

Where the object is. Without it, an object has no place in the world.

```python
player = add([sprite("bean"), pos(120, 80)])

player.pos.x = 300           # .pos is a vec2 you can read and set
player.move(100, 0)          # move, in pixels per second
player.moveTo(vec2(400, 300), 200)
```

### sprite(name, anim, frame)

Draw a loaded picture. `anim` starts a named animation straight away.

```python
loadSprite("angel", "dungeon/angel.png", sliceX=8, anims={
    "idle": {"from": 0, "to": 3, "speed": 8, "loop": True},
    "run": {"from": 4, "to": 7, "speed": 10, "loop": True},
})

a = add([sprite("angel", anim="idle"), pos(100, 100)])
a.play("run")                # switch animation
a.flipX = True               # face the other way
```

### rect(width, height, radius)

A rectangle, for a platform or a bar when a picture would be overkill.

```python
add([rect(200, 24, radius=6), pos(80, 400), color(90, 150, 70)])
```

### circle(radius)

A circle.

```python
add([circle(18), pos(400, 300), color(255, 200, 60)])
```

### text(text_str, size, width)

Words on the screen. `width` wraps them.

```python
label = add([text("Score: 0", size=28), pos(12, 12), fixed()])
label.text = "Score: 1"      # change it whenever
```

### area()

A collision box, so the object can touch things. On its own it is a trigger you
pass through; add `body()` to make it solid.

```python
coin = add([sprite("bean"), pos(300, 300), area(), "coin"])

if coin.isHovering():
    pass                     # the mouse is over it
```

### body(isStatic, mass, jumpForce)

Gravity, falling and jumping. `isStatic=True` means the thing never moves and
everything else lands on it.

```python
setGravity(2400)

add([rect(width(), 48), pos(0, height() - 48), area(), body(isStatic=True)])
player = add([sprite("bean"), pos(120, 80), area(), body(jumpForce=900)])

@onKeyPress("space")
def jump():
    if player.isGrounded():
        player.jump()
```

### anchor(value)

Which part of the object `pos()` refers to. `"topleft"` by default; `"center"`
and `"bot"` are the two you will reach for.

```python
# pos() now means where its feet are, which is what you want on a floor.
add([sprite("bean"), pos(200, 400), anchor("bot")])
```

### scale(x, y)

Bigger or smaller. One number scales both ways.

```python
add([sprite("bean"), pos(200, 200), scale(2)])
add([sprite("bean"), pos(400, 200), scale(2, 0.5)])
```

### rotate(angle)

Turn the object, in degrees.

```python
arrow = add([rect(60, 8), pos(400, 300), anchor("center"), rotate(0)])

arrow.angle = 45
arrow.rotateBy(10)
arrow.rotateTo(90)
```

### color(r, g, b)

Tint. On a `rect()` or `circle()` it is the fill; on a sprite it multiplies.

```python
add([rect(100, 100), pos(50, 50), color(255, 80, 80)])
```

### opacity(n)

How solid, from `0` to `1`.

```python
ghost = add([sprite("bean"), pos(200, 200), opacity(0.4)])
ghost.opacity = 1.0
```

### outline(width, color)

A border, for a shape.

```python
add([rect(120, 40), pos(60, 60), color(40, 40, 60), outline(3, (255, 255, 255))])
```

### z(value)

What draws on top. Higher is nearer the front.

```python
add([rect(200, 200), pos(100, 100), color(30, 30, 40), z(0)])
add([sprite("bean"), pos(150, 150), z(10)])      # in front
```

### fixed()

Stay put when the camera moves. Everything on a HUD wants this.

```python
add([text("Score: 0", size=24), pos(12, 12), fixed()])
```

### move(direction, speed)

Drift in a direction for ever, without an `onUpdate` of your own. Good for
bullets.

```python
add([sprite("bean"), pos(50, 300), move(vec2(1, 0), 400), offscreen(destroy=True)])
```

### offscreen(destroy, distance)

What to do once the object is off the edge. Bullets that leave and are never
cleaned up are the commonest slow leak in a first game.

```python
add([sprite("bean"), pos(0, 100), move(vec2(1, 0), 500),
     offscreen(destroy=True, distance=100)])
```

### tile(isObstacle)

Marks an object as part of a tile grid, for `addLevel()`. `isObstacle=True`
means paths do not go through it.

```python
add([rect(32, 32), pos(64, 64), area(), body(isStatic=True), tile(isObstacle=True)])
```

### state(start, states)

A named state machine, so an enemy can idle, chase and attack without a tangle
of booleans.

```python
enemy = add([sprite("bean"), pos(400, 300), state("idle", ["idle", "chase"])])

@enemy.onStateEnter("chase")
def start_chase():
    print("chasing")

@enemy.onStateUpdate("idle")
def waiting():
    pass

enemy.enterState("chase")
```

### health(hp, maxHP)

Hit points, and the handlers that go with them. `onDeath` fires exactly once,
however many things land in the same frame — a death handler that runs twice
drops two coins and scores twice.

```python
player = add([sprite("bean"), pos(100, 100), health(3)])

@player.onHurt
def ouch(amount):
    print("hp now", player.hp)

@player.onDeath
def died():
    player.destroy()

player.hurt(1)
player.heal(1)
player.isAlive()
```

### follow(obj, offset, speed)

Be where another object is. Without `speed` it locks on exactly, every frame,
which is what a health bar or a name label wants. With `speed` it chases at
that many pixels per second instead, which is what a pet or a hunting enemy
wants. If the target is destroyed, the follower stops where it stands.

```python
enemy = add([sprite("bean"), pos(400, 200)])
add([rect(40, 6), pos(0, 0), color(220, 60, 60),
     follow(enemy, offset=vec2(-4, -30))])

player = add([sprite("bean"), pos(100, 300)])
add([circle(10), pos(0, 0), follow(player, speed=180)])
```

---

### sentry(candidates, direction, fieldOfView, range, lineOfSight, raycastExclude, checkFrequency)

Notice when something comes into view. `fieldOfView` is the whole width of the
cone in degrees; `range` is how far it can see; `lineOfSight=True` means walls
stop it. Leave `direction` out and it looks wherever `rotate()` has the object
turned. `onObjectsSpotted` fires when it goes from seeing nothing to seeing
something, and `.spotted` is the current list.

`range` is not KAPLAY's — without it a guard sees to the end of the level, so
leaving it out behaves exactly as KAPLAY does.

```python
player = add([sprite("bean"), pos(600, 300), area(), "player"])

guard = add([sprite("bean"), pos(200, 300), area(), rotate(0),
             sentry("player", fieldOfView=70, range=300, lineOfSight=True)])

@guard.onObjectsSpotted
def seen(objects):
    print("spotted", len(objects))
```

---

### lifespan(seconds, fade)

Destroy the object after a while, fading out first if you ask. Belongs to the
bullet, rather than to a timer somewhere else holding it alive.

```python
add([sprite("bean"), pos(300, 200), lifespan(2, fade=0.5)])
```

---

## Every frame

### onUpdate(fn) / onUpdate(tag, fn)

Run something on every frame. With a tag, it runs once per object carrying it,
and the object is passed in.

```python
player = add([sprite("bean"), pos(100, 100)])

@onUpdate
def creep():
    player.pos.x += 1

add([sprite("bean"), pos(300, 100), "enemy"])

@onUpdate("enemy")
def drift(e):
    e.pos.y += 0.5
```

### run()

Not KAPLAY's API, and you almost never want it. The loop starts by itself once
your file has finished — that is the whole point. It exists for the rare
program that must start the loop early, on purpose.

```python
# Written for completeness. A normal game never calls this.
# run()
```

---

## Keyboard

Key names are KAPLAY's: `"left"`, `"right"`, `"up"`, `"down"`, `"space"`,
`"enter"`, `"escape"`, and any letter or digit as itself.

### onKeyDown(key, fn)

Every frame the key is held. This is the one for walking.

```python
player = add([sprite("bean"), pos(100, 100)])

@onKeyDown("right")
def go_right():
    player.move(320, 0)
```

### onKeyPress(key, fn)

Once, the frame the key goes down. This is the one for jumping — `onKeyDown`
would fire every frame you hold space.

```python
setGravity(2400)
player = add([sprite("bean"), pos(100, 100), area(), body()])

@onKeyPress("space")
def jump():
    if player.isGrounded():
        player.jump(900)
```

### onKeyRelease(key, fn)

Once, when the key comes back up.

```python
@onKeyRelease("space")
def let_go():
    print("released")
```

### isKeyDown(key)

Ask, rather than being told. Useful inside an `onUpdate` that already has a
reason to run.

```python
player = add([sprite("bean"), pos(100, 100)])

@onUpdate
def walk():
    if isKeyDown("left"):
        player.move(-320, 0)
    if isKeyDown("right"):
        player.move(320, 0)
```

---

## Mouse

Buttons are named — `"left"`, `"right"`, `"middle"` — and default to the left
one. pygame numbers them 1, 2, 3 with middle in the middle, which is not the
order anyone guesses.

### onClick(fn)

A left click anywhere. On an object with `area()`, use `obj.onClick` instead
and it only fires on that object.

```python
@onClick
def clicked():
    print("clicked at", mousePos())
```

### onMousePress(button, fn)

Once, when a button goes down.

```python
@onMousePress("right")
def aim():
    print("right button down")
```

### onMouseRelease(button, fn)

Once, when a button comes back up.

```python
@onMouseRelease
def fire():
    print("let go")
```

### onMouseDown(button, fn)

Every frame a button is held — for dragging or hold-to-charge.

```python
brush = add([circle(6), pos(0, 0), color(255, 80, 80)])

@onMouseDown
def drag():
    brush.pos = mousePos()
```

### onMouseMove(fn)

Whenever the mouse moves.

```python
@onMouseMove
def look():
    pass
```

### isMouseDown(button)

Is that button held right now?

```python
@onUpdate
def check():
    if isMouseDown("left"):
        pass
```

### isMousePressed(button)

Did it go down this frame?

```python
@onUpdate
def check():
    if isMousePressed():
        print("just pressed")
```

### isMouseReleased(button)

Did it come up this frame?

```python
@onUpdate
def check():
    if isMouseReleased():
        print("just released")
```

### isMouseMoved()

Did the mouse move this frame?

```python
@onUpdate
def check():
    if isMouseMoved():
        pass
```

### mousePos()

Where the mouse is, as a `vec2`, in screen coordinates.

```python
aim = add([circle(4), pos(0, 0)])

@onUpdate
def follow():
    aim.pos = mousePos()
```

### mouseDeltaPos()

How far the mouse moved this frame, as a `vec2`.

```python
@onUpdate
def look():
    d = mouseDeltaPos()
    if d.x or d.y:
        pass
```

### toWorld(pos)

Turn a screen position into a world position. With the camera moved, the mouse
is not where it looks.

```python
setCamPos(vec2(400, 0))

@onUpdate
def where():
    spot = toWorld(mousePos())
```

---

## Drawing straight to the screen

Marks for one frame — a health bar, an aim line, a grid — rather than things in
the world. They only work inside `onDraw`, and say so if you call them
elsewhere: a drawing that silently never appears is close to undebuggable.

### onDraw(fn)

Where the draw functions below are allowed. Runs after the game objects.

```python
@onDraw
def hud():
    drawText(text="Score: 0", pos=vec2(12, 12), size=24, fixed=True)
```

### drawRect(pos, width, height, color, ...)

A rectangle. `radius` rounds the corners, `fixed=True` pins it to the screen.

```python
@onDraw
def bar():
    drawRect(pos=vec2(12, 40), width=120, height=12, color=(60, 60, 60), fixed=True)
    drawRect(pos=vec2(12, 40), width=80, height=12, color=(90, 200, 90), fixed=True)
```

### drawCircle(pos, radius, color, ...)

A circle, centred on `pos`.

```python
@onDraw
def blip():
    drawCircle(pos=vec2(400, 300), radius=30, color=(255, 200, 60), opacity=0.6)
```

### drawLine(p1, p2, width, color, ...)

A line from one point to another.

```python
player = add([sprite("bean"), pos(100, 100)])

@onDraw
def aim_line():
    drawLine(p1=player.pos, p2=mousePos(), width=2, color=(255, 255, 255))
```

### drawLines(points, width, color, close, ...)

A run of connected lines. `close=True` joins the last point back to the first.

```python
@onDraw
def shape():
    drawLines(points=[vec2(100, 100), vec2(200, 140), vec2(160, 220)],
              width=3, color=(120, 200, 255), close=True)
```

### drawText(text, pos, size, color, ...)

Words, in the same font as the `text()` component.

```python
@onDraw
def label():
    drawText(text="Paused", pos=vec2(340, 280), size=32, color=(255, 255, 255))
```

### drawSprite(sprite, pos, frame, ...)

One frame of a loaded sprite, without making a game object out of it. Good for
a row of lives.

```python
@onDraw
def lives():
    for i in range(3):
        drawSprite(sprite="bean", pos=vec2(12 + i * 28, 70), width=24, height=24,
                   fixed=True)
```

---

## Pausing, and asking a question

A panel freezes the game, puts a question or a message over it, and starts
the game again when it is answered. The same lines work in a browser and on
your own computer: in a browser the panel is real HTML, so the text can be
selected and a link is a real link; on a desktop KayPy draws it.

**These call you back rather than returning an answer.** In a browser,
waiting for a click would stop the page — including the click being waited
for — so the tab would hang instead of pausing. Your function gets the answer
when there is one.

### pause()

Freeze the game, leaving the picture up. Timers, gravity, collisions and
every `onUpdate` stop; the frame is still drawn.

Key handlers keep running, which is what lets a pause menu un-pause itself.
Nothing moves while paused, because everything that moves is scaled by
`dt()` and `dt()` is zero.

```python
@onKeyPress("escape")
def toggle():
    resume() if isPaused() else pause()
```

### resume()

Start the game moving again.

```python
player = add([sprite("bean"), pos(100, 100)])
pause()
resume()
```

### isPaused()

Is the game frozen right now?

```python
label = add([text(""), pos(12, 12), fixed()])

@onUpdate
def show():
    label.text = "PAUSED" if isPaused() else ""
```

### say(text, link, button)

Pause and show a message: the text, and one button to close it. Enter or
space closes it too. `link` is a `(label, url)` pair — a real link in a
browser, and on a desktop it opens your browser.

```python
say("You found the key!")

@say("I built this in 2023.", link=("See the repo", "https://github.com"))
def after():
    print("they closed it")
```

A message has nothing to fill in, so your function is called with nothing.
Give it `ask()` if you want an answer back.

### ask(question, choices, answer, placeholder)

Pause and ask something. With `choices` it is multiple choice, and can be
answered by clicking or by pressing the number beside it. Without `choices`
it is a box to type in.

With `answer=`, your function is told **True or False**. Without it, your
function is given **what was picked or typed**.

```python
@ask("Which keyword starts a loop?", ["if", "for", "def"], answer=1)
def checked(correct):
    if correct:
        print("open sesame")

@ask("What is your name?")
def greeted(reply):
    print("Hello, " + reply)
```

`answer` may be the position of the right choice (`answer=1`) or its text
(`answer="for"`). For a typed answer it can be one string or a list of
acceptable ones, and marking ignores capitals and stray spaces — `"  PARIS "`
matches `answer="paris"`.

**Ask several and they queue up.** Only one panel is on screen at a time, so a
second `say()` or `ask()` opened while one is up waits its turn and appears
when that one is answered. Writing a quiz as a stack of decorators therefore
does what it looks like:

```python
@ask("What is your name?")
def greeted(reply):
    print("Hello, " + reply)

@ask("Which keyword starts a loop?", ["if", "for", "def"], answer=1)
def checked(correct):
    if correct:
        print("open sesame")
```

They are asked top to bottom, and the game stays paused until the last one is
answered. `close()` dismisses the panel on screen and moves on to the next;
it does not cancel the ones behind it.

### isShowing()

Is a panel up right now?

```python
say("Mind the gap.")
if isShowing():
    pass
```

### close()

Take the panel away and start the game again. Answering does this for you;
it is here for a game that needs to close one itself.

```python
say("This closes itself in a moment.")
close()
```

---

## Collisions

### onCollide(tag_a, tag_b, fn)

Every time anything tagged `tag_a` touches anything tagged `tag_b`. For one
particular object, use `obj.onCollide(tag)` instead.

```python
add([sprite("bean"), pos(100, 100), area(), "player"])
add([sprite("bean"), pos(110, 100), area(), "coin"])

@onCollide("player", "coin")
def got(p, c):
    c.destroy()
```

---

## Camera

### setCamPos(pos)

Move the camera. Anything with `fixed()` stays where it is.

```python
setCamPos(vec2(600, 200))
```

### setCamScale(n)

Zoom. Above 1 is closer in. A `vec2` zooms each axis by a different amount,
for a letterboxed cutscene or a squash as something lands.

```python
setCamScale(1.5)                # closer in, both ways
setCamScale(vec2(2, 0.4))       # twice as wide, squashed flat
```

### shake(n)

Shake the camera, once. Settles by itself.

```python
shake(12)
```

---

## Sound

### play(name, loop, paused, volume)

Play a loaded sound. Returns a handle whose `.volume` and `.paused` you can
change while it plays.

```python
loadSound("ding", "sounds/ding.wav")

s = play("ding", volume=0.5)
s.volume = 0.2
s.paused = True
```

---

## Time

### wait(seconds, fn)

Do something once, later.

```python
@wait(1.5)
def later():
    print("one and a half seconds in")
```

### loop(seconds, fn)

Do something over and over, for ever.

```python
@loop(2)
def spawn():
    add([sprite("bean"), pos(rand(0, width()), 0), area()])
```

### tween(start, end, duration, setter, ease)

Change a value smoothly over time. `setter` is called with each step.

```python
box = add([rect(40, 40), pos(50, 50), color(255, 120, 60)])

tween(50, 600, 1.2, lambda x: setattr(box.pos, "x", x), easings.easeOutQuad)
```

### easings

The curves `tween` can take, as attributes: `linear`, `easeInQuad`,
`easeOutQuad`, `easeInOutQuad`, `easeOutBounce` and the rest.

```python
box = add([circle(12), pos(50, 300)])

tween(50, 700, 1.0, lambda x: setattr(box.pos, "x", x), easings.easeOutBounce)
```

---

## Scenes

### scene(name, fn)

Define a named screen — a menu, a level, a game-over. The function builds it.

```python
@scene("menu")
def menu():
    add([text("Press space", size=32), pos(200, 280)])

    @onKeyPress("space")
    def start():
        go("game")

@scene("game")
def game():
    add([sprite("bean"), pos(100, 100)])

go("menu")
```

### go(name, *args)

Switch to a scene. Everything from the old one is thrown away first —
objects, handlers and timers — so nothing leaks between screens.

```python
@scene("level")
def level(number):
    add([text("Level " + str(number), size=28), pos(20, 20)])

go("level", 3)
```

---

## Saving

Kept in a file next to the game on a computer, and in the browser's own
storage on the web. Only things that can be written down: numbers, text,
`True`/`False`, `None`, and lists and dicts of those.

### setData(key, value)

Remember something under a name. Returns `True` if it was written — a
locked-down school account is not a reason to crash.

```python
setData("highscore", 1200)
setData("settings", {"sound": True, "level": 3})
```

### getData(key, default)

What was remembered, or `default` if there is nothing.

```python
best = getData("highscore", 0)
```

---

## Maths and helpers

### vec2(x, y)

A pair of numbers, with the arithmetic that goes with them. `vec2(3)` means
`(3, 3)`; `vec2(other)` copies.

```python
a = vec2(3, 4)
b = a.add(vec2(1, 1))
a.len()
a.unit()
a.dist(b)
a.lerp(b, 0.5)
```

### Vec2

The class itself, for `isinstance` checks. `vec2()` is how you make one.

```python
p = vec2(1, 2)
if isinstance(p, Vec2):
    pass
```

### rand(a, b)

A random float. One argument means from zero.

```python
x = rand(0, width())
```

### randi(a, b)

A random whole number, `b` not included.

```python
n = randi(1, 7)          # 1 to 6
```

### choose(seq)

One item from a list, at random.

```python
name = choose(["bean", "bean", "bean"])
```

### chance(probability)

`True` that often. `chance(0.2)` is true one time in five.

```python
@loop(1)
def maybe():
    if chance(0.3):
        add([sprite("bean"), pos(rand(0, width()), 0)])
```

### lerp(a, b, t)

Blend from `a` to `b`. Works on numbers and on `vec2`.

```python
player = add([sprite("bean"), pos(100, 100)])
target = vec2(600, 400)

@onUpdate
def chase():
    player.pos = lerp(player.pos, target, 0.05)
```

### clamp(value, low, high)

Keep a number inside a range.

```python
player = add([sprite("bean"), pos(100, 100)])

@onUpdate
def keep_in():
    player.pos.x = clamp(player.pos.x, 0, width())
```

### wave(low, high, t, func)

A value swinging between two others, for ever. Good for bobbing and pulsing.

```python
cloud = add([sprite("bean"), pos(200, 100)])

@onUpdate
def bob():
    cloud.pos.y = wave(80, 120, time() * 2)
```

### rgb(r, g, b)

A color as a plain tuple. One argument means gray, and a hex string works too.

```python
add([rect(80, 80), pos(40, 40), color(rgb(255, 120, 60))])
```

### RED

The eight named colors are plain `(r, g, b)` tuples, so they go anywhere a
color goes: `color()`, `outline()`, `setBackground()` and `background=`.

```python
add([rect(80, 80), pos(40, 40), color(RED)])
```

### GREEN

```python
add([circle(30), pos(120, 60), color(GREEN)])
```

### BLUE

```python
setBackground(BLUE)
```

### YELLOW

```python
add([text("score: 0"), pos(20, 20), color(YELLOW)])
```

### MAGENTA

```python
add([rect(40, 40), pos(200, 80), color(MAGENTA)])
```

### CYAN

```python
add([rect(60, 20), pos(60, 200), outline(3, CYAN)])
```

### WHITE

`WHITE` is `(255, 255, 255)`, which is also what `color()` gives you if you
pass it nothing at all.

```python
add([text("ready"), pos(40, 140), color(WHITE)])
```

### BLACK

```python
add([rect(50, 50), pos(150, 150), color(BLACK)])
```

### deg2rad(degrees)

Degrees to radians.

```python
r = deg2rad(90)
```

### rad2deg(radians)

Radians to degrees.

```python
d = rad2deg(3.14159)
```

---

## Debugging

### debug

`debug.inspect = True` draws every collision box, so you can see why two
things are not touching. **F1** toggles it while the game runs.

```python
debug.inspect = True
```

---

## What you can call on an object

`add()` hands back an object, and what that object can do depends on which
components it has. These are written `obj.name()` because you call them on the
thing, not on their own.

### .add([components])

Build a game object **inside** this one. A child's `pos()` is measured from its
parent rather than from the screen, and it moves when the parent moves.
Destroying the parent destroys its children too.

Use it for the things that belong to something: a sword in a hand, a health bar
over a head, a turret on a tank.

```python
player = add([sprite("bean"), pos(100, 200), area()])

sword = player.add([rect(6, 30), pos(28, 6), color(200, 200, 220), area()])

player.pos = vec2(400, 350)     # the sword goes too, still at +28, +6
```

### .destroy()

Remove it from the world. Same as `destroy(obj)`.

```python
coin = add([sprite("bean"), pos(300, 300), area()])
coin.destroy()
```

### .exists()

Is it still in the world? A handler holding an object that has already been
destroyed is a common shape for a crash.

```python
coin = add([sprite("bean"), pos(300, 300)])
coin.destroy()
if not coin.exists():
    pass
```

### .has(comp_id)

Does it have that component?

```python
player = add([sprite("bean"), pos(0, 0), area(), body()])
if player.has("body"):
    pass
```

### .is_(tag)

Does it carry that tag? Named with a trailing underscore because `is` is a
Python keyword — one of the few places the API cannot match KAPLAY exactly.

```python
e = add([sprite("bean"), pos(0, 0), "enemy"])
e.is_("enemy")
```

### .use(comp)

Add a component after the object has been made.

```python
ghost = add([sprite("bean"), pos(100, 100)])
ghost.use(area())
ghost.use(body())
```

### .comp(comp_id)

The component object itself, when you need at its internals.

```python
player = add([sprite("bean"), pos(0, 0), area(), body()])
b = player.comp("body")
```

### .move(dx, dy)

Move, in pixels per second — so it is frame-rate independent already and does
not need `dt()`. From `pos()`.

```python
player = add([sprite("bean"), pos(100, 100)])

@onKeyDown("right")
def go():
    player.move(320, 0)
```

### .moveTo(target, speed)

Head towards a point. Without a speed it arrives at once.

```python
enemy = add([sprite("bean"), pos(600, 300)])

@onUpdate
def chase():
    enemy.moveTo(vec2(100, 300), 80)
```

### .jump(force)

Jump, if it has a `body()`. Uses the component's `jumpForce` when you give no
number.

```python
setGravity(2400)
player = add([sprite("bean"), pos(100, 100), area(), body(jumpForce=900)])

@onKeyPress("space")
def jump():
    player.jump()
```

### .isGrounded()

Is it standing on something? Check this before jumping, or a player can jump
in mid-air for ever.

```python
setGravity(2400)
player = add([sprite("bean"), pos(100, 100), area(), body()])

@onKeyPress("space")
def jump():
    if player.isGrounded():
        player.jump(900)
```

### .onGround(fn)

Fires when it lands.

```python
setGravity(2400)
player = add([sprite("bean"), pos(100, 40), area(), body()])

@player.onGround
def landed():
    print("thud")
```

### .onCollide(tag, fn)

Every time this object touches something with that tag. The other object is
passed in.

```python
player = add([sprite("bean"), pos(100, 100), area()])
add([sprite("bean"), pos(105, 100), area(), "coin"])

@player.onCollide("coin")
def collect(coin):
    coin.destroy()
```

### .onCollideUpdate(tag, fn)

Every frame the two are overlapping, rather than once when they meet.

```python
player = add([sprite("bean"), pos(100, 100), area()])

@player.onCollideUpdate("lava")
def burning(lava):
    pass
```

### .onCollideEnd(tag, fn)

Once, when they stop touching.

```python
player = add([sprite("bean"), pos(100, 100), area()])

@player.onCollideEnd("water")
def out(water):
    pass
```

### .onUpdate(fn)

Every frame, for this object only.

```python
cloud = add([sprite("bean"), pos(100, 100)])

@cloud.onUpdate
def drift():
    cloud.pos.x += 0.5
```

### .onClick(fn)

A click on this object. Needs `area()`.

```python
button = add([rect(120, 40), pos(60, 60), area()])

@button.onClick
def pressed():
    print("clicked")
```

### .isHovering()

Is the mouse over it? Needs `area()`.

```python
button = add([rect(120, 40), pos(60, 60), area()])

@onUpdate
def highlight():
    if button.isHovering():
        button.color = (255, 255, 255)
```

### .play(name)

Start a named animation, on an object with an animated `sprite()`.

```python
loadSprite("angel", "dungeon/angel.png", sliceX=8, anims={
    "idle": {"from": 0, "to": 3, "speed": 8, "loop": True},
    "run": {"from": 4, "to": 7, "speed": 10, "loop": True},
})

a = add([sprite("angel"), pos(100, 100)])
a.play("run")
```

### .curAnim()

Which animation is playing, by name.

```python
loadSprite("angel", "dungeon/angel.png", sliceX=8, anims={
    "idle": {"from": 0, "to": 3, "speed": 8, "loop": True},
})

a = add([sprite("angel", anim="idle"), pos(100, 100)])
if a.curAnim() == "idle":
    pass
```

### .size()

How big it is on screen, as a `vec2`. Works for a sprite, a rect, a circle and
text.

```python
label = add([text("Score", size=24), pos(10, 10)])
w = label.size()
```

### .hurt(amount)

Take damage, on an object with `health()`.

```python
player = add([sprite("bean"), pos(100, 100), health(3)])
player.hurt(1)
```

### .heal(amount)

The other way. Never goes above `maxHP`.

```python
player = add([sprite("bean"), pos(100, 100), health(3, maxHP=5)])
player.hurt(2)
player.heal(1)
```

### .isAlive()

Are its hit points above zero?

```python
player = add([sprite("bean"), pos(100, 100), health(1)])
player.hurt(1)
alive = player.isAlive()
```

### .setHP(value)

Set hit points outright, without counting as damage or healing.

```python
player = add([sprite("bean"), pos(100, 100), health(3)])
player.setHP(2)
```

### .onHurt(fn) / .onHeal(fn) / .onDeath(fn)

Handlers for the three. `onDeath` fires **exactly once**, however many things
land in the same frame, and it does not destroy the object — so it can play an
animation first.

```python
enemy = add([sprite("bean"), pos(300, 300), health(2)])

@enemy.onHurt
def flinch(amount):
    shake(4)

@enemy.onDeath
def die():
    addKaboom(enemy.pos)
    enemy.destroy()

enemy.hurt(2)
```

### .enterState(name)

Switch a `state()` object to another state.

```python
enemy = add([sprite("bean"), pos(300, 300), state("idle", ["idle", "chase"])])
enemy.enterState("chase")
```

### .onStateEnter(name, fn)

Runs once, when it arrives in that state.

```python
enemy = add([sprite("bean"), pos(300, 300), state("idle", ["idle", "chase"])])

@enemy.onStateEnter("chase")
def begin():
    print("after them")
```

### .onStateUpdate(name, fn)

Runs every frame while it is in that state.

```python
enemy = add([sprite("bean"), pos(300, 300), state("idle", ["idle", "chase"])])

@enemy.onStateUpdate("chase")
def chasing():
    enemy.pos.x -= 1
```

### .rotateBy(degrees) / .rotateTo(degrees)

Turn by an amount, or to an angle. Needs `rotate()`.

```python
arrow = add([rect(60, 8), pos(400, 300), anchor("center"), rotate(0)])
arrow.rotateBy(15)
arrow.rotateTo(90)
```
