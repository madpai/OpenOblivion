#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Apply the hash-locked, opt-in classic TES4 player grounded motion (support range, hover, landing capture)."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from tes4_animation import REVISIONS, digest, external

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
STAMP = '.openoblivion-tes4-grounded.json'
PARENT = '.openoblivion-tes4-airborne.json'
HEADERS = {'tes4_grounded.hpp': 'apps/openmw/mwphysics/openoblivion_tes4_grounded.hpp',
           'tes4_grounded_law.hpp': 'apps/openmw/mwphysics/openoblivion_tes4_grounded_law.hpp'}


def tools_identity(revision):
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in
            (Path(__file__), HERE / 'tes4_grounded.lock.json',
             HERE / ('tes4_grounded_' + REVISIONS[revision] + '.patch'),
             *(HERE / name for name in HEADERS))}


def validate_parent(source, revision, inputs):
    from tes4_airborne import verify as verify_airborne
    airborne = verify_airborne(source)
    if airborne['base_revision'] != revision:
        raise ValueError('Grounded and airborne revisions disagree')
    for receipt in source.glob('.openoblivion-*.json'):
        if receipt.name != STAMP and set(inputs) & set(json.loads(receipt.read_text()).get('source_sha256', {})):
            raise ValueError('Grounded input overlaps an earlier receipt: ' + receipt.name)


def apply(source, revision):
    if (source / STAMP).exists():
        return verify(source)
    inputs = json.loads((HERE / 'tes4_grounded.lock.json').read_text())[REVISIONS[revision]]
    validate_parent(source, revision, inputs)
    if any((source / name).exists() for name in HEADERS.values()):
        raise ValueError('Grounded header exists without a receipt')
    with tempfile.TemporaryDirectory(prefix='openoblivion-grounded-') as tmp:
        stage = Path(tmp)
        for name, expected in inputs.items():
            if digest(source / name) != expected:
                raise ValueError('Unaudited grounded input: ' + name)
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, target)
        patch = (HERE / ('tes4_grounded_' + REVISIONS[revision] + '.patch')).read_bytes()
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
        raise ValueError('Grounded integration tools have changed')
    inputs = json.loads((HERE / 'tes4_grounded.lock.json').read_text())[REVISIONS[revision]]
    if record['input_sha256'] != inputs or record['predecessor_sha256'] != digest(source / PARENT):
        raise ValueError('Grounded predecessor changed')
    validate_parent(source, revision, inputs)
    if set(record['source_sha256']) != {*inputs, *HEADERS.values()}:
        raise ValueError('Grounded receipt has an incomplete source set')
    for name, expected in record['source_sha256'].items():
        if digest(source / name) != expected:
            raise ValueError('Grounded source changed: ' + name)
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
            raise ValueError('Native build and grounded revisions disagree')
        build['tes4_grounded'] = record
        build['engine_sha256'] = digest(binary)
        build['engine_bytes'] = binary.stat().st_size
        if 'native_sha256' in build:
            if binary.name != 'libopenmw.so':
                raise ValueError('Android record requires libopenmw.so')
            build['native_sha256']['libopenmw.so'] = digest(binary)
        build['scope'] = ('Native camera/static strips, TES4 inspection/NPC idle, embedded door sequences, the measured '
                          'player body, TES4 ground speed, airborne and grounded motion; full gameplay remains incomplete.')
        manifest.write_text(json.dumps(build, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
