#!/usr/bin/env python3
"""news-image-20261125 entry: a one-page newspaper front page summing up the
world news of Wednesday 25 November 2026, drawn pixel by pixel with pure
Python 3 standard library only (math, os, struct, zlib). No network, no
clock, no randomness: two runs write byte-identical PNG files.

Writes $MAKEFUN_OUTPUT_DIR/entry.png (default: out/entry.png), 1024x1024,
under 1 MiB."""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ------------------------------------------------------------------ palette
PAPER = (247, 242, 232)
CARD = (255, 255, 255)
INK = (16, 20, 28)
NAVY = (13, 38, 68)
GOLD = (214, 162, 60)
MUTED = (70, 70, 70)
FAINT = (110, 110, 110)
CRIMSON = (172, 32, 32)
TEAL = (12, 110, 110)
FOREST = (28, 120, 60)
ROYAL = (30, 70, 150)
AMBER = (198, 108, 18)

# ------------------------------------------------- 5x7 bitmap font (bit rows)
# One glyph = 7 integers; bit 4 is the leftmost pixel, bit 0 the rightmost.
GLYPHS = {
    "A": [14, 17, 17, 31, 17, 17, 17],
    "B": [30, 17, 17, 30, 17, 17, 30],
    "C": [14, 17, 16, 16, 16, 17, 14],
    "D": [30, 17, 17, 17, 17, 17, 30],
    "E": [31, 16, 16, 30, 16, 16, 31],
    "F": [31, 16, 16, 30, 16, 16, 16],
    "G": [14, 17, 16, 23, 17, 17, 15],
    "H": [17, 17, 17, 31, 17, 17, 17],
    "I": [14, 4, 4, 4, 4, 4, 14],
    "J": [7, 2, 2, 2, 2, 18, 12],
    "K": [17, 18, 20, 24, 20, 18, 17],
    "L": [16, 16, 16, 16, 16, 16, 31],
    "M": [17, 27, 21, 21, 17, 17, 17],
    "N": [17, 25, 21, 19, 17, 17, 17],
    "O": [14, 17, 17, 17, 17, 17, 14],
    "P": [30, 17, 17, 30, 16, 16, 16],
    "Q": [14, 17, 17, 17, 21, 18, 13],
    "R": [30, 17, 17, 30, 20, 18, 17],
    "S": [15, 16, 16, 14, 1, 1, 30],
    "T": [31, 4, 4, 4, 4, 4, 4],
    "U": [17, 17, 17, 17, 17, 17, 14],
    "V": [17, 17, 17, 17, 17, 10, 4],
    "W": [17, 17, 17, 21, 21, 27, 17],
    "X": [17, 17, 10, 4, 10, 17, 17],
    "Y": [17, 17, 10, 4, 4, 4, 4],
    "Z": [31, 1, 2, 4, 8, 16, 31],
    "0": [14, 17, 19, 21, 25, 17, 14],
    "1": [4, 12, 4, 4, 4, 4, 14],
    "2": [14, 17, 1, 6, 8, 16, 31],
    "3": [31, 2, 4, 2, 1, 17, 14],
    "4": [2, 6, 10, 18, 31, 2, 2],
    "5": [31, 16, 30, 1, 1, 17, 14],
    "6": [6, 8, 16, 30, 17, 17, 14],
    "7": [31, 1, 2, 4, 8, 8, 8],
    "8": [14, 17, 17, 14, 17, 17, 14],
    "9": [14, 17, 17, 15, 1, 2, 12],
    " ": [0, 0, 0, 0, 0, 0, 0],
    ".": [0, 0, 0, 0, 0, 12, 12],
    ",": [0, 0, 0, 0, 12, 4, 8],
    ":": [0, 12, 12, 0, 12, 12, 0],
    ";": [0, 12, 12, 0, 12, 4, 8],
    "'": [4, 4, 8, 0, 0, 0, 0],
    "-": [0, 0, 0, 14, 0, 0, 0],
    "/": [1, 2, 2, 4, 8, 8, 16],
    "(": [2, 4, 8, 8, 8, 4, 2],
    ")": [8, 4, 2, 2, 2, 4, 8],
    "&": [12, 18, 20, 8, 21, 18, 13],
    "!": [4, 4, 4, 4, 4, 0, 4],
    "?": [14, 17, 1, 6, 4, 0, 4],
    "%": [25, 26, 2, 4, 8, 11, 19],
    "+": [0, 4, 4, 31, 4, 4, 0],
    "=": [0, 0, 31, 0, 31, 0, 0],
    "$": [4, 15, 20, 14, 5, 30, 4],
    "*": [0, 10, 4, 14, 4, 10, 0],
}


def glyph_width(text, scale):
    """Pixel width of text at the given scale (6 px per char cell)."""
    return len(text) * 6 * scale - scale


# -------------------------------------------------------------------- canvas
class Page:
    """An RGB canvas backed by one flat bytearray."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bg * (w * h))

    def dot(self, x, y, col):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = col

    def fill(self, x, y, w, h, col):
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + w, self.w), min(y + h, self.h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            for _ in range(x0, x1):
                self.buf[i], self.buf[i + 1], self.buf[i + 2] = col
                i += 3

    def seg(self, x0, y0, x1, y1, col, thick=1):
        """Bresenham line with square brush of size `thick`."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        half = thick // 2
        while True:
            for a in range(-half, half + 1):
                for b in range(-half, half + 1):
                    self.dot(x0 + a, y0 + b, col)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, col, solid=True):
        if solid:
            for dy in range(-r, r + 1):
                dx = int(math.sqrt(max(r * r - dy * dy, 0)))
                self.fill(cx - dx, cy + dy, 2 * dx + 1, 1, col)
        else:
            steps = max(24, int(2 * math.pi * r))
            for i in range(steps):
                a = 2 * math.pi * i / steps
                self.dot(int(cx + r * math.cos(a)),
                         int(cy + r * math.sin(a)), col)

    def gon(self, pts, col, solid=True):
        if not solid:
            n = len(pts)
            for i in range(n):
                self.seg(pts[i][0], pts[i][1],
                         pts[(i + 1) % n][0], pts[(i + 1) % n][1], col)
            return
        ys = [p[1] for p in pts]
        n = len(pts)
        for y in range(min(ys), max(ys) + 1):
            xs = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.fill(int(xs[j]), y,
                          int(xs[j + 1]) - int(xs[j]) + 1, 1, col)

    def burst(self, cx, cy, outer, inner, col):
        pts = []
        for i in range(16):
            r = outer if i % 2 == 0 else inner
            a = math.pi * i / 8 - math.pi / 2
            pts.append((int(cx + r * math.cos(a)),
                        int(cy + r * math.sin(a))))
        self.gon(pts, col)

    def draw_text(self, x, y, s, scale, col):
        cx = x
        for ch in s.upper():
            rows = GLYPHS.get(ch, GLYPHS[" "])
            for r, bits in enumerate(rows):
                for c in range(5):
                    if bits & (1 << (4 - c)):
                        self.fill(cx + c * scale, y + r * scale,
                                  scale, scale, col)
            cx += 6 * scale
        return cx

    def draw_center(self, y, s, scale, col, x0=0, x1=None):
        if x1 is None:
            x1 = self.w
        w = glyph_width(s, scale)
        self.draw_text(x0 + (x1 - x0 - w) // 2, y, s, scale, col)


# --------------------------------------------------------------- pictograms
def art_sea_war(pg, x, y, w, h):
    """A cargo ship and a small warship on open sea, a drone above."""
    pg.fill(x, y, w, h, (208, 232, 242))
    pg.fill(x, y + h - 26, w, 26, (36, 110, 158))
    pg.fill(x, y + h - 18, w, 3, (120, 190, 220))
    # cargo ship, left
    base = y + h - 26
    pg.gon([(x + 40, base - 30), (x + 330, base - 30), (x + 372, base - 4),
            (x + 40, base - 4)], (42, 54, 68))
    pg.fill(x + 40, base - 30, 290, 6, (120, 40, 30))
    for i, col in enumerate([(200, 70, 50), (60, 110, 150),
                             (220, 160, 40), (90, 140, 90)]):
        pg.fill(x + 62 + i * 52, base - 56, 46, 26, col)
    pg.fill(x + 300, base - 62, 34, 32, (228, 228, 222))
    pg.fill(x + 304, base - 58, 26, 6, (40, 60, 90))
    # warship, right, with a hit burst above it
    pg.gon([(x + 620, base - 18), (x + 880, base - 18), (x + 912, base - 4),
            (x + 620, base - 4)], (70, 76, 84))
    pg.fill(x + 700, base - 44, 10, 26, (70, 76, 84))
    pg.fill(x + 660, base - 52, 90, 8, (70, 76, 84))
    pg.fill(x + 758, base - 78, 5, 28, (70, 76, 84))
    pg.gon([(x + 763, base - 78), (x + 790, base - 72), (x + 763, base - 66)],
           (172, 32, 32))
    pg.burst(x + 780, y + 30, 30, 12, (245, 140, 30))
    pg.burst(x + 780, y + 30, 18, 8, (255, 210, 60))
    pg.disc(x + 780, y + 30, 7, (255, 240, 180))
    # drone with dotted path
    dx, dy = x + 520, y + 22
    pg.fill(dx - 14, dy - 2, 28, 4, INK)
    pg.fill(dx - 3, dy - 8, 6, 16, INK)
    for i in range(6):
        pg.disc(dx - 60 - i * 16, dy + 26 + i * 3, 2, INK)


def art_hormuz(pg, x, y, w, h):
    """A tanker under a flame, with a rising oil-price arrow."""
    pg.fill(x, y, w, h, (232, 226, 208))
    pg.fill(x, y + h - 20, w, 20, (30, 96, 130))
    base = y + h - 20
    pg.gon([(x + 24, base - 26), (x + 250, base - 26), (x + 282, base - 4),
            (x + 24, base - 4)], (52, 52, 58))
    pg.fill(x + 24, base - 26, 226, 6, (150, 50, 30))
    pg.fill(x + 210, base - 52, 28, 26, (225, 225, 218))
    pg.burst(x + 130, y + 26, 26, 11, (240, 120, 20))
    pg.burst(x + 130, y + 26, 15, 7, (255, 200, 60))
    # oil barrel
    bx = x + w - 110
    pg.fill(bx, y + 26, 62, 52, (40, 40, 44))
    pg.fill(bx, y + 36, 62, 4, (120, 120, 120))
    pg.fill(bx, y + 62, 62, 4, (120, 120, 120))
    pg.draw_text(bx + 12, y + 44, "OIL", 2, GOLD)
    # rising arrow
    ax, ay = x + w - 210, y + h - 34
    pg.seg(ax, ay, ax + 46, ay - 26, FOREST, thick=4)
    pg.seg(ax + 46, ay - 26, ax + 78, ay - 52, FOREST, thick=4)
    pg.gon([(ax + 78, ay - 52), (ax + 62, ay - 50), (ax + 76, ay - 34)],
           FOREST)


def art_court(pg, x, y, w, h):
    """A courthouse front with columns and a gavel."""
    pg.fill(x, y, w, h, (226, 232, 240))
    cx = x + w // 2 - 90
    # pediment and columns
    pg.gon([(cx - 20, y + 34), (cx + 110, y + 6), (cx + 240, y + 34)],
           (52, 66, 92))
    pg.fill(cx - 20, y + 34, 260, 6, (52, 66, 92))
    for i in range(4):
        px = cx + 6 + i * 62
        pg.fill(px, y + 40, 18, h - 52, (240, 240, 236))
        pg.fill(px - 3, y + 40, 24, 5, (52, 66, 92))
        pg.fill(px - 3, y + h - 18, 24, 5, (52, 66, 92))
    pg.fill(cx - 20, y + h - 12, 260, 6, (52, 66, 92))
    # gavel, right
    gx, gy = x + w - 96, y + 12
    pg.seg(gx, gy + 34, gx + 44, gy + 6, (120, 80, 40), thick=6)
    pg.fill(gx + 30, gy - 2, 26, 16, (90, 60, 30))
    pg.fill(gx + 58, gy + 34, 34, 12, (90, 60, 30))


def art_servers(pg, x, y, w, h):
    """Server racks and a rising chart, with the AI order figure."""
    pg.fill(x, y, w, h, (22, 30, 42))
    for rx in (x + 26, x + 118):
        pg.fill(rx, y + 10, 72, h - 20, (58, 68, 84))
        for row in range(5):
            ry = y + 16 + row * 12
            pg.fill(rx + 6, ry, 60, 8, (30, 38, 52))
            pg.disc(rx + 14, ry + 4, 2, (80, 220, 120))
            pg.disc(rx + 24, ry + 4, 2, (255, 200, 60))
    # rising chart line
    ox, oy = x + 220, y + h - 18
    pg.seg(ox, oy, ox + 50, oy - 22, (80, 220, 120), thick=4)
    pg.seg(ox + 50, oy - 22, ox + 96, oy - 40, (80, 220, 120), thick=4)
    pg.gon([(ox + 96, oy - 40), (ox + 80, oy - 38), (ox + 94, oy - 22)],
           (80, 220, 120))
    pg.draw_text(x + 330, y + 14, "$60BN", 3, (80, 220, 120))
    pg.draw_text(x + 330, y + 42, "AI ORDERS", 2, (200, 210, 220))


def art_gaza(pg, x, y, w, h):
    """A city skyline at dusk with an aid crate in front."""
    pg.fill(x, y, w, h, (250, 230, 210))
    pg.disc(x + w - 60, y + 18, 14, (245, 190, 90))
    base = y + h - 6
    heights = [30, 48, 26, 58, 40, 52, 28, 44]
    bw = w // len(heights)
    for i, bh in enumerate(heights):
        bx = x + i * bw + 2
        pg.fill(bx, base - bh, bw - 4, bh, (64, 56, 50))
        for wy in range(base - bh + 6, base - 6, 12):
            pg.fill(bx + 4, wy, 5, 6, (240, 200, 90))
    # aid crate with a red cross
    cx, cy = x + 30, y + h - 44
    pg.fill(cx, cy, 52, 38, (245, 245, 240))
    pg.fill(cx + 22, cy + 6, 8, 26, CRIMSON)
    pg.fill(cx + 13, cy + 15, 26, 8, CRIMSON)


# ------------------------------------------------------------------- stories
# Headlines verified against reporting published 25 November 2026 (Reuters,
# Bloomberg, AP, Straits daily brief, Global Eye live wire, BD Global Times).
LEAD = dict(kicker="UKRAINE - WAR AT SEA", accent=CRIMSON, art=art_sea_war,
            head=["RUSSIA CALLS SHIP STRIKES", "TERRORISM AS KYIV CONFIRMS"],
            sub=["ZELENSKIY: UKRAINE HIT RUSSIAN CARGO SHIP IN GULF OF FINLAND",
                 "AND SANK A WARSHIP OFF LIBYA - NORWAY URGES CAUTION"])

GRID = [
    dict(kicker="STRAIT OF HORMUZ", accent=TEAL, art=art_hormuz,
         head=["FOURTH TANKER HIT BY MINE"],
         sub=["IRAN CLAIMS NEW BLAST IN HORMUZ;",
              "OIL JUMPS - BRENT $91.40"]),
    dict(kicker="USA - TECH TRIAL", accent=ROYAL, art=art_court,
         head=["HUAWEI GUILTY ON 10", "OF 12 COUNTS"],
         sub=["BROOKLYN JURY CONVICTS ON FRAUD,",
              "SANCTIONS AND TRADE SECRETS"]),
    dict(kicker="MARKETS - AI BOOM", accent=FOREST, art=art_servers,
         head=["DELL AI ORDERS HIT $60BN"],
         sub=["REVENUE $54.9BN BEATS FORECASTS,",
              "BUT AI SHARES SLIDE - DELL -11%"]),
    dict(kicker="GAZA - AID CRISIS", accent=AMBER, art=art_gaza,
         head=["GAZA TOLL 74,746 AS", "HUNGER GROWS"],
         sub=["WFP: 266 MILLION FACE ACUTE",
              "FOOD INSECURITY WORLDWIDE"]),
]

ALSO_TOP = ("ALSO: ENGLAND LEVEL T20 SERIES - DONALD 85 OFF 32 BEATS AUSTRALIA")
ALSO_BOT = ("BJP AND SAD REUNITE FOR PUNJAB 2027 - SARKOZY CASE ORDERED TO TRIAL")


# --------------------------------------------------------------------- layout
def card_frame(pg, x, y, w, h):
    pg.fill(x, y, w, h, CARD)
    pg.fill(x, y, w, 2, INK)
    pg.fill(x, y + h - 2, w, 2, INK)
    pg.fill(x, y, 2, h, INK)
    pg.fill(x + w - 2, y, 2, h, INK)


def render():
    pg = Page(W, H, PAPER)
    # outer frame
    pg.fill(0, 0, W, 6, INK)
    pg.fill(0, H - 6, W, 6, INK)
    pg.fill(0, 0, 6, H, INK)
    pg.fill(W - 6, 0, 6, H, INK)

    # ---- masthead
    pg.fill(0, 6, W, 162, NAVY)
    pg.draw_center(24, "THE WORLD IN ONE DAY", 2, GOLD)
    pg.draw_center(56, "25 NOVEMBER 2026", 8, CARD)
    pg.draw_center(132, "WEDNESDAY - THE DAY IN ONE PAGE", 2, GOLD)
    pg.fill(16, 164, W - 32, 3, GOLD)

    # ---- standfirst
    pg.draw_center(182, "WAR AT SEA, A STRAIT ON EDGE, AND AN AI BOOM THAT COOLED",
                   2, INK)

    # ---- lead story, full width
    lx, ly, lw, lh = 16, 206, 992, 236
    card_frame(pg, lx, ly, lw, lh)
    pg.fill(lx + 2, ly + 2, lw - 4, 26, LEAD["accent"])
    pg.draw_text(lx + 14, ly + 10, LEAD["kicker"], 2, CARD)
    LEAD["art"](pg, lx + 2, ly + 28, lw - 4, 92)
    hy = ly + 130
    for line in LEAD["head"]:
        pg.draw_center(hy, line, 4, INK, lx + 14, lx + lw - 14)
        hy += 34
    sy = hy + 4
    for line in LEAD["sub"]:
        pg.draw_center(sy, line, 2, MUTED, lx + 14, lx + lw - 14)
        sy += 19

    # ---- four stories, 2 x 2
    gx0, gw = 16, 488
    gy0, gh, gap = 454, 226, 12
    for i, st in enumerate(GRID):
        col, row = i % 2, i // 2
        x = gx0 + col * (gw + 16)
        y = gy0 + row * (gh + gap)
        card_frame(pg, x, y, gw, gh)
        pg.fill(x + 2, y + 2, gw - 4, 24, st["accent"])
        pg.draw_text(x + 14, y + 9, st["kicker"], 2, CARD)
        st["art"](pg, x + 2, y + 26, gw - 4, 78)
        hy = y + 112
        for line in st["head"]:
            pg.draw_center(hy, line, 3, INK, x + 14, x + gw - 14)
            hy += 24
        sy = hy + 4
        for line in st["sub"]:
            pg.draw_center(sy, line, 2, MUTED, x + 14, x + gw - 14)
            sy += 19

    # ---- footer
    fy = 930
    pg.fill(0, fy, W, 78, NAVY)
    pg.draw_center(fy + 12, ALSO_TOP, 2, GOLD)
    pg.draw_center(fy + 38, ALSO_BOT, 2, CARD)
    pg.draw_center(1010, "SOURCES: REUTERS, BLOOMBERG, AP - REPORTED 25 NOVEMBER 2026",
                   1, FAINT)
    return pg


# ----------------------------------------------------------------- PNG writer
def png_bytes(pg):
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    body = bytearray()
    for row in range(pg.h):
        body.append(0)  # filter: none
        start = row * pg.w * 3
        body += pg.buf[start:start + pg.w * 3]
    header = struct.pack(">IIBBBBB", pg.w, pg.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) +
            chunk(b"IDAT", zlib.compress(bytes(body), 9)) +
            chunk(b"IEND", b""))


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(outdir, exist_ok=True)
    data = png_bytes(render())
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s %dx%d %d bytes" % (path, W, H, len(data)))


if __name__ == "__main__":
    main()
