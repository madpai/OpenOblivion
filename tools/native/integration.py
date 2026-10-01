#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Apply the audited camera-only patch externally and record a native build."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CAMERA = 'apps/openmw/mwrender/'
BASES = {
    '46bd4599203ee52ffc0f3e8edb3fc159a0303a49': {
        'camera.cpp': '73231f097e9fac31b3a5dc99a5263d573651480f02cffbd9a31aacf56c7b5520',
        'camera.hpp': 'a2a5b4062f206cfa219077eded71b4a0fc6d7863a1cac99a4448b784c70e72af'},
    'f4bec41444214a7903bebd178389ca22ca13f646': {
        'camera.cpp': '9cf61eaf668587c09aea7980c4f837b03c613c988f7848e25d969e97be6d1ed0',
        'camera.hpp': '1c324020ec251055fbf48428264862fe35202ac33883d3f0e55d31d10b309d2b'},
}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def external(path):
    path = path.expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError('Native source, binaries and evidence must stay outside the public checkout')
    return path


def tools_identity():
    return {p.relative_to(ROOT).as_posix(): digest(p)
            for p in (Path(__file__), HERE / 'grounded_eye.hpp', HERE / 'camera_grounded_eye.patch')}


def apply(source, revision):
    stamp = source / '.openoblivion-native-source.json'
    if stamp.exists():
        raise ValueError('Source already has an integration record; use a fresh external checkout')
    for name, sha in BASES[revision].items():
        if digest(source / CAMERA / name) != sha:
            raise ValueError('Unaudited camera input: ' + name)
    if (source / CAMERA / 'openoblivion_grounded_eye.hpp').exists():
        raise ValueError('Native header already exists')
    patch = (HERE / 'camera_grounded_eye.patch').read_bytes()
    command = ['patch', '-p1', '--batch', '--forward', '--fuzz=0']
    subprocess.run(command + ['--dry-run'], input=patch, cwd=source, check=True)
    subprocess.run(command, input=patch, cwd=source, check=True)
    shutil.copyfile(HERE / 'grounded_eye.hpp', source / CAMERA / 'openoblivion_grounded_eye.hpp')
    files = [CAMERA + n for n in ('camera.cpp', 'camera.hpp', 'openoblivion_grounded_eye.hpp')]
    record = {'schema': 1, 'base_revision': revision, 'tools_sha256': tools_identity(),
              'source_sha256': {n: digest(source / n) for n in files}}
    stamp.write_text(json.dumps(record, indent=2) + '\n')
    return record


def record_build(source, binary, output):
    record = json.loads((source / '.openoblivion-native-source.json').read_text())
    if record['tools_sha256'] != tools_identity():
        raise ValueError('Integration tools have changed since source preparation')
    for name, sha in record['source_sha256'].items():
        if digest(source / name) != sha:
            raise ValueError('Native integration source changed: ' + name)
    record.update(engine_sha256=digest(binary), engine_bytes=binary.stat().st_size,
                  engine_kind='openoblivion-native-integration',
                  environment_switch='OPENOBLIVION_GROUNDED_EYE=1',
                  scope='Camera-only native build; device validation requires separate evidence')
    if output.exists():
        raise ValueError('Build evidence already exists')
    output.write_text(json.dumps(record, indent=2) + '\n')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('apply', 'record'))
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--revision', choices=BASES)
    parser.add_argument('--binary', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    source = external(args.source)
    if args.action == 'apply':
        if not args.revision:
            parser.error('apply requires --revision')
        result = apply(source, args.revision)
    else:
        if not args.binary or not args.output:
            parser.error('record requires --binary and --output')
        result = record_build(source, external(args.binary), external(args.output))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
