#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Fail closed on game assets and binary files in prospective Git content."""
import argparse
from pathlib import Path, PurePosixPath
import subprocess
import sys

BLOCKED = set('esm esp esl bsa ba2 nif kf hkx dds wav mp3 ogg flac fuz lip exe dll '
              'oalmap oalasset apk aab so a zip 7z rar tar gz xz png jpg jpeg webp gif '
              'mp4 webm sqlite db'.split())
MAGIC = (b'BSA\0', b'DDS ', b'TES4', b'Gamebryo File Format', b'NetImmerse File Format',
         b'MZ', b'\x7fELF', b'PK\x03\x04', b'RIFF', b'OggS', b'\x89PNG')


def reason(name, data, symlink=False):
    parts = PurePosixPath(name.lower()).parts
    if any(p in ('data', 'data files', 'extracted', 'private', 'game-data') for p in parts):
        return 'private/game-data directory'
    if PurePosixPath(name.lower()).suffix.lstrip('.') in BLOCKED:
        return 'game asset, binary or archive extension'
    if symlink:
        return 'symlinks are not public fixtures'
    if data.startswith(MAGIC):
        return 'game/binary magic signature'
    if b'\0' in data:
        return 'binary content'
    try:
        data.decode('utf-8')
    except UnicodeDecodeError:
        return 'non-UTF-8 content'
    return None


def check(root, history=False):
    root = Path(root).resolve()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args])
    errors = []
    # Check index blobs as well as working files: a clean worktree cannot hide
    # a prohibited staged version. NUL delimiters support paths with spaces.
    for entry in git('ls-files', '-s', '-z').split(b'\0'):
        if not entry:
            continue
        meta, rawname = entry.split(b'\t', 1)
        mode, oid, stage = meta.decode().split()
        name = rawname.decode()
        if stage != '0':
            errors.append((name, 'unmerged index'))
            continue
        if mode == '160000':
            errors.append((name, 'unreviewed submodule'))
            continue
        why = reason(name, git('cat-file', 'blob', oid), mode == '120000')
        if why:
            errors.append((name, 'index: ' + why))
    names = git('ls-files', '--cached', '--others', '--exclude-standard', '-z').split(b'\0')
    for rawname in set(names):
        if not rawname:
            continue
        name = rawname.decode()
        path = root / name
        if not path.exists() and not path.is_symlink():
            continue
        if path.is_dir():
            errors.append((name, 'directory/submodule'))
            continue
        why = reason(name, b'' if path.is_symlink() else path.read_bytes(), path.is_symlink())
        if why:
            errors.append((name, 'worktree: ' + why))
    if history:
        for commit in git('rev-list', '--all').decode().splitlines():
            for entry in git('ls-tree', '-r', '-z', commit).split(b'\0'):
                if not entry:
                    continue
                meta, rawname = entry.split(b'\t', 1)
                mode, kind, oid = meta.decode().split()
                name = rawname.decode()
                if kind != 'blob':
                    errors.append((name, 'history: unreviewed submodule'))
                    continue
                why = reason(name, git('cat-file', 'blob', oid), mode == '120000')
                if why:
                    errors.append((name, 'history: ' + why))
    return sorted(set(errors))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--history', action='store_true')
    args = parser.parse_args()
    try:
        errors = check(args.root, args.history)
    except (OSError, subprocess.CalledProcessError) as error:
        print('Content guard could not inspect repository: ' + str(error), file=sys.stderr)
        sys.exit(1)
    for name, why in errors:
        print(name + ': ' + why, file=sys.stderr)
    if errors:
        sys.exit(1)
    print('Public content guard passed')

