#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Record private identity, native scanner output, elapsed time and peak RSS."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--executable', required=True, type=Path)
parser.add_argument('--plugin', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path, help='Fresh directory outside the checkout')
args = parser.parse_args()
output = args.output.expanduser().resolve()
if output == ROOT or ROOT in output.parents:
    parser.error('Raw content reports must be outside the public checkout')
if output.exists():
    parser.error('Output directory already exists; preserve previous evidence')
plugin = args.plugin.expanduser().resolve(strict=True)
exe = args.executable.expanduser().resolve(strict=True)
digest = hashlib.sha256()
with plugin.open('rb') as source:
    for chunk in iter(lambda: source.read(1024 * 1024), b''):
        digest.update(chunk)
output.mkdir(parents=True)
start = time.monotonic()
try:
    run = subprocess.run([str(exe), str(plugin)], capture_output=True, text=True, timeout=120)
except subprocess.TimeoutExpired as error:
    (output / 'failure.txt').write_text(str(error))
    sys.exit(1)
elapsed = time.monotonic() - start
(output / 'stdout.txt').write_text(run.stdout)
(output / 'stderr.txt').write_text(run.stderr)
metrics = {
    'schema': 1,
    'input_path': str(plugin),
    'input_sha256': digest.hexdigest(),
    'executable_path': str(exe),
    'executable_sha256': hashlib.sha256(exe.read_bytes()).hexdigest(),
    'returncode': run.returncode,
    'elapsed_seconds': round(elapsed, 4),
    'max_rss_kib_linux': resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
    'scope': 'Container/subrecord scanning; not world rendering or gameplay',
}
if run.returncode == 0:
    try:
        metrics['summary'] = json.loads(run.stdout)
    except json.JSONDecodeError:
        metrics['report_error'] = 'Native stdout was not a JSON summary'
        run.returncode = 1
metrics['returncode'] = run.returncode
(output / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
print('Private scan evidence recorded; exit status ' + str(run.returncode))
sys.exit(run.returncode)
