#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Same-cell TES4 doors stay open until used again."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/android'))
import build_personal


class DoorActivationTest(unittest.TestCase):
    def test_five_second_stub_becomes_a_toggle(self):
        patched = build_personal.same_cell_doors_stay_open(build_personal.DOOR_FIVE_SECOND_STUB + "\nreturn {}\n")
        self.assertIn("door.enabled = not door.enabled", patched)
        self.assertIn("OPENOBLIVION_DOOR toggle", patched)
        self.assertNotIn("newSimulationTimer", patched)
        self.assertNotIn("require('openmw.async')", patched)
        self.assertIn("actor:teleport", patched)
        self.assertEqual(patched, build_personal.same_cell_doors_stay_open(patched))

    def test_unknown_handler_is_rejected(self):
        with self.assertRaises(ValueError):
            build_personal.same_cell_doors_stay_open("local function ESM4DoorActivation() end\n")


if __name__ == '__main__':
    unittest.main()
