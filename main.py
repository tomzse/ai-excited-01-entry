#!/usr/bin/env python3
import os
import math
import zlib
import struct

WIDTH = 1024
HIGHT = 1024

def clamp(v, low=0, high=255):
    return max(low, min(high, int(v)))

def blend(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t)
    )

def draw_canvas():
    buf = bytearray(WIDTH * HIGHT * 3)

    # 1. Sky Gradient & Stars & Clouds
    # Sky colors: Top (indigo: 15, 12, 45), Mid-upper (magenta: 85, 25, 75), Mid-lower (orange: 175, 70, 45), Horizon (gold/amber: 225, 150, 60)
    sky_top = (15, 12, 45)
    sky_mid1 = (85, 25, 75)
    sky_mid2 = (175, 70, 45)
    sky_horizon = (225, 150, 60)

    # Horizon y around 620
    horizon_y = 620

    for y in range(HIGHT):
        # Determine sky vs dune
        # We will compute dunes later, but sky base first
        if y < horizon_y:
            t = y / horizon_y
            if t < 0.4:
                col = blend(sky_top, sky_mid1, t / 0.4)
            elif t < 0.75:
                col = blend(sky_mid1, sky_mid2, (t - 0.4) / 0.35)
            else:
                col = blend(sky_mid2, sky_horizon, (t - 0.75) / 0.25)
        else:
            col = sky_horizon # placeholder before dunes
        
        row_offset = y * WIDTH * 3
        for x in range(WIDTH):
            buf[row_offset + x * 3] = col[0]
            buf[row_offset + x * 1 + 1] = col[1]
            buf[row_offset + x * 1 + 2] = col[2]

    def set_pixel(x, y, rgb, alpha=1.0):
        if 0 <= x < WIDTH and 0 <= y < HIGHT:
            idx = (y * WIDTH + x) * 3
            if alpha >= 1.0:
                buf[idx] = clamp(rgb[0])
                buf[idx+1] = clamp(rgb[1])
                buf[idx+2] = clamp(rgb[2])
            else:
                buf[idx] = clamp(buf[idx] * (1 - alpha) + rgb[0] * alpha)
                buf[idx+1] = clamp(buf[idx+1] * (1 - alpha) + rgb[1] * alpha)
                buf[idx+2] = clamp(buf[idx+2] * (1 - alpha) + rgb[2] * alpha)

    def draw_circle(cx, cy, radius, rgb, alpha=1.0):
        min_x = max(0, int(cx - radius - 1))
        max_x = min(WIDTH, int(cx + radius + 2))
        min_y = max(0, int(cy - radius - 1))
        max_y = min(HIGHT, int(cy + radius + 2))
        r2 = radius * radius
        for y in range(min_y, max_y):
            dy = y - cy
            for x in range(min_x, max_x):
                dx = x - cx
                dist2 = dx*dx + dy*dy
                if dist2 <= r2:
                    # anti-alias edge
                    d = math.sqrt(dist2)
                    a = alpha
                    if radius > 1 and d > radius - 1:
                        a *= (radius - d)
                    set_pixel(x, y, rgb, a)

    def draw_ellipse(cx, cy, rx, ry, rgb, alpha=1.0, angle=0.0):
        # Rotated ellipse support for organic whale body
        cos_a = math.cos(-angle)
        sin_a = math.sin(-angle)
        min_x = max(0, int(cx - max(rx, ry) - 2))
        max_x = min(WIDTH, int(cx + max(rx, ry) + 3))
        min_y = max(0, int(cy - max(rx, ry) - 2))
        max_y = min(HIGHT, int(cy + max(rx, ry) + 3))
        
        for y in range(min_y, max_y):
            dy = y - cy
            for x in range(min_x, max_x):
                dx = x - cx
                # rotate
                rx_val = dx * cos_a - dy * sin_a
                ry_val = dx * sin_a + dy * cos_a
                val = (rx_val / rx) ** 2 + (ry_val / ry) ** 2
                if val <= 1.0:
                    # anti-alias near edge
                    edge = math.sqrt(val)
                    a = alpha
                    if edge > 0.85:
                        a *= max(0.0, (1.0 - edge) / 0.15)
                    set_pixel(x, y, rgb, a)

    # Stars in upper sky (deterministic coordinates)
    stars = [
        (120, 80, 200), (340, 50, 220), (510, 110, 180), (780, 70, 240), (920, 130, 200),
        (200, 160, 150), (450, 190, 210), (680, 140, 230), (880, 190, 190), (60, 220, 170),
        (310, 250, 200), (600, 230, 220), (810, 270, 180), (150, 310, 210), (410, 330, 240)
    ]
    for sx, sy, sbri in stars:
        draw_circle(sx, sy, 1.5, (sbri, sbri, 255), 0.8)
        draw_circle(sx, sy, 3.0, (sbri, sbri, 255), 0.2)

    # Soft elliptical clouds in upper-mid sky
    clouds = [
        (250, 220, 90, 25, (220, 150, 180), 0.25),
        (750, 280, 120, 30, (230, 160, 170), 0.2),
        (500, 180, 140, 22, (210, 140, 170), 0.22)
    ]
    for cx, cy, crx, cry, ccol, ca in clouds:
        draw_ellipse(cx, cy, crx, cry, ccol, ca)

    # Setting Sun low on horizon behind whale body: center around (550, 600)
    sun_cx, sun_cy = 540, 600
    sun_radius = 90
    # Sun glow outer rings
    for r in range(sun_radius + 40, sun_radius, -5):
        glow_alpha = 0.05 * (1.0 - (r - sun_radius) / 40.0)
        draw_circle(sun_cx, sun_cy, r, (255, 200, 100), glow_alpha)
    # Sun disc
    for y in range(max(0, sun_cy - sun_radius), min(HIGHT, sun_cy + sun_radius + 1)):
        dy = y - sun_cy
        for x in range(max(0, sun_cx - sun_radius), min(WIDTH, sun_cx + sun_radius + 1)):
            dx = x - sun_cx
            if dx*dx + dy*dy <= sun_radius*sun_radius:
                # Gradient on sun disc: warm pale gold to yellow-white
                t_sun = (dy + sun_radius) / (2 * sun_radius)
                scol = (255, int(230 + 25 * t_sun), int(150 + 80 * t_sun))
                set_pixel(x, y, scol, 0.95)

    # Dunes across bottom: 3 layers
    # Layer 3 (Back dune, dark mauve/brown): y ~ 540 down
    # Layer 2 (Mid dune, warm brown): y ~ 620 down
    # Layer 1 (Front dune, bright gold/sand): y ~ 720 down

    def dune_y3(x):
        return 550 + 35 * math.sin(x * 0.003 + 1.2) + 20 * math.cos(x * 0.007)
    
    def dune_y2(x):
        return 630 + 40 * math.sin(x * 0.004 + 2.5) + 25 * math.sin(x * 0.008 + 0.5)

    def dune_y1(x):
        return 730 + 50 * math.sin(x * 0.0035 + 4.1) + 30 * math.cos(x * 0.006 + 1.0)

    for y in range(horizon_y, HIGHT):
        row_offset = y * WIDTH * 3
        for x in range(WIDTH):
            d3 = dune_y3(x)
            d2 = dune_y2(x)
            d1 = dune_y1(x)

            if y >= d1:
                # Front dune: bright gold/sand
                dt = (y - d1) / (HIGHT - d1 + 1)
                col = (int(215 - dt * 40), int(160 - dt * 30), int(80 - dt * 20))
            elif y >= d2:
                # Mid dune: warm brown
                dt = (y - d2) / (d1 - d2 + 1)
                col = (int(150 - dt * 20), int(95 - dt * 15), int(60 - dt * 10))
            elif y >= d3:
                # Back dune: dark mauve/brown
                dt = (y - d3) / (d2 - d3 + 1)
                col = (int(95 - dt * 15), int(55 - dt * 10), int(65 - dt * 10))
            else:
                # Sky near horizon
                t = y / horizon_y
                col = blend(sky_mid2, sky_horizon, (t - 0.75) / 0.25)

            buf[row_offset + x * 3] = col[0]
            buf[row_offset + x * 1 + 1] = col[1]
            buf[row_offset + x * 1 + 2] = col[2]

    # Caravan of 5 camels on mid-dune ridge at right (x around 680 to 920, y around dune_y1 or dune_y2)
    def draw_camel(cx, cy, scale=1.0, with_rider=False):
        # Silhouette color
        cc = (45, 25, 20)
        # Body (ellipse)
        bw = int(22 * scale)
        bh = int(12 * scale)
        draw_ellipse(cx, cy - int(10 * scale), bw, bh, cc)
        # Hump
        hw = int(8 * scale)
        hh = int(9 * scale)
        draw_ellipse(cx - int(2 * scale), cy - int(20 * scale), hw, hh, cc)
        # Neck & Head
        # Neck curve from body front up to head
        nx, ny = cx + int(12 * scale), cy - int(12 * scale)
        for i in range(12):
            t = i / 11.0
            px = int(cx + int(10 * scale) + t * int(8 * scale))
            py = int(cy - int(10 * scale) - t * int(18 * scale))
            draw_circle(px, py, max(1.5, int(2.5 * scale)), cc)
        # Head
        draw_circle(cx + int(18 * scale), cy - int(27 * scale), int(3 * scale), cc)
        # 4 Legs (thin lines)
        leg_len = int(18 * scale)
        # Front legs
        for leg_dx in [int(10 * scale), int(14 * scale)]:
            for ly in range(leg_len):
                set_pixel(cx + leg_dx, cy - int(4 * scale) + ly, cc)
        # Back legs
        for leg_dx in [-int(10 * scale), -int(6 * scale)]:
            for ly in range(leg_len):
                set_pixel(cx + leg_dx, cy - int(4 * scale) + ly, cc)
        # Rider if requested
        if with_rider:
            draw_circle(cx - int(2 * scale), cy - int(32 * scale), int(3.5 * scale), (240, 220, 180))

    camel_positions = [
        (720, int(dune_y1(720)) - 2, 0.85, True),
        (770, int(dune_y1(770)) - 2, 0.9, False),
        (825, int(dune_y1(825)) - 2, 1.0, True),
        (875, int(dune_y1(875)) - 2, 0.95, False),
        (920, int(dune_y1(920)) - 2, 0.8, False)
    ]
    for cx, cy, scl, wr in camel_positions:
        draw_camel(cx, cy, scl, wr)

    # THE WHALE: Colossal whale breaching diagonally from lower-left to upper-right.
    # Path center from (240, 830) up-right to (780, 280). Angle ~ -45 degrees (-0.785 rad).
    # Let's construct the whale body along a smooth arc or parametric spline.
    # We will draw a series of overlapping ellipses along the smooth curve from tail flukes to head.

    whale_start_x, whale_start_y = 220, 860 # Head end exiting the dune
    whale_end_x, whale_end_y = 780, 260   # Tail flukes end high in the sky

    # Let's define control points for the curved organic body (banana/crescent shape):
    # We can sample 30 points along a quadratic bezier or smooth curve.
    # P0 = (220, 860), P1 = (450, 520), P2 = (780, 260)
    p0 = (220, 860)
    p1 = (460, 500)
    p2 = (780, 260)

    steps = 80
    body_coords = []
    for i in range(steps + 1):
        t = i / float(steps)
        # Quadratic bezier
        bx = (1 - t)**2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
        by = (1 - t)**2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
        
        # Thickness profile along t: t=0 (head, radius ~35), t=0.5 (torso, radius ~60), t=1.0 (tail stock, radius ~15)
        if t < 0.15:
            # Head rounded blunt shape
            r = 35 + t * 50
        elif t < 0.7:
            # Main torso (dominates frame)
            r = 55 + 15 * math.sin((t - 0.15) / 0.55 * math.pi)
        else:
            # Tapering tail stock
            r = 55 * (1.0 - (t - 0.7) / 0.3) + 12
        body_coords.append((bx, by, r))

    # Draw whale body segments (smooth organic gradient: dark blue-gray underside, rich deep blue-gray body, iridescent light top)
    body_base_col = (40, 55, 85)
    body_top_col = (110, 135, 170)
    body_belly_col = (25, 35, 50)

    for bx, by, r in body_coords:
        # Draw filled circle/ellipse at each point with shading
        steps_r = int(r)
        for dy in range(-steps_r - 2, steps_r + 3):
            for dx in range(-steps_r - 2, steps_r + 3):
                dist = math.sqrt(dx*dx + dy*dy)
                if dist <= r:
                    px = int(bx + dx)
                    py = int(by + dy)
                    # Shading based on vertical offset (top vs bottom of whale body)
                    shade = dy / (r + 1e-5) # -1.0 (top) to +1.0 (bottom)
                    if shade < 0:
                        # Upper side: lighter highlight
                        col = blend(body_base_col, body_top_col, -shade)
                    else:
                        # Lower side: darker belly shadow
                        col = blend(body_base_col, body_belly_col, shade)
                    set_pixel(px, py, col)

    # Head details at p0 (220, 860):
    # Small white eye with dark pupil
    eye_x, eye_y = p0[0] - 10, p0[1] - 5
    draw_circle(eye_x, eye_y, 4, (240, 240, 240))
    draw_circle(eye_x - 1, eye_y, 2, (15, 20, 30))

    # Spout above head: fan of 5-7 white droplets arcing upward plus soft white mist cloud
    spout_base_x, spout_base_y = p0[0] - 15, p0[1] - 30
    # Mist cloud
    for mc_dx, mc_dy, mc_r in [(-10, -20, 18), (0, -30, 22), (12, -22, 16), (5, -40, 14)]:
        draw_circle(spout_base_x + mc_dx, spout_base_y + mc_dy, mc_r, (230, 240, 250), 0.35)
    # Spout droplets arcing
    droplets = [
        (-25, -15), (-35, -30), (-40, -50), (-20, -45), (-5, -60),
        (5, -55), (18, -40), (25, -25), (10, -35), (-12, -55)
    ]
    for d_dx, d_dy in droplets:
        draw_circle(spout_base_x + d_dx, spout_base_y + d_dy, 2.5, (255, 255, 255), 0.9)
        draw_circle(spout_base_x + d_dx, spout_base_y + d_dy, 4.5, (220, 235, 250), 0.3)

    # Dorsal fin on upper back (around t=0.4)
    df_idx = int(len(body_coords) * 0.4)
    df_x, df_y, _ = body_coords[df_idx]
    # Draw triangular dorsal fin pointing up-left
    for fy in range(25):
        width_at_y = int(16 * (1.0 - fy / 25.0))
        for fx in range(-width_at_y, width_at_y // 2 + 2):
            set_pixel(int(df_x + fx - 5), int(df_y - r - fy), (50, 70, 100))

    # Flipper protruding from lower side of body (around t=0.25)
    fl_idx = int(len(body_coords) * 0.25)
    fl_x, fl_y, _ = body_coords[fl_idx]
    draw_ellipse(fl_x - 15, fl_y + 25, 22, 8, (45, 60, 90), angle=0.6)

    # TAIL FLUKES at upper end p2 (780, 260): TWO DISTINCT TAIL FLUKES (horizontal, fan-shaped, like a butterfly - big and obvious)
    fluke_cx, fluke_cy = p2[0], p2[1]
    # Left fluke and right fluke
    draw_ellipse(fluke_cx - 35, fluke_cy - 15, 35, 14, (70, 90, 120), angle=-0.3)
    draw_ellipse(fluke_cx + 35, fluke_cy - 15, 35, 14, (70, 90, 120), angle=0.3)
    # Center notch/peduncle connection
    draw_circle(fluke_cx, fluke_cy, 12, (60, 80, 110))

    # BREACH POINT: white water spray (many small droplets plus foam arcs) and flying sand particles where the whale exits the dune (p0)
    spray_center_x, spray_center_y = p0[0], p0[1]
    # Foam arcs
    for r_arc in range(15, 60, 8):
        for angle_deg in range(130, 225, 5):
            rad = math.radians(angle_deg)
            sx = int(spray_center_x + r_arc * math.cos(rad))
            sy = int(spray_center_y + r_arc * math.sin(rad))
            draw_circle(sx, sy, 2.5, (255, 255, 255), 0.7)
    # Random-looking deterministic spray droplets & sand particles
    for i in range(120):
        # deterministic pseudo-random offset using sine/cosine hash
        px = spray_center_x + int(80 * math.sin(i * 17.3))
        py = spray_center_y + int(60 * math.cos(i * 31.7)) - 10
        if (i % 2 == 0):
            # Water droplet (white/cyan-white)
            draw_circle(px, py, 2.0, (240, 250, 255), 0.8)
        else:
            # Sand particle (golden/amber)
            draw_circle(px, py, 1.5, (230, 180, 100), 0.9)

    # CAPTION: THE DESERT DREAMED OF THE SEA in a clean 5x7 bitmap font, centered near bottom (y = 960), below a thin gold horizontal line (y = 940)
    line_y = 935
    for lx in range(150, WIDTH - 150):
        set_pixel(lx, line_y, (235, 180, 80))
        set_pixel(lx, line_y + 1, (235, 180, 80), 0.5)

    # Simple 5x7 bitmap font dictionary for uppercase letters and spaces
    FONT_5X7 = {
        'A': [0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11],
        'B': [0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E],
        'C': [0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E],
        'D': [0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E],
        'E': [0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F],
        'F': [0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10],
        'G': [0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F],
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
        'Y': [0x11, 0x11, 0x11, 0x0A, 0x04, 0x04, 0x04],
        'Z': [0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F],
        ' ': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    }

    caption_text = "THE DESERT DREAMED OF THE SEA"
    char_w = 5
    char_h = 7
    scale_f = 3
    spacing = 2
    total_w = len(caption_text) * (char_w * scale_f + spacing * scale_f) - spacing * scale_f
    start_x = (WIDTH - total_w) // 2
    start_y = 965

    curr_x = start_x
    for ch in caption_text:
        glyph = FONT_5X7.get(ch, FONT_5X7[' '])
        for row_idx, row_val in enumerate(glyph):
            for col_idx in range(char_w):
                if (row_val >> (char_w - 1 - col_idx)) & 1:
                    # Draw scaled pixel block
                    for sy_off in range(scale_f):
                        for sx_off in range(scale_f):
                            px = curr_x + col_idx * scale_f + sx_off
                            py = start_y + row_idx * scale_f + sy_off
                            set_pixel(px, py, (255, 245, 220))
        curr_x += (char_w * scale_f + spacing * scale_f)

    return buf

def write_png(filepath, width, height, rgb_buf):
    # Construct PNG file bytes
    # Signature
    png_data = bytearray(b'\x89PNG\r\n\x1a\n')

    def add_chunk(chunk_type, data):
        png_data.extend(struct.pack('>I', len(data)))
        png_data.extend(chunk_type)
        png_data.extend(data)
        crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        png_data.extend(struct.pack('>I', crc))

    # IHDR chunk: width, height, bit depth (8), color type (2 = RGB), compression (0), filter (0), interlace (0)
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    add_chunk(b'IHDR', ihdr_data)

    # IDAT chunk: filter byte (0) + scanline data for each row
    raw_scanlines = bytearray()
    row_stride = width * 3
    for y in range(height):
        raw_scanlines.append(0) # filter type 0 (None)
        start = y * row_stride
        raw_scanlines.extend(rgb_buf[start:start + row_stride])

    compressed_data = zlib.compress(bytes(raw_scanlines), level=6)
    add_chunk(b'IDAT', compressed_data)

    # IEND chunk
    add_chunk(b'IEND', b'')

    # Ensure parent dir exists
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, 'wb') as f:
        f.write(png_data)

def main():
    # Output path rule: os.environ.get('MAKEFUN_OUTPUT_DIR', '/output') / 'entry.png'
    out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'entry.png')

    pixels = draw_canvas()
    write_png(out_path, WIDTH, HIGHT, pixels)
    print(f"Successfully generated entry.png at {out_path} ({len(pixels)} RGB bytes)")

if __name__ == '__main__':
    main()
