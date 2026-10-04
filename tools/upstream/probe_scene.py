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
import shutil
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
parser.add_argument('--installed-data', action='store_true', help='Load all installed BSAs and the measured classic expansion plugins')
parser.add_argument('--phone-qa', action='store_true', help='Also exercise the original read-only phone camera/player diagnostics')
parser.add_argument('--tes4-interactions', action='store_true', help='Exercise native TES4 names, container snapshots and preview UI')
parser.add_argument('--tes4-animation', action='store_true', help='Observe default TES4 NPC idle over two loops and capture its body pose')
parser.add_argument('--tes4-doors', action='store_true', help='Activate the Vilverin gate and compare closed/open/closed collision')
parser.add_argument('--door-traversal', action='store_true', help='Also walk the current native player body into and through the Vilverin gate')
parser.add_argument('--audio-capture', action='store_true', help='Capture enabled door audio through OpenAL Soft wave output into private evidence')
parser.add_argument('--camera-repair', action='store_true', help='Exercise the original preview camera fallback')
parser.add_argument('--grounded-eye', action='store_true', help='Explicitly enable the unshipped stair eye-height experiment')
parser.add_argument('--native-manifest', type=Path, help='External recorded native camera integration build')
parser.add_argument('--native-grounded-eye', action='store_true', help='Enable the post-physics native filter in that build')
parser.add_argument('--missing-player-model', action='store_true', help='Fault injection: deliberately omit the base player model')
parser.add_argument('--player-collision-model', type=Path, help='Load this exact OSGT player model using the Android preview settings rewrite')
parser.add_argument('--authored-collision', action='store_true', help='Enable the native fixed OL_STATIC strip loader without the door driver')
parser.add_argument('--original-body', action='store_true', help='Enable the measured classic TES4 player hull in a recorded body build')
parser.add_argument('--tes4-movement', action='store_true', help='Enable the classic TES4 player ground-speed formula in a recorded build')
parser.add_argument('--tes4-player', action='store_true', help='Render the player as the TES4 Player record in a recorded player build')
parser.add_argument('--phone-overlay', action='store_true', help='Mount the phone launcher overlay (scripts, sky, generated TES4 stats) as on Android')
parser.add_argument('--sky-osgt', action='store_true', help='Use the phone overlay OSGT sky atmosphere instead of the template COLLADA file')
parser.add_argument('--async-physics-threads', type=int, choices=range(5), help='Explicit physics worker count for a controlled comparison')
parser.add_argument('--camera-motion', action='store_true', help='Bounded movement/turning probe; changes controls for two seconds')
parser.add_argument('--player-movement', action='store_true', help='Native player trajectory: walk, stop, jump and landing; no scripted camera motion')
parser.add_argument('--movement-camera', choices=('default', 'third'), default='default', help='Camera view for the movement probe')
parser.add_argument('--movement-shot-time', type=float, default=6.5, help='Probe time of the screenshot (seconds)')
parser.add_argument('--movement-duration', type=float, default=12.0, help='Seconds before the movement probe quits')
parser.add_argument('--movement-pitch', type=float, default=0, help='Initial look pitch in degrees (positive looks down)')
parser.add_argument('--movement-face', action='store_true', help='Place a static camera in front of the nearest actor face at the shot time')
parser.add_argument('--movement-face-distance', type=float, default=70, help='Distance of the face camera; negative views from the far side')
parser.add_argument('--movement-face-angle', type=float, default=0, help='Degrees around the actor from the way it faces')
parser.add_argument('--movement-face-height', type=float, default=148, help='Height of the face camera target above the actor origin')
parser.add_argument('--movement-give', help='Comma separated generated item ids given to the player and equipped')
parser.add_argument('--movement-weapon', help='Generated item id (oo4_xxxxxx) the player is given and wields')
parser.add_argument('--movement-ui', choices=('inventory', 'loot'), help='Open this menu at the shot time and capture it')
parser.add_argument('--movement-attack', action='store_true', help='Request a TES4 player attack every 1.5 s (phone overlay)')
parser.add_argument('--movement-gait', choices=('walk', 'run', 'sneak', 'none'), default='walk', help='Gait the movement probe requests')
parser.add_argument('--movement-turn', type=float, default=0, help='Initial turn in degrees through native player controls')
parser.add_argument('--movement-position', type=float, nargs=3, help='Optional private test placement X Y Z in the selected cell')
parser.add_argument('--movement-heading', type=float, default=0, help='World Z rotation in degrees for optional test placement')
parser.add_argument('--movement-fixture', action='store_true', help='Use the original clear stair cell alongside the public Template')
parser.add_argument('--movement-surface', choices=('stairs', 'ramp', 'wall', 'ceiling'), default='stairs')
parser.add_argument('--raw-eye', action='store_true', help='Diagnostic control: disable only the grounded eye filter')
args = parser.parse_args()
if args.player_collision_model and args.missing_player_model:
    parser.error('Choose either a supplied player model or missing-model fault injection')
if args.audio_capture and not (args.tes4_doors and args.door_traversal):
    parser.error('Audio capture requires --tes4-doors --door-traversal near the sound source')
if args.door_traversal and not args.tes4_doors:
    parser.error('Gate traversal requires --tes4-doors')
if args.tes4_doors and (args.start != 'Vilverin' or args.player_movement or args.tes4_interactions
                      or args.tes4_animation or not args.native_manifest):
    parser.error('Door observations require native Vilverin without another automation driver')
if args.tes4_animation and (args.player_movement or args.tes4_interactions or not args.native_manifest):
    parser.error('Animation observation requires a native build without the movement/container driver')
if args.original_body and (not args.native_manifest or not args.player_collision_model):
    parser.error('--original-body requires --native-manifest and the Android --player-collision-model')
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
if args.installed_data and (args.scene_data or args.movement_fixture):
    parser.error('--installed-data requires the full owner Data directory')
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
       'content=' + ('player_movement_probe.omwscripts' if args.player_movement else
                    'tes4_doors_probe.omwscripts' if args.tes4_doors else
                    'tes4_animation_probe.omwscripts' if args.tes4_animation else 'scene_probe.omwscripts'),
       'encoding=win1252']
if args.tes4_player and (not native_manifest or not native_manifest.get('tes4_player')):
    parser.error('--tes4-player requires a recorded player integration')
if args.tes4_movement and (not native_manifest or not native_manifest.get('tes4_movement')):
    parser.error('--tes4-movement requires a recorded movement integration')
if args.original_body and not native_manifest.get('tes4_body'):
    parser.error('--original-body requires a recorded body integration')
if args.tes4_doors:
    if not native_manifest.get('tes4_doors'):
        parser.error('Door observations require a recorded door integration')
    sys.path.insert(0, str(ROOT / 'tools/android'))
    from build_personal import same_cell_doors_stay_open
    door_data = output / 'door-data'
    door_script = door_data / 'scripts/omw/activationhandlers.lua'
    door_script.parent.mkdir(parents=True)
    original = work / 'build/resources/vfs/scripts/omw/activationhandlers.lua'
    door_script.write_text(same_cell_doors_stay_open(original.read_text()))
    (door_data / 'scripts/openoblivion_door_config.lua').write_text(
        'return {traversal=' + ('true' if args.door_traversal else 'false')
        + ',audio=' + ('true' if args.audio_capture else 'false') + '}\n')
    if args.audio_capture:
        (output / 'alsoft.conf').write_text(
            '[general]\nsample-type=float32\nchannels=stereo\nfrequency=48000\ndither=false\n'
            '[wave]\nfile=/evidence/door-audio.wav\n')
    cfg += ['data=/door-data']
if args.phone_qa or args.camera_repair:
    cfg += ['data=/phone-qa-data']
if args.player_collision_model:
    sys.path.insert(0, str(ROOT / 'tools/android'))
    from build_personal import player_collision_settings
    player_model = args.player_collision_model.expanduser().resolve(strict=True)
    player_data = output / 'player-data'
    (player_data / 'meshes').mkdir(parents=True)
    shutil.copyfile(player_model, player_data / 'meshes/basicplayer.osgt')
    cfg += ['data=/player-data']
if args.phone_qa: cfg += ['content=phone_qa.omwscripts']
if args.tes4_interactions:
    cfg += ['data=/phone-qa-data', 'content=container.omwscripts', 'content=tes4_interactions_probe.omwscripts']
if args.camera_repair:
    cfg += ['content=' + ('camera_stairs_candidate.omwscripts' if args.grounded_eye else 'camera_repair.omwscripts')]
if args.camera_motion: cfg += ['content=camera_motion_probe.omwscripts']
if args.player_movement:
    movement_data = output / 'movement-data'
    (movement_data / 'scripts').mkdir(parents=True)
    position = '{' + ','.join(repr(v) for v in args.movement_position) + '}' if args.movement_position else 'nil'
    (movement_data / 'scripts/openoblivion_movement_config.lua').write_text(
        'return {turn=' + repr(math.radians(args.movement_turn)) + ', position=' + position
        + ', heading=' + repr(math.radians(args.movement_heading)) + ', gait=' + repr(args.movement_gait) + ', camera=' + repr(args.movement_camera) + ', shot=' + repr(args.movement_shot_time) + ', attack=' + ('true' if args.movement_attack else 'false') + ', duration=' + repr(args.movement_duration) + ', ui=' + (repr(args.movement_ui) if args.movement_ui else 'nil') + ', pitch=' + repr(math.radians(args.movement_pitch)) + ', face=' + ('true' if args.movement_face else 'false') + ', give=' + (repr(args.movement_give) if args.movement_give else 'nil') + ', weapon=' + (repr(args.movement_weapon) if args.movement_weapon else 'nil') + ', faceDistance=' + repr(args.movement_face_distance) + ', faceAngle=' + repr(args.movement_face_angle) + ', faceHeight=' + repr(args.movement_face_height) + '}\n')
    cfg += ['data=/movement-data']
    if args.raw_eye:
        (movement_data / 'scripts/openoblivion_grounded_eye.lua').write_text(
            '-- Original diagnostic zero-offset control; never included in the APK.\n'
            'return {new=function() return {reset=function() end, update=function() return 0 end} end}\n')
if args.movement_fixture:
    fixture_data = output / 'fixture-data'
    generate_movement_fixture(fixture_data, args.movement_surface)
if args.installed_data:
    sys.path.insert(0, str(ROOT / 'tools/android'))
    from payload import installed_data
    _, archives, plugins = installed_data(data)
    cfg += ['content=' + name for name in plugins if name != 'Oblivion.esm']
    cfg += ['fallback-archive=' + name for name in archives]
else:
    for archive in ([] if scene_data or args.movement_fixture else sorted(data.glob('*.bsa'))):
        if archive.name.startswith('Oblivion - '):
            cfg.append('fallback-archive=' + archive.name)
if args.phone_overlay:
    overlay_dir = output / 'phone-overlay'
    shutil.copytree(ROOT / 'tools/android/overlay', overlay_dir)
    sys.path.insert(0, str(ROOT / 'tools/android'))
    from tes4_stats import lua as stats_lua, npc_lua, npc_table, stats as master_stats
    (overlay_dir / 'scripts/openoblivion_tes4_stats_values.lua').write_text(stats_lua(master_stats(data / 'Oblivion.esm')))
    (overlay_dir / 'scripts/openoblivion_tes4_npc_values.lua').write_text(npc_lua(npc_table(data / 'Oblivion.esm')))
    from tes4_rules_addon import build as rules_addon
    from tes4_items import build as items_build
    item_records, items_lua = items_build(data / 'Oblivion.esm')
    (overlay_dir / 'openoblivion_rules.omwaddon').write_bytes(rules_addon(item_records))
    (overlay_dir / 'scripts/openoblivion_tes4_items_values.lua').write_text(items_lua)
    from menu_textures import write as write_menu_textures
    write_menu_textures(overlay_dir / 'textures')
    args.sky_osgt = True
    cfg += ['data=/phone-overlay', 'content=openoblivion_rules.omwaddon', 'content=start_position.omwscripts']
elif args.sky_osgt:
    cfg.append('data=/phone-overlay')
(config / 'openmw.cfg').write_text('\n'.join(cfg) + '\n')
settings = (template / 'settings.cfg').read_text()
# This setting belongs in the existing Models section of the upstream template.
settings = settings.replace('[Models]', '[Models]\nload unsupported nif files = true', 1)
if args.audio_capture:
    # Isolate effects in this evidence run; shipped volume settings stay intact.
    settings += '\n[Sound]\nmusic volume = 0\n'
if args.missing_player_model:
    settings = settings.replace('meshes/BasicPlayer.dae', 'meshes/openoblivion_missing_player.dae')
if args.player_collision_model:
    settings = player_collision_settings(settings)
if args.sky_osgt:
    settings = settings.replace('meshes/sky_atmosphere.dae', 'meshes/sky_atmosphere.osgt')
if args.async_physics_threads is not None:
    settings += '\n[Physics]\nasync num threads = ' + str(args.async_physics_threads) + '\n'
(config / 'settings.cfg').write_text(settings + '\n[Video]\nresolution x = 800\nresolution y = 600\n')
container_name = 'openoblivion-scene-' + uuid.uuid4().hex[:12]
command = ['docker', 'run', '--rm', '--init', '--name', container_name, '--network', 'none', '--cpus', '4', '--memory', '12g',
           '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
           '--user', f'{os.getuid()}:{os.getgid()}',
           '--env', 'XDG_CONFIG_HOME=/evidence/xdg-config',
           '--env', 'XDG_DATA_HOME=/evidence/xdg-data',
           '--env', 'XDG_CACHE_HOME=/evidence/xdg-cache',
           '--env', 'XDG_RUNTIME_DIR=/evidence/runtime',
           '--env', 'LIBGL_ALWAYS_SOFTWARE=1', '--env', 'ALSOFT_DRIVERS=' + ('wave' if args.audio_capture else 'null'),
           *(['--env', 'ALSOFT_CONF=/evidence/alsoft.conf'] if args.audio_capture else []),
           *(['--env', 'OPENOBLIVION_AUTHORED_COLLISION=1'] if args.tes4_doors or args.authored_collision else []),
           *(['--env', 'OPENOBLIVION_ORIGINAL_BODY=1'] if args.original_body else []),
           *(['--env', 'OPENOBLIVION_TES4_MOVEMENT=1'] if args.tes4_movement else []),
           *(['--env', 'OPENOBLIVION_TES4_PLAYER=1'] if args.tes4_player else []),
           *(['--env', 'OPENOBLIVION_GROUNDED_EYE=1'] if args.native_grounded_eye else []),
           '--volume', f'{work}:/work:ro',
           *(['--volume', f'{fixture_data}:/fixture-data:ro'] if args.movement_fixture else
             ['--volume', f'{data / "Oblivion.esm"}:/scene-master/Oblivion.esm:ro',
              '--volume', f'{scene_data}:/scene-slice:ro'] if scene_data else ['--volume', f'{data}:/game:ro']),
           *(['--volume', f'{ROOT / "tools/android"}:/phone-qa-data:ro'] if args.phone_qa or args.camera_repair or args.tes4_interactions else []),
           *(['--volume', f'{output / "phone-overlay"}:/phone-overlay:ro'] if args.phone_overlay else
             ['--volume', f'{ROOT / "tools/android/overlay"}:/phone-overlay:ro'] if args.sky_osgt else []),
           '--volume', f'{template}:/template:ro',
           '--volume', f'{ROOT / "tools/upstream"}:/probe-data:ro',
           *(['--volume', f'{door_data}:/door-data:ro'] if args.tes4_doors else []),
           *(['--volume', f'{player_data}:/player-data:ro'] if args.player_collision_model else []),
           *(['--volume', f'{movement_data}:/movement-data:ro'] if args.player_movement else []),
           '--volume', f'{output}:/evidence', '--workdir', '/work/build',
           '--entrypoint', 'xvfb-run', args.image, '-a', '-e', '/evidence/xvfb.log', '-s', '-screen 0 800x600x24',
           './openmw', '--config', '/evidence/config', '--skip-menu',
           *([] if args.audio_capture else ['--no-sound']), '--no-grab',
           '--start', args.start]
start = time.monotonic()
image_id = subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', args.image], text=True).strip()
expected_revision = json.loads((ROOT / 'docs/research/upstreams.lock.json').read_text())['OpenMW/openmw']['revision']
try:
    result = subprocess.run(command, capture_output=True, text=True, timeout=120 + max(0, int(args.movement_duration) - 12))
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
interactions_verified = ('OPENOBLIVION_TES4_INTERACTIONS actors=' in log
                         and 'OPENOBLIVION_CONTAINER name=' in log
                         and 'OPENOBLIVION_CONTAINER_UI_CAPTURED' in log
                         and 'OPENOBLIVION_NPC skeleton_nodes=' in log
                         and 'Lua error:' not in log)
if args.tes4_interactions and not interactions_verified: complete = False
animation_samples = {}
for sample in re.finditer(r'OPENOBLIVION_ANIMATION_SAMPLE id=(\S+) elapsed=([\d.]+) time=([\d.]+) loops=(\d+)', log):
    animation_samples.setdefault(sample[1], {})[float(sample[2])] = (float(sample[3]), int(sample[4]))
animation_observations = {}
for actor, samples in animation_samples.items():
    values = [value for _, value in sorted(samples.items())]
    wraps = sum(after[0] < before[0] for before, after in zip(values, values[1:]))
    animation_observations[actor] = {'samples': len(values), 'loop_wraps': wraps,
        'first_time': values[0][0], 'last_time': values[-1][0]}
animation_verified = (bool(animation_observations) and 'Lua error:' not in log
                      and 'OPENOBLIVION_NPC idle_source=' in log
                      and all(row['samples'] >= 10 and row['loop_wraps'] >= 2
                              for row in animation_observations.values()))
if args.tes4_animation and not animation_verified: complete = False
door_collision = {float(m[1]): int(m[2]) for m in re.finditer(
    r'OPENOBLIVION_DOOR_COLLISION elapsed=([\d.]+) hits=(\d+)', log)}
windows = [('closed', 1.6, 2.9), ('open', 5, 6.8), ('closed_again', 9, 10.9)]
if args.door_traversal:
    windows = [('closed', 1.6, 6.8), ('open', 9, 11.8), ('closed_again', 14, 15.9)]
door_windows = {name: [hits for when, hits in sorted(door_collision.items()) if low <= when < high]
                for name, low, high in windows}
door_clocks = {group: [(float(m[1]), m[2] == 'true') for m in re.finditer(
    r'OPENOBLIVION_DOOR_CLOCK group=' + group + r' elapsed=[\d.]+ time=([\d.]+) playing=(true|false)', log)]
    for group in ('open', 'close')}
doors_verified = (all(door_windows.values()) and 'Lua error:' not in log
    and 'OPENOBLIVION_DOOR_CYCLE_DONE' in log and 'OPENOBLIVION_DOOR busy sequence=' in log
    and 'OPENOBLIVION_DOOR swing sequence=Open' in log and 'OPENOBLIVION_DOOR swing sequence=Close' in log
    and 'OPENOBLIVION_DOOR toggle enabled=' not in log
    and min(door_windows['closed']) > 0
    and max(door_windows['open']) * 2 < min(door_windows['closed'])
    and abs(min(door_windows['closed_again']) - min(door_windows['closed'])) <= 2
    and all(any(playing for _, playing in samples)
            and any(not playing and abs(time - 1.3666667) < 0.03 for time, playing in samples)
            for samples in door_clocks.values()))
if args.tes4_doors and not doors_verified: complete = False
door_body_by_time = {float(m[1]): (float(m[1]), float(m[2]), float(m[3]), float(m[4]), m[5] == 'true')
            for m in re.finditer(r'OPENOBLIVION_DOOR_BODY elapsed=([\d.]+) x=([\d.eE+-]+) y=([\d.eE+-]+) z=([\d.eE+-]+) grounded=(true|false)', log)}
door_body = [row for _, row in sorted(door_body_by_time.items())]
door_blocked = [row for row in door_body if 5.5 <= row[0] < 6.8]
door_crossed = [row for row in door_body if 10 <= row[0] < 11.8]
door_traversal_verified = (bool(door_blocked) and bool(door_crossed)
    and all(row[2] < 0 and row[4] for row in door_blocked)
    and max(row[2] for row in door_blocked) - min(row[2] for row in door_blocked) < 1
    and all(row[2] > 50 for row in door_crossed))
if args.door_traversal and not door_traversal_verified: complete = False
audio_verified = ('OPENOBLIVION_DOOR_AUDIO open playing=true' in log
                  and 'OPENOBLIVION_DOOR_AUDIO close playing=true' in log
                  and (output / 'door-audio.wav').is_file()
                  and (output / 'door-audio.wav').stat().st_size > 44)
if args.audio_capture and not audio_verified: complete = False
repair_activated = 'OPENOBLIVION_CAMERA_REPAIR activated:' in log
motion = re.search(r'OPENOBLIVION_CAMERA_MOTION distance=([\d.eE+-]+) camera_player_distance=([\d.eE+-]+) yaw=([\d.eE+-]+)', log)
motion_verified = bool(motion and float(motion[1]) > 1 and float(motion[2]) < 256 and abs(float(motion[3])) > 0.1)
if args.camera_motion and not motion_verified: complete = False
if args.camera_repair and args.missing_player_model and not repair_activated: complete = False
movement = analyze_movement(log) if args.player_movement else None
if movement is not None and not movement['trajectory_complete']: complete = False
metrics = {'schema': 1, 'stock_engine_returncode': result.returncode, 'probe_complete': complete,
           'audio_capture_enabled': args.audio_capture, 'door_audio_playback_verified': audio_verified,
           'tes4_doors_enabled': args.tes4_doors, 'tes4_doors_verified': doors_verified,
           'door_traversal_enabled': args.door_traversal, 'door_traversal_verified': door_traversal_verified,
           'door_body_samples': len(door_body), 'door_body_blocked_samples': door_blocked,
           'door_body_crossed_samples': door_crossed,
           'tes4_door_collision_windows': door_windows,
           'tes4_animation_enabled': args.tes4_animation,
           'tes4_animation_verified': animation_verified,
           'tes4_animation_observations': animation_observations,
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
           'bounded_visual_slice': bool(scene_data), 'complete_installed_data': args.installed_data,
           'phone_qa_enabled': args.phone_qa,
           'tes4_interactions_enabled': args.tes4_interactions,
           'tes4_interactions_verified': interactions_verified,
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
if args.tes4_doors:
    probe_sources += [ROOT / 'tools/upstream/tes4_doors_probe.omwscripts',
                      ROOT / 'tools/upstream/scripts/openoblivion_tes4_doors_global.lua',
                      ROOT / 'tools/upstream/scripts/openoblivion_tes4_doors_local.lua',
                      ROOT / 'tools/upstream/scripts/openoblivion_tes4_doors_player.lua',
                      ROOT / 'tools/android/build_personal.py']
if args.tes4_animation:
    probe_sources += [ROOT / 'tools/upstream/tes4_animation_probe.omwscripts',
                      ROOT / 'tools/upstream/scripts/openoblivion_tes4_animation_global.lua',
                      ROOT / 'tools/upstream/scripts/openoblivion_tes4_animation_actor.lua',
                      ROOT / 'tools/upstream/scripts/openoblivion_tes4_animation_player.lua']
if args.tes4_interactions:
    probe_sources += [ROOT / 'tools/upstream/tes4_interactions_probe.omwscripts',
                      ROOT / 'tools/upstream/scripts/openoblivion_tes4_interactions_probe.lua',
                      ROOT / 'tools/upstream/scripts/openoblivion_tes4_interactions_close_probe.lua',
                      ROOT / 'tools/android/container.omwscripts',
                      ROOT / 'tools/android/scripts/openoblivion_container.lua',
                      ROOT / 'tools/android/scripts/openoblivion_container_items.lua',
                      ROOT / 'tools/android/scripts/openoblivion_container_ui.lua']
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
if args.player_collision_model:
    failed = "Failed to load 'meshes/basicplayer.osgt'" in log
    metrics['player_collision_model'] = {'path': str(player_model),
        'sha256': hashlib.sha256(player_model.read_bytes()).hexdigest(), 'load_failed': failed,
        'settings_rewrite_sha256': hashlib.sha256((ROOT / 'tools/android/build_personal.py').read_bytes()).hexdigest()}
    complete = complete and not failed
    metrics['probe_complete'] = complete
metrics['authored_collision_enabled'] = args.tes4_doors or args.authored_collision
metrics['original_body_enabled'] = args.original_body
metrics['tes4_movement_enabled'] = args.tes4_movement
metrics['tes4_player_enabled'] = args.tes4_player
body_logged = 'OpenOblivion original TES4 player body: half extents' in log
metrics['original_body_logged'] = body_logged
if body_logged != args.original_body:
    complete = False
    metrics['probe_complete'] = complete
if args.async_physics_threads is not None:
    metrics['async_physics_threads'] = args.async_physics_threads
if args.movement_fixture:
    metrics['fixture_files_sha256'] = {p.relative_to(fixture_data).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in fixture_data.rglob('*') if p.is_file()}
(output / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
print('Private upstream scene probe complete=' + str(complete))
sys.exit(0 if complete else 1)
