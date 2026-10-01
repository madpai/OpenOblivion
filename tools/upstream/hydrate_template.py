#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Materialize only the audited template's public game data from locked LFS pointers.

Uses GitLab's revision-specific raw endpoint; no Git LFS implementation copied.
Assets remain outside the public OpenOblivion checkout.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from check_upstream import LFS_POINTER, check

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
args = parser.parse_args()
source = args.source.expanduser().resolve(strict=True)
if source == ROOT or ROOT in source.parents:
    parser.error('Template data must remain outside OpenOblivion')
revision = check(source, 'OpenMW/example-suite')
names = subprocess.check_output(['git', '-C', str(source), 'ls-tree', '-r', '--name-only', revision,
                                 '--', 'game_template/data'], text=True).splitlines()
hydrated = 0
for name in names:
    original = subprocess.check_output(['git', '-C', str(source), 'show', revision + ':' + name])
    pointer = LFS_POINTER.fullmatch(original)
    if not pointer or (source / name).read_bytes() != original:
        continue
    size = int(pointer[2])
    if size > 64 * 1024 * 1024:
        raise ValueError('Template object exceeds authored 64 MiB download budget')
    url = ('https://gitlab.com/OpenMW/example-suite/-/raw/' + revision + '/'
           + urllib.parse.quote(name, safe='/'))
    with urllib.request.urlopen(url, timeout=30) as response:
        content = response.read(size + 1)
    if len(content) != size or hashlib.sha256(content).hexdigest() != pointer[1].decode():
        raise ValueError('Template LFS size/hash mismatch: ' + name)
    (source / name).write_bytes(content)
    hydrated += 1
check(source, 'OpenMW/example-suite')
print('Verified public template; hydrated objects=' + str(hydrated))
