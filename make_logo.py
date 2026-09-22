#!/usr/bin/env python3
"""Turn the supplied logo into a usable transparent mark, and the icon sizes.

    python3 make_logo.py            build static/creature.png and the icons
    python3 make_logo.py --proof    ...and a proof sheet to look at

WHAT WAS WRONG WITH THE SOURCE

`logo.png` is a JPEG. Not a PNG with a misleading name in some harmless way —
the file is JPEG data, which has no alpha channel at all, so it could never
have been transparent whatever it was called. The checkerboard behind the
snake is painted pixels: an image generator drew a *picture of* transparency
rather than producing any.

Three things follow, and this script deals with each.

1. THE BACKGROUND HAS TO COME OFF BY POSITION, NOT COLOUR

The obvious approach is to delete every pixel that matches the checkerboard.
It ruins the logo. The controller is grey — (173, 187, 188) and
(190, 203, 209) — and the checkerboard is (211, 211, 211) and (252, 252, 252).
Any threshold loose enough to catch the checkerboard's darker squares also
eats the controller's highlights and leaves holes in the middle of the art.

So it floods in from the border. Background is whatever is *connected to the
edge* and looks like checkerboard; the controller is enclosed by the snake, so
the flood never reaches it. Colour alone cannot tell the two apart. Position
can.

"Looks like checkerboard" means near-neutral AND light, and neutral is the
part doing the work: the checkerboard is pure grey, while everything in the
artwork that is nearly as bright carries a colour cast.

2. ENCLOSED BACKGROUND NEEDS A SECOND PASS

A flood from the edge cannot reach a sealed region, and the counter of the P
in "Py" is sealed — it kept its checkerboard, inside the letter, which is
exactly the sort of thing nobody notices until it is on a website. So after
the flood, any *remaining* checkerboard-coloured region smaller than a
fiftieth of the image is background too. The controller is safe from this for
the same reason as before: it is not checkerboard-coloured.

3. THE JPEG HALO HAS TO BE EATEN, NOT FEATHERED

Compression fuzzes every edge into a pale fringe. Feathering the mask keeps
it; the fringe is simply softer. So the background is dilated a pixel into the
artwork before feathering, which costs an outline pixel nobody will miss and
removes a halo that is invisible on white and glaring on a dark page — which
is where this logo lives.

WHAT IS NOT KEPT

The wordmark and the two taglines baked into the bottom of the image. They are
dark navy, which disappears on a dark background; they cannot be restyled,
searched, selected, or translated; and they are the part of a raster logo that
ages worst. The site sets that text in HTML instead, where it takes its colour
from the theme like everything else. Only the creature is kept.
"""
from __future__ import annotations

import argparse
import pathlib
import sys
from collections import deque

try:
    from PIL import Image, ImageFilter
except ImportError:
    sys.exit("make_logo.py needs Pillow:  pip install -r requirements.txt")

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = HERE / "logo.png"
STATIC = HERE / "static"

NEUTRAL = 14        # how far from pure grey a background pixel may be
# And how light. The window here is narrow and both edges matter: the
# checkerboard's darker square is 209, so this must stay below it — and the
# snake's drop shadow runs 150-195, so anything lower eats the shadow's pale
# half and leaves its dark half behind. The result of getting this wrong is a
# shadow broken into grey dashes, which looks like damage rather than a
# shadow, and only shows up once the logo is on a dark page.
LIGHT = 203
# Measured, not guessed: the last row containing snake green is 562 and the
# first row containing wordmark blue is 575, so anywhere between is safe. An
# earlier value of 766 came from looking for blank horizontal bands, which
# found the gaps *inside* the taglines and cut straight through the wordmark.
CREATURE_BOTTOM = 572
ENCLOSED_MAX = 0.02     # a sealed background region is at most this much of the image


def looks_like_background(rgb):
    r, g, b = rgb[:3]
    return max(r, g, b) - min(r, g, b) <= NEUTRAL and min(r, g, b) >= LIGHT


def background_mask(im):
    """White where the image is background, black where the art is."""
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    queue = deque()

    def consider(x, y):
        if not seen[y * w + x] and looks_like_background(px[x, y]):
            seen[y * w + x] = 1
            queue.append((x, y))

    for x in range(w):
        consider(x, 0)
        consider(x, h - 1)
    for y in range(h):
        consider(0, y)
        consider(w - 1, y)

    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                consider(nx, ny)

    # Second pass: sealed regions the flood could not reach — the P's counter.
    filled = 0
    for start_y in range(h):
        for start_x in range(w):
            if seen[start_y * w + start_x] or not looks_like_background(px[start_x, start_y]):
                continue
            region, todo = [], deque([(start_x, start_y)])
            seen[start_y * w + start_x] = 2
            while todo:
                x, y = todo.popleft()
                region.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]
                            and looks_like_background(px[nx, ny])):
                        seen[ny * w + nx] = 2
                        todo.append((nx, ny))
            if len(region) <= w * h * ENCLOSED_MAX:
                for x, y in region:
                    seen[y * w + x] = 1
                filled += 1

    mask = Image.new("L", (w, h))
    mask.putdata([255 if s == 1 else 0 for s in seen])
    return mask, filled


def cut_out(path):
    im = Image.open(path).convert("RGB")
    mask, sealed = background_mask(im)

    # Eat the JPEG halo, then soften what is left. MaxFilter(3) leaves a
    # visible fringe on a dark background; 5 costs an outline pixel nobody
    # will miss and removes it.
    mask = mask.filter(ImageFilter.MaxFilter(5))
    alpha = mask.filter(ImageFilter.GaussianBlur(0.6)).point(lambda v: 255 - v)

    out = im.convert("RGBA")
    out.putalpha(alpha)
    return out, sealed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proof", action="store_true",
                    help="also write a sheet showing it on light and dark")
    args = ap.parse_args()

    if not SOURCE.is_file():
        sys.exit(f"no {SOURCE.name} in the repo root")

    STATIC.mkdir(exist_ok=True)
    full, sealed = cut_out(SOURCE)
    print(f"  cut out the background ({sealed} sealed region(s) filled too)")

    creature = full.crop((0, 0, full.width, CREATURE_BOTTOM))
    creature = creature.crop(creature.getbbox())
    creature.save(STATIC / "creature.png")
    print(f"  static/creature.png    {creature.width}x{creature.height}")

    for size, name in ((32, "favicon.png"), (180, "icon-180.png"),
                       (512, "icon-512.png")):
        icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        art = creature.copy()
        art.thumbnail((size, size), Image.LANCZOS)
        icon.paste(art, ((size - art.width) // 2, (size - art.height) // 2))
        icon.save(STATIC / name)
        print(f"  static/{name:<18} {size}x{size}")

    # The social card is flattened onto the site's own background: every
    # service that renders one composites it onto white otherwise, and the
    # page is not white.
    card = Image.new("RGB", (1200, 630), (255, 255, 255))
    art = creature.copy()
    art.thumbnail((460, 460), Image.LANCZOS)
    card.paste(art, ((1200 - art.width) // 2, (630 - art.height) // 2 - 30), art)
    card.save(STATIC / "social.png")
    print(f"  static/social.png      1200x630")

    if args.proof:
        pad = 30
        cw, ch = creature.size
        sheet = Image.new("RGB", (cw * 2 + pad * 3, ch + pad * 2), (255, 255, 255))
        sheet.paste(Image.new("RGB", (cw + pad * 2, ch + pad * 2), (27, 34, 44)),
                    (cw + pad * 2 - pad, 0))
        sheet.paste(creature, (pad, pad), creature)
        sheet.paste(creature, (cw + pad * 2, pad), creature)
        sheet.save(HERE / "logo-proof.png")
        print("\n  logo-proof.png — on white and on the site's background")
    return 0


if __name__ == "__main__":
    sys.exit(main())
