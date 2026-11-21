#!/usr/bin/env python3
"""main.py — travel poster for KALIX, a place that does not exist.

Stdlib only (math, os, struct, zlib). Writes one deterministic 1024x1024 PNG
to /output/entry.png.

KALIX: a high salt basin beneath an immense sky. One landmark - the Spire, a
single tall stone needle rising from the basin - and one promise: late
afternoon light that burns the needle's edge to a bright rim while it throws
a long shadow across the salt. The place's name is carved once into the stone
terrace that runs the horizon, set into the picture rather than laid on top
of it.
"""
import math
import os
import struct
import zlib

W = H = 1024
STRIDE = W * 3

# Palette: high desert at late afternoon, sharp light, long shadow.
SKY_TOP = (16, 24, 44)      # deep indigo at zenith
SKY_HOR = (232, 136, 48)    # burnt gold at the horizon
SUN = (254, 228, 150)       # pale sun disc
GLOW = [(246, 132, 52), (250, 184, 120), (252, 216, 178)]  # sun glow shells
SALT_TOP = (220, 210, 188)  # pale salt at the horizon
SALT_BOT = (140, 128, 104)  # deeper salt toward the front
TERRACE = (156, 132, 98)    # lit stone of the horizon terrace
CARVE = (58, 42, 26)        # deep shadow in the carved letter slots
SPIRE_LIT = (206, 176, 130)  # sun-facing face of the needle
SPIRE_SHADE = (86, 62, 42)   # backlit face of the needle
SPIRE_RIM = (242, 200, 140)  # bright rim where the sun grazes it
CAST = (82, 70, 50)          # the spire's long shadow on the salt

HORIZON_Y = 650  # sky/salt split, hidden behind the terrace
TERRACE_TOP = 646
TERRACE_BOT = 704

# Spire: one tall thin stone needle, CX center, backlit from the lower right.
SP_CX = 640
SP_HALF = 14
SP_TOP = 250
SP_BASE = TERRACE_BOT  # rises out of the terrace at ground level
SUN_X, SUN_Y = 900, 500  # low right: late afternoon, long shadow to the lower left

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


def shadow(buf, top_y, bot_y, x_a, x_b, shift, color):
    """Cast shadow: trapezoid from (x_a,x_b) at top_y shifting left by `shift`
    at bot_y. Sun low right throws the spire's shadow to the lower left."""
    c = bytes(color)
    for y in range(top_y, bot_y):
        t = (y - top_y) / max(1, bot_y - top_y)
        sx = shift * t
        x0 = max(0, int(x_a - sx))
        x1 = min(W, int(x_b - sx))
        off = y * STRIDE + x0 * 3
        buf[off:off + (x1 - x0) * 3] = c * (x1 - x0)


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

    # 1. Sky gradient: deep indigo at zenith -> burnt gold at the horizon.
    for y in range(HORIZON_Y):
        t = y / (HORIZON_Y - 1)
        r = int(SKY_TOP[0] * (1 - t) + SKY_HOR[0] * t)
        g = int(SKY_TOP[1] * (1 - t) + SKY_HOR[1] * t)
        b = int(SKY_TOP[2] * (1 - t) + SKY_HOR[2] * t)
        row = bytes((r, g, b)) * W
        off = y * STRIDE
        buf[off:off + STRIDE] = row

    # 2. Salt basin gradient below the horizon.
    for y in range(HORIZON_Y, H):
        t = (y - HORIZON_Y) / (H - 1 - HORIZON_Y)
        r = int(SALT_TOP[0] * (1 - t) + SALT_BOT[0] * t)
        g = int(SALT_TOP[1] * (1 - t) + SALT_BOT[1] * t)
        b = int(SALT_TOP[2] * (1 - t) + SALT_BOT[2] * t)
        row = bytes((r, g, b)) * W
        off = y * STRIDE
        buf[off:off + STRIDE] = row

    # 3. Stone terrace running the horizon; the name lives here, carved in.
    rect(buf, 0, TERRACE_TOP, W, TERRACE_BOT, TERRACE)

    # 4. Sun, low right: late afternoon, backlighting the spire's right edge.
    for r, col in zip((96, 68, 46), GLOW):
        disc(buf, SUN_X, SUN_Y, r, col)
    disc(buf, SUN_X, SUN_Y, 34, SUN)

    # 5. Place name carved once into the terrace (set into the scene, not
    #    laid on top of it): recessed dark slots in the lit stone.
    NAME = "KALIX"
    scale = 7
    total_w = (len(NAME) * 6 - 1) * scale  # 6 = 5-col glyph + 1-col gap
    tx = (W - total_w) // 2
    ty = TERRACE_TOP + 10
    text(buf, NAME, tx, ty, scale, CARVE)

    # 6. The spire's long shadow across the salt, thrown to the lower left.
    shadow(buf, TERRACE_BOT, 1000, SP_CX - SP_HALF, SP_CX + SP_HALF, 260, CAST)

    # 7. Landmark: one tall thin stone needle rising out of the terrace.
    #    Left face backlit (shade), right face lit, bright grazing rim.
    for y in range(SP_TOP, SP_BASE + 1):
        rect(buf, SP_CX - SP_HALF, y, SP_CX, y + 1, SPIRE_SHADE)   # backlit face
        rect(buf, SP_CX, y, SP_CX + SP_HALF, y + 1, SPIRE_LIT)     # lit face
        rect(buf, SP_CX + SP_HALF - 4, y, SP_CX + SP_HALF, y + 1, SPIRE_RIM)

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
