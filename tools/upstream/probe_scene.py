#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Run a bounded private stock-OpenMW scene check with software OpenGL/Xvfb."""
import argparse
import hashlib
import json
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

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--build-work', required=True, type=Path, help='Container work directory containing build/openmw')
parser.add_argument('--template', required=True, type=Path, help='Pinned external OpenMW Example Suite checkout')
parser.add_argument('--data', required=True, type=Path, help="Owner's classic Oblivion Data directory")
parser.add_argument('--start', required=True, help='TES4 cell editor ID')
parser.add_argument('--output', required=True, type=Path, help='Fresh private evidence directory')
parser.add_argument('--image', default='openoblivion-research-build:founding')
args = parser.parse_args()
output = args.output.expanduser().resolve()
if output == ROOT or ROOT in output.parents:
    parser.error('Scene reports and screenshots must be outside the public checkout')
if output.exists():
    parser.error('Output directory already exists')
work = args.build_work.expanduser().resolve(strict=True)
data = args.data.expanduser().resolve(strict=True)
template = args.template.expanduser().resolve(strict=True)
check(template, 'OpenMW/example-suite')
if not (work / 'build/openmw').is_file() or not (data / 'Oblivion.esm').is_file():
    parser.error('A built stock engine and owner Oblivion.esm are required')
output.mkdir(parents=True, mode=0o700)
(output / 'runtime').mkdir(mode=0o700)
config = output / 'config'
config.mkdir()
cfg = ['replace=content', 'replace=fallback-archive',
       'resources=/work/build/resources', 'data=/template/game_template/data',
       'data=/game', 'data=/probe-data', 'content=template.omwgame',
       'content=Oblivion.esm', 'content=scene_probe.omwscripts', 'encoding=win1252']
for archive in sorted(data.glob('*.bsa')):
    if archive.name.startswith('Oblivion - '):
        cfg.append('fallback-archive=' + archive.name)
(config / 'openmw.cfg').write_text('\n'.join(cfg) + '\n')
settings = (template / 'settings.cfg').read_text()
# This setting belongs in the existing Models section of the upstream template.
settings = settings.replace('[Models]', '[Models]\nload unsupported nif files = true', 1)
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
           '--volume', f'{work}:/work:ro', '--volume', f'{data}:/game:ro',
           '--volume', f'{template}:/template:ro',
           '--volume', f'{ROOT / "tools/upstream"}:/probe-data:ro',
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
metrics = {'schema': 1, 'stock_engine_returncode': result.returncode, 'probe_complete': complete,
           'elapsed_seconds': round(time.monotonic() - start, 4), 'start_cell': args.start,
           'template_revision': check(template, 'OpenMW/example-suite'),
           'expected_engine_revision': expected_revision, 'engine_revision_matches': revision_matches,
           'observed_cell': cell_sample[2] if cell_sample else None,
           'observed_cell_id': cell_sample[1] if cell_sample else None,
           'observed_exterior': cell_sample[3] == 'true' if cell_sample else None,
           'requested_cell_matches': cell_matches,
           'docker_image_id': image_id,
           'master_sha256': hashlib.sha256((data / 'Oblivion.esm').read_bytes()).hexdigest(),
           'engine_sha256': hashlib.sha256((work / 'build/openmw').read_bytes()).hexdigest(),
           'screenshots': screens, 'scope': 'Private scene load/screenshot; software OpenGL, not Vulkan or gameplay'}
(output / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
print('Private upstream scene probe complete=' + str(complete))
sys.exit(0 if complete else 1)
