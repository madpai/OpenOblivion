#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Verify the exact upstream revision and all tracked files before building."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def check(path):
    path = Path(path).resolve()
    lock = json.loads((ROOT / 'docs/research/upstreams.lock.json').read_text())['OpenMW/openmw']
    def git(*args):
        return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()
    if git('rev-parse', '--show-toplevel') != str(path):
        raise ValueError('Expected the upstream repository root')
    if git('rev-parse', 'HEAD') != lock['revision']:
        raise ValueError('OpenMW revision differs from upstreams.lock.json')
    if git('status', '--porcelain', '--untracked-files=normal'):
        raise ValueError('OpenMW checkout is dirty; build in a separate directory')
    # Force content checks even when index stat caches or assume-unchanged hide edits.
    entries = git('ls-tree', '-r', 'HEAD').splitlines()
    for entry in entries:
        meta, name = entry.split('\t', 1)
        mode, kind, expected = meta.split()
        if kind != 'blob':
            continue
        file = path / name
        if mode == '120000':
            import os
            content = os.fsencode(os.readlink(file))
        else:
            content = file.read_bytes()
        import hashlib
        actual = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
        if actual != expected:
            raise ValueError('Modified upstream file: ' + name)
    return lock['revision']


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2:
            raise ValueError('Usage: check_upstream.py OPENMW_SOURCE')
        print('Verified OpenMW ' + check(sys.argv[1]))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
