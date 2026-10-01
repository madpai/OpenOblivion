#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Apply the bounded static-collision patch to an external OpenMW checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
LOADER = 'components/nifbullet/bulletnifloader.cpp'
HEADER = 'components/nifbullet/openoblivion_authored_strips.hpp'
STAMP = '.openoblivion-authored-collision.json'
BASES = {
    '46bd4599203ee52ffc0f3e8edb3fc159a0303a49': {
        'loader_sha256': 'd6eb13007b07c03e359c40f6bd29e596804b7f812167c904883779f7d342fbc2',
        'patch': 'authored_collision_desktop.patch',
    },
    'f4bec41444214a7903bebd178389ca22ca13f646': {
        'loader_sha256': '6cafec42e7f0231331656d88fdb47b730b4bb4c0e707fbd9377d200884abf2be',
        'patch': 'authored_collision_android.patch',
    },
}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def external(path):
    path = path.expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError('Native source must stay outside the public checkout')
    return path


def apply(source, revision):
    base = BASES[revision]
    loader = source / LOADER
    header = source / HEADER
    stamp = source / STAMP
    if stamp.exists() or header.exists():
        raise ValueError('Authored-collision integration is already present')
    if digest(loader) != base['loader_sha256']:
        raise ValueError('Unaudited bulletnifloader.cpp for ' + revision)
    patch = (HERE / base['patch']).read_bytes()
    command = ['patch', '-p1', '--batch', '--forward', '--fuzz=0']
    subprocess.run(command + ['--dry-run'], input=patch, cwd=source, check=True)
    subprocess.run(command, input=patch, cwd=source, check=True)
    shutil.copyfile(HERE / 'authored_strips.hpp', header)
    record = {
        'schema': 1,
        'base_revision': revision,
        'loader_sha256_before': base['loader_sha256'],
        'patch': 'tools/native/' + base['patch'],
        'patch_sha256': digest(HERE / base['patch']),
        'header_sha256': digest(header),
        'loader_sha256_after': digest(loader),
        'switch': 'OPENOBLIVION_AUTHORED_COLLISION=1',
        'scope': 'Fixed OL_STATIC bhkNiTriStripsShape only; render-mesh fallback remains',
    }
    stamp.write_text(json.dumps(record, indent=2) + '\n')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--revision', required=True, choices=BASES)
    args = parser.parse_args()
    print(json.dumps(apply(external(args.source), args.revision), indent=2))


if __name__ == '__main__':
    main()
