#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Run a bounded private stock-OpenMW scene check with software OpenGL/Xvfb."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from check_upstream import check
from movement_analysis import analyze as analyze_movement
from movement_fixture import generate as generate_movement_fixture

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--build-work', required=True, type=Path, help='Container work directory containing build/openmw')
parser.add_argument('--template', required=True, type=Path, help='Pinned external OpenMW Example Suite checkout')
parser.add_argument('--data', type=Path, help="Owner's classic Oblivion Data directory; required outside original fixtures")
parser.add_argument('--start', required=True, help='TES4 cell editor ID')
parser.add_argument('--output', required=True, type=Path, help='Fresh private evidence directory')
parser.add_argument('--image', default='openoblivion-research-build:founding')
parser.add_argument('--scene-data', type=Path, help='Optional private loose visual slice; mount only the master, without full BSAs')
parser.add_argument('--phone-qa', action='store_true', help='Also exercise the original read-only phone camera/player diagnostics')
parser.add_argument('--camera-repair', action='store_true', help='Exercise the original preview camera fallback')
parser.add_argument('--grounded-eye', action='store_true', help='Explicitly enable the unshipped stair eye-height experiment')
parser.add_argument('--native-manifest', type=Path, help='External recorded native camera integration build')
parser.add_argument('--native-grounded-eye', action='store_true', help='Enable the post-physics native filter in that build')
parser.add_argument('--missing-player-model', action='store_true', help='Fault injection: deliberately omit the base player model')
parser.add_argument('--camera-motion', action='store_true', help='Bounded movement/turning probe; changes controls for two seconds')
parser.add_argument('--player-movement', action='store_true', help='Native player trajectory: walk, stop, jump and landing; no scripted camera motion')
parser.add_argument('--movement-turn', type=float, default=0, help='Initial turn in degrees through native player controls')
parser.add_argument('--movement-position', type=float, nargs=3, help='Optional private test placement X Y Z in the selected cell')
parser.add_argument('--movement-heading', type=float, default=0, help='World Z rotation in degrees for optional test placement')
parser.add_argument('--movement-fixture', action='store_true', help='Use the original clear stair cell alongside the public Template')
parser.add_argument('--movement-surface', choices=('stairs', 'ramp', 'wall', 'ceiling'), default='stairs')
parser.add_argument('--raw-eye', action='store_true', help='Diagnostic control: disable only the grounded eye filter')
args = parser.parse_args()
if args.movement_surface != 'stairs' and not args.movement_fixture:
    parser.error('Original surface selection requires --movement-fixture')
if args.native_grounded_eye and (not args.native_manifest or not args.camera_repair or args.grounded_eye):
    parser.error('Native smoothing requires --native-manifest --camera-repair and cannot use the Lua experiment')
if args.player_movement and args.camera_motion:
    parser.error('Player and camera motion drivers cannot run together')
if args.movement_fixture and (not args.player_movement or args.start != 'OpenOblivionStairs'):
    parser.error('Original stairs require --player-movement --start OpenOblivionStairs')
if args.movement_fixture and args.scene_data:
    parser.error('Original movement fixtures cannot mount an owner scene slice')
if args.raw_eye and (not args.player_movement or not args.camera_repair):
    parser.error('--raw-eye requires --player-movement --camera-repair')
if args.grounded_eye and not args.camera_repair:
    parser.error('--grounded-eye requires --camera-repair')
if args.raw_eye and not args.grounded_eye:
    parser.error('--raw-eye requires the experimental --grounded-eye path')
if not math.isfinite(args.movement_turn) or abs(args.movement_turn) > 360:
    parser.error('Movement turn must be finite, between -360 and 360 degrees')
if args.movement_turn and not args.player_movement:
    parser.error('Movement turn requires --player-movement')
if args.movement_position and (not args.player_movement or not all(math.isfinite(x) for x in args.movement_position)):
    parser.error('Finite movement position requires --player-movement')
if not math.isfinite(args.movement_heading) or abs(args.movement_heading) > 360:
    parser.error('Movement heading must be finite, between -360 and 360 degrees')
if args.movement_heading and not args.movement_position:
    parser.error('Movement heading requires --movement-position')
output = args.output.expanduser().resolve()
if output == ROOT or ROOT in output.parents:
    parser.error('Scene reports and screenshots must be outside the public checkout')
if output.exists():
    parser.error('Output directory already exists')
work = args.build_work.expanduser().resolve(strict=True)
native_manifest = None
if args.native_manifest:
    native_path = args.native_manifest.expanduser().resolve(strict=True)
    if native_path == ROOT or ROOT in native_path.parents:
        parser.error('Native build evidence must remain external')
    native_manifest = json.loads(native_path.read_text())
    if (native_manifest.get('schema') != 1
            or native_manifest.get('engine_kind') != 'openoblivion-native-integration'
            or native_manifest.get('base_revision') != json.loads((ROOT / 'docs/research/upstreams.lock.json').read_text())['OpenMW/openmw']['revision']
            or native_manifest.get('engine_sha256') != hashlib.sha256((work / 'build/openmw').read_bytes()).hexdigest()):
        parser.error('Native build provenance/binary mismatch')
    for name, sha in native_manifest['tools_sha256'].items():
        if name not in ('tools/native/integration.py', 'tools/native/grounded_eye.hpp', 'tools/native/camera_grounded_eye.patch') or hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != sha:
            parser.error('Native integration tool mismatch')
if not args.movement_fixture and not args.data:
    parser.error('--data is required for owner scenes')
data = args.data.expanduser().resolve(strict=True) if args.data else None
template = args.template.expanduser().resolve(strict=True)
scene_data = args.scene_data.expanduser().resolve(strict=True) if args.scene_data else None
if scene_data and (scene_data == ROOT or ROOT in scene_data.parents or not scene_data.is_dir()):
    parser.error('Scene slice must be an external private directory')
check(template, 'OpenMW/example-suite')
if not (work / 'build/openmw').is_file() or (not args.movement_fixture and not (data / 'Oblivion.esm').is_file()):
    parser.error('A built stock engine and owner Oblivion.esm are required')
output.mkdir(parents=True, mode=0o700)
(output / 'runtime').mkdir(mode=0o700)
config = output / 'config'
config.mkdir()
cfg = ['replace=content', 'replace=fallback-archive',
       'resources=/work/build/resources', 'data=/template/game_template/data',
       *(['data=/fixture-data'] if args.movement_fixture else
         ['data=/scene-master', 'data=/scene-slice'] if scene_data else ['data=/game']),
       'data=/probe-data', 'content=template.omwgame',
       'content=' + ('original_movement.esp' if args.movement_fixture else 'Oblivion.esm'),
       'content=' + ('player_movement_probe.omwscripts' if args.player_movement else 'scene_probe.omwscripts'),
       'encoding=win1252']
if args.phone_qa or args.camera_repair:
    cfg += ['data=/phone-qa-data']
if args.phone_qa: cfg += ['content=phone_qa.omwscripts']
if args.camera_repair:
    cfg += ['content=' + ('camera_stairs_candidate.omwscripts' if args.grounded_eye else 'camera_repair.omwscripts')]
if args.camera_motion: cfg += ['content=camera_motion_probe.omwscripts']
if args.player_movement:
    movement_data = output / 'movement-data'
    (movement_data / 'scripts').mkdir(parents=True)
    position = '{' + ','.join(repr(v) for v in args.movement_position) + '}' if args.movement_position else 'nil'
    (movement_data / 'scripts/openoblivion_movement_config.lua').write_text(
        'return {turn=' + repr(math.radians(args.movement_turn)) + ', position=' + position
        + ', heading=' + repr(math.radians(args.movement_heading)) + '}\n')
    cfg += ['data=/movement-data']
    if args.raw_eye:
        (movement_data / 'scripts/openoblivion_grounded_eye.lua').write_text(
            '-- Original diagnostic zero-offset control; never included in the APK.\n'
            'return {new=function() return {reset=function() end, update=function() return 0 end} end}\n')
if args.movement_fixture:
    fixture_data = output / 'fixture-data'
    generate_movement_fixture(fixture_data, args.movement_surface)
for archive in ([] if scene_data or args.movement_fixture else sorted(data.glob('*.bsa'))):
    if archive.name.startswith('Oblivion - '):
        cfg.append('fallback-archive=' + archive.name)
(config / 'openmw.cfg').write_text('\n'.join(cfg) + '\n')
settings = (template / 'settings.cfg').read_text()
# This setting belongs in the existing Models section of the upstream template.
settings = settings.replace('[Models]', '[Models]\nload unsupported nif files = true', 1)
if args.missing_player_model:
    settings = settings.replace('meshes/BasicPlayer.dae', 'meshes/openoblivion_missing_player.dae')
(config / 'settings.cfg').write_text(settings + '\n[Video]\nresolution x = 800\nresolution y = 600\n')
container_name = 'openoblivion-scene-' + uuid.uuid4().hex[:12]
command = ['docker', 'run', '--rm', '--init', '--name', container_name, '--network', 'none', '--cpus', '4', '--memory', '12g',
           '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
           '--user', f'{os.getuid()}:{os.getgid()}',
           '--env', 'XDG_CONFIG_HOME=/evidence/xdg-config',
           '--env', 'XDG_DATA_HOME=/evidence/xdg-data',
           '--env', 'XDG_CACHE_HOME=/evidence/xdg-cache',
           '--env', 'XDG_RUNTIME_DIR=/evidence/runtime',
           '--env', 'LIBGL_ALWAYS_SOFTWARE=1', '--env', 'ALSOFT_DRIVERS=null',
           *(['--env', 'OPENOBLIVION_GROUNDED_EYE=1'] if args.native_grounded_eye else []),
           '--volume', f'{work}:/work:ro',
           *(['--volume', f'{fixture_data}:/fixture-data:ro'] if args.movement_fixture else
             ['--volume', f'{data / "Oblivion.esm"}:/scene-master/Oblivion.esm:ro',
              '--volume', f'{scene_data}:/scene-slice:ro'] if scene_data else ['--volume', f'{data}:/game:ro']),
           *(['--volume', f'{ROOT / "tools/android"}:/phone-qa-data:ro'] if args.phone_qa or args.camera_repair else []),
           '--volume', f'{template}:/template:ro',
           '--volume', f'{ROOT / "tools/upstream"}:/probe-data:ro',
           *(['--volume', f'{movement_data}:/movement-data:ro'] if args.player_movement else []),
           '--volume', f'{output}:/evidence', '--workdir', '/work/build',
           '--entrypoint', 'xvfb-run', args.image, '-a', '-e', '/evidence/xvfb.log', '-s', '-screen 0 800x600x24',
           './openmw', '--config', '/evidence/config', '--skip-menu', '--no-sound', '--no-grab',
           '--start', args.start]
start = time.monotonic()
image_id = subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', args.image], text=True).strip()
expected_revision = json.loads((ROOT / 'docs/research/upstreams.lock.json').read_text())['OpenMW/openmw']['revision']
try:
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
except subprocess.TimeoutExpired as error:
    subprocess.run(['docker', 'stop', '--timeout', '5', container_name], capture_output=True, timeout=15)
    for name, content in (('stdout.txt', error.stdout), ('stderr.txt', error.stderr)):
        (output / name).write_bytes(content.encode() if isinstance(content, str) else (content or b''))
    (output / 'timeout.txt').write_text(str(error))
    sys.exit(1)
(output / 'stdout.txt').write_text(result.stdout)
(output / 'stderr.txt').write_text(result.stderr)
log = result.stdout + result.stderr
for path in output.rglob('openmw.log'):
    log += path.read_text(errors='replace')
screens = [str(p.relative_to(output)) for p in output.rglob('*.png')]
revision_matches = ('Revision: ' + expected_revision[:10]) in log
cell_sample = re.search(r'OPENOBLIVION_SCENE_PROBE cell=(\S+) name=(.*?) exterior=(true|false)', log)
cell_matches = cell_sample is not None and cell_sample[2].casefold() == args.start.casefold()
complete = ('OPENOBLIVION_SCENE_PROBE_DONE' in log and bool(screens) and result.returncode == 0
            and revision_matches and cell_matches)
if args.native_grounded_eye and 'OPENOBLIVION_NATIVE_GROUNDED_EYE enabled:' not in log:
    complete = False
repair_activated = 'OPENOBLIVION_CAMERA_REPAIR activated:' in log
motion = re.search(r'OPENOBLIVION_CAMERA_MOTION distance=([\d.eE+-]+) camera_player_distance=([\d.eE+-]+) yaw=([\d.eE+-]+)', log)
motion_verified = bool(motion and float(motion[1]) > 1 and float(motion[2]) < 256 and abs(float(motion[3])) > 0.1)
if args.camera_motion and not motion_verified: complete = False
if args.camera_repair and args.missing_player_model and not repair_activated: complete = False
movement = analyze_movement(log) if args.player_movement else None
if movement is not None and not movement['trajectory_complete']: complete = False
metrics = {'schema': 1, 'stock_engine_returncode': result.returncode, 'probe_complete': complete,
           'elapsed_seconds': round(time.monotonic() - start, 4), 'start_cell': args.start,
           'template_revision': check(template, 'OpenMW/example-suite'),
           'expected_engine_revision': expected_revision, 'engine_revision_matches': revision_matches,
           'observed_cell': cell_sample[2] if cell_sample else None,
           'observed_cell_id': cell_sample[1] if cell_sample else None,
           'observed_exterior': cell_sample[3] == 'true' if cell_sample else None,
           'requested_cell_matches': cell_matches,
           'docker_image_id': image_id,
           'master_sha256': None if args.movement_fixture else hashlib.sha256((data / 'Oblivion.esm').read_bytes()).hexdigest(),
           'engine_sha256': hashlib.sha256((work / 'build/openmw').read_bytes()).hexdigest(),
           'engine_kind': 'openoblivion-native-integration' if native_manifest else 'stock-upstream',
           'native_integration': native_manifest, 'native_grounded_eye_enabled': args.native_grounded_eye,
           'bounded_visual_slice': bool(scene_data), 'phone_qa_enabled': args.phone_qa,
           'camera_repair_enabled': args.camera_repair, 'missing_player_model_injected': args.missing_player_model,
           'experimental_grounded_eye_enabled': args.grounded_eye,
           'camera_motion_enabled': args.camera_motion,
           'camera_repair_activated': repair_activated, 'camera_motion_verified': motion_verified,
           'motion_distance': float(motion[1]) if motion else None,
           'motion_camera_player_distance': float(motion[2]) if motion else None,
           'player_movement_enabled': args.player_movement, 'movement_initial_turn_degrees': args.movement_turn,
           'original_stair_fixture': args.movement_fixture,
           'original_movement_surface': args.movement_surface if args.movement_fixture else None,
           'grounded_eye_disabled_for_control': args.raw_eye,
           'movement_start_position': args.movement_position, 'movement_start_heading_degrees': args.movement_heading,
           'player_movement': movement,
           'screenshots': screens, 'scope': 'Private scene load/screenshot; software OpenGL, not Vulkan or gameplay'}
probe_sources = [Path(__file__).resolve()]
if args.camera_repair:
    probe_sources += [ROOT / 'tools/android/camera_repair.omwscripts',
                      ROOT / 'tools/android/scripts/openoblivion_preview_camera.lua']
if args.grounded_eye:
    probe_sources += [ROOT / 'tools/android/camera_stairs_candidate.omwscripts',
                      ROOT / 'tools/android/scripts/openoblivion_preview_camera_candidate.lua',
                      ROOT / 'tools/android/scripts/openoblivion_grounded_eye.lua',
                      ROOT / 'tools/android/scripts/openoblivion_stair_qa.lua']
if args.phone_qa:
    probe_sources += [ROOT / 'tools/android/phone_qa.omwscripts',
                      ROOT / 'tools/android/scripts/openoblivion_phone_qa.lua']
if args.player_movement:
    probe_sources += [ROOT / 'tools/upstream/movement_analysis.py',
                      ROOT / 'tools/upstream/player_movement_probe.omwscripts',
                      ROOT / 'tools/upstream/scripts/openoblivion_player_movement_probe.lua',
                      ROOT / 'tools/upstream/scripts/openoblivion_player_movement_setup.lua']
    if args.movement_fixture: probe_sources.append(ROOT / 'tools/upstream/movement_fixture.py')
    metrics['movement_config_sha256'] = hashlib.sha256(
        (movement_data / 'scripts/openoblivion_movement_config.lua').read_bytes()).hexdigest()
    if args.raw_eye:
        metrics['raw_eye_control_sha256'] = hashlib.sha256(
            (movement_data / 'scripts/openoblivion_grounded_eye.lua').read_bytes()).hexdigest()
metrics['probe_tools_sha256'] = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in probe_sources}
if args.movement_fixture:
    metrics['fixture_files_sha256'] = {p.relative_to(fixture_data).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in fixture_data.rglob('*') if p.is_file()}
(output / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
print('Private upstream scene probe complete=' + str(complete))
sys.exit(0 if complete else 1)
