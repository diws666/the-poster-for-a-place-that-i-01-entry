#!/usr/bin/env python3
"""main.py — travel poster for Elarion, a place that does not exist.

Stdlib only (zlib + struct). Writes one deterministic 1024x1024 PNG to
/output/entry.png: amber dusk over a still glassy bay, the place's name set
large across the sky, and a single backlit natural stone arch rising from the
water as the landmark. Composition leads the eye: name -> arch -> horizon.
"""
import math
import os
import struct
import zlib

W = H = 1024
STRIDE = W * 3

# Purposeful palette (4 hues + shading): deep sky, sunset orange, pale sun,
# glassy teal sea, warm arch stone, dark foreground rocks, off-white type.
SKY_TOP = (14, 34, 56)      # deep navy-blue at zenith
SKY_HOR = (246, 128, 38)    # sunset orange at the horizon
SUN = (253, 232, 142)       # pale yellow sun disc
GLOW = [(250, 150, 80), (252, 196, 136), (254, 222, 178)]  # sun glow shells
SEA_TOP = (26, 102, 116)    # teal at the horizon
SEA_BOT = (12, 48, 64)      # deep teal at the bottom
REFLECT = (44, 132, 146)    # sun reflection on the water
ARCH = (244, 228, 200)      # lit arch stone (warm cream)
ARCH_SHADE = (190, 150, 100)  # backlit arch face
ARCH_RIM = (254, 244, 224)    # bright rim catching the sun
ROCK = (16, 26, 38)         # foreground rock silhouettes
TEXT = (248, 244, 234)      # place name lettering
TEXT_SHADOW = (30, 44, 60)  # drop shadow for legibility

HORIZON = 660  # sky/sea split line


def disc(buf, cx, cy, r, color):
    """Fill a flat disc (circle) of color into the RGB buffer."""
    c = bytes(color)
    r2 = r * r
    y0 = max(0, cy - r)
    y1 = min(H, cy + r + 1)
    for y in range(y0, y1):
        dy = y - cy
        dx = int(math.sqrt(r2 - dy * dy))
        x0 = max(0, cx - dx)
        x1 = min(W, cx + dx + 1)
        off = y * STRIDE + x0 * 3
        buf[off:off + (x1 - x0) * 3] = c * (x1 - x0)


def ellipse(buf, cx, cy, rx, ry, color):
    """Fill a flat axis-aligned ellipse."""
    c = bytes(color)
    rx2 = rx * rx
    ry2 = ry * ry
    y0 = max(0, cy - ry)
    y1 = min(H, cy + ry + 1)
    for y in range(y0, y1):
        dy = y - cy
        dx = int(math.sqrt(max(0, rx2 * (1.0 - (dy * dy) / ry2))))
        x0 = max(0, cx - dx)
        x1 = min(W, cx + dx + 1)
        off = y * STRIDE + x0 * 3
        buf[off:off + (x1 - x0) * 3] = c * (x1 - x0)


def rect(buf, x0, y0, x1, y1, color):
    c = bytes(color)
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    row = c * ((x1 - x0) * 3)
    for y in range(y0, y1):
        off = y * STRIDE + x0 * 3
        buf[off:off + len(row)] = row


# 5x7 bitmap font (rows top to bottom, '#' = ink), capitals only.
FONT = {
    'A': ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    'B': ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    'C': ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    'D': ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    'E': ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    'F': ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    'G': ["01111", "10000", "10000", "10011", "10001", "10001", "01111"],
    'H': ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    'I': ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    'J': ["11111", "00100", "00100", "00100", "00100", "10100", "01110"],
    'K': ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    'L': ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    'M': ["10001", "11011", "11111", "10101", "10001", "10001", "10001"],
    'N': ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    'O': ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    'P': ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    'Q': ["01110", "10001", "10001", "10001", "10101", "10010", "01100"],
    'R': ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    'S': ["01110", "10001", "10000", "01110", "00001", "10001", "01110"],
    'T': ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    'U': ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    'V': ["10001", "10001", "10001", "10001", "01010", "01010", "00100"],
    'W': ["10001", "10001", "10101", "10101", "11111", "10001", "10001"],
    'X': ["10001", "01010", "00100", "01010", "00100", "01010", "10001"],
    'Y': ["10001", "01010", "00100", "00100", "00100", "00100", "00100"],
    'Z': ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
}


def text(buf, s, x0, y0, scale, color):
    """Draw bitmap text; returns width occupied."""
    x = 0
    for ch in s:
        glyph = FONT[ch]
        for ry, row in enumerate(glyph):
            for rx, bit in enumerate(row):
                if bit == '1':
                    ox = x0 + x + rx * scale
                    oy = y0 + ry * scale
                    sq = bytes(color) * scale
                    for yy in range(scale):
                        off = (oy + yy) * STRIDE + ox * 3
                        buf[off:off + scale * 3] = sq
        x += (5 + 1) * scale  # 5-col glyph + 1-col gap
    return x - 1 * scale  # width without trailing gap


def png_bytes(width, height, buf):
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter: none
        raw += buf[y * STRIDE:(y + 1) * STRIDE]
    compressed = zlib.compress(bytes(raw), 6)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    out = bytearray(b"\x89PNG\r\n\x1a\n")
    out += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    out += chunk(b"IDAT", compressed)
    out += chunk(b"IEND", b"")
    return bytes(out)


def main():
    buf = bytearray(W * H * 3)

    # 1. Sky gradient: deep navy at top -> sunset orange at horizon.
    for y in range(HORIZON):
        t = y / (HORIZON - 1)
        r = int(SKY_TOP[0] * (1 - t) + SKY_HOR[0] * t)
        g = int(SKY_TOP[1] * (1 - t) + SKY_HOR[1] * t)
        b = int(SKY_TOP[2] * (1 - t) + SKY_HOR[2] * t)
        row = bytes((r, g, b)) * W
        off = y * STRIDE
        buf[off:off + STRIDE] = row

    # 2. Sea gradient below the horizon.
    for y in range(HORIZON, H):
        t = (y - HORIZON) / (H - 1 - HORIZON)
        r = int(SEA_TOP[0] * (1 - t) + SEA_BOT[0] * t)
        g = int(SEA_TOP[1] * (1 - t) + SEA_BOT[1] * t)
        b = int(SEA_TOP[2] * (1 - t) + SEA_BOT[2] * t)
        row = bytes((r, g, b)) * W
        off = y * STRIDE
        buf[off:off + STRIDE] = row

    # Horizon line.
    rect(buf, 0, HORIZON - 1, W, HORIZON + 1, (6, 20, 28))

    # 3. Sun glow (largest first), sun sits right of center above the arch.
    SUN_X, SUN_Y = 640, 560
    for r, col in zip((170, 130, 95), GLOW):
        disc(buf, SUN_X, SUN_Y, r, col)
    disc(buf, SUN_X, SUN_Y, 42, SUN)

    # 4. Sun reflection on the water.
    ellipse(buf, SUN_X, 760, 90, 110, REFLECT)
    ellipse(buf, SUN_X, 700, 50, 40, (64, 160, 174))

    # 5. Landmark: one backlit natural stone arch standing in the bay.
    #    Sun sits to the right of it: left face in shade, right face lit,
    #    bright rim on the sun-facing edges.
    CX = 512
    CAP_TOP = 340
    CAP_BASE = 470
    CAP_RX = 112
    for y in range(CAP_TOP, CAP_BASE + 1):
        dy = y - CAP_BASE
        half = int(math.sqrt(max(0.0, CAP_RX * CAP_RX - dy * dy)))
        if half == 0:
            continue
        rect(buf, CX - half, y, CX, y + 1, ARCH_SHADE)    # backlit left face
        rect(buf, CX, y, CX + half, y + 1, ARCH)          # lit right face
        rect(buf, CX + half - 6, y, CX + half, y + 1, ARCH_RIM)  # sun-facing rim
    # Pillars down into the sea.
    rect(buf, CX - 102, CAP_BASE, CX - 58, HORIZON + 1, ARCH_SHADE)
    rect(buf, CX + 58, CAP_BASE, CX + 102, HORIZON + 1, ARCH)
    rect(buf, CX + 96, CAP_BASE, CX + 102, HORIZON + 1, ARCH_RIM)
    # Opening between the pillars shows the sky above the horizon and the
    # bay below it (the sky/sea loops already painted both).
    ellipse(buf, CX, 705, 100, 20, (36, 122, 134))

    # 6. Foreground rocks framing the view.
    ellipse(buf, 120, 990, 190, 62, ROCK)
    ellipse(buf, 880, 955, 150, 58, ROCK)

    # 7. Place name, set large across the sky above the arch.
    NAME = "ELARION"
    scale = 15
    total_w = (len(NAME) * 6 - 1) * scale  # 6 = 5-col glyph + 1-col gap
    tx = (W - total_w) // 2
    ty = 120
    text(buf, NAME, tx + 4, ty + 4, scale, TEXT_SHADOW)  # drop shadow
    text(buf, NAME, tx, ty, scale, TEXT)                  # letters

    # 8. Write the PNG.
    data = png_bytes(W, H, buf)
    os.makedirs("/output", exist_ok=True)
    with open("/output/entry.png", "wb") as f:
        f.write(data)

    # Gate check: dimensions and size.
    w = struct.unpack(">I", data[16:20])[0]
    h = struct.unpack(">I", data[20:24])[0]
    print("wrote /output/entry.png: %dx%d, %d bytes" % (w, h, len(data)))
    assert w == 1024 and h == 1024
    assert len(data) <= 1_048_576


if __name__ == "__main__":
    main()
