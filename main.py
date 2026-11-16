#!/usr/bin/env python3
"""ai-excited-01 entry (v2): draw one exciting image, write /output/entry.png.

A tiny lit city rides on the back of a colossal sea turtle, mid-stride
through a golden-hour ocean, sun low on the horizon, birds scattering
in a wide arc, foam bursting from the lifted flipper and a wake curling
behind. Extreme scale contrast, one thrilling moment, flat vector
style so the idea still hits at 300 px wide.

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
HORIZON = 700

# ---- palette: bolder golden hour ------------------------------------
SKY_TOP = (20, 12, 58)        # deep indigo, top of sky
SKY_MID = (128, 38, 132)      # magenta purple
SKY_LOW = (232, 92, 70)       # coral
SKY_HOR = (252, 166, 64)      # gold at the horizon
SUN_CORE = (255, 220, 120)    # sun disc
SUN_HALO = (255, 164, 66)     # sun glow ring
GLOW = (244, 130, 70)         # sun outer glow, pre-blended with the sky
CLOUD = (248, 182, 108)       # warm cloud bellies
CLOUD_HI = (255, 216, 152)    # cloud tops catching sun
SEA = (10, 70, 84)            # deep teal sea
SEA_LIGHT = (52, 148, 160)    # sea streaks
SUN_PATH = (238, 152, 60)     # sun reflection on the water
WAVE = (36, 120, 138)         # curling wake body
SHELL = (30, 96, 72)          # turtle shell
SHELL_DARK = (16, 68, 50)     # shell shadow plates
SHELL_PLATE = (52, 130, 98)   # shell plate tops
RIM = (252, 206, 110)         # warm rim light on the shell
SKIN = (78, 146, 112)         # turtle neck, head, flippers
SKIN_DARK = (36, 86, 64)      # turtle shadow side
CITY = (30, 20, 52)           # city silhouette
WINDOW = (255, 218, 110)      # lit windows
BEAM = (255, 236, 175)        # lighthouse beam
BIRD = (26, 14, 46)           # birds
SPRAY = (214, 236, 228)       # spray and foam


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


# ---- scene: sky, sun, clouds, sea, wake -------------------------------
def draw_sky(c):
    c.vgrad(0, HORIZON, [(0.0, SKY_TOP), (0.45, SKY_MID),
                         (0.75, SKY_LOW), (1.0, SKY_HOR)])


def draw_sun(c):
    c.disc(815, 545, 200, GLOW)
    c.disc(815, 545, 160, SUN_HALO)
    c.disc(815, 545, 98, SUN_CORE)


def draw_clouds(c):
    # long speed-streak clouds, thin and overlapping, lit from below
    c.ellipse(190, 150, 180, 10, CLOUD)
    c.ellipse(540, 96, 230, 12, CLOUD_HI)
    c.ellipse(860, 235, 150, 10, CLOUD)
    c.ellipse(300, 305, 185, 10, CLOUD_HI)
    c.ellipse(660, 185, 125, 8, CLOUD)
    c.ellipse(120, 420, 130, 9, CLOUD_HI)
    c.ellipse(470, 430, 110, 8, CLOUD)
    # a few small puffs catching the sun
    c.ellipse(730, 330, 60, 9, CLOUD_HI)
    c.ellipse(250, 210, 55, 8, CLOUD)


def draw_sea(c):
    c.rect(0, HORIZON, W - 1, H - 1, SEA)
    # wide shimmering sun-path under the sun: a column of gold dashes
    for y, x0, x1 in ((726, 716, 918), (758, 700, 936), (792, 726, 912),
                      (828, 706, 930), (864, 730, 906), (900, 712, 924),
                      (936, 734, 900), (972, 720, 916), (1004, 740, 896)):
        c.rect(x0, y, x1, y + 6, SUN_PATH)
    # cool streaks across the open water, left and right of the path
    for y, x0, x1 in ((742, 30, 320), (798, 60, 260), (856, 20, 300),
                      (916, 90, 340), (972, 30, 250), (1010, 120, 330)):
        c.rect(x0, y, x1, y + 5, SEA_LIGHT)
    # tiny sailboat far right, for scale against the turtle
    c.poly([(952, 766), (963, 736), (974, 766)], SPRAY)
    c.rect(945, 766, 981, 774, CITY)
    # an even tinier boat far left, almost lost in the light
    c.poly([(52, 742), (60, 722), (68, 742)], SPRAY)
    c.rect(47, 742, 73, 748, CITY)


def draw_wake(c):
    # foam flecks where the shell meets the sea — small broken marks in
    # the visible water just above the shell's edge, so they read as
    # spray, not plates
    for x, y, r in ((60, 730, 5), (100, 725, 6), (150, 735, 5),
                    (190, 745, 4), (230, 748, 5), (860, 725, 5),
                    (900, 735, 6), (950, 728, 5), (990, 740, 5),
                    (1010, 760, 4), (990, 940, 6), (1010, 900, 5)):
        c.disc(x, y, r, SPRAY)


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
    c.ellipse(470, 1052, 545, 340, RIM)
    c.ellipse(470, 1064, 545, 340, SHELL)
    # shell plates: hexagons with dark gaps showing the shell beneath
    for cx, cy, r in ((315, 795, 64), (470, 752, 72), (625, 795, 64),
                      (265, 915, 60), (425, 895, 68), (580, 915, 60),
                      (705, 855, 54), (370, 985, 62), (555, 985, 62),
                      (680, 960, 48)):
        c.poly(_hexagon(cx, cy, r), SHELL_DARK)
        c.poly(_hexagon(cx, cy, r - 12), SHELL_PLATE)
    # tail poking out on the right, bigger than before
    c.poly([(905, 855), (1012, 900), (908, 935)], SKIN_DARK)
    # neck and head, facing left: a thick neck rising from the shoulder,
    # head with a snout so it reads as a turtle, not a blob
    c.thick_line(230, 880, 135, 700, 78, SKIN)
    c.ellipse(105, 678, 68, 52, SKIN)
    c.ellipse(48, 690, 26, 20, SKIN)
    c.disc(82, 668, 9, BIRD)
    c.disc(79, 665, 3, SPRAY)
    c.thick_line(52, 700, 108, 692, 6, SKIN_DARK)
    # rear flipper planted, front flipper lifted mid-stroke with a foot
    c.thick_line(740, 960, 762, 1012, 76, SKIN)
    c.ellipse(764, 1018, 58, 18, SKIN)
    c.thick_line(310, 950, 212, 1006, 70, SKIN)
    c.ellipse(196, 1012, 55, 20, SKIN)
    c.disc(158, 1018, 10, SKIN)
    c.disc(182, 1020, 10, SKIN)
    c.disc(206, 1016, 9, SKIN)


def draw_city(c):
    # a taller, busier skyline riding the shell's top curve, baseline ~745
    buildings = [(258, 40, 58), (304, 34, 84), (344, 46, 66),
                 (396, 38, 102), (440, 34, 74), (480, 44, 62),
                 (530, 36, 92), (572, 30, 64), (608, 42, 78)]
    for x0, w, h in buildings:
        c.rect(x0, 745 - h, x0 + w, 762, CITY)
        for row in range(745 - h + 8, 745 - 6, 11):
            for col in range(x0 + 6, x0 + w - 4, 9):
                if (row + col) % 2 == 0:
                    c.rect(col, row, col + 4, row + 6, WINDOW)
    # domed hall between the towers
    c.rect(500, 700, 560, 762, CITY)
    c.ellipse(530, 700, 30, 22, CITY)
    c.disc(530, 676, 4, WINDOW)
    # central tower with spire and beacon
    c.rect(452, 600, 496, 762, CITY)
    c.poly([(452, 600), (496, 600), (474, 548)], CITY)
    c.disc(474, 544, 6, WINDOW)
    # lighthouse with a wide beam toward the sun
    c.rect(640, 630, 664, 762, CITY)
    c.rect(640, 630, 664, 644, WINDOW)
    c.poly([(664, 634), (790, 600), (790, 680)], BEAM)


def draw_birds(c):
    # a wide arc sweeping up-left, and a small flock near the sun
    for x, y, s in ((150, 185, 17), (205, 150, 14), (265, 122, 15),
                    (325, 102, 12), (385, 88, 13), (445, 82, 11),
                    (505, 82, 12)):
        c.thick_line(x - s, y, x, y - 6, 4, BIRD)
        c.thick_line(x, y - 6, x + s, y, 4, BIRD)
    for x, y, s in ((668, 225, 13), (712, 195, 11), (752, 168, 12),
                    (788, 148, 10)):
        c.thick_line(x - s, y, x, y - 6, 4, BIRD)
        c.thick_line(x, y - 6, x + s, y, 4, BIRD)


def draw_spray(c):
    # a big burst kicked up by the lifted front flipper
    for x, y, r in ((168, 1000, 9), (140, 982, 6), (198, 970, 7),
                    (116, 1012, 8), (234, 986, 5), (150, 1020, 7),
                    (94, 1000, 6), (254, 1004, 6), (210, 950, 5),
                    (120, 962, 5), (262, 962, 4), (180, 940, 4)):
        c.disc(x, y, r, SPRAY)


def build_image():
    c = Canvas(W, H)
    draw_sky(c)
    draw_sun(c)
    draw_clouds(c)
    draw_sea(c)
    draw_turtle(c)
    draw_wake(c)
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
