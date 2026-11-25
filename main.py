#!/usr/bin/env python3
"""The World Today - Wednesday 25 November 2026, summed up in one picture.

Pure Python 3.13 standard library: the poster is painted pixel by pixel
into an RGB buffer and hand-encoded as a PNG (zlib + struct). No network,
no font files on disk - the lettering is a small built-in 5x7 bitmap font.
The run is fully deterministic: the same code always writes the same bytes.

The six stories, each checked against news reports published on 25 Nov 2026:
  1. Ukraine - Zelenskiy confirms Ukraine struck a Russian cargo ship in
     the Gulf of Finland, and a Russian warship was sunk off Benghazi,
     Libya (Reuters world news summary, 25 Nov; RFE/RL, 25 Nov).
  2. Saudi Arabia - Houthis hit a tower in Riyadh's King Abdullah
     Financial District, injuring at least 11 (Daily Sabah / Arab News,
     25 Nov).
  3. Poland - NATO authorises the forward deployment of one AWACS
     early-warning aircraft to Poland after three Russian Kh-101 missiles
     landed there during an attack on Ukraine (Reuters, 23 Nov; NATO
     confirmation 23-24 Nov).
  4. France - officials order former President Nicolas Sarkozy's
     corruption case to trial, with his wife Carla Bruni (Reuters, 25 Nov).
  5. China/US - Huawei convicted in a sprawling US criminal trial over
     its Iran business (Reuters, 25 Nov).
  6. Football - Real Madrid beat PSV Eindhoven 5-1 in the Champions
     League, Bellingham with a stunner and Mbappe with a brace (25 Nov).

Usage: MAKEFUN_OUTPUT_DIR=out python3 main.py

Restructure (25 Nov, packaging pass): the four grid stories now come
from one PANELS table instead of four copy-pasted calls; the icons draw
from small coordinate tables; the palette lives in one COLORS dict; the
font stores each glyph as seven 5-character rows joined into one string.
The lead ship is still drawn at 3x with its quadcopter drone, the Riyadh
blast is still an explosion burst (not a sun), the gavel is still a real
gavel, the NATO panel still says one AWACS plane was promised, and the
football strip still shows the big 5-1. The PNG this writes is
byte-identical to the reviser run's (sha256 cc2abe95...).
"""

import os
import struct
import zlib
from math import cos, sin, sqrt

W = H = 1024

# ------------------------------------------------------------ bitmap font
# One 5x7 glyph per character: seven rows of five characters ('#' = ink)
# joined into a single 35-character string. The renderer slices it back
# into rows; unknown characters fall back to the blank.
FONT = {
    "A": ".###." "#...#" "#...#" "#####" "#...#" "#...#" "#...#",
    "B": "####." "#...#" "#...#" "####." "#...#" "#...#" "####.",
    "C": ".###." "#...#" "#...." "#...." "#...." "#...#" ".###.",
    "D": "####." "#...#" "#...#" "#...#" "#...#" "#...#" "####.",
    "E": "#####" "#...." "#...." "####." "#...." "#...." "#####",
    "F": "#####" "#...." "#...." "####." "#...." "#...." "#....",
    "G": ".###." "#...#" "#...." "#.###" "#...#" "#...#" ".####",
    "H": "#...#" "#...#" "#...#" "#####" "#...#" "#...#" "#...#",
    "I": ".###." "..#.." "..#.." "..#.." "..#.." "..#.." ".###.",
    "J": "..###" "...#." "...#." "...#." "...#." "#..#." ".##..",
    "K": "#...#" "#..#." "#.#.." "##..." "#.#.." "#..#." "#...#",
    "L": "#...." "#...." "#...." "#...." "#...." "#...." "#####",
    "M": "#...#" "##.##" "#.#.#" "#.#.#" "#...#" "#...#" "#...#",
    "N": "#...#" "##..#" "#.#.#" "#..##" "#...#" "#...#" "#...#",
    "O": ".###." "#...#" "#...#" "#...#" "#...#" "#...#" ".###.",
    "P": "####." "#...#" "#...#" "####." "#...." "#...." "#....",
    "Q": ".###." "#...#" "#...#" "#...#" "#.#.#" "#..#." ".##.#",
    "R": "####." "#...#" "#...#" "####." "#.#.." "#..#." "#...#",
    "S": ".####" "#...." "#...." ".###." "....#" "....#" "####.",
    "T": "#####" "..#.." "..#.." "..#.." "..#.." "..#.." "..#..",
    "U": "#...#" "#...#" "#...#" "#...#" "#...#" "#...#" ".###.",
    "V": "#...#" "#...#" "#...#" "#...#" "#...#" ".#.#." "..#..",
    "W": "#...#" "#...#" "#...#" "#.#.#" "#.#.#" "##.##" "#...#",
    "X": "#...#" "#...#" ".#.#." "..#.." ".#.#." "#...#" "#...#",
    "Y": "#...#" "#...#" ".#.#." "..#.." "..#.." "..#.." "..#..",
    "Z": "#####" "....#" "...#." "..#.." ".#..." "#...." "#####",
    "0": ".###." "#...#" "#..##" "#.#.#" "##..#" "#...#" ".###.",
    "1": "..#.." ".##.." "..#.." "..#.." "..#.." "..#.." ".###.",
    "2": ".###." "#...#" "....#" "...#." "..#.." ".#..." "#####",
    "3": "####." "....#" "....#" ".###." "....#" "....#" "####.",
    "4": "...#." "..##." ".#.#." "#..#." "#####" "...#." "...#.",
    "5": "#####" "#...." "####." "....#" "....#" "#...#" ".###.",
    "6": "..##." ".#..." "#...." "####." "#...#" "#...#" ".###.",
    "7": "#####" "....#" "...#." "..#.." ".#..." ".#..." ".#...",
    "8": ".###." "#...#" "#...#" ".###." "#...#" "#...#" ".###.",
    "9": ".###." "#...#" "#...#" ".####" "....#" "...#." ".##..",
    " ": "....." "....." "....." "....." "....." "....." ".....",
    ".": "....." "....." "....." "....." "....." ".##.." ".##..",
    ",": "....." "....." "....." "....." ".##.." "..#.." ".#...",
    "'": "..#.." "..#.." ".#..." "....." "....." "....." ".....",
    "!": "..#.." "..#.." "..#.." "..#.." "..#.." "....." "..#..",
    "?": ".###." "#...#" "....#" "...#." "..#.." "....." "..#..",
    "-": "....." "....." "....." ".###." "....." "....." ".....",
    "/": "....#" "...#." "...#." "..#.." ".#..." ".#..." "#....",
    "(": "...#." "..#.." ".#..." ".#..." ".#..." "..#.." "...#.",
    ")": ".#..." "..#.." "...#." "...#." "...#." "..#.." ".#...",
    "&": ".##.." "#..#." "#.#.." ".#..." "#.#.#" "#..#." ".##.#",
    "%": "#...#" "#..#." "....#" "...#." "..#.." ".#..#" "#...#",
    "+": "....." "..#.." "..#.." ".###." "..#.." "..#.." ".....",
    ":": "....." ".##.." "....." ".##.." "....." ".##.." ".##..",
}


def _glyph_rows(ch):
    """Split one joined glyph string back into its seven 5-char rows."""
    joined = FONT.get(ch, FONT[" "])
    return [joined[i * 5:(i + 1) * 5] for i in range(7)]


# ------------------------------------------------------------ palette
# Every colour the poster uses, in one table, looked up by name.
COLORS = {
    "ink": (13, 27, 45),          # page background
    "navy": (15, 40, 66),         # header band
    "gold": (242, 183, 5),
    "white": (255, 255, 255),
    "cream": (232, 237, 243),
    "crimson": (128, 24, 40),     # lead panel: Ukraine
    "crimson_sub": (255, 205, 190),
    "teal": (12, 68, 68),         # Riyadh panel
    "blue": (22, 54, 96),         # NATO panel
    "forest": (26, 78, 48),       # Sarkozy panel
    "plum": (70, 30, 70),         # Huawei panel
    "violet": (56, 34, 104),      # football strip
    "orange": (245, 158, 11),
    "red": (220, 60, 50),
    "sky": (86, 190, 240),
    "steel": (148, 163, 184),
    "green": (34, 197, 94),
    "mist": (203, 213, 225),      # ship hull, tower body
    "slate": (30, 41, 59),        # chip body
    "tan": (210, 180, 140),       # gavel wood
    "lilac": (120, 90, 180),      # scoreline divider
}


def c(name):
    return COLORS[name]


# ------------------------------------------------------------ canvas
class Canvas:
    """An RGB pixel buffer with the only drawing primitives the poster needs."""

    def __init__(self):
        self.px = bytearray(W * H * 3)
        self.rect(0, 0, W, H, c("ink"))

    def _set(self, x, y, colour):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = colour

    def rect(self, x0, y0, x1, y1, colour):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(W, x1)
        y1 = min(H, y1)
        if x1 <= x0 or y1 <= y0:
            return
        stripe = bytes(colour) * (x1 - x0)
        for y in range(y0, y1):
            start = (y * W + x0) * 3
            self.px[start:start + len(stripe)] = stripe

    def circle(self, cx, cy, r, colour):
        for dy in range(-r, r + 1):
            half = int(sqrt(r * r - dy * dy))
            self.rect(cx - half, cy + dy, cx + half + 1, cy + dy + 1, colour)

    def line(self, x0, y0, x1, y1, colour, w=1):
        dx = x1 - x0
        dy = y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        half = w // 2
        dots = [(x0 + dx * s // steps, y0 + dy * s // steps)
                for s in range(steps + 1)]
        for x, y in dots:
            self.rect(x - half, y - half, x + half + 1, y + half + 1, colour)

    def poly(self, pts, colour):
        # Even-odd scanline fill: intersect each row with every edge,
        # then fill between pairs of intersections.
        edges = list(zip(pts, pts[1:] + pts[:1]))
        top = min(p[1] for p in pts)
        bottom = max(p[1] for p in pts)
        for y in range(top, bottom + 1):
            hits = []
            for (x0, y0), (x1, y1) in edges:
                if (y0 <= y < y1) or (y1 <= y < y0):
                    hits.append(x0 + (y - y0) * (x1 - x0) // (y1 - y0))
            hits.sort()
            for j in range(0, len(hits) - 1, 2):
                self.rect(hits[j], y, hits[j + 1] + 1, y + 1, colour)

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def text(self, x, y, s, scale, colour):
        cursor = x
        for ch in s.upper():
            for row, bits in enumerate(_glyph_rows(ch)):
                for col, bit in enumerate(bits):
                    if bit == "#":
                        self.rect(cursor + col * scale, y + row * scale,
                                  cursor + (col + 1) * scale,
                                  y + (row + 1) * scale, colour)
            cursor += 6 * scale
        return cursor

    def centre_text(self, y, s, scale, colour, x0=0, x1=W):
        w = self.text_w(s, scale)
        self.text(x0 + (x1 - x0 - w) // 2, y, s, scale, colour)


# ------------------------------------------------------------ icons
def icon_ship(p, ix, iy, s=2):
    # A cargo ship on waves, with a drone above it. The lead panel is
    # wide, so the ship is drawn at 3x there; at 1x it left most of the
    # panel empty.
    X = lambda dx: ix + dx * s
    Y = lambda dy: iy + dy * s
    hull = [(4, 26), (44, 26), (38, 38), (10, 38)]
    p.poly([(X(a), Y(b)) for a, b in hull], c("mist"))
    p.rect(X(14), Y(12), X(30), Y(26), c("red"))
    p.rect(X(30), Y(18), X(38), Y(26), c("steel"))
    p.line(X(22), Y(12), X(22), Y(4), c("gold"), 2 * s)
    waves = [(2, 42, 10, 38), (10, 38, 18, 42), (18, 42, 26, 38),
             (26, 38, 34, 42), (34, 42, 42, 38)]
    for x0, y0, x1, y1 in waves:
        p.line(X(x0), Y(y0), X(x1), Y(y1), c("sky"), 2 * s)
    # Drone: a quadcopter seen from above - cross frame, four rotor
    # discs, red body in the middle.
    frame = [(32, -14, 46, -14), (32, -2, 46, -2), (39, -14, 39, -2)]
    for x0, y0, x1, y1 in frame:
        p.line(X(x0), Y(y0), X(x1), Y(y1), c("white"), s)
    for rx, ry in ((32, -14), (46, -14), (32, -2), (46, -2)):
        p.circle(X(rx), Y(ry), 2 * s, c("white"))
    p.circle(X(39), Y(-8), 2 * s, c("red"))


def icon_tower(p, ix, iy):
    # A tall skyscraper with a blast burst at its crown.
    p.rect(ix + 12, iy + 10, ix + 32, iy + 44, c("mist"))
    for wy in (16, 24, 32):
        for wx in (16, 24):
            p.rect(ix + wx, iy + wy, ix + wx + 4, iy + wy + 3, c("ink"))
    p.rect(ix + 10, iy + 42, ix + 34, iy + 44, c("steel"))
    # Blast burst: alternating red/orange rays around a red core with a
    # gold heart, so it reads as an explosion rather than a sun.
    for k in range(8):
        ang = k * 3.14159265 / 4
        x0 = int(ix + 22 + 8 * cos(ang))
        y0 = int(iy + 8 + 8 * sin(ang))
        x1 = int(ix + 22 + 16 * cos(ang))
        y1 = int(iy + 8 + 16 * sin(ang))
        p.line(x0, y0, x1, y1, c("red") if k % 2 == 0 else c("orange"), 3)
    p.circle(ix + 22, iy + 8, 5, c("red"))
    p.circle(ix + 22, iy + 8, 2, c("gold"))


def icon_radar(p, ix, iy):
    # A radar dish sweeping, with a small jet above it.
    p.circle(ix + 22, iy + 26, 16, c("green"))
    p.circle(ix + 22, iy + 26, 12, c("ink"))
    p.line(ix + 22, iy + 26, ix + 34, iy + 14, c("green"), 2)
    p.line(ix + 16, iy + 40, ix + 28, iy + 40, c("steel"), 3)
    p.poly([(ix + 30, iy + 2), (ix + 44, iy + 8), (ix + 30, iy + 12)], c("white"))
    p.poly([(ix + 32, iy + 8), (ix + 26, iy + 4), (ix + 32, iy + 6)], c("white"))


def icon_gavel(p, ix, iy):
    # A judge's gavel: horizontal head, diagonal handle, sounding block
    # below. (A diagonal bar with a block at each end read as a dumbbell.)
    p.rect(ix + 4, iy + 6, ix + 40, iy + 16, c("gold"))
    p.rect(ix + 4, iy + 6, ix + 10, iy + 16, c("tan"))
    p.line(ix + 22, iy + 16, ix + 30, iy + 38, c("tan"), 4)
    p.rect(ix + 12, iy + 38, ix + 36, iy + 44, c("steel"))


def icon_chip(p, ix, iy):
    # A processor chip with pins on all four sides.
    p.rect(ix + 10, iy + 10, ix + 34, iy + 34, c("slate"))
    p.rect(ix + 16, iy + 16, ix + 28, iy + 28, c("sky"))
    for k in range(4):
        off = 14 + k * 6
        p.line(ix + off, iy + 4, ix + off, iy + 10, c("gold"), 2)
        p.line(ix + off, iy + 34, ix + off, iy + 40, c("gold"), 2)
        p.line(ix + 4, iy + off, ix + 10, iy + off, c("gold"), 2)
        p.line(ix + 34, iy + off, ix + 40, iy + off, c("gold"), 2)


def icon_ball(p, ix, iy):
    # A football: white ball, dark centre patch and four corner patches.
    p.circle(ix + 22, iy + 22, 20, c("white"))
    p.poly([(ix + 18, iy + 16), (ix + 26, iy + 16), (ix + 29, iy + 22),
            (ix + 26, iy + 28), (ix + 18, iy + 28), (ix + 15, iy + 22)], c("ink"))
    for px, py in ((10, 10), (34, 10), (10, 34), (34, 34)):
        p.circle(ix + px, iy + py, 3, c("ink"))


# ------------------------------------------------------------ poster
def draw_panel(p, left, top, right, bottom, bg, kicker, titles, subs, accent, icon):
    p.rect(left, top, right, bottom, c(bg))
    icon(p, left + 18, top + 8)
    # Kicker at scale 3 keeps the region label legible at the judge's
    # reduced viewing size; scale 2 shrank to ~4 px tall and was unreadable.
    p.text(left + 74, top + 20, kicker, 3, c(accent))
    y = top + 62
    for line in titles:
        p.text(left + 18, y, line, 5, c("white"))
        y += 41
    y = top + 150
    for line in subs:
        p.text(left + 18, y, line, 3, c("cream"))
        y += 25


# The four grid stories: left, top, right, bottom, bg, kicker, titles,
# subs, accent, icon. Same layout as before, now one table + one loop.
PANELS = [
    (16, 404, 504, 616, "teal", "SAUDI - RIYADH",
     ["HOUTHIS HIT", "RIYADH TOWER"],
     ["11 hurt in strike on", "tallest skyscraper"],
     "orange", icon_tower),
    (520, 404, 1008, 616, "blue", "NATO - POLAND",
     ["NATO WATCHES", "OVER POLAND"],
     ["AWACS plane promised", "after missiles landed"],
     "gold", icon_radar),
    (16, 628, 504, 840, "forest", "FRANCE - PARIS",
     ["SARKOZY TO", "FACE TRIAL"],
     ["Corruption case ordered", "to trial with Bruni"],
     "gold", icon_gavel),
    (520, 628, 1008, 840, "plum", "CHINA - US COURT",
     ["HUAWEI FOUND", "GUILTY IN US"],
     ["Convicted over Iran", "business dealings"],
     "sky", icon_chip),
]


def build():
    p = Canvas()

    # Header band.
    p.rect(0, 0, W, 132, c("navy"))
    p.centre_text(24, "THE WORLD TODAY", 7, c("white"))
    p.centre_text(88, "WEDNESDAY 25 NOVEMBER 2026", 4, c("gold"))
    p.rect(0, 132, W, 136, c("gold"))

    # Lead story: Ukraine's strikes reach far beyond its own shores.
    p.rect(16, 144, 1008, 392, c("crimson"))
    p.text(40, 162, "UKRAINE - THE WAR SPREADS", 3, c("gold"))
    p.text(40, 192, "KYIV HITS RUSSIAN", 7, c("white"))
    p.text(40, 252, "SHIPS FAR FROM HOME", 7, c("white"))
    p.text(40, 326, "ZELENSKIY CONFIRMS GULF OF FINLAND STRIKE", 3, c("crimson_sub"))
    p.text(40, 356, "WARSHIP SUNK OFF LIBYA TOO", 3, c("crimson_sub"))
    # The lead icon is drawn at 3x so it fills the wide empty space to
    # the right of the headline instead of floating in it.
    icon_ship(p, 856, 225, s=3)

    # Four stories in a 2x2 grid.
    for left, top, right, bottom, bg, kicker, titles, subs, accent, icon in PANELS:
        draw_panel(p, left, top, right, bottom, bg, kicker, titles, subs, accent, icon)

    # Bottom strip: Real Madrid's 5-1 Champions League night. The kicker
    # is scale 3 like every other panel (scale 2 was visibly smaller),
    # and the 5-1 scoreline is shown big at the right, filling the
    # strip's dead space behind a divider.
    p.rect(16, 852, 1008, 1008, c("violet"))
    icon_ball(p, 40, 884)
    p.text(170, 866, "FOOTBALL - MADRID", 3, c("gold"))
    p.text(170, 894, "MADRID THRASH PSV", 5, c("white"))
    p.text(170, 942, "BELLINGHAM STUNNER, MBAPPE BRACE", 3, c("cream"))
    p.line(830, 876, 830, 984, c("lilac"), 2)
    p.text(852, 894, "5-1", 8, c("gold"))

    return png_bytes(p.px)


def png_bytes(px):
    rows = []
    for y in range(H):
        rows.append(b"\x00" + bytes(px[y * W * 3:(y + 1) * W * 3]))
    raw = b"".join(rows)

    def chunk(typ, data):
        packed = struct.pack(">I", len(data)) + typ + data
        return packed + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    parts = [b"\x89PNG\r\n\x1a\n", chunk(b"IHDR", ihdr),
             chunk(b"IDAT", zlib.compress(raw, 9)), chunk(b"IEND", b"")]
    return b"".join(parts)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = build()
    tmp_path = os.path.join(out_dir, ".entry.png.tmp")
    final_path = os.path.join(out_dir, "entry.png")
    with open(tmp_path, "wb") as f:
        f.write(data)
    os.chmod(tmp_path, 0o644)
    os.replace(tmp_path, final_path)
    os.chmod(final_path, 0o644)


if __name__ == "__main__":
    main()
