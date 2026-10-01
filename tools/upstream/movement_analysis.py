# SPDX-License-Identifier: GPL-3.0-only
"""Original analysis of native-player trajectories; camera motion is excluded."""
import math
import re

SAMPLE = re.compile(r'OPENOBLIVION_PLAYER_MOVEMENT t=([\d.eE+-]+) phase=(settle|walk|stop|jump|land) '
                    r'x=([\d.eE+-]+) y=([\d.eE+-]+) z=([\d.eE+-]+) grounded=(true|false) expected_speed=([\d.eE+-]+)')


def analyze(log):
    # Captured stdout and the engine log may repeat the same samples.
    samples = {}
    for match in SAMPLE.finditer(log):
        time, phase, x, y, z, grounded, speed = match.groups()
        numbers = [float(v) for v in (time, x, y, z, speed)]
        if not all(math.isfinite(v) for v in numbers):
            raise ValueError('Non-finite player trajectory')
        samples[numbers[0]] = dict(t=numbers[0], phase=phase, x=numbers[1], y=numbers[2],
                                  z=numbers[3], grounded=grounded == 'true', expected_speed=numbers[4])
    ordered = [samples[t] for t in sorted(samples)]
    discontinuities = []
    for a,b in zip(ordered,ordered[1:]):
        # Authored diagnostic bound, not an engine movement limit. Reject a
        # respawn/teleport as evidence of a successful walk or jump.
        distance3 = math.sqrt(sum((b[axis]-a[axis])**2 for axis in ('x','y','z')))
        if distance3 > 128 + max(a['expected_speed'],b['expected_speed'])*4*(b['t']-a['t']):
            discontinuities.append({'from':a['t'],'to':b['t'],'distance':distance3})
    walking = [s for s in ordered if s['phase'] == 'walk']
    stopping = [s for s in ordered if s['phase'] == 'stop' and s['t'] >= 6.2]
    landing = [s for s in ordered if s['phase'] == 'land']
    def horizontal(a, b): return math.hypot(b['x']-a['x'], b['y']-a['y'])
    walk_pairs = list(zip(walking, walking[1:]))
    duration = sum(b['t']-a['t'] for a,b in walk_pairs)
    distance = sum(horizontal(a,b) for a,b in walk_pairs)
    requested = sum((b['t']-a['t'])*a['expected_speed'] for a,b in walk_pairs)
    slow_time = sum(b['t']-a['t'] for a,b in walk_pairs
                    if horizontal(a,b) < (b['t']-a['t'])*a['expected_speed']*0.25)
    stop_drift = max((horizontal(stopping[0],s) for s in stopping), default=None) if stopping else None
    jump_base = stopping[-1]['z'] if stopping else None
    jump_height = max((s['z']-jump_base for s in landing), default=None) if jump_base is not None else None
    complete = all(len(group) >= 3 for group in (walking,stopping,landing)) and ordered[-1]['t'] >= 11.5
    continuous = complete and not discontinuities
    return {'samples': ordered, 'trajectory_complete': complete,
            'trajectory_discontinuities': discontinuities, 'continuous_trajectory': continuous,
            'walk_seconds': duration, 'walk_horizontal_path': distance,
            'walk_horizontal_displacement': horizontal(walking[0],walking[-1]) if walking else None,
            'walk_requested_distance': requested, 'walk_distance_ratio': distance/requested if requested > 0 else None,
            'walk_slow_seconds': slow_time,
            'walk_vertical_range': max(s['z'] for s in walking)-min(s['z'] for s in walking) if walking else None,
            'walk_grounded_fraction': sum(s['grounded'] for s in walking)/len(walking) if walking else None,
            'stop_horizontal_drift': stop_drift, 'jump_height': jump_height,
            'landing_grounded': landing[-1]['grounded'] if landing else None,
            'walk_detected': continuous and distance > 50,
            'walk_response_verified': continuous and distance > 50 and requested > 0
                and 0.5 <= distance/requested <= 1.25 and slow_time < duration*0.2,
            'stop_verified': continuous and stop_drift is not None and stop_drift < 1,
            'jump_landing_verified': continuous and jump_height is not None and jump_height > 10 and landing[-1]['grounded'],
            'collision_fidelity_verified': False}
