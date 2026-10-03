#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Original private installed-data inventory and bounded ZIP payload planner."""
import hashlib
from pathlib import Path, PurePosixPath
import zipfile

PART_BYTES = 1500 * 1024 * 1024
BASE_ARCHIVES = (
    'Oblivion - Misc.bsa', 'Oblivion - Textures - Compressed.bsa',
    'Oblivion - Meshes.bsa', 'Oblivion - Sounds.bsa',
    'Oblivion - Voices1.bsa', 'Oblivion - Voices2.bsa',
)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_paths(paths):
    seen = set()
    for file, name in paths:
        path = PurePosixPath(name)
        if (not name or path.is_absolute() or '..' in path.parts or '\\' in name
                or ':' in name or path.as_posix() != name or name.casefold() in seen):
            raise ValueError('Invalid or ambiguous payload path: ' + name)
        if file.is_symlink() or not file.is_file():
            raise ValueError('Payload input must be a regular file: ' + str(file))
        seen.add(name.casefold())


def installed_data(data):
    """Include every installed Data file, preserving bytes and relative paths.

    This is an installation snapshot, not mod discovery or load-order recovery.
    Refuse symbolic links and executable modules rather than silently omitting
    them from a package advertised as complete.
    """
    paths = []
    for file in sorted(data.rglob('*')):
        if file.is_symlink():
            raise ValueError('Installed Data contains a symbolic link: ' + str(file))
        if not file.is_file():
            continue
        if file.suffix.casefold() in ('.exe', '.dll', '.so'):
            raise ValueError('Game executables are not payload assets: ' + str(file))
        paths.append((file, 'data/' + file.relative_to(data).as_posix()))
    validate_paths(paths)
    names = {name.removeprefix('data/') for _, name in paths}
    required = {'Oblivion.esm', *BASE_ARCHIVES}
    if not required <= names:
        raise ValueError('Incomplete classic installation: ' + ', '.join(sorted(required - names)))
    archives = [*BASE_ARCHIVES, *sorted(name for name in names
                                      if '/' not in name and name.lower().endswith('.bsa')
                                      and name not in BASE_ARCHIVES)]
    # Only these measured classic plugins are enabled. Other installed plugins
    # remain packaged; this tool never guesses an owner's mod load order.
    plugins = ['Oblivion.esm', *[name for name in ('DLCShiveringIsles.esp', 'Knights.esp') if name in names]]
    return paths, archives, plugins


def partition(paths, limit=PART_BYTES):
    """Whole files in stable order, each bounded below ZIP32/Java size limits."""
    if limit <= 0:
        raise ValueError('Positive payload part limit required')
    validate_paths(paths)
    parts, part, size = [], [], 0
    for file, name in paths:
        length = file.stat().st_size
        if length > limit:
            raise ValueError('Asset exceeds a payload part limit: ' + name)
        if part and size + length > limit:
            parts.append(part); part, size = [], 0
        part.append((file, name)); size += length
    if part:
        parts.append(part)
    return parts


def write_zip(output, paths):
    validate_paths(paths)
    if output.is_symlink():
        raise ValueError('Payload output must not be a symbolic link')
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6, allowZip64=False) as archive:
        for file, name in paths:
            archive.write(file, name)
    if output.stat().st_size >= 1900 * 1024 * 1024:
        raise ValueError('Payload part exceeds the APK asset budget')
    return {'asset': output.name, 'size': output.stat().st_size, 'sha256': digest(output)}


def verify_parts(directory, manifest):
    """Stream every packaged entry against the independent source-file manifest."""
    expected = {entry['path']: entry for entry in manifest['files']}
    if len(expected) != len(manifest['files']):
        raise ValueError('Duplicate payload manifest entry')
    for part in manifest['parts']:
        name = part['asset']
        if Path(name).name != name:
            raise ValueError('Invalid payload part')
        file = directory / name
        if file.stat().st_size != part['size'] or digest(file) != part['sha256']:
            raise ValueError('Payload part digest mismatch')
        with zipfile.ZipFile(file) as archive:
            for member in archive.infolist():
                entry = expected.pop(member.filename, None)
                if entry is None or member.is_dir() or member.file_size != entry['size']:
                    raise ValueError('Unexpected or incorrect packaged file')
                with archive.open(member) as stream:
                    if hashlib.file_digest(stream, 'sha256').hexdigest() != entry['sha256']:
                        raise ValueError('Packaged asset digest mismatch: ' + member.filename)
    if expected:
        raise ValueError('Incomplete packaged payload')
