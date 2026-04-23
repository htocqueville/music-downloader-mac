#!/usr/bin/env python3
"""
Generate soundloader.icns — a teardrop with concentric sound-wave arcs.

Design:
  • Deep purple/indigo gradient background, rounded corners (macOS-style)
  • White teardrop pointing upward, clean and sharp
  • Three concentric U-shaped arcs below the drop (sound waves)

Run:   python3 scripts/generate_icon.py
Output: assets/soundloader.icns
"""

import math
import os
import subprocess
from PIL import Image, ImageDraw, ImageFilter

# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def cubic_bezier(p0, p1, p2, p3, n=150):
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        x = mt**3*p0[0] + 3*mt**2*t*p1[0] + 3*mt*t**2*p2[0] + t**3*p3[0]
        y = mt**3*p0[1] + 3*mt**2*t*p1[1] + 3*mt*t**2*p2[1] + t**3*p3[1]
        pts.append((x, y))
    return pts


def arc_points(cx, cy, r, start_deg, end_deg, n=250):
    if end_deg <= start_deg:
        end_deg += 360
    pts = []
    for i in range(n + 1):
        a = math.radians(start_deg + (end_deg - start_deg) * i / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


# ---------------------------------------------------------------------------
# Master drawing (always at MASTER_SIZE, then scaled down)
# ---------------------------------------------------------------------------

MASTER_SIZE = 2048   # 2× oversize for anti-aliasing


def build_master():
    S = MASTER_SIZE
    sc = S / 1024

    def s(v):
        return v * sc

    # ── Background gradient ──────────────────────────────────────────────────
    # Bilinear: top-left #1a0f40 → bottom-right #3d1a78
    tl = (26, 15, 64)
    br = (61, 26, 120)
    mid = tuple((tl[i] + br[i]) // 2 for i in range(3))
    g = Image.new('RGBA', (2, 2))
    g.putpixel((0, 0), tl + (255,))
    g.putpixel((1, 0), mid + (255,))
    g.putpixel((0, 1), mid + (255,))
    g.putpixel((1, 1), br + (255,))
    bg = g.resize((S, S), Image.BILINEAR)

    # Rounded-rect mask (macOS 2024-style corner radius ≈ 22.4% of width)
    rr_mask = Image.new('L', (S, S), 0)
    rr_draw = ImageDraw.Draw(rr_mask)
    corner = int(s(230))
    rr_draw.rounded_rectangle([(0, 0), (S - 1, S - 1)], radius=corner, fill=255)

    canvas = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    canvas.paste(bg, mask=rr_mask)

    # ── Teardrop geometry ────────────────────────────────────────────────────
    #
    # All coordinates in 1024-space, then multiplied by sc.
    #
    # Geometry:
    #   Apex  : (512, 110)
    #   Circle: center (512, 460), radius 205
    #   Bottom: y = 460 + 205 = 665
    #
    # Tangent points (mathematically derived):
    #   dist apex→center = 350
    #   sin α = 205/350 ≈ 0.586  →  α ≈ 35.8°
    #   Left  tangent ≈ (346, 340)
    #   Right tangent ≈ (678, 340)
    #
    # Arc: clockwise from right (324°) through bottom to left (216°) = 252°
    #
    # Bezier CP chosen so:
    #   • C¹ continuity at the tangent points (smooth join with arc)
    #   • ~22° half-angle at apex → visible sharp tip

    apex = (s(512), s(110))
    cx, cy, cr = s(512), s(460), s(205)
    lt = (s(346), s(340))
    rt = (s(678), s(340))

    # Control points (1024-space)
    # Left side: LT → apex  (C¹ at LT, ~22° at apex)
    left_curve  = cubic_bezier(lt,
                               (s(402), s(264)),   # tangent to circle at LT
                               (s(499), s(138)),   # sharp approach to apex
                               apex)
    # Right side: apex → RT (mirror)
    right_curve = cubic_bezier(apex,
                               (s(525), s(138)),
                               (s(622), s(264)),
                               rt)
    # Bottom arc: RT →(clockwise)→ LT
    bottom_arc  = arc_points(cx, cy, cr, 324.2, 215.8)

    teardrop = left_curve + right_curve[1:] + bottom_arc[1:]

    # ── Very subtle ambient glow (blur=6 at 1024-scale) ─────────────────────
    glow = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.polygon(teardrop, fill=(180, 140, 255, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(int(s(6))))
    canvas = Image.alpha_composite(canvas, glow)

    draw = ImageDraw.Draw(canvas)

    # ── Drop fill — clean white with very slight lavender tint ───────────────
    draw.polygon(teardrop, fill=(252, 248, 255, 248))

    # Subtle inner gradient illusion: a slightly brighter zone in the upper body
    # of the drop (not at the apex, so the tip stays clean).
    hx, hy = s(490), s(295)
    hw, hh = s(85), s(100)
    draw.ellipse([(hx - hw, hy - hh), (hx + hw, hy + hh)],
                 fill=(255, 255, 255, 55))

    # ── Sound waves (U-shaped arcs below drop) ───────────────────────────────
    # Centered at the bottom of the drop: (512, 665).
    # Arc from 0° to 180° traces the bottom semicircle (opening downward).
    wc_x, wc_y = s(512), s(665)

    wave_params = [
        # (radius, line_width, alpha)
        (s(72),  int(s(32)), 240),
        (s(146), int(s(24)), 150),
        (s(220), int(s(16)), 72),
    ]

    for r, w, alpha in wave_params:
        bbox = [wc_x - r, wc_y - r, wc_x + r, wc_y + r]
        draw.arc(bbox, start=0, end=180, fill=(255, 255, 255, alpha), width=w)

    return canvas   # 2048×2048 RGBA


# ---------------------------------------------------------------------------
# Build iconset and .icns
# ---------------------------------------------------------------------------

ICONSET_DIR = '/tmp/soundloader.iconset'
OUTPUT_ICNS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'assets', 'soundloader.icns'
)

ICON_SIZES = {
    'icon_16x16.png':      16,
    'icon_16x16@2x.png':   32,
    'icon_32x32.png':      32,
    'icon_32x32@2x.png':   64,
    'icon_128x128.png':    128,
    'icon_128x128@2x.png': 256,
    'icon_256x256.png':    256,
    'icon_256x256@2x.png': 512,
    'icon_512x512.png':    512,
    'icon_512x512@2x.png': 1024,
}

os.makedirs(ICONSET_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_ICNS), exist_ok=True)

print('Drawing master…')
master = build_master()

rendered_sizes = {}
for filename, px in ICON_SIZES.items():
    if px not in rendered_sizes:
        print(f'  Scaling to {px}×{px}…')
        rendered_sizes[px] = master.resize((px, px), Image.LANCZOS)
    rendered_sizes[px].save(os.path.join(ICONSET_DIR, filename))

print('Compiling .icns…')
subprocess.run(['iconutil', '-c', 'icns', ICONSET_DIR, '-o', OUTPUT_ICNS], check=True)

print(f'Done → {OUTPUT_ICNS}')
