#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Original trajectories catch misleading movement/landing acceptance."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/upstream'))
from movement_analysis import analyze


def trace(*, walking=True, stop_drift=False, lands=True):
    samples = []
    for t in (1, 2, 3, 4, 5):
        samples.append((t, 'walk', t*100 if walking else 0, t*16, True))
    end_x = 500 if walking else 0
    for t in (6.25, 6.5, 6.75):
        samples.append((t, 'stop', end_x+(t-6.25)*24 if stop_drift else end_x, 80, True))
    for t,z,grounded in ((7.2,90,False),(8,125,False),(11.7,80,lands)):
        samples.append((t,'land',end_x,z,grounded))
    return '\n'.join(f'OPENOBLIVION_PLAYER_MOVEMENT t={t} phase={phase} x={x} y=0 z={z} '
                     f'grounded={str(grounded).lower()} expected_speed=100' for t,phase,x,z,grounded in samples)


class PlayerMovementAnalysis(unittest.TestCase):
    def test_player_walk_stop_and_jump_with_duplicate_logs(self):
        log = trace()
        data = analyze(log+'\n'+log)
        self.assertEqual(len(data['samples']), 11)
        self.assertAlmostEqual(data['walk_horizontal_displacement'], 400)
        self.assertAlmostEqual(data['walk_distance_ratio'], 1)
        self.assertTrue(data['walk_detected'])
        self.assertTrue(data['walk_response_verified'])
        self.assertTrue(data['stop_verified'])
        self.assertTrue(data['jump_landing_verified'])

    def test_vertical_motion_and_camera_motion_cannot_pass_walking(self):
        data = analyze(trace(walking=False)+'\nOPENOBLIVION_CAMERA_MOTION distance=1000 camera_player_distance=124 yaw=2')
        self.assertTrue(data['trajectory_complete'])
        self.assertGreater(data['walk_vertical_range'], 0)
        self.assertFalse(data['walk_detected'])
        self.assertEqual(data['walk_distance_ratio'], 0)
        self.assertGreater(data['walk_slow_seconds'], 0)

    def test_drift_or_unlanded_jump_fails_its_gate(self):
        data = analyze(trace(stop_drift=True,lands=False))
        self.assertTrue(data['walk_detected'])
        self.assertFalse(data['stop_verified'])
        self.assertFalse(data['jump_landing_verified'])

    def test_respawn_or_teleport_cannot_pass_movement(self):
        data = analyze(trace().replace('x=300 ', 'x=4300 ', 1))
        self.assertTrue(data['trajectory_complete'])
        self.assertTrue(data['trajectory_discontinuities'])
        self.assertFalse(data['walk_detected'])
        self.assertFalse(data['walk_response_verified'])
        self.assertFalse(data['jump_landing_verified'])

    def test_incomplete_or_nonfinite_trajectory_not_accepted(self):
        data = analyze(trace().splitlines()[0])
        self.assertFalse(data['trajectory_complete'])
        self.assertFalse(data['walk_detected'])
        with self.assertRaises(ValueError):
            analyze(trace().replace('x=100 ', 'x=1e999 ', 1))


if __name__ == '__main__': unittest.main()
