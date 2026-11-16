#!/usr/bin/env python3
"""
'The Desert Dreamed of the Sea'
Entry for make.fun ai-excited-01 bounty.
Pure Python standard library implementation (struct, zlib).
"""

import os
import sys
import struct
import zlib
import math

WIDTH = 1024
HEIGHT = 1024

def create_png(width, height, rgba_data):
    """Encodes raw RGBA pixel data into a valid PNG byte string using standard library."""
    def chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    # Build filtered scanlines (filter type 0 = None)
    row_size = width * 4
    raw_scanlines = bytearray()
    for y in range(height):
        raw_scanlines.append(0)  # filter type 0
        start = y * row_size
        raw_scanlines.extend(rgba_data[start:start + row_size])

    compressed = zlib.compress(raw_scanlines, level=9)

    # PNG Header
    signature = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    ihdr_chunk = chunk(b'IHDR', ihdr_data)
    idat_chunk = chunk(b'IDAT', compressed)
    iend_chunk = chunk(b'IEND', b'')

    return signature + ihdr_chunk + idat_chunk + iend_chunk

# 5x7 Bitmap Font for characters (A-Z, space, period)
FONT_5X7 = {
    'A': [0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11],
    'B': [0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E],
    'C': [0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E],
    'D': [0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E],
    'E': [0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F],
    'F': [0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10],
    'G': [0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0E],
    'H': [0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11],
    'I': [0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E],
    'J': [0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C],
    'K': [0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11],
    'L': [0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F],
    'M': [0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11],
    'N': [0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11],
    'O': [0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E],
    'P': [0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10],
    'Q': [0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D],
    'R': [0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11],
    'S': [0x0E, 0x11, 0x10, 0x0E, 0x01, 0x11, 0x0E],
    'T': [0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04],
    'U': [0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E],
    'V': [0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04],
    'W': [0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11],
    'X': [0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11],
    'Y': [0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04],
    'Z': [0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F],
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    '.': [0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C],
}

def draw_text(pixels, text, start_x, start_y, scale=3, color=(255, 230, 180, 255)):
    cur_x = start_x
    for char in text.upper():
        glyph = FONT_5X7.get(char, FONT_5X7[' '])
        for row_idx, row_val in enumerate(glyph):
            for col_idx in range(5):
                if (row_val >> (4 - col_idx)) & 1:
                    for sx in range(scale):
                        for sy in range(scale):
                            px = cur_x + col_idx * scale + sx
                            py = start_y + row_idx * scale + sy
                            if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                                idx = (py * WIDTH + px) * 4
                                # Alpha blend
                                src_a = color[3] / 255.0
                                dst_r, dst_g, dst_b, dst_a = pixels[idx], pixels[idx+1], pixels[idx+2], pixels[idx+3]
                                r = int(color[0] * src_a + dst_r * (1 - src_a))
                                g = int(color[1] * src_a + dst_g * (1 - src_a))
                                b = int(color[2] * src_a + dst_b * (1 - src_a))
                                a = min(255, color[3] + dst_a)
                                pixels[idx] = r
                                pixels[idx+1] = g
                                pixels[idx+2] = b
                                pixels[idx+3] = a
        cur_x += (5 + 1) * scale

def main():
    # Initialize pixel buffer (RGBA)
    pixels = bytearray(WIDTH * HEIGHT * 4)

    # 1. SKY GRADIENT & BACKGROUND
    # Horizon at y = 680
    HORIZON = 680
    for y in range(HEIGHT):
        for x in range(WIDTH):
            idx = (y * WIDTH + x) * 4
            if y < HORIZON:
                # Vertical gradient: indigo (20,15,50) at top -> magenta (120,30,90) at mid -> deep orange (230,110,40) at horizon
                t = y / HORIZON
                if t < 0.5:
                    u = t * 2.0
                    r = int(20 * (1 - u) + 120 * u)
                    g = int(15 * (1 - u) + 30 * u)
                    b = int(50 * (1 - u) + 90 * u)
                else:
                    u = (t - 0.5) * 2.0
                    r = int(120 * (1 - u) + 230 * u)
                    g = int(30 * (1 - u) + 110 * u)
                    b = int(90 * (1 - u) + 40 * u)
            else:
                # Below horizon (will be overwritten by dunes, but default base)
                r, g, b = 230, 110, 40
            pixels[idx] = r
            pixels[idx+1] = g
            pixels[idx+2] = b
            pixels[idx+3] = 255

    # 2. STARS (deterministic positions)
    stars = [
        (120, 80), (340, 50), (520, 110), (780, 70), (910, 140),
        (210, 180), (450, 150), (670, 90), (850, 200), (950, 80),
        (80, 240), (300, 220), (600, 210), (730, 170), (160, 120)
    ]
    for (sx, sy) in stars:
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = sx + dx, sy + dy
                if 0 <= nx < WIDTH and 0 <= ny < HORIZON:
                    idx = (ny * WIDTH + nx) * 4
                    # Soft star glow
                    dist = abs(dx) + abs(dy)
                    intensity = 255 if dist == 0 else 150 if dist == 1 else 60
                    pixels[idx] = min(255, pixels[idx] + intensity)
                    pixels[idx+1] = min(255, pixels[idx+1] + intensity)
                    pixels[idx+2] = min(255, pixels[idx+2] + intensity)

    # 3. SOFT CLOUDS
    clouds = [
        (250, 220, 120, 35, 140, 90, 110),
        (750, 280, 150, 40, 160, 80, 100),
        (500, 170, 100, 30, 130, 100, 120)
    ]
    for (cx, cy, rx, ry, cr, cg, cb) in clouds:
        for y in range(max(0, cy - ry), min(HORIZON, cy + ry)):
            for x in range(max(0, cx - rx), min(WIDTH, cx + rx)):
                norm_sq = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if norm_sq <= 1.0:
                    alpha = (1.0 - math.sqrt(norm_sq)) * 0.35
                    idx = (y * WIDTH + x) * 4
                    pixels[idx] = int(pixels[idx] * (1 - alpha) + cr * alpha)
                    pixels[idx+1] = int(pixels[idx+1] * (1 - alpha) + cg * alpha)
                    pixels[idx+2] = int(pixels[idx+2] * (1 - alpha) + cb * alpha)

    # 4. SETTING SUN WITH GLOW RING
    SUN_X, SUN_Y, SUN_R = 640, 560, 110
    for y in range(max(0, SUN_Y - SUN_R - 60), min(HORIZON, SUN_Y + SUN_R + 60)):
        for x in range(max(0, SUN_X - SUN_R - 60), min(WIDTH, SUN_X + SUN_R + 60)):
            dist = math.sqrt((x - SUN_X)**2 + (y - SUN_Y)**2)
            idx = (y * WIDTH + x) * 4
            if dist <= SUN_R:
                # Pale gold disc
                factor = 1.0 - (dist / SUN_R) * 0.2
                pixels[idx] = min(255, int(255 * factor))
                pixels[idx+1] = min(255, int(235 * factor))
                pixels[idx+2] = min(255, int(160 * factor))
            elif dist <= SUN_R + 50:
                # Glow halo ring
                ring_t = (dist - SUN_R) / 50.0
                alpha = (1.0 - ring_t) * 0.4
                r = int(pixels[idx] * (1 - alpha) + 255 * alpha)
                g = int(pixels[idx+1] * (1 - alpha) + 180 * alpha)
                b = int(pixels[idx+2] * (1 - alpha) + 80 * alpha)
                pixels[idx] = r
                pixels[idx+1] = g
                pixels[idx+2] = b

    # 5. DUNES (3 layers)
    # Layer 1 (Back, dark mauve/brown)
    for x in range(WIDTH):
        dune_y = int(620 + 40 * math.sin(x * 0.005 + 1.2) + 20 * math.cos(x * 0.01))
        for y in range(dune_y, HEIGHT):
            idx = (y * WIDTH + x) * 4
            # gradient down dune
            depth = (y - dune_y) / (HEIGHT - dune_y + 1)
            r = int(110 + 20 * depth)
            g = int(65 + 15 * depth)
            b = int(55 + 10 * depth)
            pixels[idx] = r
            pixels[idx+1] = g
            pixels[idx+2] = b

    # Layer 2 (Mid, warm brown)
    for x in range(WIDTH):
        dune_y = int(720 + 50 * math.cos(x * 0.006 - 0.5) + 25 * math.sin(x * 0.012))
        for y in range(dune_y, HEIGHT):
            idx = (y * WIDTH + x) * 4
            depth = (y - dune_y) / (HEIGHT - dune_y + 1)
            r = int(170 + 25 * depth)
            g = int(100 + 20 * depth)
            b = int(60 + 15 * depth)
            pixels[idx] = r
            pixels[idx+1] = g
            pixels[idx+2] = b

    # Layer 3 (Front, bright gold sand)
    for x in range(WIDTH):
        dune_y = int(820 + 60 * math.sin(x * 0.004 + 2.5) + 30 * math.cos(x * 0.008))
        for y in range(dune_y, HEIGHT):
            idx = (y * WIDTH + x) * 4
            depth = (y - dune_y) / (HEIGHT - dune_y + 1)
            r = int(220 + 25 * depth)
            g = int(150 + 20 * depth)
            b = int(75 + 15 * depth)
            pixels[idx] = r
            pixels[idx+1] = g
            pixels[idx+2] = b

    # 6. COLOSSAL WHALE BREACHING DIAGONALLY
    # Whale body curve from lower-left (200, 850) to upper-right (820, 280)
    # Let's define a parametric path for the whale body
    WHALE_COLOR = (40, 45, 95)
    RIM_COLOR = (255, 200, 110)

    # We can rasterize the whale body as a thick smooth ribbon/ellipse along a diagonal path
    def in_whale(x, y):
        # Path parameter t from 0 (head in air / upper right) to 1 (tail in dunes / lower left)
        # Centerline approx: x(t) = 820 - 620*t, y(t) = 280 + 570*t
        # Let's test distance to the centerline curve or segments
        # Simpler: check distance to line segments from (200,850) to (820,280) with variable thickness (thick in middle, tapered at ends)
        x1, y1 = 200, 850  # Tail / breach point
        x2, y2 = 820, 280  # Head / snout
        
        dx = x2 - x1
        dy = y2 - y1
        length_sq = dx*dx + dy*dy
        if length_sq == 0:
            return False, 0
            
        t = ((x - x1) * dx + (y - y1) * dy) / length_sq
        if -0.1 <= t <= 1.1:
            # Closest point on line
            cx = x1 + t * dx
            cy = y1 + t * dy
            dist = math.sqrt((x - cx)**2 + (y - cy)**2)
            
            # Width profile along t: taper at ends (t=0 and t=1), thickest around t=0.4 (approx 120 pixels radius)
            # t=0: tail (r=30), t=0.4: body (r=120), t=1.0: head (r=50)
            if t < 0.2:
                radius = 30 + t * 450  # 30 to 120
            elif t < 0.7:
                radius = 120 - (t - 0.2) * 20  # 120 to 110
            else:
                radius = 110 * (1.1 - t) / 0.4 + 20  # tapers to head
                
            if dist <= radius:
                # Check for rim light on upper-left edge (where light hits back)
                is_rim = (x - cx) < -radius * 0.6 and t > 0.1
                return True, is_rim
        return False, False

    # Draw whale body
    for y in range(HEIGHT):
        for x in range(WIDTH):
            inside, rim = in_whale(x, y)
            if inside:
                idx = (y * WIDTH + x) * 4
                if rim:
                    pixels[idx] = RIM_COLOR[0]
                    pixels[idx+1] = RIM_COLOR[1]
                    pixels[idx+2] = RIM_COLOR[2]
                else:
                    pixels[idx] = WHALE_COLOR[0]
                    pixels[idx+1] = WHALE_COLOR[1]
                    pixels[idx+2] = WHALE_COLOR[2]

    # Add dorsal fin, flipper, eye, and blowhole spout details
    # Dorsal fin around (550, 420)
    for y in range(350, 460):
        for x in range(480, 580):
            # Triangle shape for dorsal fin
            if y >= 380 and x - 480 + (y - 380) * 0.8 <= 80 and x >= 490:
                idx = (y * WIDTH + x) * 4
                if 0 <= idx < len(pixels) - 3:
                    # Rim light on left edge of fin
                    if x < 510:
                        pixels[idx] = RIM_COLOR[0]
                        pixels[idx+1] = RIM_COLOR[1]
                        pixels[idx+2] = RIM_COLOR[2]
                    else:
                        pixels[idx] = WHALE_COLOR[0]
                        pixels[idx+1] = WHALE_COLOR[1]
                        pixels[idx+2] = WHALE_COLOR[2]

    # Flipper around (400, 600)
    for y in range(540, 680):
        for x in range(320, 440):
            if (y - 540) > 0.5 * abs(x - 380):
                idx = (y * WIDTH + x) * 4
                if 0 <= idx < len(pixels) - 3:
                    pixels[idx] = WHALE_COLOR[0]
                    pixels[idx+1] = WHALE_COLOR[1]
                    pixels[idx+2] = WHALE_COLOR[2]

    # Blowhole spout (white water spray arcing up from head around (760, 320))
    for sy_off in range(-80, 20):
        for sx_off in range(-40, 40):
            spout_x = 760 + sx_off + int(sy_off * 0.5)
            spout_y = 320 + sy_off
            if 0 <= spout_x < WIDTH and 0 <= spout_y < HEIGHT:
                dist_spray = math.sqrt(sx_off**2 + (sy_off + 30)**2)
                if dist_spray < 35:
                    idx = (spout_y * WIDTH + spout_x) * 4
                    alpha = max(0.0, 1.0 - dist_spray / 35.0) * 0.8
                    pixels[idx] = int(pixels[idx] * (1 - alpha) + 240 * alpha)
                    pixels[idx+1] = int(pixels[idx+1] * (1 - alpha) + 245 * alpha)
                    pixels[idx+2] = int(pixels[idx+2] * (1 - alpha) + 255 * alpha)

    # 7. BREACH POINT (Water spray, foam, sand burst at lower left around (200, 850))
    for by in range(750, 950):
        for bx in range(100, 320):
            dist_breach = math.sqrt((bx - 200)**2 + (by - 850)**2)
            if dist_breach < 90:
                idx = (by * WIDTH + bx) * 4
                if 0 <= idx < len(pixels) - 3:
                    mix = 1.0 - (dist_breach / 90.0)
                    # Blend foam white and golden sand burst
                    r = int(pixels[idx] * (1 - mix) + 235 * mix)
                    g = int(pixels[idx+1] * (1 - mix) + 220 * mix)
                    b = int(pixels[idx+2] * (1 - mix) + 190 * mix)
                    pixels[idx] = r
                    pixels[idx+1] = g
                    pixels[idx+2] = b

    # 8. CARAVAN OF FIVE TINY CAMELS on dune ridge at right (around x=840..920, y=780)
    camel_positions = [850, 875, 900, 920, 940]
    for cx in camel_positions:
        # Each camel: small dark silhouette with legs and hump
        cy = int(795 + 15 * math.sin(cx * 0.006 - 0.5))
        for dy in range(-12, 5):
            for dx in range(-8, 9):
                # Body and hump
                if (dy >= -6 and abs(dx) <= 6) or (dy < -6 and dy >= -12 and abs(dx) <= 3):
                    px, py = cx + dx, cy + dy
                    if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                        idx = (py * WIDTH + px) * 4
                        pixels[idx] = 40
                        pixels[idx+1] = 25
                        pixels[idx+2] = 20

    # 9. CAPTION & DIVIDER LINE
    # Thin gold horizontal line at y = 940
    for x in range(150, WIDTH - 150):
        for y in range(940, 943):
            idx = (y * WIDTH + x) * 4
            pixels[idx] = 255
            pixels[idx+1] = 215
            pixels[idx+2] = 120

    # Caption text: "THE DESERT DREAMED OF_THE SEA" -> "THE DESERT DREAMED OF THE SEA"
    caption_text = "THE DESERT DREAMED OF THE SEA"
    # Each char is 5 cols wide + 1 space = 6 pixels per char, scale 3 -> 18 pixels per char. 29 chars * 18 = 522 pixels wide.
    # Center at WIDTH / 2 = 512 -> start_x = 512 - 522//2 = 251.
    draw_text(pixels, caption_text, start_x=235, start_y=965, scale=3, color=(255, 235, 190, 255))

    # 10. OUTPUT WRITING
    out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    if not os.path.exists(out_dir):
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception:
            out_dir = '.'
            os.makedirs(out_dir, exist_ok=True)

    out_path = os.path.join(out_dir, 'entry.png')
    png_bytes = create_png(WIDTH, HEIGHT, pixels)
    
    with open(out_path, 'wb') as f:
        f.write(png_bytes)

    print(f"Successfully wrote {len(png_bytes)} bytes to {out_path}")

if __name__ == '__main__':
    main()
