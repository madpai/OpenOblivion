#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Apply the hash-locked, opt-in measured classic TES4 player body."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from tes4_animation import REVISIONS, digest, external

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
STAMP = '.openoblivion-tes4-body.json'
PARENT = '.openoblivion-tes4-doors.json'
HEADERS = {'tes4_body.hpp': 'apps/openmw/mwphysics/openoblivion_tes4_body.hpp'}


def tools_identity(revision):
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in
            (Path(__file__), HERE / 'tes4_body.lock.json',
             HERE / ('tes4_body_' + REVISIONS[revision] + '.patch'),
             *(HERE / name for name in HEADERS))}


def validate_parent(source, revision, inputs):
    from tes4_doors import verify as verify_doors
    doors = verify_doors(source)
    if doors['base_revision'] != revision:
        raise ValueError('Body and door revisions disagree')
    if set(inputs) & set(doors['source_sha256']):
        raise ValueError('Body input overlaps the door receipt')


def apply(source, revision):
    if (source / STAMP).exists():
        return verify(source)
    inputs = json.loads((HERE / 'tes4_body.lock.json').read_text())[REVISIONS[revision]]
    validate_parent(source, revision, inputs)
    if any((source / name).exists() for name in HEADERS.values()):
        raise ValueError('Body header exists without a receipt')
    with tempfile.TemporaryDirectory(prefix='openoblivion-body-') as tmp:
        stage = Path(tmp)
        for name, expected in inputs.items():
            if digest(source / name) != expected:
                raise ValueError('Unaudited body input: ' + name)
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, target)
        patch = (HERE / ('tes4_body_' + REVISIONS[revision] + '.patch')).read_bytes()
        command = ['patch', '-p1', '--batch', '--forward', '--fuzz=0']
        subprocess.run(command + ['--dry-run'], input=patch, cwd=stage, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(command, input=patch, cwd=stage, check=True, stdout=subprocess.DEVNULL)
        for name, destination in HEADERS.items():
            (stage / destination).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(HERE / name, stage / destination)
        names = [*inputs, *HEADERS.values()]
        record = {'schema': 1, 'base_revision': revision, 'input_sha256': inputs,
                  'predecessor_sha256': digest(source / PARENT),
                  'tools_sha256': tools_identity(revision),
                  'source_sha256': {name: digest(stage / name) for name in names}}
        for name in names:
            shutil.copyfile(stage / name, source / name)
        (source / STAMP).write_text(json.dumps(record, indent=2) + '\n')
    return record


def verify(source):
    record = json.loads((source / STAMP).read_text())
    revision = record['base_revision']
    if record['tools_sha256'] != tools_identity(revision):
        raise ValueError('Body integration tools have changed')
    inputs = json.loads((HERE / 'tes4_body.lock.json').read_text())[REVISIONS[revision]]
    if record['input_sha256'] != inputs or record['predecessor_sha256'] != digest(source / PARENT):
        raise ValueError('Body predecessor changed')
    validate_parent(source, revision, inputs)
    if set(record['source_sha256']) != {*inputs, *HEADERS.values()}:
        raise ValueError('Body receipt has an incomplete source set')
    for name, expected in record['source_sha256'].items():
        if digest(source / name) != expected:
            raise ValueError('Body source changed: ' + name)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('apply', 'verify', 'record'))
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--revision', choices=REVISIONS)
    parser.add_argument('--binary', type=Path)
    parser.add_argument('--manifest', type=Path)
    args = parser.parse_args()
    source = external(args.source)
    if args.action == 'apply':
        if not args.revision:
            parser.error('apply requires --revision')
        record = apply(source, args.revision)
    else:
        record = verify(source)
    if args.action == 'record':
        if not args.binary or not args.manifest:
            parser.error('record requires --binary and --manifest')
        binary, manifest = external(args.binary), external(args.manifest)
        build = json.loads(manifest.read_text())
        if build['base_revision'] != record['base_revision']:
            raise ValueError('Native build and body revisions disagree')
        build['tes4_body'] = record
        build['engine_sha256'] = digest(binary)
        build['engine_bytes'] = binary.stat().st_size
        if 'native_sha256' in build:
            if binary.name != 'libopenmw.so':
                raise ValueError('Android record requires libopenmw.so')
            build['native_sha256']['libopenmw.so'] = digest(binary)
        build['scope'] = ('Native camera/static strips, TES4 inspection/NPC idle, embedded door '
                          'sequences and the opt-in measured player body; full gameplay remains incomplete.')
        manifest.write_text(json.dumps(build, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
