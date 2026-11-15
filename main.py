#!/usr/bin/env python3
"""ai-excited-01 entry: draw one exciting image, write it to /output/entry.png.

A tiny lit city rides on the back of a colossal sea turtle, mid-stride
through a golden-hour ocean, sun low on the horizon, birds scattering.
Extreme scale contrast, one thrilling moment, flat vector style so the
idea still hits at 300 px wide.

Drawn procedurally into a 1024x1024 RGB buffer and encoded as PNG by
hand (zlib + struct). Standard library only: no network, no clock, no
randomness, so two runs write byte-identical output.
"""
import math
import os
import struct
import sys
import zlib

W = 1024
H = 1024

# ---- palette: golden-hour flat vector -------------------------------
SKY_TOP = (24, 16, 64)        # deep indigo, top of sky
SKY_MID = (122, 44, 139)      # magenta purple
SKY_LOW = (226, 87, 76)       # coral
SKY_HOR = (249, 160, 63)      # gold at the horizon
SUN_CORE = (255, 215, 106)    # sun disc
SUN_HALO = (255, 158, 61)     # sun glow ring
CLOUD = (247, 178, 103)       # warm cloud bellies
CLOUD_HI = (255, 214, 150)    # cloud tops catching sun
SEA = (13, 74, 88)            # deep teal sea
SEA_LIGHT = (46, 139, 154)    # sea streaks
SUN_PATH = (232, 145, 58)     # sun reflection on the water
SHELL = (29, 91, 69)          # turtle shell
SHELL_DARK = (18, 72, 54)     # shell shadow plates
SHELL_PLATE = (47, 122, 92)   # shell plate tops
RIM = (249, 200, 107)         # warm rim light on the shell
SKIN = (74, 140, 108)          # turtle neck, head, legs
SKIN_DARK = (38, 88, 66)      # turtle shadow side
CITY = (34, 22, 54)           # city silhouette
WINDOW = (255, 215, 106)      # lit windows
BEAM = (255, 233, 168)        # lighthouse beam
BIRD = (28, 16, 48)           # birds
SPRAY = (207, 232, 224)       # spray and foam


def _lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _chunk(tag, data):
    out = struct.pack(">I", len(data)) + tag + data
    out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return out


def encode_png(canvas):
    """Encode a Canvas as a whole PNG: signature, IHDR, one IDAT, IEND."""
    raw = bytearray()
    for row in canvas.rows:
        raw.append(0)  # filter: none
        raw += row
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))


class Canvas:
    """An RGB pixel buffer with fast span-based flat drawing."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.rows = [bytearray(w * 3) for _ in range(h)]

    def span(self, y, x0, x1, rgb):
        """Fill one horizontal run [x0, x1] on row y with a flat colour."""
        if y < 0 or y >= self.h:
            return
        x0 = max(0, x0)
        x1 = min(self.w - 1, x1)
        if x1 < x0:
            return
        self.rows[y][x0 * 3:(x1 + 1) * 3] = bytes(rgb) * (x1 - x0 + 1)

    def rect(self, x0, y0, x1, y1, rgb):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            self.span(y, x0, x1, rgb)

    def vgrad(self, y0, y1, stops):
        """Vertical gradient over rows y0..y1 through (t, colour) stops."""
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            t = (y - y0) / max(1, y1 - y0)
            for i in range(len(stops) - 1):
                t0, c0 = stops[i]
                t1, c1 = stops[i + 1]
                if t0 <= t <= t1:
                    self.span(y, 0, self.w - 1,
                              _lerp(c0, c1, (t - t0) / max(1e-9, t1 - t0)))
                    break

    def disc(self, cx, cy, r, rgb):
        """Filled circle, centre (cx, cy), radius r."""
        for dy in range(-r, r + 1):
            half = int((r * r - dy * dy) ** 0.5)
            self.span(cy + dy, cx - half, cx + half, rgb)

    def ellipse(self, cx, cy, rx, ry, rgb):
        """Filled axis-aligned ellipse."""
        for dy in range(-ry, ry + 1):
            f = 1.0 - (dy * dy) / float(ry * ry)
            half = int(rx * (f ** 0.5)) if f > 0 else 0
            self.span(cy + dy, cx - half, cx + half, rgb)

    def poly(self, pts, rgb):
        """Filled polygon from a list of (x, y) vertices, scanline fill."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if y0 == y1:
                    continue
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.span(y, int(round(xs[i])), int(round(xs[i + 1])), rgb)

    def thick_line(self, x0, y0, x1, y1, w, rgb):
        """A thick straight segment, drawn as a quad plus round caps."""
        dx, dy = x1 - x0, y1 - y0
        ln = (dx * dx + dy * dy) ** 0.5
        if ln == 0:
            self.disc(x0, y0, w // 2, rgb)
            return
        nx, ny = -dy / ln * w / 2.0, dx / ln * w / 2.0
        self.poly([(int(x0 + nx), int(y0 + ny)), (int(x1 + nx), int(y1 + ny)),
                   (int(x1 - nx), int(y1 - ny)), (int(x0 - nx), int(y0 - ny))],
                  rgb)
        self.disc(x0, y0, w // 2, rgb)
        self.disc(x1, y1, w // 2, rgb)


# ---- scene: sky, sun, clouds, sea ------------------------------------
GLOW = (240, 122, 68)         # sun outer glow, pre-blended with the sky


def draw_sky(c):
    c.vgrad(0, 719, [(0.0, SKY_TOP), (0.45, SKY_MID),
                     (0.75, SKY_LOW), (1.0, SKY_HOR)])


def draw_sun(c):
    c.disc(800, 560, 190, GLOW)
    c.disc(800, 560, 150, SUN_HALO)
    c.disc(800, 560, 88, SUN_CORE)


def draw_clouds(c):
    c.ellipse(210, 170, 130, 15, CLOUD)
    c.ellipse(620, 110, 160, 16, CLOUD_HI)
    c.ellipse(880, 300, 110, 13, CLOUD)
    c.ellipse(140, 330, 100, 13, CLOUD_HI)
    c.ellipse(470, 250, 90, 11, CLOUD)


def draw_sea(c):
    c.rect(0, 720, W - 1, H - 1, SEA)
    # sun shimmer: short dashes only where the sea is visible
    for y, x0, x1 in ((748, 950, 1015), (800, 955, 1010), (860, 20, 90),
                      (920, 960, 1015), (985, 30, 110)):
        c.rect(x0, y, x1, y + 5, SUN_PATH)
    # long shimmer streaks across the water
    for y, x0, x1 in ((748, 40, 420), (792, 880, 1010), (858, 30, 300),
                      (912, 900, 1020), (968, 60, 380), (1005, 850, 1020)):
        c.rect(x0, y, x1, y + 5, SEA_LIGHT)
    # tiny sailboat far right, for scale against the turtle
    c.poly([(955, 772), (966, 742), (977, 772)], SPRAY)
    c.rect(948, 772, 984, 780, CITY)


# ---- scene: turtle, city, birds, spray --------------------------------
def _hexagon(cx, cy, r):
    pts = []
    for i in range(6):
        ang = math.pi * (0.5 + i / 3.0)
        pts.append((int(cx + r * 0.94 * math.cos(ang)),
                    int(cy + r * math.sin(ang))))
    return pts


def draw_turtle(c):
    # rim light: gold shell shifted up, then the green shell over it
    c.ellipse(480, 1038, 520, 330, RIM)
    c.ellipse(480, 1050, 520, 330, SHELL)
    # shell plates: hexagons with dark gaps showing the shell beneath
    for cx, cy, r in ((330, 800, 62), (480, 760, 70), (630, 800, 62),
                      (280, 920, 58), (430, 900, 66), (580, 920, 58),
                      (700, 860, 52), (380, 990, 60), (560, 990, 60)):
        c.poly(_hexagon(cx, cy, r), SHELL_DARK)
        c.poly(_hexagon(cx, cy, r - 12), SHELL_PLATE)
    # tail poking out on the right
    c.poly([(898, 848), (996, 892), (902, 922)], SKIN_DARK)
    # neck and head, facing left: thick neck rising from the shell's shoulder
    c.thick_line(215, 875, 130, 725, 64, SKIN)
    c.ellipse(112, 702, 62, 48, SKIN)
    c.disc(88, 694, 8, BIRD)
    c.disc(85, 691, 3, SPRAY)
    c.thick_line(70, 722, 128, 714, 6, SKIN_DARK)
    # rear leg planted, front leg lifted mid-stride with a clear foot
    c.thick_line(725, 950, 745, 1006, 72, SKIN)
    c.ellipse(746, 1012, 56, 18, SKIN)
    c.thick_line(310, 950, 228, 1008, 68, SKIN)
    c.ellipse(218, 1012, 52, 20, SKIN)
    c.disc(182, 1018, 10, SKIN)
    c.disc(206, 1020, 10, SKIN)


def draw_city(c):
    # mini skyline riding the shell's top curve, baseline ~y 745
    buildings = [(280, 42, 55), (330, 36, 80), (374, 48, 62),
                 (430, 40, 95), (478, 34, 70), (520, 46, 58),
                 (574, 38, 85), (620, 30, 60)]
    for x0, w, h in buildings:
        c.rect(x0, 745 - h, x0 + w, 762, CITY)
        for row in range(745 - h + 8, 745 - 6, 12):
            for col in range(x0 + 6, x0 + w - 4, 10):
                if (row + col) % 3 == 0:
                    c.rect(col, row, col + 4, row + 6, WINDOW)
    # central tower with spire and beacon
    c.rect(452, 600, 496, 762, CITY)
    c.poly([(452, 600), (496, 600), (474, 560)], CITY)
    c.disc(474, 556, 5, WINDOW)
    # lighthouse with a beam toward the sun
    c.rect(616, 648, 640, 762, CITY)
    c.rect(616, 648, 640, 660, WINDOW)
    c.poly([(640, 652), (772, 606), (772, 668)], BEAM)


def draw_birds(c):
    for x, y, s in ((300, 150, 16), (360, 120, 12), (180, 220, 13),
                    (700, 200, 15), (760, 160, 11), (520, 90, 12)):
        c.thick_line(x - s, y, x, y - 6, 4, BIRD)
        c.thick_line(x, y - 6, x + s, y, 4, BIRD)


def draw_spray(c):
    # droplets and foam kicked up by the lifted front foot
    for x, y, r in ((168, 1000, 8), (142, 984, 5), (196, 972, 6),
                    (118, 1012, 7), (232, 988, 4), (152, 1020, 6),
                    (96, 1002, 5), (252, 1006, 5)):
        c.disc(x, y, r, SPRAY)


def build_image():
    c = Canvas(W, H)
    draw_sky(c)
    draw_sun(c)
    draw_clouds(c)
    draw_sea(c)
    draw_turtle(c)
    draw_city(c)
    draw_birds(c)
    draw_spray(c)
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    data = encode_png(build_image())
    if len(data) > 1048576:
        raise ValueError("entry.png is over 1 MiB: %d bytes" % len(data))
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "entry.png"), "wb") as handle:
        handle.write(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
