#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Fetch the pinned OpenMW commit outside the public checkout."""
import argparse
import json
from pathlib import Path
import subprocess
from check_upstream import ROOT, check

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cache', type=Path, required=True)
args = parser.parse_args()
cache = args.cache.expanduser().resolve()
if cache == ROOT or ROOT in cache.parents:
    parser.error('The dependency cache must be outside the public checkout')
dest = cache / 'openmw'
lock = json.loads((ROOT / 'docs/research/upstreams.lock.json').read_text())['OpenMW/openmw']
if not dest.exists():
    dest.mkdir(parents=True)
    subprocess.run(['git', 'init', str(dest)], check=True)
    subprocess.run(['git', '-C', str(dest), 'remote', 'add', 'origin', lock['url']], check=True)
    subprocess.run(['git', '-C', str(dest), 'fetch', '--depth', '1', 'origin', lock['revision']], check=True)
    subprocess.run(['git', '-C', str(dest), 'checkout', '--detach', 'FETCH_HEAD'], check=True)
print('Verified OpenMW ' + check(dest))
print(dest)

