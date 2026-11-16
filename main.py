#!/usr/bin/env python3
"""The Desert Dreamed of the Sea -- ai-excited-01 entry (v4).

A colossal whale breaches the desert at sunset while a tiny camel caravan
crosses the dunes below. Procedural art, Python standard library only,
fully deterministic: two runs produce byte-identical PNG output.

Output: $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png),
1024x1024 RGB PNG, under 1 MiB.
"""

import math
import os
import struct
import zlib

W = H = 1024


# ---------- deterministic pseudo-random (fixed-seed LCG) ----------
class Rng:
    def __init__(self, seed):
        self.s = seed & 0x7FFFFFFF

    def next(self):
        self.s = (1103515245 * self.s + 12345) & 0x7FFFFFFF
        return self.s / 0x7FFFFFFF

    def range(self, a, b):
        return a + (b - a) * self.next()

    def choice(self, seq):
        return seq[int(self.next() * len(seq)) % len(seq)]


# ---------- canvas ----------
class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)

    def hspan(self, x0, x1, y, c):
        """Fill solid horizontal span [x0, x1) on row y."""
        if y < 0 or y >= self.h:
            return
        x0 = max(0, x0)
        x1 = min(self.w, x1)
        if x1 <= x0:
            return
        i0 = (y * self.w + x0) * 3
        self.px[i0:i0 + (x1 - x0) * 3] = bytes(c) * (x1 - x0)

    def hspan_blend(self, x0, x1, y, c, a):
        """Blend horizontal span [x0, x1) on row y with alpha 0..1."""
        if y < 0 or y >= self.h:
            return
        x0 = max(0, x0)
        x1 = min(self.w, x1)
        if x1 <= x0:
            return
        ia = 1.0 - a
        r, g, b = c
        px = self.px
        base = (y * self.w + x0) * 3
        for x in range(x0, x1):
            i = base + (x - x0) * 3
            px[i] = int(px[i] * ia + r * a)
            px[i + 1] = int(px[i + 1] * ia + g * a)
            px[i + 2] = int(px[i + 2] * ia + b * a)

    def poly(self, pts, c):
        """Fill a polygon (scanline, even-odd)."""
        ys = [p[1] for p in pts]
        y0 = max(0, int(math.floor(min(ys))))
        y1 = min(self.h - 1, int(math.ceil(max(ys))))
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x0, yy0 = pts[i]
                x1, yy1 = pts[(i + 1) % n]
                if (yy0 <= y < yy1) or (yy1 <= y < yy0):
                    t = (y - yy0) / (yy1 - yy0)
                    xs.append(x0 + t * (x1 - x0))
            if len(xs) < 2:
                continue
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                xa = int(math.ceil(xs[k]))
                xb = int(math.floor(xs[k + 1]))
                if xb >= xa:
                    self.hspan(xa, xb + 1, y, c)

    def poly_blend(self, pts, c, a):
        ys = [p[1] for p in pts]
        y0 = max(0, int(math.floor(min(ys))))
        y1 = min(self.h - 1, int(math.ceil(max(ys))))
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x0, yy0 = pts[i]
                x1, yy1 = pts[(i + 1) % n]
                if (yy0 <= y < yy1) or (yy1 <= y < yy0):
                    t = (y - yy0) / (yy1 - yy0)
                    xs.append(x0 + t * (x1 - x0))
            if len(xs) < 2:
                continue
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                xa = int(math.ceil(xs[k]))
                xb = int(math.floor(xs[k + 1]))
                if xb >= xa:
                    self.hspan_blend(xa, xb + 1, y, c, a)

    def disc(self, cx, cy, r, c):
        y0 = max(0, int(cy - r))
        y1 = min(self.h - 1, int(cy + r) + 1)
        for y in range(y0, y1 + 1):
            dy = y - cy
            dx = math.sqrt(max(0.0, r * r - dy * dy))
            self.hspan(int(cx - dx), int(cx + dx) + 1, y, c)

    def disc_blend(self, cx, cy, r, c, a):
        y0 = max(0, int(cy - r))
        y1 = min(self.h - 1, int(cy + r) + 1)
        for y in range(y0, y1 + 1):
            dy = y - cy
            dx = math.sqrt(max(0.0, r * r - dy * dy))
            self.hspan_blend(int(cx - dx), int(cx + dx) + 1, y, c, a)

    def ellipse(self, cx, cy, rx, ry, c, rot=0.0):
        self.poly(ellipse_pts(cx, cy, rx, ry, rot), c)

    def ellipse_blend(self, cx, cy, rx, ry, c, a, rot=0.0):
        self.poly_blend(ellipse_pts(cx, cy, rx, ry, rot), c, a)

    def line(self, x0, y0, x1, y1, c, w=1):
        """Thick line as discs along the segment."""
        dx = x1 - x0
        dy = y1 - y0
        steps = int(max(abs(dx), abs(dy))) + 1
        r = w / 2.0
        for i in range(steps + 1):
            t = i / steps if steps else 0.0
            self.disc(x0 + dx * t, y0 + dy * t, r, c)

    def polyline(self, pts, c, w=1):
        for i in range(len(pts) - 1):
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], c, w)


def ellipse_pts(cx, cy, rx, ry, rot, n=56):
    pts = []
    co, si = math.cos(rot), math.sin(rot)
    for i in range(n):
        a = 2.0 * math.pi * i / n
        ex, ey = rx * math.cos(a), ry * math.sin(a)
        pts.append((cx + ex * co - ey * si, cy + ex * si + ey * co))
    return pts


def lerp_color(c1, c2, t):
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


# ---------- 5x7 bitmap font ----------
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "11001", "10101", "10011", "10011", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(cv, text, x, y, scale, color, shadow=None):
    if shadow is not None:
        draw_text(cv, text, x + 2, y + 2, scale, shadow, None)
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT[' '])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == '1':
                    px = cx + col * scale
                    py = y + row * scale
                    for dy in range(scale):
                        cv.hspan(px, px + scale, py + dy, color)
        cx += 6 * scale


# ---------- scene ----------
SKY_STOPS = [
    (0, (21, 10, 48)),
    (230, (48, 19, 72)),
    (420, (106, 36, 82)),
    (570, (190, 63, 72)),
    (690, (247, 110, 58)),
    (790, (255, 178, 102)),
    (1024, (255, 178, 102)),
]

BODY = (43, 39, 99)
BELLY_OUT = (74, 69, 144)
BELLY_IN = (96, 90, 174)
RIM = (255, 196, 107)
DARK = (28, 15, 38)


def sky_color(y):
    for i in range(len(SKY_STOPS) - 1):
        y0, c0 = SKY_STOPS[i]
        y1, c1 = SKY_STOPS[i + 1]
        if y0 <= y <= y1:
            t = (y - y0) / max(1, y1 - y0)
            return lerp_color(c0, c1, t)
    return SKY_STOPS[-1][1]


def draw_sky(cv):
    for y in range(H):
        cv.hspan(0, W, y, sky_color(y))


def draw_stars(cv, rng):
    for _ in range(110):
        x = rng.range(0, W)
        y = rng.range(0, 430)
        fade = 1.0 - y / 430.0
        a = 0.25 + 0.65 * fade * rng.range(0.4, 1.0)
        col = (255, 240, 220) if rng.next() < 0.7 else (255, 210, 140)
        if rng.next() < 0.18:
            cv.disc_blend(x, y, 1.4, col, a)
        else:
            cv.hspan_blend(int(x), int(x) + 1, int(y), col, a)


def draw_clouds(cv):
    # Each cloud is two overlapping soft ellipses, so the silhouette
    # reads as a cloud rather than a flat pill.
    for cx, cy, rx, ry, a in [
        (210, 295, 150, 12, 0.26),
        (760, 215, 190, 10, 0.24),
        (520, 150, 120, 9, 0.26),
        (880, 330, 120, 9, 0.22),
    ]:
        cv.ellipse_blend(cx, cy, rx, ry, (217, 106, 128), a)
        cv.ellipse_blend(cx - rx * 0.3, cy - ry * 0.9, rx * 0.45, ry * 0.9,
                         (224, 112, 138), a)


def draw_sun(cv):
    cx, cy = 640, 470
    cv.disc_blend(cx, cy, 190, (255, 138, 77), 0.18)
    cv.disc_blend(cx, cy, 150, (255, 162, 94), 0.22)
    cv.disc_blend(cx, cy, 125, (255, 196, 107), 0.30)
    cv.disc(cx, cy, 105, (255, 233, 168))
    cv.disc(cx, cy, 80, (255, 246, 207))


# Whale geometry: body axis from tail to nose.
TAIL = (250.0, 700.0)
NOSE = (840.0, 290.0)
AXIS_LEN = math.hypot(NOSE[0] - TAIL[0], NOSE[1] - TAIL[1])
DIR = ((NOSE[0] - TAIL[0]) / AXIS_LEN, (NOSE[1] - TAIL[1]) / AXIS_LEN)
NORM = (-DIR[1], DIR[0])  # points toward the belly (down-right)
ANGLE = math.atan2(DIR[1], DIR[0])
MAX_HALF = 105.0

PROFILE = [
    (0.00, 0.10), (0.12, 0.30), (0.25, 0.55), (0.40, 0.80),
    (0.55, 0.96), (0.68, 1.00), (0.80, 0.97), (0.90, 0.86),
    (0.96, 0.70), (1.00, 0.52),
]


def profile(t):
    for i in range(len(PROFILE) - 1):
        t0, v0 = PROFILE[i]
        t1, v1 = PROFILE[i + 1]
        if t0 <= t <= t1:
            u = (t - t0) / (t1 - t0)
            u = u * u * (3.0 - 2.0 * u)
            return v0 + (v1 - v0) * u
    return PROFILE[-1][1]


def axis_pt(t):
    return (TAIL[0] + DIR[0] * AXIS_LEN * t,
            TAIL[1] + DIR[1] * AXIS_LEN * t)


def whale_outline():
    upper = []
    lower = []
    for k in range(101):
        t = k / 100.0
        ax, ay = axis_pt(t)
        w = profile(t) * MAX_HALF
        upper.append((ax - NORM[0] * w, ay - NORM[1] * w))
        lower.append((ax + NORM[0] * w, ay + NORM[1] * w))
    return upper, lower


def draw_whale(cv, rng):
    upper, lower = whale_outline()
    # Tail flukes (drawn first so the body overlaps the base).
    ax, ay = TAIL
    dx, dy = DIR
    nx, ny = NORM
    fluke = [
        (ax + dx * 20 - nx * 12, ay + dy * 20 - ny * 12),
        (ax - dx * 25 - nx * 70, ay - dy * 25 - ny * 70),
        (ax - dx * 62 - nx * 108, ay - dy * 62 - ny * 108),
        (ax - dx * 55 - nx * 55, ay - dy * 55 - ny * 55),
        (ax - dx * 30, ay - dy * 30),
        (ax - dx * 55 + nx * 55, ay - dy * 55 + ny * 55),
        (ax - dx * 62 + nx * 108, ay - dy * 62 + ny * 108),
        (ax - dx * 25 + nx * 70, ay - dy * 25 + ny * 70),
        (ax + dx * 20 + nx * 12, ay + dy * 20 + ny * 12),
    ]
    cv.poly(fluke, BODY)
    # Body.
    cv.poly(upper + lower[::-1], BODY)
    # Dorsal fin.
    u36 = upper[36]
    u40 = upper[40]
    u44 = upper[44]
    tip = (u40[0] - nx * 42 + dx * 6, u40[1] - ny * 42 + dy * 6)
    cv.poly([u36, tip, u44], BODY)
    # Pectoral flipper poking below the belly.
    fx, fy = axis_pt(0.62)
    cv.ellipse(fx + nx * 100, fy + ny * 100, 62, 14, (34, 30, 86),
               rot=ANGLE - 0.45)
    # Belly shading: two nested ellipses inside the body.
    bx, by = axis_pt(0.58)
    cv.ellipse(bx + nx * 28, by + ny * 28, 230, 36, BELLY_OUT, rot=ANGLE)
    cv.ellipse(bx + nx * 30, by + ny * 30, 185, 23, BELLY_IN, rot=ANGLE)
    # Golden rim light along the back.
    rim_pts = [upper[k] for k in range(4, 97, 2)]
    cv.polyline(rim_pts, RIM, w=5)
    # Mouth line near the nose.
    mouth = []
    for k in range(80, 100, 3):
        t = k / 100.0
        mx, my = axis_pt(t)
        w = profile(t) * MAX_HALF - 8
        mouth.append((mx + nx * w, my + ny * w))
    cv.polyline(mouth, (29, 24, 72), w=2)
    # Eye.
    ex, ey = axis_pt(0.86)
    ex -= nx * 25
    ey -= ny * 25
    cv.disc(ex, ey, 7, (20, 16, 46))
    cv.disc(ex - 2, ey - 2, 2, (255, 255, 255))
    # Blowhole spout.
    sx, sy = upper[88]
    for _ in range(12):
        a = math.radians(rng.range(-125, -55))
        d = rng.range(12, 60)
        cv.disc(sx + math.cos(a) * d, sy + math.sin(a) * d,
                rng.range(1.5, 3.5), (255, 243, 214))


def far_ridge(x):
    return 712 + 16 * math.sin(x * 0.011 + 1.2) + 7 * math.sin(x * 0.027 + 0.4)


def mid_ridge(x):
    return 812 + 12 * math.sin(x * 0.008 + 2.1) + 6 * math.sin(x * 0.021)


def fore_ridge(x):
    return 905 + 14 * math.sin(x * 0.006 + 0.7) + 8 * math.sin(x * 0.017 + 2.8)


def draw_dune(cv, ridge, color, crest):
    pts = [(float(x), ridge(x)) for x in range(0, W + 1, 8)]
    pts.append((float(W), float(H)))
    pts.append((0.0, float(H)))
    cv.poly(pts, color)
    for x in range(0, W, 2):
        cv.disc(x, ridge(x), 1, crest)


def draw_spray(cv, rng):
    bx, by = 300.0, 692.0
    # Foam where the whale exits the sand.
    cv.ellipse_blend(bx, by + 14, 120, 12, (255, 243, 214), 0.85)
    cv.ellipse_blend(bx, by + 10, 75, 8, (255, 255, 255), 0.90)
    # Water sheets arcing up.
    for ang in (-100, -80, -60):
        a = math.radians(ang)
        pts = []
        for k in range(11):
            u = k / 10.0
            pts.append((bx + math.cos(a) * 220 * u,
                        by + math.sin(a) * 220 * u + 90 * u * u))
        cv.polyline(pts, (255, 237, 208), w=3)
    # Water droplets.
    for _ in range(130):
        a = math.radians(rng.range(-170, -10))
        d = rng.range(20, 230)
        x = bx + math.cos(a) * d
        y = by + math.sin(a) * d + d * d * 0.0015
        col = (255, 243, 214) if rng.next() < 0.6 else (255, 196, 107)
        cv.disc(x, y, rng.range(1.5, 4.5), col)
    # Sand spray.
    sands = [(217, 138, 61), (232, 163, 77), (201, 122, 46), (240, 180, 94)]
    for _ in range(70):
        a = math.radians(rng.range(-125, -25))
        d = rng.range(15, 115)
        x = 315 + math.cos(a) * d
        y = 700 + math.sin(a) * d + d * d * 0.002
        cv.disc(x, y, rng.range(1.5, 3.5), rng.choice(sands))


def draw_camel(cv, x, base_y, s, rider=False):
    c = DARK
    cv.ellipse(x, base_y - 13 * s, 10.5 * s, 5.5 * s, c)
    cv.disc(x - 1 * s, base_y - 18 * s, 4.5 * s, c)
    cv.line(x + 8 * s, base_y - 15 * s, x + 12.5 * s, base_y - 25 * s, c,
            w=max(2, round(3 * s)))
    cv.ellipse(x + 14.5 * s, base_y - 26 * s, 3.2 * s, 2.4 * s, c)
    for lx, fx in ((-7, -8), (-2, -2), (3, 4), (8, 9)):
        cv.line(x + lx * s, base_y - 9 * s, x + fx * s, base_y, c, w=2)
    cv.line(x - 10.5 * s, base_y - 13 * s, x - 13 * s, base_y - 6 * s, c, w=2)
    if rider:
        cv.line(x - 1 * s, base_y - 22 * s, x - 1 * s, base_y - 29 * s, c, w=2)
        cv.disc(x - 1 * s, base_y - 31 * s, 2 * s, c)


def draw_caravan(cv):
    for i, (x, s) in enumerate([(585, 1.15), (645, 1.0), (710, 1.25),
                                (775, 1.05), (845, 1.15)]):
        draw_camel(cv, x, far_ridge(x) - 1, s, rider=(i in (0, 2)))


def draw_birds(cv):
    for x, y, s in [(150, 190, 1.4), (205, 160, 1.2), (265, 205, 1.5),
                    (330, 175, 1.1), (195, 250, 1.2)]:
        cv.line(x - 8 * s, y - 3 * s, x, y, (42, 24, 64), w=2)
        cv.line(x, y, x + 8 * s, y - 3 * s, (42, 24, 64), w=2)


def draw_caption(cv):
    text = "THE DESERT DREAMED OF THE SEA"
    scale = 4
    tw = text_width(text, scale)
    x0 = (W - tw) // 2
    y0 = 932
    cv.hspan(330, 694, 912, RIM)
    cv.hspan(330, 694, 913, RIM)
    draw_text(cv, text, x0, y0, scale, (255, 217, 160), shadow=(16, 8, 28))


def vignette(cv):
    col2 = [((x - 512) / 512.0) ** 2 for x in range(W)]
    row2 = [((y - 512) / 512.0) ** 2 for y in range(H)]
    px = cv.px
    for y in range(H):
        r2 = row2[y]
        base = y * W * 3
        for x in range(W):
            d2 = col2[x] + r2
            if d2 > 0.55:
                f = 1.0 - 0.14 * (d2 - 0.55)
                i = base + x * 3
                px[i] = int(px[i] * f)
                px[i + 1] = int(px[i + 1] * f)
                px[i + 2] = int(px[i + 2] * f)


def render():
    cv = Canvas(W, H)
    rng = Rng(20261116)
    draw_sky(cv)
    draw_stars(cv, rng)
    draw_clouds(cv)
    draw_sun(cv)
    draw_birds(cv)
    draw_whale(cv, rng)
    draw_dune(cv, far_ridge, (110, 47, 82), (163, 74, 99))
    draw_spray(cv, rng)
    draw_caravan(cv)
    draw_dune(cv, mid_ridge, (67, 27, 62), (122, 58, 94))
    draw_dune(cv, fore_ridge, (34, 16, 42), (90, 44, 80))
    draw_caption(cv)
    vignette(cv)
    return cv


# ---------- PNG encoding ----------
def png_chunk(typ, data):
    return (struct.pack(">I", len(data)) + typ + data +
            struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))


def write_png(cv, path):
    raw = bytearray()
    row_bytes = W * 3
    for y in range(H):
        raw.append(0)
        raw += cv.px[y * row_bytes:(y + 1) * row_bytes]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    out = b"\x89PNG\r\n\x1a\n"
    out += png_chunk(b"IHDR", ihdr)
    out += png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    out += png_chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(out)
    return len(out)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(render(), path)
    print(f"wrote {path} {size} bytes")


if __name__ == "__main__":
    main()
