#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Fetch a pinned research dependency outside the public checkout."""
import argparse
import json
from pathlib import Path
import subprocess
from check_upstream import ROOT, check

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cache', type=Path, required=True)
parser.add_argument('--project', choices=('openmw', 'example-suite'), default='openmw')
args = parser.parse_args()
cache = args.cache.expanduser().resolve()
if cache == ROOT or ROOT in cache.parents:
    parser.error('The dependency cache must be outside the public checkout')
dest = cache / args.project
key = 'OpenMW/' + args.project
lock = json.loads((ROOT / 'docs/research/upstreams.lock.json').read_text())[key]
if not dest.exists():
    dest.mkdir(parents=True)
    subprocess.run(['git', 'init', str(dest)], check=True)
    subprocess.run(['git', '-C', str(dest), 'remote', 'add', 'origin', lock['url']], check=True)
    subprocess.run(['git', '-C', str(dest), 'fetch', '--depth', '1', 'origin', lock['revision']], check=True)
    subprocess.run(['git', '-C', str(dest), 'checkout', '--detach', 'FETCH_HEAD'], check=True)
print('Verified ' + key + ' ' + check(dest, key))
print(dest)
