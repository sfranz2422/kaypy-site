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

## Lesson 1 — Loops

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

## Coming next

**Lesson 2 — Conditionals.** `if`, `elif`, `else`, and making a game react:
losing health, opening a door only when you have the key, a hazard that only
hurts if you land on it.

Then lists, functions, and putting all four together into a game you keep.

Teaching with this, or stuck on something? There is a
[Discord](https://discord.gg/sVXnsDZNm).
