#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Verify the exact upstream revision and all tracked files before building."""
import json
import hashlib
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LFS_POINTER = re.compile(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n')


def check(path, key='OpenMW/openmw'):
    path = Path(path).resolve()
    lock = json.loads((ROOT / 'docs/research/upstreams.lock.json').read_text())[key]
    def git(*args):
        return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()
    if git('rev-parse', '--show-toplevel') != str(path):
        raise ValueError('Expected the upstream repository root')
    if git('rev-parse', 'HEAD') != lock['revision']:
        raise ValueError(key + ' revision differs from upstreams.lock.json')
    staged = subprocess.run(['git', '-C', str(path), 'diff', '--cached', '--quiet']).returncode
    if staged or git('ls-files', '--others', '--exclude-standard'):
        raise ValueError(key + ' checkout is dirty; build in a separate directory')
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
        actual = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
        if actual != expected:
            # Only the audited public template uses LFS. Verify materialized
            # assets against the pointer in the pinned Git object, never the index.
            if key == 'OpenMW/example-suite':
                original = subprocess.check_output(['git', '-C', str(path), 'cat-file', 'blob', expected])
                pointer = LFS_POINTER.fullmatch(original)
                if pointer and len(content) == int(pointer[2]) and hashlib.sha256(content).hexdigest() == pointer[1].decode():
                    continue
            raise ValueError('Modified upstream file: ' + name)
    return lock['revision']


if __name__ == '__main__':
    try:
        import argparse
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('source')
        parser.add_argument('--key', default='OpenMW/openmw')
        args = parser.parse_args()
        print('Verified ' + args.key + ' ' + check(args.source, args.key))
    except (KeyError, ValueError, OSError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
