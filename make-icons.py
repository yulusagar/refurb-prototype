#!/usr/bin/env python3
"""
Generate Refurb QC app icons using only Python stdlib (no Pillow needed).
Run once:  python3 make-icons.py
Produces:  assets/icon-192.png  assets/icon-512.png  assets/apple-touch-icon.png
"""

import os, struct, zlib, math

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')

BG = (61, 76, 212)    # #3D4CD4  brand indigo
FG = (255, 255, 255)  # white

# ── Checkmark geometry (normalised 0-1 coords) ───────────────────────────────
# Short arm: (0.22, 0.52) → (0.40, 0.70)
# Long arm:  (0.40, 0.70) → (0.78, 0.28)
CHECK_SEGS = [
    (0.22, 0.52, 0.40, 0.70),
    (0.40, 0.70, 0.78, 0.28),
]
STROKE  = 0.072   # half-width of the stroke (normalised)
AA_BAND = 0.012   # anti-alias fade width

def _seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    denom  = dx*dx + dy*dy
    if denom == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px-ax)*dx + (py-ay)*dy) / denom))
    return math.hypot(px - (ax + t*dx), py - (ay + t*dy))

def pixel(nx, ny):
    """Return (r, g, b) for a normalised pixel position."""
    d = min(_seg_dist(nx, ny, *seg) for seg in CHECK_SEGS)
    if d <= STROKE - AA_BAND:
        return FG
    if d <= STROKE:
        t = (STROKE - d) / AA_BAND   # 1 = fully white, 0 = fully bg
        return tuple(int(FG[i]*t + BG[i]*(1.0-t)) for i in range(3))
    return BG

def make_png(size):
    """Rasterise the icon at `size`×`size` and return PNG bytes."""
    rows = bytearray()
    for y in range(size):
        rows.append(0)          # PNG filter byte: None
        ny = (y + 0.5) / size
        for x in range(size):
            nx = (x + 0.5) / size
            rows += bytearray(pixel(nx, ny))

    def chunk(tag, data):
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', crc)

    ihdr_data = struct.pack('>II', size, size) + bytes([8, 2, 0, 0, 0])
    png  = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', ihdr_data)
    png += chunk(b'IDAT', zlib.compress(bytes(rows), 9))
    png += chunk(b'IEND', b'')
    return png

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for size, name in [(512, 'icon-512.png'), (192, 'icon-192.png'), (180, 'apple-touch-icon.png')]:
        path = os.path.join(OUT, name)
        print(f'Generating {name} ({size}×{size}) …', end=' ', flush=True)
        data = make_png(size)
        with open(path, 'wb') as f:
            f.write(data)
        print(f'done  ({len(data):,} bytes)')
    print('All icons created in assets/')
