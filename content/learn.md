# Learn Python

Python, taught with a game on the screen.

Most Python lessons ask you to print things. Printing is fine, and you will do
plenty of it here — but a loop that prints `Wave 3 incoming` is a loop you have
to *imagine*. A loop that puts forty tiles on the screen is a loop you can
point at.

So every lesson here does both. The idea first, in plain Python, where you can
see exactly what happened. Then the same idea building something you can play.

**You need nothing installed.** Open the [playground](../play/), type, press
Run. If you would rather work on your own machine, [Get started](../start/)
takes four commands.

> **What this is not.** This is not the [guide](../guide/). The guide teaches
> the engine — sprites, collision, scenes — and assumes you already know what a
> variable and a function are. These pages teach Python itself, and use the
> engine to make it visible.

---

## Lesson 1 — Conditionals

**By the end of this you can:** make a program choose, compare values with
`==` and `<`, chain decisions with `elif`, combine tests with `and` and `or`,
and make a game react to what is actually happening.

### The problem conditionals solve

Here is a program with no decision in it:

```python
health = 100
health = health - 30
print("Health:", health)
```

```
Health: 70
```

It works. It also does exactly the same thing every single time you run it,
which is the problem. A game that cannot notice anything is not a game — it is
an animation. Something has to be able to ask *has this happened yet?*

That question is `if`:

```python
health = 30

if health < 50:
    print("Warning: low health")

print("Still playing")
```

```
Warning: low health
Still playing
```

Change `health` to 70 and run it again. The warning disappears and
`Still playing` is all you get. The program now behaves differently depending
on what is true, and nothing about the code changed.

Two things to notice, because both catch people:

- The line ends in a **colon**.
- The line underneath is **indented**. That indent is what says "this belongs
  to the `if`". `print("Still playing")` is back out at the left, so it is not
  part of the decision and always runs.

### Asking the question

The thing between `if` and the colon is a **comparison**, and it comes out
either `True` or `False`:

```python
print(10 > 5)
print(10 < 5)
print(10 == 10)
print(10 != 10)
print(10 >= 10)
print(3 <= 2)
```

```
True
False
True
False
True
False
```

- `>` and `<` — bigger than, smaller than.
- `>=` and `<=` — bigger *or equal*, smaller *or equal*.
- `==` — **equal**. Two equals signs, always.
- `!=` — not equal.

**`=` and `==` are different and it matters.** One equals sign *stores*:
`health = 30` puts 30 into health. Two equals signs *asks*: `health == 30` is a
question whose answer is True or False. Writing this:

```text
if health = 30:
```

is not a typo Python can forgive — it stops with `SyntaxError: invalid syntax`,
because you asked it to store something in the middle of a question. It is the
most common mistake in this lesson, and the error message does not explain
itself, so learn what the message means rather than what it says.

### `else` — the other path

`if` on its own does something or does nothing. `else` gives it somewhere to go:

```python
score = 40

if score >= 50:
    print("You win")
else:
    print("Try again")
```

```
Try again
```

Exactly one of those two lines will print, always. That is the point of
`else`: there is no way to fall through both.

### `elif` — more than two answers

Real games have more than two outcomes. `elif` — short for "else if" — chains
them:

```python
score = 78

if score >= 90:
    print("Rank: S")
elif score >= 75:
    print("Rank: A")
elif score >= 50:
    print("Rank: B")
else:
    print("Rank: C")
```

```
Rank: A
```

Python checks them **top to bottom and stops at the first one that is True**.
78 is not 90 or more, so it moves on. 78 *is* 75 or more, so it prints
`Rank: A` and skips everything below — including `score >= 50`, which is also
true. First match wins.

That "stops at the first true one" is the whole reason `elif` exists. Watch
what happens with three separate `if` statements instead:

```python
score = 95

if score >= 90:
    print("Rank: S")
if score >= 75:
    print("Rank: A")
if score >= 50:
    print("Rank: B")
```

```
Rank: S
Rank: A
Rank: B
```

Three ranks for one score. Each `if` is its own separate question, so all
three get asked and all three are true. Nothing errors — you just get nonsense,
which is the worst kind of bug to find.

**Order matters too.** If you put `score >= 50` first, every score of 50 or
more prints `Rank: B` and the better ranks can never be reached. With `elif`,
put the hardest test at the top.

### `and`, `or`, `not`

Sometimes one question is not enough:

```python
has_key = True
door_locked = True

if has_key and door_locked:
    print("You unlock the door")

if has_key or door_locked:
    print("At least one of those is true")

if not has_key:
    print("You need a key")
```

```
You unlock the door
At least one of those is true
```

- `and` — **both** have to be true.
- `or` — **at least one** has to be true.
- `not` — flips it.

The third one printed nothing, because `has_key` is True, so `not has_key` is
False.

`True` and `False` are real Python values, spelled with a capital letter. You
can store one in a variable like anything else, and a variable holding one is
already a question you can ask:

```python
game_over = False

if not game_over:
    print("Keep going")
```

```
Keep going
```

You never need to write `if game_over == True`. `if game_over` says the same
thing and reads like English.

### Now put it on the screen

A health bar that tells you how worried to be:

```python
from kaypy import *

kaypy(width=800, height=600, background=[20, 24, 36])

health = 30

if health > 60:
    bar = GREEN
elif health > 25:
    bar = YELLOW
else:
    bar = RED

add([rect(health * 4, 30), pos(40, 40), color(bar)])
add([text("Health: " + str(health), size=24), pos(40, 90)])
```

Press Run. The bar is short and yellow, because 30 is more than 25 but not
more than 60.

> **Change one number.** Set `health` to 80 and run it again — long and green.
> Then 10 — short and red. One variable, three completely different pictures,
> and you did not touch the drawing code. That separation is what conditionals
> buy you.

`GREEN`, `YELLOW` and `RED` are colors the engine already knows. There are
eight of them, and they are only numbers — `print(RED)` gives `(255, 0, 0)`.

### Deciding every frame

The examples so far decide once, when the program starts. A game has to keep
deciding, so the test goes inside something that runs every frame:

```python
from kaypy import *

kaypy(width=800, height=600, background=[20, 24, 36])
loadSprite("bean", "images/bean.png")

player = add([sprite("bean"), pos(100, 300), area()])

@onUpdate
def wrap_around():
    player.pos.x = player.pos.x + 3
    if player.pos.x > width():
        player.pos.x = 0
```

The bean walks right, and the moment it goes past the right-hand edge the `if`
notices and puts it back at 0. Run it and watch it loop forever.

`width()` is the width of the window, so this works whatever size you made it.
That is worth more than typing `800` — a number you typed by hand is wrong the
day you change the window.

## Watch for

**`==` asks, `=` stores.** The error is `SyntaxError: invalid syntax` and it
points at the `if` line.

**The colon and the indent are both required.** Forgetting the colon is a
syntax error. Forgetting the indent gives you `IndentationError: expected an
indented block`.

**Use `elif`, not a stack of separate `if`s** — unless you really do want every
true one to happen.

**Put the hardest test first** in an `elif` chain, or it can never be reached.

**Do not compare to `True`.** Write `if ready:` rather than `if ready == True:`.

## Classwork 1 — The Damage Check

Build a program that reacts to a single number.

Start from this and press Run to see where you are:

```python
from kaypy import *

kaypy(width=800, height=600, background=[20, 24, 36])

health = 45

add([text("Health: " + str(health), size=28), pos(40, 40)])
```

Now add, one at a time, running after each:

1. A bar under the text: `rect(health * 4, 24)` at `pos(40, 90)`.
2. Color it with an `if` / `elif` / `else` chain — green above 60, yellow above
   25, red otherwise.
3. A message under the bar that says `Critical!` **only** when health is below
   20. Use a plain `if`, with no `else`.
4. A second variable, `shield = True`, and a line that prints `Shield holding`
   to the console when the shield is up **and** health is above 0.

Change `health` and rerun until you have seen all three bar colors, and made
`Critical!` appear and disappear.

**Stretch:** make `Critical!` appear only when health is below 20 **and** the
shield is down. What do you set the two variables to so that it shows?

## Classwork 2 — The Locked Door

Two sprites and one decision.

```python
from kaypy import *

kaypy(width=800, height=600, background=[20, 24, 36])
loadSprite("bean", "images/bean.png")
loadSprite("key", "images/key.png")
loadSprite("door", "images/door.png")

has_key = False

add([sprite("door"), pos(600, 260)])
add([sprite("bean"), pos(120, 280), area()])
```

1. Add the key to the screen at `pos(340, 300)` — but **only when `has_key` is
   False**. Once it has been picked up there is nothing left to draw.
2. Add a label at `pos(40, 40)` that says `You have the key` or
   `The door is locked`, depending on `has_key`.
3. Set `has_key = True` and run it again. The key should vanish and the label
   should change, and you only changed one word.

**Stretch:** add a `moves_left` number. The label should say `Out of moves`
when it reaches 0, whatever `has_key` is — so that test has to come *first* in
the chain. Prove it by setting `has_key = True` and `moves_left = 0` together.

## Check yourself

What does this print?

```python
lives = 3

if lives > 5:
    print("Plenty")
elif lives > 0:
    print("Careful")
elif lives > 2:
    print("Fine")
else:
    print("Game over")
```

```
Careful
```

<details markdown="1">
<summary>Why not "Fine"?</summary>

`lives > 2` is true — 3 is more than 2 — but Python never gets there. It takes
the **first** branch that is true, which is `lives > 0`, prints `Careful`, and
skips the rest of the chain.

That third branch can never run at all. Any number that passes `lives > 2` has
already passed `lives > 0` one line earlier. A branch that is impossible to
reach is not an error and Python will not warn you, which is exactly why the
order of an `elif` chain is worth reading twice.

</details>

---

## Lesson 2 — Loops

**By the end of this you can:** repeat work without repeating yourself, count
with `range()`, keep a running total, and build a whole level out of six lines.

### The problem loops solve

Say three waves of enemies are coming. You could write it out:

```python
print("Wave 1 incoming")
print("Wave 2 incoming")
print("Wave 3 incoming")
```

```
Wave 1 incoming
Wave 2 incoming
Wave 3 incoming
```

That works. Now make it thirty waves. Or three hundred. Or let the number
change while the game is running.

The moment you find yourself copying a line and changing one small thing in it,
you want a loop:

```python
for wave in range(1, 4):
    print("Wave", wave, "incoming")
```

```
Wave 1 incoming
Wave 2 incoming
Wave 3 incoming
```

Same output, one copy of the line. `wave` is a variable Python creates for you
and fills in with a different value each time round.

### `range()` counts for you

`range()` is where the numbers come from, and it has three forms:

```python
print(list(range(5)))
print(list(range(1, 6)))
print(list(range(0, 101, 25)))
```

```
[0, 1, 2, 3, 4]
[1, 2, 3, 4, 5]
[0, 25, 50, 75, 100]
```

- `range(5)` — five numbers, **starting at 0**, so it stops at 4.
- `range(1, 6)` — start at 1, **stop before 6**.
- `range(0, 101, 25)` — start, stop, and how big a step.

**The stop number is not included.** This catches everybody once:

```python
for wave in range(1, 10):
    print(wave, end=" ")
```

```
1 2 3 4 5 6 7 8 9 
```

Nine waves, not ten. If you want 1 to 10, you write `range(1, 11)` — the stop
number is where it *stops*, not the last number it uses. Say it out loud as
"up to but not including" and it stops being a surprise.

### Now put it on the screen

Here is the same `for` loop, building something:

```python
from kaypy import *

kaypy(width=800, height=600, background=[20, 24, 36])
loadSprite("coin", "images/coin.png")

for i in range(8):
    add([sprite("coin"), pos(80 + i * 80, 300), area(), "coin"])
```

Eight coins in a row. Press Run and count them.

The whole trick is `80 + i * 80`. On the first pass `i` is 0, so the coin goes
at x = 80. Next time `i` is 1, so x = 160. Then 240. The loop variable is doing
the arithmetic that spaces them out, which is why you get a row rather than
eight coins stacked in one place.

> **Change one number.** Make it `range(20)` and watch them run off the edge of
> the screen. Change `i * 80` to `i * 30` and they overlap. Change the `300` to
> `300 + i * 20` and the row becomes a staircase. Do all three before you read
> on — this is the part where loops stop being abstract.

### A loop inside a loop

One loop makes a row. A loop inside a loop makes a grid:

```python
from kaypy import *

kaypy(width=800, height=600, background=[20, 24, 36])
loadSprite("steel", "images/steel.png")

for row in range(4):
    for col in range(10):
        add([sprite("steel"), pos(col * 64, 300 + row * 64), area()])
```

Forty tiles, from six lines.

Read it in the right order and it is not hard: the **outer** loop picks a row
and holds still; the **inner** loop runs all the way across that row before the
outer one moves on. Row 0, ten tiles. Row 1, ten tiles. Four rows, ten each,
forty in total.

The indentation is doing real work here. `add(...)` is indented twice because
it belongs to the inner loop. Pull it back one level and it runs once per row
instead of once per column — four tiles instead of forty.

### `while` — when you do not know how many

`for` is for when you know the count. `while` is for when you know the
*condition*:

```python
shield = 100

while shield > 0:
    shield = shield - 30
    print("Hit! Shield:", shield)

print("Shield down")
```

```
Hit! Shield: 70
Hit! Shield: 40
Hit! Shield: 10
Hit! Shield: -20
Shield down
```

Look at that last number. The shield ends on **−20**, not 0.

Nothing went wrong — `while` checks its condition *before* each pass, not
during one. When the shield was 10, `10 > 0` was true, so Python ran the body
one more time and took another 30 off. The check does not interrupt a pass
halfway through.

That is worth sitting with, because it is the shape of a hundred real bugs: a
character that takes one hit too many, a timer that goes one tick past zero.

### Keeping a running total

The pattern is: start a variable at zero, and add to it inside the loop.

```python
total_gold = 0

for chest in range(1, 5):
    total_gold = total_gold + 25
    print("Opened chest", chest, "- gold is now", total_gold)

print("Run total:", total_gold)
```

```
Opened chest 1 - gold is now 25
Opened chest 2 - gold is now 50
Opened chest 3 - gold is now 75
Opened chest 4 - gold is now 100
Run total: 100
```

`total_gold = total_gold + 25` looks like nonsense in maths — nothing equals
itself plus 25. It is not maths. Python works out the **right side first**,
using the value the box currently holds, and then puts the answer back in the
box. Old value in, new value out.

`total_gold` has to be created **before** the loop. Put it inside and it gets
reset to zero on every pass, and you end up with 25 no matter how many chests
you open.

---

## Watch for

**The stop number is not included.** `range(1, 10)` gives you nine numbers.

**Indentation decides what repeats.** Everything indented under the `for` line
runs every time round. The first line that goes back out to the left is the
loop ending.

**Build the total before the loop, not inside it.**

**Never write your own `while True:` in a game.**

```python
# DO NOT do this in a kaypy program.
while True:
    coin.pos.x = coin.pos.x + 1
```

In console Python this is how you keep something going. In a kaypy program the
loop is **already running** — it starts as soon as your file has been read.
Writing your own means the engine never gets a turn: the picture never appears,
the page stops responding, and you have to reload the tab. Nothing is printed
and nothing crashes, which is what makes it confusing.

When you want something to happen every frame, ask for it instead:

```python
from kaypy import *

kaypy(width=800, height=600, background=[20, 24, 36])
loadSprite("coin", "images/coin.png")

coin = add([sprite("coin"), pos(100, 300)])

@onUpdate
def drift():
    coin.pos.x = coin.pos.x + 2
```

That is the same idea — do this over and over — handed to the engine, which
runs it once per frame and still has time to draw.

---

## Classwork 1 — The Boss Fight

A boss has 200 health. Your weapon does 35 damage a hit. You do not know how
many hits that takes, so this is a `while` loop.

1. Make a variable `hits`, starting at 0.
2. Make a variable `total_damage`, starting at 0.
3. Loop `while total_damage < 200`.
4. Inside the loop, add 1 to `hits` and 35 to `total_damage`, then print both.
5. After the loop, print how many hits it took.
6. Print the overkill — how far past 200 you went.

<details markdown="1">
<summary>Solution</summary>

```python
hits = 0
total_damage = 0

while total_damage < 200:
    hits = hits + 1
    total_damage = total_damage + 35
    print("Hit", hits, "- total damage", total_damage)

print("Boss down in", hits, "hits")
print("Overkill:", total_damage - 200)
```

```
Hit 1 - total damage 35
Hit 2 - total damage 70
Hit 3 - total damage 105
Hit 4 - total damage 140
Hit 5 - total damage 175
Hit 6 - total damage 210
Boss down in 6 hits
Overkill: 10
```

Six hits, and 10 damage wasted on a boss that was already dead. That overkill
number is the same `while` overshoot as the shield — the condition is checked
between passes, not during one.

</details>

---

## Classwork 2 — The Level Builder

Build a whole level with loops, then print a report of what you built. Start
from this:

```python
from kaypy import *

kaypy(width=800, height=600, background=[18, 22, 34])

loadSprite("steel", "images/steel.png")
loadSprite("coin", "images/coin.png")
loadSprite("spike", "images/spike.png")
```

1. Make three counters, all starting at 0: `floor_tiles`, `coins`, `spikes`.
2. A `for` loop over `range(13)` that adds a steel tile at `pos(col * 64, 520)`.
   Give each one `area()` and `body(isStatic=True)` so it is solid.
3. Add 1 to `floor_tiles` inside that loop.
4. A second loop, `range(4)`, stacking four more steel tiles at x = 704 going
   **up** from the floor. Count those in `floor_tiles` too.
5. A loop over `range(9)` putting coins at `pos(90 + i * 64, 430)`, counting
   them in `coins`.
6. Spikes every third tile: loop over `range(0, 13, 3)` and add a spike at
   `pos(col * 64, 470)`. Count them.
7. A **nested** loop making a coin pyramid: `for row in range(3)`, and inside
   it `for col in range(row + 1)`. Three rows — one coin, then two, then three.
   Count each one.
8. Print a report: the three counters, each on its own line.
9. Print the total of all three.

*Work out step 7 on paper before you type it. How many coins is a pyramid with
rows of 1, 2 and 3? Your report should agree with you — and if it does not, the
loop is not doing what you think.*

**Stretch:** make the spikes step `range(0, 13, 2)` instead. How many spikes
now, and why is it not double?

<details markdown="1">
<summary>Solution</summary>

```python
from kaypy import *

kaypy(width=800, height=600, background=[18, 22, 34])

loadSprite("steel", "images/steel.png")
loadSprite("coin", "images/coin.png")
loadSprite("spike", "images/spike.png")

floor_tiles = 0
coins = 0
spikes = 0

# 1. The floor: one row of steel all the way across.
for col in range(13):
    add([sprite("steel"), pos(col * 64, 520), area(), body(isStatic=True)])
    floor_tiles = floor_tiles + 1

# 2. A wall of crates on the right, four high.
for row in range(4):
    add([sprite("steel"), pos(704, 520 - (row + 1) * 64), area(),
         body(isStatic=True)])
    floor_tiles = floor_tiles + 1

# 3. A line of coins to collect.
for i in range(9):
    add([sprite("coin"), pos(90 + i * 64, 430), area(), "coin"])
    coins = coins + 1

# 4. Spikes every third floor tile.
for col in range(0, 13, 3):
    add([sprite("spike"), pos(col * 64, 470), area(), "spike"])
    spikes = spikes + 1

# 5. A coin pyramid above the crates.
for row in range(3):
    for col in range(row + 1):
        add([sprite("coin"), pos(660 - row * 20 + col * 40, 120 + row * 44)])
        coins = coins + 1

print("--- LEVEL REPORT ---")
print("Steel tiles :", floor_tiles)
print("Coins       :", coins)
print("Spikes      :", spikes)
print("Objects     :", floor_tiles + coins + spikes)
```

```
--- LEVEL REPORT ---
Steel tiles : 17
Coins       : 15
Spikes      : 5
Objects     : 37
```

Seventeen tiles is 13 across plus 4 up. Fifteen coins is 9 in the line plus 6
in the pyramid — 1 + 2 + 3. Five spikes, because `range(0, 13, 3)` gives
0, 3, 6, 9, 12 and then stops before 13.

The stretch answer: `range(0, 13, 2)` gives 0, 2, 4, 6, 8, 10, 12 — seven, not
ten. Halving the step does not double the count, because the stop number has
not moved.

</details>

---

## Check yourself

How many times does the body of this loop run?

```python
for i in range(2, 9, 3):
    print(i)
```

<details markdown="1">
<summary>Answer</summary>

**Three times**, printing 2, 5 and 8. Start at 2, step 3 each time, stop
before 9 — the next value would be 11, which is past the end, so it never
happens.

</details>

---

## Lesson 3 — Lists

**By the end of this you can:** keep many values in one name, reach any of
them by number, add and remove items while the program runs, ask whether
something is in there, and loop over the whole thing.

### The problem lists solve

You already know how to hold one thing:

```python
enemy = "ghosty"
print(enemy)
```

```
ghosty
```

Now hold three. The obvious way is three variables:

```python
enemy1 = "ghosty"
enemy2 = "bobo"
enemy3 = "gigagantrum"
print(enemy1, enemy2, enemy3)
```

```
ghosty bobo gigagantrum
```

That works right up until it doesn't. How do you spawn *all* of them? Three
lines. How about twenty enemies? Twenty variables and twenty lines. And you
cannot loop over them, because `enemy1` and `enemy2` are unrelated names that
happen to look similar — Python sees no connection at all.

A **list** is one name holding many values, in order:

```python
enemies = ["ghosty", "bobo", "gigagantrum"]
print(enemies)
print(len(enemies))
```

```
['ghosty', 'bobo', 'gigagantrum']
3
```

Square brackets, commas between the items. `len()` tells you how many are in
there.

### Reaching one item

Each item has a position number, and you get at it with square brackets:

```python
enemies = ["ghosty", "bobo", "gigagantrum"]

print(enemies[0])
print(enemies[1])
print(enemies[2])
```

```
ghosty
bobo
gigagantrum
```

**Counting starts at 0.** The first item is `enemies[0]`, not `enemies[1]`.
This feels wrong for about a week and then never bothers you again. It is the
same 0 that `range(5)` starts at, which is not a coincidence.

So the last item of a three-item list is at index 2 — one less than the
length. Asking for `enemies[3]` does not give you nothing; it stops the
program with `IndexError: list index out of range`.

There is a shortcut for counting from the end:

```python
enemies = ["ghosty", "bobo", "gigagantrum"]

print(enemies[-1])
print(enemies[-2])
```

```
gigagantrum
bobo
```

`-1` is the last item, whatever the length is. That is worth knowing, because
`enemies[len(enemies) - 1]` is the same thing written the long way.

### Changing a list while it runs

A list is not fixed once you make it. This is the part that makes it useful in
a game:

```python
bag = ["coin", "key"]

bag.append("bomb")
print(bag)

bag.remove("key")
print(bag)

print(len(bag))
```

```
['coin', 'key', 'bomb']
['coin', 'bomb']
2
```

- `append()` adds one item **to the end**.
- `remove()` takes out the **first** item matching what you name.
- `len()` keeps up on its own — you never maintain a count yourself.

You can also change an item in place, by assigning to its position:

```python
bag = ["coin", "key", "bomb"]
bag[1] = "lamp"
print(bag)
```

```
['coin', 'lamp', 'bomb']
```

**`remove()` on something that is not there is an error**, so it is usually
paired with a check — which is the next thing.

### Asking what is in there

`in` answers a yes-or-no question about a list, and gives you back `True` or
`False` — so it goes straight into an `if`:

```python
bag = ["coin", "key"]

print("key" in bag)
print("bomb" in bag)

if "key" in bag:
    print("The door opens")
else:
    print("The door is locked")
```

```
True
False
The door opens
```

This is the safe way to use `remove()`:

```python
bag = ["coin", "key"]

if "bomb" in bag:
    bag.remove("bomb")

print(bag)
```

```
['coin', 'key']
```

Nothing was removed and nothing crashed. Without the `if`, that `remove()`
would have stopped the program.

### Looping over a list

This is where lists and loops meet, and it is the reason both lessons exist:

```python
enemies = ["ghosty", "bobo", "gigagantrum"]

for enemy in enemies:
    print("Spawning", enemy)
```

```
Spawning ghosty
Spawning bobo
Spawning gigagantrum
```

Read it out loud: *for each enemy in enemies*. The loop variable holds one
item at a time, and the loop runs exactly as many times as there are items —
you never write the number 3 anywhere. Add a fourth enemy to the list and the
loop handles it with no other change. That is the whole point.

You do not usually need `range()` and index numbers to walk a list. But when
you want the position as well as the item, `enumerate()` gives you both:

```python
scores = [120, 340, 90]

for i, score in enumerate(scores):
    print(i, score)
```

```
0 120
1 340
2 90
```

### A few more things lists do

```python
scores = [120, 340, 90, 500]

print(sum(scores))
print(max(scores))
print(min(scores))
print(sorted(scores))
print(scores)
```

```
1050
500
90
[90, 120, 340, 500]
[120, 340, 90, 500]
```

Look at the last two lines. `sorted()` hands back a **new** sorted list and
leaves the original alone — which is why `scores` still prints in its old
order underneath. If you want to sort the list itself, `scores.sort()` does
that and returns nothing.

And you can take a slice — a piece of a list — with two numbers:

```python
scores = [500, 340, 120, 90, 10]

print(scores[0:3])
print(scores[:3])
print(scores[2:])
```

```
[500, 340, 120]
[500, 340, 120]
[120, 90, 10]
```

The same "up to but not including" rule as `range()`: `scores[0:3]` gives you
items 0, 1 and 2, and stops before 3. Leaving a number out means "from the
start" or "to the end". `scores[:3]` is how you take a top three.

### Now put it on the screen

One list, one loop, a row of enemies:

```python
from kaypy import *

kaypy(width=800, height=600, background=[20, 24, 36])
loadSprite("ghosty", "images/ghosty.png")
loadSprite("bobo", "images/bobo.png")
loadSprite("gigagantrum", "images/gigagantrum.png")

wave = ["ghosty", "bobo", "ghosty", "gigagantrum", "bobo"]

for i, name in enumerate(wave):
    add([sprite(name), pos(100 + i * 130, 260), area(), "enemy"])
```

Five enemies, spaced out, and the list decides which is which. `i` does the
spacing exactly as it did in the loops lesson; `name` picks the sprite.

> **Change the list.** Add `"ghosty"` to the end and run it — six enemies, no
> other edit. Put the same name in five times for a wave of one kind. Delete
> two and the row gets shorter. You are editing the *data*, not the code, and
> that is the difference a list makes.

### Building a list as the game runs

Lists are most useful when they grow. Here every object that gets made is kept
so you can do something to all of them later:

```python
from kaypy import *

kaypy(width=800, height=600, background=[20, 24, 36])

coins = []

for i in range(6):
    coin = add([rect(20, 20), pos(80 + i * 100, 300), color(YELLOW)])
    coins.append(coin)

print("made", len(coins), "coins")

for coin in coins:
    coin.pos.y = coin.pos.y - 40
```

```
made 6 coins
```

The first loop makes them and remembers each one. The second loop moves every
one of them 40 pixels up. Without the list you would have six variables and
no way to talk about all of them at once.

## Watch for

**Counting starts at 0.** The last item is at `len(thing) - 1`, or just `-1`.

**`IndexError: list index out of range`** means you asked for a position that
is not there. Usually it is an off-by-one — check whether you meant `- 1`.

**`append()` takes one item.** `bag.append("coin", "key")` is an error. Two
items means two calls, or `bag.extend(["coin", "key"])`.

**`remove()` needs the item to be there**, so check with `in` first.

**`sorted()` gives a new list; `.sort()` changes the one you have** and returns
`None`. Writing `scores = scores.sort()` throws your list away and leaves you
with `None` — and nothing complains until you try to use it.

**An empty list is `[]`**, and `if bag:` is False when it is empty. You do not
need `if len(bag) > 0:`.

## Classwork 1 — The Inventory

A bag you can put things in and take things out of.

```python
from kaypy import *

kaypy(width=800, height=600, background=[20, 24, 36])
loadSprite("coin", "images/coin.png")
loadSprite("key", "images/key.png")
loadSprite("lamp", "images/lamp.png")

bag = ["coin", "key"]

add([text("Bag:", size=28), pos(40, 40)])
```

One step at a time, running after each:

1. Loop over `bag` and draw each item as a sprite in a row starting at
   `pos(40, 100)`, 90 pixels apart. Use `enumerate()` for the spacing.
2. Under the row, a label showing how many things you are carrying — use
   `len(bag)`, not a number you typed.
3. `bag.append("lamp")` **before** the drawing loop. Run it. Three sprites and
   the count says 3, and you did not touch the drawing code.
4. A `CAPACITY = 3` limit: only append when `len(bag) < CAPACITY`, otherwise
   print `Bag is full` to the console.
5. Remove the key — safely. Check `if "key" in bag:` first, then
   `bag.remove("key")`.

**Stretch:** draw the bag sorted alphabetically without changing the order you
actually carry things in. Which of `sorted(bag)` and `bag.sort()` do you want,
and why does it matter here?

## Classwork 2 — The Wave Spawner

The list decides the wave. Each wave is harder than the last because the list
gets longer.

```python
from kaypy import *

kaypy(width=800, height=600, background=[20, 24, 36])
loadSprite("ghosty", "images/ghosty.png")
loadSprite("bobo", "images/bobo.png")
loadSprite("gigagantrum", "images/gigagantrum.png")

wave = ["ghosty", "ghosty"]
wave_number = 1
```

1. Draw the wave: loop over it with `enumerate()` and put each sprite on
   screen, spaced across the window.
2. A label at the top showing the wave number and how many enemies are in it.
3. Make wave 2: `wave.append("bobo")` and add 1 to `wave_number`, then run it
   again. Three enemies.
4. Make wave 3 harder still by appending `"gigagantrum"`. Four enemies, and
   each wave is one line of change.
5. Use a conditional from Lesson 1: if the wave has more than three enemies,
   label it `DANGER` — otherwise `Clear`.

**Stretch:** space the enemies using `width()` divided by `len(wave)` instead
of a fixed 130 pixels, so the row always fits no matter how long the list gets.
Add six more enemies and check that nothing runs off the edge.

## Check yourself

What does this print?

```python
loot = ["coin", "key", "coin"]

loot.remove("coin")
loot.append("gem")

print(loot)
print(len(loot))
print("coin" in loot)
```

```
['key', 'coin', 'gem']
3
True
```

<details markdown="1">
<summary>Why is there still a coin?</summary>

`remove()` takes out the **first** match and then stops. There were two coins,
so one of them is still there — at position 1, because everything after the
removed item shifts down to fill the gap.

That is why `"coin" in loot` is still `True`, and why `remove()` in a loop
catches people out: it does not remove *all* of something, only the next one
it finds.

</details>

---

## Coming next

**Lesson 4 — Functions.** Naming a piece of work so you can ask for it by
name, passing it what it needs, and getting an answer back — the step that
turns a long program into a short one.

Then all four together, in a game you keep.

Teaching with this, or stuck on something? There is a
[Discord](https://discord.gg/sVXnsDZNm).
