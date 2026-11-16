#!/usr/bin/env python3
"""The Desert Dreamed of the Sea.

A colossal whale breaches out of a desert dune sea at sunset while a tiny
camel caravan crosses the ridge below. Pure Python stdlib, fully
deterministic: two runs write byte-identical PNGs.

Entry for make.fun ai-excited-01, "Make the AI judge excited".
Draws a 1024x1024 PNG to $MAKEFUN_OUTPUT_DIR/entry.png (or /output).
"""

import math
import os
import struct
import zlib

W = H = 1024
S = 2                      # supersample factor (render at 2048, downsample)
W2 = W * S
H2 = H * S
buf = bytearray(W2 * H2 * 3)


# ---------------------------------------------------------------- palette
def C(r, g, b):
    return bytes((r, g, b))


SKY_STOPS = [
    (0.00, C(26, 13, 58)),
    (0.22, C(66, 26, 92)),
    (0.42, C(138, 44, 96)),
    (0.58, C(205, 74, 58)),
    (0.70, C(255, 138, 60)),
    (0.82, C(255, 190, 100)),
    (1.00, C(255, 210, 130)),
]
SUN_CORE = C(255, 224, 138)
SUN_HALO1 = C(255, 184, 94)
SUN_HALO2 = C(255, 154, 77)
WHALE = C(34, 42, 80)
WHALE_BELLY = C(93, 118, 168)
WHALE_RIM = C(255, 210, 122)
WHALE_MOUTH = C(58, 74, 125)
DUNE_FAR = C(138, 64, 56)
DUNE_MID = C(101, 44, 51)
DUNE_NEAR = C(66, 29, 40)
CREST_GOLD = C(224, 120, 64)
SILHOUETTE = C(28, 14, 22)
SAND1 = C(255, 210, 122)
SAND2 = C(255, 184, 94)
SAND3 = C(255, 243, 214)
BIRD = C(42, 18, 48)
TEXT_GOLD = C(255, 217, 143)


# ---------------------------------------------------------------- raster
def put_span(y, x0, x1, col):
    """Fill a horizontal span of the supersampled buffer (fast slice)."""
    if y < 0 or y >= H2:
        return
    if x0 < 0:
        x0 = 0
    if x1 > W2:
        x1 = W2
    if x1 <= x0:
        return
    i = (y * W2 + x0) * 3
    buf[i:i + (x1 - x0) * 3] = col * (x1 - x0)


def put_pixel(x, y, col):
    if 0 <= x < W2 and 0 <= y < H2:
        i = (y * W2 + x) * 3
        buf[i:i + 3] = col


def mix(c0, c1, t):
    return bytes((
        int(c0[0] + (c1[0] - c0[0]) * t),
        int(c0[1] + (c1[1] - c0[1]) * t),
        int(c0[2] + (c1[2] - c0[2]) * t),
    ))


def sky():
    """Vertical sunset gradient, row by row (whole-row slice fills)."""
    for y in range(H2):
        f = y / (H2 - 1)
        for k in range(len(SKY_STOPS) - 1):
            f0, c0 = SKY_STOPS[k]
            f1, c1 = SKY_STOPS[k + 1]
            if f0 <= f <= f1:
                t = 0.0 if f1 == f0 else (f - f0) / (f1 - f0)
                put_span(y, 0, W2, mix(c0, c1, t))
                break


def disc(cx, cy, r, col):
    """Filled circle, scanline spans. Coords in supersampled space."""
    r2 = r * r
    for y in range(max(0, cy - r), min(H2, cy + r + 1)):
        dy = y - cy
        dx = int(math.sqrt(max(0, r2 - dy * dy)))
        put_span(y, cx - dx, cx + dx + 1, col)


def ellipse(cx, cy, rx, ry, col):
    for y in range(max(0, cy - ry), min(H2, cy + ry + 1)):
        dy = (y - cy) / ry
        dx = int(rx * math.sqrt(max(0.0, 1.0 - dy * dy)))
        put_span(y, cx - dx, cx + dx + 1, col)


def poly(pts, col):
    """Scanline polygon fill. pts: list of (x, y) ints, supersampled."""
    n = len(pts)
    ys = [p[1] for p in pts]
    y0 = max(0, min(ys))
    y1 = min(H2 - 1, max(ys))
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x0, yy0 = pts[i]
            x1, yy1 = pts[(i + 1) % n]
            if (yy0 <= y < yy1) or (yy1 <= y < yy0):
                t = (y - yy0) / (yy1 - yy0)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            put_span(y, int(xs[k]), int(xs[k + 1]) + 1, col)


def thick_line(x0, y0, x1, y1, r, col):
    """A line drawn as a chain of discs (for necks, crest light, mouth)."""
    dx, dy = x1 - x0, y1 - y0
    steps = max(1, int(math.hypot(dx, dy) // max(1, r)) + 1)
    for i in range(steps + 1):
        t = i / steps
        disc(int(x0 + dx * t), int(y0 + dy * t), r, col)


# ------------------------------------------------------- deterministic rnd
def rnd(i):
    """Deterministic pseudo-random in [0, 1) from an integer index."""
    return ((i * 2654435761) % 100000) / 100000.0


# ------------------------------------------------------------------- sun
def sun():
    cx, cy, r = 310 * S, 560 * S, 100 * S
    disc(cx, cy, r + 36 * S, SUN_HALO2)
    disc(cx, cy, r + 18 * S, SUN_HALO1)
    disc(cx, cy, r, SUN_CORE)


# ------------------------------------------------------------------ dunes
def dune_crest(base, amp1, f1, ph1, amp2, f2, ph2):
    """Crest y (1024 space) as a sum of two sines."""
    def y_at(x):
        return (base + amp1 * math.sin(x * f1 + ph1)
                + amp2 * math.sin(x * f2 + ph2))
    return y_at


def dune(y_at, col):
    pts = []
    step = 8
    for x in range(0, W + 1, step):
        pts.append((x * S, int(y_at(x)) * S))
    pts.append((W2, H2))
    pts.append((0, H2))
    poly(pts, col)


def crest_light(y_at, col, lift=4):
    """A continuous thin highlight following the dune crest."""
    prev = None
    for x in range(0, W + 1, 6):
        pt = (x * S, (int(y_at(x)) - lift) * S)
        if prev is not None:
            thick_line(prev[0], prev[1], pt[0], pt[1], 2 * S, col)
        prev = pt


# ------------------------------------------------------------------ whale
def cubic(p0, p1, p2, p3, t):
    mt = 1.0 - t
    x = (mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0]
         + 3 * mt * t * t * p2[0] + t ** 3 * p3[0])
    y = (mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1]
         + 3 * mt * t * t * p2[1] + t ** 3 * p3[1])
    dx = (3 * mt * mt * (p1[0] - p0[0]) + 6 * mt * t * (p2[0] - p1[0])
          + 3 * t * t * (p3[0] - p2[0]))
    dy = (3 * mt * mt * (p1[1] - p0[1]) + 6 * mt * t * (p2[1] - p1[1])
          + 3 * t * t * (p3[1] - p2[1]))
    return (x, y), (dx, dy)


def whale_width(t):
    """Body half-width profile along the spine (1024 space)."""
    w = 62.0 + 58.0 * math.sin(math.pi * min(t * 1.05, 1.0)) ** 0.9
    if t > 0.80:
        w *= 1.0 - 0.78 * (t - 0.80) / 0.20
    return w


def whale():
    p0 = (150.0, 800.0)
    p1 = (330.0, 540.0)
    p2 = (620.0, 320.0)
    p3 = (862.0, 268.0)
    n = 48
    spine = []
    upper = []
    lower = []
    for i in range(n + 1):
        t = i / n
        (x, y), (dx, dy) = cubic(p0, p1, p2, p3, t)
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        w = whale_width(t)
        spine.append((x, y, nx, ny, w))
        upper.append((int((x + nx * w) * S), int((y + ny * w) * S)))
        lower.append((int((x - nx * w) * S), int((y - ny * w) * S)))
    # rounded head cap (half circle around the head point, facing backwards)
    # cap[k] runs from lower[0] (a=-90) around the back point to upper[0]
    (hx, hy), (dx, dy) = cubic(p0, p1, p2, p3, 0.0)
    ln = math.hypot(dx, dy) or 1.0
    tx, ty = dx / ln, dy / ln
    nx, ny = -ty, tx
    r0 = whale_width(0.0)
    cap = []
    for k in range(13):
        a = math.pi * (k / 12.0 - 0.5)   # -90..+90 deg
        cx = hx - tx * r0 * math.cos(a) + nx * r0 * math.sin(a)
        cy = hy - ty * r0 * math.cos(a) + ny * r0 * math.sin(a)
        cap.append((int(cx * S), int(cy * S)))
    # outline: upper edge head->tail, lower edge tail->head, cap closes head
    outline = upper + list(reversed(lower)) + cap[1:-1]
    # broad tail flukes, fanning out from the tail stock (body overlaps roots)
    # the two lobes mirror each other across the tail axis, like a whale's
    tx0, ty0 = p3
    poly([(int((tx0 - 14) * S), int((ty0 - 18) * S)),
          (905 * S, 195 * S), (945 * S, 178 * S), (905 * S, 235 * S),
          (int((tx0 + 10) * S), int((ty0 + 4) * S))], WHALE)
    poly([(int((tx0 - 14) * S), int((ty0 + 18) * S)),
          (905 * S, 341 * S), (945 * S, 358 * S), (905 * S, 301 * S),
          (int((tx0 + 10) * S), int((ty0 - 4) * S))], WHALE)
    poly(outline, WHALE)
    # long pectoral fin sweeping down from the lower side, near the head
    fx, fy, fnx, fny, fw = spine[14]
    fln = math.hypot(fnx, fny) or 1.0
    # tangent at spine[14], from neighbouring spine points
    txa, tya, _, _, _ = spine[13]
    txb, tyb, _, _, _ = spine[15]
    tdx, tdy = txb - txa, tyb - tya
    tl = math.hypot(tdx, tdy) or 1.0
    tdx, tdy = tdx / tl, tdy / tl
    rx, ry = fx + fnx * fw * 0.85, fy + fny * fw * 0.85
    tipx, tipy = rx + fnx * 120 - tdx * 70, ry + fny * 120 - tdy * 70
    poly([(int((rx + tdx * 26) * S), int((ry + tdy * 26) * S)),
          (int(tipx * S), int(tipy * S)),
          (int((rx - tdx * 34 + fnx * 18) * S),
           int((ry - tdy * 34 + fny * 18) * S))], WHALE)
    # lighter belly stripe along the lower edge (the +n side faces the dunes)
    belly_up = []
    belly_lo = []
    for (x, y, nx, ny, w) in spine:
        ox, oy = x + nx * w * 0.45, y + ny * w * 0.45
        bw = w * 0.25
        belly_up.append((int((ox + nx * bw) * S), int((oy + ny * bw) * S)))
        belly_lo.append((int((ox - nx * bw) * S), int((oy - ny * bw) * S)))
    poly(belly_up + list(reversed(belly_lo)), WHALE_BELLY)
    # golden rim light: a continuous line along the top edge (-n side)
    for i in range(n):
        x0, y0, nx0, ny0, w0 = spine[i]
        x1, y1, nx1, ny1, w1 = spine[i + 1]
        thick_line(int((x0 - nx0 * (w0 - 5)) * S),
                   int((y0 - ny0 * (w0 - 5)) * S),
                   int((x1 - nx1 * (w1 - 5)) * S),
                   int((y1 - ny1 * (w1 - 5)) * S),
                   2 * S, WHALE_RIM)
    # eye: a pale glint near the head, on the upper side
    x, y, nx, ny, w = spine[3]
    disc(int((x - nx * w * 0.35) * S), int((y - ny * w * 0.35) * S),
         6 * S, SAND3)
    # mouth: a quiet curve along the lower jaw (+n side)
    mx0, my0, _, _, _ = spine[1]
    mx1, my1, _, _, _ = spine[9]
    _, _, mnx, mny, mw = spine[5]
    thick_line(int((mx0 + mnx * mw * 0.55) * S),
               int((my0 + mny * mw * 0.55) * S),
               int((mx1 + mnx * mw * 0.55) * S),
               int((my1 + mny * mw * 0.55) * S),
               2 * S, WHALE_MOUTH)


# ------------------------------------------------------- sand burst, spray
def sand_burst():
    bx, by = 175 * S, 830 * S
    # crown shards flying up out of the dune
    for i in range(9):
        a = math.radians(-168 + i * 20 + rnd(i) * 10)
        d = (55 + rnd(i + 40) * 75) * S
        tipx = bx + math.cos(a) * d
        tipy = by + math.sin(a) * d * 0.8
        base = 7 * S + rnd(i + 80) * 4 * S
        px, py = math.cos(a + 1.5708), math.sin(a + 1.5708)
        col = SAND1 if i % 2 == 0 else SAND2
        poly([(int(tipx), int(tipy)),
              (int(bx + px * base), int(by + py * base)),
              (int(bx - px * base), int(by - py * base))], col)
    # grains arcing away from the breach
    for i in range(140):
        a = math.radians(-178 + rnd(i) * 175)
        d = (18 + rnd(i + 200) ** 1.6 * 175) * S
        gx = bx + math.cos(a) * d
        gy = by + math.sin(a) * d * 0.75 + (d / S) ** 2 * 0.012 * S
        r = (1.2 + rnd(i + 300) * 3.4) * S
        col = (SAND1, SAND2, SAND3)[i % 3]
        disc(int(gx), int(gy), int(r), col)
    # droplets shaken off the whale's back, clearly in the sky above it
    for i in range(18):
        t = 0.25 + rnd(i + 500) * 0.55
        (x, y), (dx, dy) = cubic((150.0, 800.0), (330.0, 540.0),
                                 (620.0, 320.0), (862.0, 268.0), t)
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        w = whale_width(t)
        off = w + 25 + rnd(i + 600) * 140
        ox = -nx * off + (rnd(i + 650) - 0.5) * 60
        oy = -ny * off - rnd(i + 700) * 40
        disc(int((x + ox) * S), int((y + oy) * S),
             int((1.5 + rnd(i + 800) * 2.5) * S), SAND3)


# ----------------------------------------------------------------- camels
def camel(x, y_base, s):
    """Tiny silhouetted camel with rider, standing on the dune crest."""
    col = SILHOUETTE
    ellipse(int(x * S), int((y_base - 13 * s) * S),
            int(13 * s * S), int(7 * s * S), col)
    disc(int((x - 5 * s) * S), int((y_base - 19 * s) * S),
         int(4.5 * s * S), col)
    disc(int((x + 5 * s) * S), int((y_base - 19 * s) * S),
         int(4.5 * s * S), col)
    thick_line(int((x + 11 * s) * S), int((y_base - 17 * s) * S),
               int((x + 17 * s) * S), int((y_base - 30 * s) * S),
               int(2.5 * s * S), col)
    disc(int((x + 18 * s) * S), int((y_base - 31 * s) * S),
         int(3 * s * S), col)
    for lx in (-9, -4, 4, 9):
        x0 = int((x + lx * s) * S)
        y0 = int((y_base - 9 * s) * S)
        y1 = int(y_base * S)
        for yy in range(y0, y1 + 1):
            put_span(yy, x0, x0 + int(2 * s * S), col)
    # rider
    disc(int(x * S), int((y_base - 27 * s) * S), int(2.5 * s * S), col)
    thick_line(int(x * S), int((y_base - 25 * s) * S),
               int(x * S), int((y_base - 19 * s) * S),
               int(2 * s * S), col)


def birds():
    for (x, y, s) in [(700, 180, 1.0), (758, 148, 0.8), (822, 205, 1.1),
                      (648, 232, 0.7), (880, 150, 0.75)]:
        thick_line(int((x - 11 * s) * S), int(y * S),
                   int(x * S), int((y + 6 * s) * S), 2 * S, BIRD)
        thick_line(int(x * S), int((y + 6 * s) * S),
                   int((x + 11 * s) * S), int(y * S), 2 * S, BIRD)


def stars():
    for i in range(26):
        x = 40 + rnd(i) * 940
        y = 24 + rnd(i + 100) * 260
        r = (0.8 + rnd(i + 200) * 1.4) * S
        disc(int(x * S), int(y * S), int(r), SAND3)


# ------------------------------------------------------------------ caption
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
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
    "'": ("00100", "00100", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
}


def caption(text, y_top, scale):
    """Draw centred 5x7 pixel-font text (1024-space coords)."""
    cell = 6 * scale
    width = len(text) * cell - scale
    x = (W - width) // 2
    for ch in text:
        glyph = FONT.get(ch, FONT[' '])
        for row in range(7):
            for col_i in range(5):
                if glyph[row][col_i] == '1':
                    px = (x + col_i * scale) * S
                    py = (y_top + row * scale) * S
                    for yy in range(py, py + scale * S):
                        put_span(yy, px, px + scale * S, TEXT_GOLD)
        x += cell


# --------------------------------------------------------------------- png
def chunk(typ, data):
    out = struct.pack('>I', len(data)) + typ + data
    out += struct.pack('>I', zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(path, pixels):
    raw = bytearray()
    row_bytes = W * 3
    for y in range(H):
        raw.append(0)
        raw += pixels[y * row_bytes:(y + 1) * row_bytes]
    data = zlib.compress(bytes(raw), 9)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', data)
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


def downsample():
    """Average each 2x2 block of the supersampled buffer into 1024x1024."""
    out = bytearray(W * H * 3)
    for y in range(H):
        r0 = (2 * y) * W2 * 3
        r1 = (2 * y + 1) * W2 * 3
        for x in range(W):
            i0 = r0 + (2 * x) * 3
            i1 = r1 + (2 * x) * 3
            o = (y * W + x) * 3
            for c in range(3):
                out[o + c] = (buf[i0 + c] + buf[i0 + 3 + c]
                              + buf[i1 + c] + buf[i1 + 3 + c]) // 4
    return out


# -------------------------------------------------------------------- main
def main():
    out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR') or '/output'
    os.makedirs(out_dir, exist_ok=True)

    sky()
    stars()
    sun()
    far = dune_crest(700, 26, 0.004, 0.7, 12, 0.011, 0.0)
    dune(far, DUNE_FAR)
    whale()
    sand_burst()
    mid = dune_crest(800, 30, 0.0035, 2.0, 14, 0.009, 1.0)
    dune(mid, DUNE_MID)
    crest_light(mid, CREST_GOLD)
    near = dune_crest(895, 22, 0.004, 4.0, 10, 0.012, 0.0)
    dune(near, DUNE_NEAR)
    crest_light(near, SAND1, lift=3)
    for (x, s) in [(600, 1.0), (690, 0.85), (782, 1.1)]:
        camel(x, near(x) + 1, s)
    birds()
    caption("THE DESERT DREAMED OF THE SEA", 958, 5)

    write_png(os.path.join(out_dir, 'entry.png'), downsample())


if __name__ == '__main__':
    main()
