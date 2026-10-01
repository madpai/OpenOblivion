#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Fail closed on game assets and binary files in prospective Git content."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import re

BLOCKED = set('esm esp esl bsa ba2 nif kf hkx dds wav mp3 ogg flac fuz lip exe dll '
              'oalmap oalasset apk aab so a zip 7z rar tar gz xz png jpg jpeg webp gif '
              'mp4 webm sqlite db'.split())
MAGIC = (b'BSA\0', b'DDS ', b'TES4', b'Gamebryo File Format', b'NetImmerse File Format',
         b'MZ', b'\x7fELF', b'PK\x03\x04', b'RIFF', b'OggS', b'\x89PNG')
MEDIA_MANIFEST = 'docs/media/screenshots.json'


def approved_images(data):
    """An exact, reviewed documentation screenshot allowlist, not an asset glob."""
    if data is None: return {}
    manifest = json.loads(data)
    if manifest.get('schema') != 1 or not isinstance(manifest.get('screenshots'), list):
        raise ValueError('Invalid screenshot provenance manifest')
    if len(manifest['screenshots']) > 10:
        raise ValueError('Too many approved documentation screenshots')
    result = {}
    for entry in manifest['screenshots']:
        name = entry.get('path', '')
        if (not re.fullmatch(r'docs/media/[a-z0-9-]+\.(jpg|png)', name)
                or name in result or entry.get('kind') != 'runtime-screenshot'
                or entry.get('scope') != 'documentation'
                or not isinstance(entry.get('bytes'), int) or not 0 < entry['bytes'] <= 2*1024*1024
                or not re.fullmatch(r'[0-9a-f]{64}', entry.get('sha256', ''))
                or not entry.get('publication_authorization') or not entry.get('provenance')):
            raise ValueError('Invalid approved documentation screenshot')
        result[name] = entry
    return result


def reason(name, data, symlink=False, images=None):
    parts = PurePosixPath(name.lower()).parts
    if any(p in ('data', 'data files', 'extracted', 'private', 'game-data') for p in parts):
        return 'private/game-data directory'
    if symlink:
        return 'symlinks are not public fixtures'
    if name in (images or {}):
        entry = images[name]
        valid_magic = data.startswith(b'\xff\xd8\xff') if name.endswith('.jpg') else data.startswith(b'\x89PNG\r\n\x1a\n')
        if len(data) == entry['bytes'] and valid_magic and hashlib.sha256(data).hexdigest() == entry['sha256']:
            return None
        return 'documentation screenshot differs from its reviewed hash/size/type'
    if PurePosixPath(name.lower()).suffix.lstrip('.') in BLOCKED:
        return 'game asset, binary or archive extension'
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
    def media(data, scope):
        try:
            return approved_images(data)
        except (ValueError, TypeError, AttributeError):
            errors.append((MEDIA_MANIFEST, scope + ': invalid screenshot provenance manifest'))
            return {}
    index_entries = git('ls-files', '-s', '-z').split(b'\0')
    index_media = None
    for entry in index_entries:
        if not entry: continue
        meta, rawname = entry.split(b'\t', 1)
        mode, oid, stage = meta.decode().split()
        if rawname.decode() == MEDIA_MANIFEST and mode == '100644' and stage == '0':
            index_media = git('cat-file', 'blob', oid)
    index_images = media(index_media, 'index')
    manifest_path = root / MEDIA_MANIFEST
    work_images = media(manifest_path.read_bytes() if manifest_path.is_file() and not manifest_path.is_symlink() else None, 'worktree')
    # Check index blobs as well as working files: a clean worktree cannot hide
    # a prohibited staged version. NUL delimiters support paths with spaces.
    for entry in index_entries:
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
        why = reason(name, git('cat-file', 'blob', oid), mode == '120000', index_images)
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
        why = reason(name, b'' if path.is_symlink() else path.read_bytes(), path.is_symlink(), work_images)
        if why:
            errors.append((name, 'worktree: ' + why))
    if history:
        for commit in git('rev-list', '--all').decode().splitlines():
            entries = git('ls-tree', '-r', '-z', commit).split(b'\0')
            history_media = None
            for entry in entries:
                if not entry: continue
                meta, rawname = entry.split(b'\t', 1)
                mode, kind, oid = meta.decode().split()
                if rawname.decode() == MEDIA_MANIFEST and mode == '100644' and kind == 'blob':
                    history_media = git('cat-file', 'blob', oid)
            history_images = media(history_media, 'history')
            for entry in entries:
                if not entry:
                    continue
                meta, rawname = entry.split(b'\t', 1)
                mode, kind, oid = meta.decode().split()
                name = rawname.decode()
                if kind != 'blob':
                    errors.append((name, 'history: unreviewed submodule'))
                    continue
                why = reason(name, git('cat-file', 'blob', oid), mode == '120000', history_images)
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
