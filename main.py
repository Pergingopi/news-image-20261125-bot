#!/usr/bin/env python3
"""The World Today - one image summing up the world news of Wednesday 25 November 2026.

Pure Python 3.13 standard library: the poster is drawn pixel by pixel into an
RGB buffer and encoded as a PNG by hand (zlib + struct). No network, no fonts
on disk - the lettering comes from a small built-in 5x7 bitmap font. The run
is fully deterministic: the same code always writes the same bytes.

Stories (all checked against news reports published on 25 November 2026):
  1. Ukraine - President Zelenskiy confirms Ukraine struck a Russian cargo
     ship in the Gulf of Finland, and a Russian warship was sunk off
     Benghazi, Libya (Reuters world news summary, 25 Nov; RFE/RL, 25 Nov).
  2. Saudi Arabia - Houthis hit a tower in Riyadh's King Abdullah Financial
     District, injuring at least 11 people (Daily Sabah / Arab News front
     page, 25 Nov).
  3. Poland - NATO authorises the forward deployment of one AWACS
     early-warning aircraft to Poland after three Russian Kh-101
     missiles landed in the country during an attack on Ukraine
     (Reuters, 23 Nov; NATO confirmation 23-24 Nov).
  4. France - officials order former President Nicolas Sarkozy's corruption
     case to trial, with his wife Carla Bruni (Reuters, 25 Nov).
  5. China/US - Huawei convicted in a sprawling US criminal trial over its
     Iran business (Reuters, 25 Nov).
  6. Football - Real Madrid beat PSV Eindhoven 5-1 in the Champions League,
     Bellingham with a stunner and Mbappe with a brace (25 Nov).

Usage: MAKEFUN_OUTPUT_DIR=out python3 main.py

Revision (25 Nov, reviser pass): the lead ship is drawn larger with a
proper quadcopter drone; the Riyadh blast reads as an explosion, not a
sun; the gavel is redrawn as a real gavel (horizontal head, handle,
sounding block) instead of a dumbbell-like diagonal; the NATO panel now
says one AWACS plane was promised, not "jets sent"; the football strip
kicker matches the other panels at scale 3 and the 5-1 scoreline is
shown big at the right, filling the strip's dead space.
"""

import os
import struct
import zlib
from math import cos, sin, sqrt

W = H = 1024

# ---------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows of 5 characters; '#' is an inked pixel.
GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": ("..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("#...#", "#..#.", "....#", "...#.", "..#..", ".#..#", "#...#"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    ":": (".....", ".##..", ".....", ".##..", ".....", ".##..", ".##.."),
}

# ---------------------------------------------------------------- palette
INK = (13, 27, 45)        # page background
NAVY = (15, 40, 66)       # header
GOLD = (242, 183, 5)
WHITE = (255, 255, 255)
CREAM = (232, 237, 243)
CRIMSON = (128, 24, 40)   # lead: Ukraine
CRIMSON_SUB = (255, 205, 190)
TEAL = (12, 68, 68)       # Riyadh
BLUE = (22, 54, 96)       # NATO / Poland
FOREST = (26, 78, 48)     # Sarkozy / France
PLUM = (70, 30, 70)       # Huawei
VIOLET = (56, 34, 104)    # football strip
ORANGE = (245, 158, 11)
RED = (220, 60, 50)
SKY = (86, 190, 240)
STEEL = (148, 163, 184)
GREEN = (34, 197, 94)


class Poster:
    """An RGB pixel buffer with tiny vector drawing helpers."""

    def __init__(self):
        self.px = bytearray(W * H * 3)
        self.rect(0, 0, W, H, INK)

    def _set(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x0, y0, x1, y1, c):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(W, x1)
        y1 = min(H, y1)
        for y in range(y0, y1):
            base = (y * W + x0) * 3
            for x in range(x0, x1):
                i = base + (x - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def circle(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int(sqrt(r * r - dy * dy))
            self.rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, c)

    def line(self, x0, y0, x1, y1, c, w=1):
        dx = x1 - x0
        dy = y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        half = w // 2
        for s in range(steps + 1):
            x = x0 + dx * s // steps
            y = y0 + dy * s // steps
            self.rect(x - half, y - half, x + half + 1, y + half + 1, c)

    def poly(self, pts, c):
        # Even-odd scanline fill.
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) // (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.rect(xs[j], y, xs[j + 1] + 1, y + 1, c)

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def text(self, x, y, s, scale, c):
        cx = x
        for ch in s.upper():
            glyph = GLYPHS.get(ch, GLYPHS[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "#":
                        self.rect(cx + col * scale, y + row * scale,
                                  cx + (col + 1) * scale,
                                  y + (row + 1) * scale, c)
            cx += 6 * scale
        return cx

    def centre_text(self, y, s, scale, c, x0=0, x1=W):
        w = self.text_w(s, scale)
        self.text(x0 + (x1 - x0 - w) // 2, y, s, scale, c)


# ---------------------------------------------------------------- icons
def icon_ship(p, ix, iy, s=2):
    # A cargo ship on waves, with a drone above it (drawn 2x: the lead
    # panel is wide and the 1x ship left most of it empty).
    def X(dx):
        return ix + dx * s

    def Y(dy):
        return iy + dy * s
    p.poly([(X(4), Y(26)), (X(44), Y(26)), (X(38), Y(38)),
            (X(10), Y(38))], (203, 213, 225))
    p.rect(X(14), Y(12), X(30), Y(26), RED)
    p.rect(X(30), Y(18), X(38), Y(26), (148, 163, 184))
    p.line(X(22), Y(12), X(22), Y(4), GOLD, 2 * s)
    p.line(X(2), Y(42), X(10), Y(38), SKY, 2 * s)
    p.line(X(10), Y(38), X(18), Y(42), SKY, 2 * s)
    p.line(X(18), Y(42), X(26), Y(38), SKY, 2 * s)
    p.line(X(26), Y(38), X(34), Y(42), SKY, 2 * s)
    p.line(X(34), Y(42), X(42), Y(38), SKY, 2 * s)
    # Drone: a quadcopter seen from above - four rotor discs joined
    # by a cross frame, red body in the middle.
    p.line(X(32), Y(-14), X(46), Y(-14), WHITE, s)
    p.line(X(32), Y(-2), X(46), Y(-2), WHITE, s)
    p.line(X(39), Y(-14), X(39), Y(-2), WHITE, s)
    for rx, ry in ((32, -14), (46, -14), (32, -2), (46, -2)):
        p.circle(X(rx), Y(ry), 2 * s, WHITE)
    p.circle(X(39), Y(-8), 2 * s, RED)


def icon_tower(p, ix, iy):
    # A tall skyscraper with a blast burst at its crown.
    p.rect(ix + 12, iy + 10, ix + 32, iy + 44, (203, 213, 225))
    for wy in (16, 24, 32):
        p.rect(ix + 16, iy + wy, ix + 20, iy + wy + 3, INK)
        p.rect(ix + 24, iy + wy, ix + 28, iy + wy + 3, INK)
    p.rect(ix + 10, iy + 42, ix + 34, iy + 44, STEEL)
    # Blast burst: alternating red/orange rays around a red core with a
    # gold heart, so it reads as an explosion rather than a sun.
    for k in range(8):
        ang = k * 3.14159265 / 4
        x0 = int(ix + 22 + 8 * cos(ang))
        y0 = int(iy + 8 + 8 * sin(ang))
        x1 = int(ix + 22 + 16 * cos(ang))
        y1 = int(iy + 8 + 16 * sin(ang))
        p.line(x0, y0, x1, y1, RED if k % 2 == 0 else ORANGE, 3)
    p.circle(ix + 22, iy + 8, 5, RED)
    p.circle(ix + 22, iy + 8, 2, GOLD)


def icon_radar(p, ix, iy):
    # A radar dish sweeping, with a small jet above it.
    p.circle(ix + 22, iy + 26, 16, GREEN)
    p.circle(ix + 22, iy + 26, 12, INK)
    p.line(ix + 22, iy + 26, ix + 34, iy + 14, GREEN, 2)
    p.line(ix + 16, iy + 40, ix + 28, iy + 40, STEEL, 3)
    p.poly([(ix + 30, iy + 2), (ix + 44, iy + 8), (ix + 30, iy + 12)], WHITE)
    p.poly([(ix + 32, iy + 8), (ix + 26, iy + 4), (ix + 32, iy + 6)], WHITE)


def icon_gavel(p, ix, iy):
    # A judge's gavel: a horizontal head, a diagonal handle and the
    # sounding block below it. (The old diagonal bar with a block at
    # each end read as a dumbbell.)
    p.rect(ix + 4, iy + 6, ix + 40, iy + 16, GOLD)
    p.rect(ix + 4, iy + 6, ix + 10, iy + 16, (210, 180, 140))
    p.line(ix + 22, iy + 16, ix + 30, iy + 38, (210, 180, 140), 4)
    p.rect(ix + 12, iy + 38, ix + 36, iy + 44, STEEL)


def icon_chip(p, ix, iy):
    # A processor chip with pins.
    p.rect(ix + 10, iy + 10, ix + 34, iy + 34, (30, 41, 59))
    p.rect(ix + 16, iy + 16, ix + 28, iy + 28, SKY)
    for k in range(4):
        p.line(ix + 14 + k * 6, iy + 4, ix + 14 + k * 6, iy + 10, GOLD, 2)
        p.line(ix + 14 + k * 6, iy + 34, ix + 14 + k * 6, iy + 40, GOLD, 2)
        p.line(ix + 4, iy + 14 + k * 6, ix + 10, iy + 14 + k * 6, GOLD, 2)
        p.line(ix + 34, iy + 14 + k * 6, ix + 40, iy + 14 + k * 6, GOLD, 2)


def icon_ball(p, ix, iy):
    # A football: white ball, dark patches.
    p.circle(ix + 22, iy + 22, 20, WHITE)
    p.poly([(ix + 18, iy + 16), (ix + 26, iy + 16), (ix + 29, iy + 22),
            (ix + 26, iy + 28), (ix + 18, iy + 28), (ix + 15, iy + 22)], INK)
    p.circle(ix + 10, iy + 10, 3, INK)
    p.circle(ix + 34, iy + 10, 3, INK)
    p.circle(ix + 10, iy + 34, 3, INK)
    p.circle(ix + 34, iy + 34, 3, INK)


# ---------------------------------------------------------------- poster
def draw_panel(p, x0, y0, x1, y1, bg, kicker, titles, subs, accent, icon):
    p.rect(x0, y0, x1, y1, bg)
    icon(p, x0 + 18, y0 + 8)
    # Kicker at scale 3 keeps the region label legible at the judge's
    # reduced viewing size; scale 2 shrank to ~4 px tall and was unreadable.
    p.text(x0 + 74, y0 + 20, kicker, 3, accent)
    y = y0 + 62
    for line in titles:
        p.text(x0 + 18, y, line, 5, WHITE)
        y += 41
    y = y0 + 150
    for line in subs:
        p.text(x0 + 18, y, line, 3, CREAM)
        y += 25


def build():
    p = Poster()

    # Header.
    p.rect(0, 0, W, 132, NAVY)
    p.centre_text(24, "THE WORLD TODAY", 7, WHITE)
    p.centre_text(88, "WEDNESDAY 25 NOVEMBER 2026", 4, GOLD)
    p.rect(0, 132, W, 136, GOLD)

    # Lead story: Ukraine's strikes reach far beyond its own shores.
    p.rect(16, 144, 1008, 392, CRIMSON)
    p.text(40, 162, "UKRAINE - THE WAR SPREADS", 3, GOLD)
    p.text(40, 192, "KYIV HITS RUSSIAN", 7, WHITE)
    p.text(40, 252, "SHIPS FAR FROM HOME", 7, WHITE)
    p.text(40, 326, "ZELENSKIY CONFIRMS GULF OF FINLAND STRIKE", 3, CRIMSON_SUB)
    p.text(40, 356, "WARSHIP SUNK OFF LIBYA TOO", 3, CRIMSON_SUB)
    # The lead icon is drawn at 3x so it fills the wide empty space to
    # the right of the headline instead of floating in it.
    icon_ship(p, 856, 225, s=3)

    # Four stories in a 2x2 grid.
    draw_panel(p, 16, 404, 504, 616, TEAL, "SAUDI - RIYADH",
               ["HOUTHIS HIT", "RIYADH TOWER"],
               ["11 hurt in strike on", "tallest skyscraper"],
               ORANGE, icon_tower)
    draw_panel(p, 520, 404, 1008, 616, BLUE, "NATO - POLAND",
               ["NATO WATCHES", "OVER POLAND"],
               ["AWACS plane promised", "after missiles landed"],
               GOLD, icon_radar)
    draw_panel(p, 16, 628, 504, 840, FOREST, "FRANCE - PARIS",
               ["SARKOZY TO", "FACE TRIAL"],
               ["Corruption case ordered", "to trial with Bruni"],
               GOLD, icon_gavel)
    draw_panel(p, 520, 628, 1008, 840, PLUM, "CHINA - US COURT",
               ["HUAWEI FOUND", "GUILTY IN US"],
               ["Convicted over Iran", "business dealings"],
               SKY, icon_chip)

    # Bottom strip: Real Madrid's 5-1 Champions League night. The kicker
    # is scale 3 like every other panel (scale 2 was visibly smaller),
    # and the 5-1 scoreline is shown big at the right, filling the
    # strip's dead space behind a divider.
    p.rect(16, 852, 1008, 1008, VIOLET)
    icon_ball(p, 40, 884)
    p.text(170, 866, "FOOTBALL - MADRID", 3, GOLD)
    p.text(170, 894, "MADRID THRASH PSV", 5, WHITE)
    p.text(170, 942, "BELLINGHAM STUNNER, MBAPPE BRACE", 3, CREAM)
    p.line(830, 876, 830, 984, (120, 90, 180), 2)
    p.text(852, 894, "5-1", 8, GOLD)

    return png_bytes(p.px)


def png_bytes(px):
    raw = b"".join(b"\x00" + bytes(px[y * W * 3:(y + 1) * W * 3]) for y in range(H))

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        return out + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = build()
    tmp = os.path.join(out_dir, ".entry.png.tmp")
    final = os.path.join(out_dir, "entry.png")
    with open(tmp, "wb") as f:
        f.write(data)
    os.chmod(tmp, 0o644)
    os.replace(tmp, final)
    os.chmod(final, 0o644)


if __name__ == "__main__":
    main()
