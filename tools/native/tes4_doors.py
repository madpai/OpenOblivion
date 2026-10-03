#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Apply hash-locked embedded TES4 door clips and keyframed-box collision."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from tes4_animation import REVISIONS, digest, external, validate_tools as validate_animation_tools

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
STAMP = '.openoblivion-tes4-doors.json'
PARENTS = ('.openoblivion-tes4-animation.json', '.openoblivion-authored-collision.json')
HEADERS = {
    'tes4_sequences.hpp': 'components/nifosg/openoblivion_tes4_sequences.hpp',
    'animated_boxes.hpp': 'components/nifbullet/openoblivion_animated_boxes.hpp',
}
OVERLAP = {'components/nifosg/nifloader.cpp', 'components/nifosg/openoblivion_tes4_kf.hpp'}
COLLISION = 'components/nifbullet/bulletnifloader.cpp'


def tools_identity(revision):
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in
            (Path(__file__), HERE / 'tes4_doors.lock.json',
             HERE / ('tes4_doors_' + REVISIONS[revision] + '.patch'),
             *(HERE / name for name in HEADERS))}


def validate_tools(record):
    if record['tools_sha256'] != tools_identity(record['base_revision']):
        raise ValueError('Door integration tools have changed')


def validate_parents(source, revision, inputs):
    animation = json.loads((source / PARENTS[0]).read_text())
    collision = json.loads((source / PARENTS[1]).read_text())
    validate_animation_tools(animation)
    if animation['base_revision'] != revision or collision['base_revision'] != revision:
        raise ValueError('Door predecessor revisions disagree')
    for name, expected in animation['source_sha256'].items():
        if name in OVERLAP:
            if inputs[name] != expected:
                raise ValueError('Door adapter does not extend the recorded animation')
        elif digest(source / name) != expected:
            raise ValueError('Unrelated animation source changed: ' + name)
    from tes4_interactions import validate_tools as validate_interactions
    predecessor = source / '.openoblivion-tes4-interactions.json'
    interactions = json.loads(predecessor.read_text())
    validate_interactions(interactions)
    actor = 'apps/openmw/mwrender/esm4npcanimation.cpp'
    if (digest(predecessor) != animation['predecessor_sha256']
            or interactions['base_revision'] != revision
            or interactions['source_sha256'][actor] != animation['input_sha256'][actor]):
        raise ValueError('Door animation ancestry changed')
    for name, expected in interactions['source_sha256'].items():
        if name != actor and digest(source / name) != expected:
            raise ValueError('Unrelated interaction source changed: ' + name)
    from authored_collision import BASES, HEADER
    base = BASES[revision]
    if (collision['loader_sha256_before'] != base['loader_sha256']
            or inputs[COLLISION] != collision['loader_sha256_after']
            or collision['patch'] != 'tools/native/' + base['patch']
            or collision['patch_sha256'] != digest(HERE / base['patch'])
            or collision['header_sha256'] != digest(HERE / 'authored_strips.hpp')
            or digest(source / HEADER) != collision['header_sha256']):
        raise ValueError('Fixed-strip collision ancestry changed')


def apply(source, revision):
    if (source / STAMP).exists():
        return verify(source)
    from tes4_animation import verify as verify_animation
    verify_animation(source)
    inputs = json.loads((HERE / 'tes4_doors.lock.json').read_text())[REVISIONS[revision]]
    validate_parents(source, revision, inputs)
    if any((source / name).exists() for name in HEADERS.values()):
        raise ValueError('Door header exists without a receipt')
    with tempfile.TemporaryDirectory(prefix='openoblivion-doors-') as tmp:
        stage = Path(tmp)
        for name, expected in inputs.items():
            if digest(source / name) != expected:
                raise ValueError('Unaudited door input: ' + name)
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, target)
        patch = (HERE / ('tes4_doors_' + REVISIONS[revision] + '.patch')).read_bytes()
        command = ['patch', '-p1', '--batch', '--forward', '--fuzz=0']
        subprocess.run(command + ['--dry-run'], input=patch, cwd=stage, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(command, input=patch, cwd=stage, check=True, stdout=subprocess.DEVNULL)
        for name, destination in HEADERS.items():
            shutil.copyfile(HERE / name, stage / destination)
        names = [*inputs, *HEADERS.values()]
        record = {'schema': 1, 'base_revision': revision, 'input_sha256': inputs,
                  'predecessor_sha256': {name: digest(source / name) for name in PARENTS},
                  'tools_sha256': tools_identity(revision),
                  'source_sha256': {name: digest(stage / name) for name in names}}
        for name in names:
            shutil.copyfile(stage / name, source / name)
        (source / STAMP).write_text(json.dumps(record, indent=2) + '\n')
    return record


def verify(source):
    record = json.loads((source / STAMP).read_text())
    revision = record['base_revision']
    validate_tools(record)
    inputs = json.loads((HERE / 'tes4_doors.lock.json').read_text())[REVISIONS[revision]]
    if (record['input_sha256'] != inputs or record['predecessor_sha256']
            != {name: digest(source / name) for name in PARENTS}):
        raise ValueError('Door predecessor changed')
    validate_parents(source, revision, inputs)
    if set(record['source_sha256']) != {*inputs, *HEADERS.values()}:
        raise ValueError('Door receipt has an incomplete source set')
    for name, expected in record['source_sha256'].items():
        if digest(source / name) != expected:
            raise ValueError('Door source changed: ' + name)
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
            raise ValueError('Native build and door revisions disagree')
        build['tes4_doors'] = record
        build['engine_sha256'] = digest(binary)
        build['engine_bytes'] = binary.stat().st_size
        if 'native_sha256' in build:
            if binary.name != 'libopenmw.so':
                raise ValueError('Android record requires libopenmw.so')
            build['native_sha256']['libopenmw.so'] = digest(binary)
        build['scope'] = ('Native camera/static strips, TES4 inspection/NPC idle and embedded '
                          'door sequences with authored keyframed boxes; full gameplay remains incomplete.')
        manifest.write_text(json.dumps(build, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
