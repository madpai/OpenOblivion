#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Geometry of the touch cluster in TouchControls.java. The formulas match that file."""
import unittest


def side(width, height):
    value = min(width, height) * 0.105
    cap = height * 0.14
    if value > cap:
        value = cap
    if value < 48:
        value = 48
    return value


def gap(width, height):
    return max(6.0, side(width, height) * 0.16)


def bottom_gap(height):
    return height * 0.13


def primary(width, height, slot):
    edge = side(width, height)
    spacing = gap(width, height)
    right = width - spacing
    bottom = height - bottom_gap(height) - edge - slot * (edge + spacing)
    return (right - edge, bottom, right, bottom + edge)


def extra(width, height, index):
    edge = side(width, height)
    spacing = gap(width, height)
    row, col = divmod(index, 2)
    use = primary(width, height, 0)
    right = use[0] - spacing - (1 - col) * (edge + spacing)
    top = use[1] - (4 - row) * (edge + spacing)
    return (right - edge, top, right, top + edge)


def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


class TouchLayout(unittest.TestCase):
    def test_closed_cluster_leaves_the_look_surface_clear(self):
        for width, height in ((1920, 1080), (2400, 1080), (1280, 720), (960, 540)):
            buttons = [primary(width, height, slot) for slot in range(4)]
            for i, a in enumerate(buttons):
                self.assertGreaterEqual(a[2] - a[0], 48, (width, height))
                self.assertGreaterEqual(a[3] - a[1], 48, (width, height))
                self.assertGreaterEqual(a[0], width * 0.4, (width, height, a))
                self.assertLessEqual(a[2], width)
                self.assertGreaterEqual(a[1], 0)
                self.assertLessEqual(a[3], height)
                for b in buttons[i + 1:]:
                    self.assertFalse(overlaps(a, b), (width, height, a, b))

    def test_open_tray_stays_off_the_stick_and_the_center(self):
        for width, height in ((1920, 1080), (2400, 1080), (1280, 720), (960, 540)):
            buttons = [primary(width, height, slot) for slot in range(4)]
            buttons += [extra(width, height, index) for index in range(10)]
            for i, a in enumerate(buttons):
                self.assertGreaterEqual(a[0], width * 0.45, (width, height, a))
                self.assertGreaterEqual(a[1], 0, (width, height, a))
                self.assertLessEqual(a[3], height + 0.01, (width, height, a))
                self.assertGreaterEqual(a[2] - a[0], 48, (width, height))
                for b in buttons[i + 1:]:
                    self.assertFalse(overlaps(a, b), (width, height, a, b))


if __name__ == '__main__':
    unittest.main()
