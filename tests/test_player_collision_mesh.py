#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""The phone stand-in for the template collision box, and the settings rewrite that selects it."""
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/android'))
import build_personal


# id-mesh-2-positions-array in the example-suite BasicPlayer.dae Collision mesh.
DAE_CORNERS = (
    -13.3072, 13.3072, 140.0,
    13.3072, -13.3072, 140.0,
    13.3072, 13.3072, 140.0,
    13.3072, -13.3072, 140.0,
    -13.3072, -13.3072, 1.7012,
    13.3072, -13.3072, 1.7012,
    13.3072, 13.3072, 140.0,
    13.3072, -13.3072, 1.7012,
    13.3072, 13.3072, 1.7012,
    -13.3072, 13.3072, 1.7012,
    13.3072, -13.3072, 1.7012,
    -13.3072, -13.3072, 1.7012,
    -13.3072, 13.3072, 140.0,
    13.3072, 13.3072, 1.7012,
    -13.3072, 13.3072, 1.7012,
    -13.3072, -13.3072, 140.0,
    -13.3072, 13.3072, 1.7012,
    -13.3072, -13.3072, 1.7012,
    -13.3072, 13.3072, 140.0,
    -13.3072, -13.3072, 140.0,
    13.3072, -13.3072, 140.0,
    -13.3072, -13.3072, 140.0,
    13.3072, -13.3072, 140.0,
    -13.3072, 13.3072, 1.7012,
    13.3072, 13.3072, 1.7012,
    13.3072, -13.3072, 1.7012,
    13.3072, 13.3072, 140.0,
    -13.3072, -13.3072, 140.0,
    -13.3072, 13.3072, 140.0,
    -13.3072, 13.3072, 1.7012,
)


def bounds(values):
    xs, ys, zs = values[0::3], values[1::3], values[2::3]
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


class PlayerCollisionMesh(unittest.TestCase):
    def test_osgt_matches_the_dae_collision_corners(self):
        text = (ROOT / 'tools/android/meshes/basicplayer.osgt').read_text()
        self.assertIn('Name "Collision"', text)
        numbers = [float(token) for token in re.findall(r'[-+]?\d+\.\d+', text.split('VertexArray', 1)[1])]
        self.assertEqual(len(numbers), 24)
        self.assertEqual(bounds(numbers), bounds(DAE_CORNERS))
        self.assertEqual(bounds(numbers), (-13.3072, 13.3072, -13.3072, 13.3072, 1.7012, 140.0))

    def test_settings_rewrite_leaves_animation_files_alone(self):
        source = (
            '[Models]\n'
            'xbaseanim = meshes/BasicPlayer.dae\n'
            'baseanim = meshes/BasicPlayer.dae\n'
            'xbaseanimkf = meshes/BasicPlayer.dae\n'
            'skyatmosphere = meshes/sky_atmosphere.dae\n'
        )
        rewritten = build_personal.player_collision_settings(source)
        self.assertIn('xbaseanim = meshes/basicplayer.osgt\n', rewritten)
        self.assertIn('baseanim = meshes/basicplayer.osgt\n', rewritten)
        self.assertIn('xbaseanimkf = meshes/BasicPlayer.dae\n', rewritten)
        self.assertIn('skyatmosphere = meshes/sky_atmosphere.dae\n', rewritten)


if __name__ == '__main__':
    unittest.main()
