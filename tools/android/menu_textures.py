#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Original inventory item frames (equipped, enchanted, barter) the host
inventory draws behind item icons; the template game ships none. Uncompressed
64x64 BGRA DDS; the host uses the top-left 42x42 of a 64x64 frame."""
import math
import struct

FRAMES = {
    'menu_icon_equip.dds': (196, 150, 70),
    'menu_icon_barter.dds': (90, 160, 90),
    'menu_icon_magic.dds': (90, 120, 220),
    'menu_icon_magic_equip.dds': (170, 110, 220),
    'menu_icon_magic_barter.dds': (90, 170, 200),
}
SIZE, USED = 64, 42


def frame(color):
    pixels = bytearray()
    centre = (USED - 1) / 2
    for y in range(SIZE):
        for x in range(SIZE):
            if x >= USED or y >= USED:
                pixels += b'\0\0\0\0'
                continue
            edge = min(x, y, USED - 1 - x, USED - 1 - y)
            glow = max(0.0, 1.0 - math.hypot(x - centre, y - centre) / (USED * 0.62))
            alpha = 0.95 if edge < 1 else 0.55 if edge < 2 else 0.12 + 0.28 * glow
            r, g, b = (int(c * (1.0 if edge < 2 else 0.55 + 0.45 * glow)) for c in color)
            pixels += bytes((b, g, r, int(255 * alpha)))
    pf = struct.pack('<II4sIIIII', 32, 0x41, b'\0\0\0\0', 32, 0x00ff0000, 0x0000ff00, 0x000000ff, 0xff000000)
    header = struct.pack('<4sIIIIIII44x', b'DDS ', 124, 0x100f, SIZE, SIZE, SIZE * 4, 0, 1) + pf + struct.pack('<I16x', 0x1000)
    return header + bytes(pixels)


def write(directory):
    directory.mkdir(parents=True, exist_ok=True)
    for name, color in FRAMES.items():
        (directory / name).write_bytes(frame(color))
