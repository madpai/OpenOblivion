#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Apply and verify the audited TES4 KF/idle integration in external sources."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REVISIONS = {
    '46bd4599203ee52ffc0f3e8edb3fc159a0303a49': 'desktop',
    'f4bec41444214a7903bebd178389ca22ca13f646': 'android',
}
STAMP = '.openoblivion-tes4-animation.json'
PREDECESSOR = '.openoblivion-tes4-interactions.json'
ACTOR = 'apps/openmw/mwrender/esm4npcanimation.cpp'
HEADERS = {
    'tes4_animation.hpp': 'components/nifosg/openoblivion_tes4_animation.hpp',
    'tes4_kf.hpp': 'components/nifosg/openoblivion_tes4_kf.hpp',
    'tes4_skin.hpp': 'apps/openmw/mwrender/openoblivion_tes4_skin.hpp',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def external(path):
    path = path.expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError('Native sources and binaries must stay external')
    return path


def tools_identity(revision):
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in
            (Path(__file__), HERE / 'tes4_animation.lock.json',
             HERE / ('tes4_animation_' + REVISIONS[revision] + '.patch'),
             *(HERE / name for name in HEADERS))}


def apply(source, revision):
    if (source / STAMP).exists():
        return verify(source)
    from tes4_interactions import verify as verify_interactions
    predecessor = verify_interactions(source)
    if predecessor['base_revision'] != revision:
        raise ValueError('Interaction and animation revisions disagree')
    inputs = json.loads((HERE / 'tes4_animation.lock.json').read_text())[REVISIONS[revision]]
    if predecessor['source_sha256'][ACTOR] != inputs[ACTOR]:
        raise ValueError('Actor input differs from the audited interaction checkpoint')
    if any((source / name).exists() for name in HEADERS.values()):
        raise ValueError('Animation header exists without a receipt')
    with tempfile.TemporaryDirectory(prefix='openoblivion-animation-') as tmp:
        stage = Path(tmp)
        for name, expected in inputs.items():
            if digest(source / name) != expected:
                raise ValueError('Unaudited animation source: ' + name)
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, target)
        patch = (HERE / ('tes4_animation_' + REVISIONS[revision] + '.patch')).read_bytes()
        command = ['patch', '-p1', '--batch', '--forward', '--fuzz=0']
        subprocess.run(command + ['--dry-run'], input=patch, cwd=stage, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(command, input=patch, cwd=stage, check=True, stdout=subprocess.DEVNULL)
        for name, destination in HEADERS.items():
            shutil.copyfile(HERE / name, stage / destination)
        names = [*inputs, *HEADERS.values()]
        record = {'schema': 1, 'base_revision': revision, 'input_sha256': inputs,
                  'predecessor_sha256': digest(source / PREDECESSOR),
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
        raise ValueError('Animation tools have changed')
    inputs = json.loads((HERE / 'tes4_animation.lock.json').read_text())[REVISIONS[revision]]
    if record['input_sha256'] != inputs or record['predecessor_sha256'] != digest(source / PREDECESSOR):
        raise ValueError('Animation predecessor has changed')
    predecessor = json.loads((source / PREDECESSOR).read_text())
    from tes4_interactions import validate_tools
    validate_tools(predecessor)
    if predecessor['base_revision'] != revision or predecessor['source_sha256'][ACTOR] != inputs[ACTOR]:
        raise ValueError('Animation does not extend the recorded actor source')
    if set(record['source_sha256']) != {*inputs, *HEADERS.values()}:
        raise ValueError('Animation receipt has an incomplete source set')
    for name, expected in record['source_sha256'].items():
        if digest(source / name) != expected:
            raise ValueError('Animation source has changed: ' + name)
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
            raise ValueError('Native build and animation revisions disagree')
        build['tes4_animation'] = record
        build['engine_sha256'] = digest(binary)
        build['engine_bytes'] = binary.stat().st_size
        if 'native_sha256' in build:
            if binary.name != 'libopenmw.so':
                raise ValueError('Android record requires libopenmw.so')
            build['native_sha256']['libopenmw.so'] = digest(binary)
        build['scope'] = ('Native camera/static collision, TES4 inspection, shared skinning and '
                          'TES4 transform KF decoding/default NPC idle; full gameplay remains incomplete.')
        manifest.write_text(json.dumps(build, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
