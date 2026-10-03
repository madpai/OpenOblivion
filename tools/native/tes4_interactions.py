#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Apply hash-locked TES4 name/container and shared-skeleton integration."""
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
HEADER = 'apps/openmw/mwlua/types/openoblivion_tes4_bindings.hpp'
LOCK_HEADER = 'components/esm4/openoblivion_reference_locks.hpp'
STAMP = '.openoblivion-tes4-interactions.json'
ACTOR_SOURCE = 'apps/openmw/mwrender/esm4npcanimation.cpp'
# Published 0.12/0.13 tool identity. All other tool hashes must still match.
PREVIOUS_TOOL = '6b49cc0edb6e87594fa6029a0b5b357bfa1dbf40ef7f6b413a38a8dbe65ebc10'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def external(path):
    path = path.expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError('Native source and binaries must remain external')
    return path


def tools_identity(revision):
    label = REVISIONS[revision]
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in
            (Path(__file__), HERE / 'tes4_bindings.hpp', HERE / 'reference_locks.hpp', HERE / 'tes4_interactions.lock.json',
             HERE / ('tes4_interactions_' + label + '.patch'))}


def validate_tools(record):
    expected = tools_identity(record['base_revision'])
    actual = record['tools_sha256']
    previous = dict(expected, **{'tools/native/tes4_interactions.py': PREVIOUS_TOOL})
    if actual not in (expected, previous):
        raise ValueError('Interaction tools have changed')


def remove_partial(text):
    # Only used after a complete input hash matches the interrupted handoff.
    for line in (
        '        constexpr std::string_view ESM4Creature = "ESM4Creature";\n',
        '        constexpr std::string_view ESM4Npc = "ESM4Npc";\n',
        '            { ESM::REC_CREA4, ObjectTypeName::ESM4Creature },\n',
        '            { ESM::REC_NPC_4, ObjectTypeName::ESM4Npc },\n',
        '        addESM4CreatureBindings(addType(ObjectTypeName::ESM4Creature, { ESM::REC_CREA4 }), context);\n',
        '        addESM4NpcBindings(addType(ObjectTypeName::ESM4Npc, { ESM::REC_NPC_4 }), context);\n',
        '    void addESM4NpcBindings(sol::table npc, const Context& context);\n',
        '    void addESM4CreatureBindings(sol::table creature, const Context& context);\n',
        '    void addESM4ContainerBindings(sol::table container, const Context& context);\n',
    ):
        text = text.replace(line, '')
    return text.replace(
        '        addESM4ContainerBindings(addType(ObjectTypeName::ESM4Container, { ESM::REC_CONT4 }), context);',
        '        addType(ObjectTypeName::ESM4Container, { ESM::REC_CONT4 });')


def apply(source, revision):
    label = REVISIONS[revision]
    locks = json.loads((HERE / 'tes4_interactions.lock.json').read_text())[label]
    stamp = source / STAMP
    if stamp.exists():
        return verify(source)
    if (source / HEADER).exists() or (source / LOCK_HEADER).exists():
        raise ValueError('Integration header exists without a receipt')
    # Stage and verify every input before changing the source tree.
    with tempfile.TemporaryDirectory(prefix='openoblivion-tes4-') as tmp:
        staged = Path(tmp)
        for name, expected in locks['base'].items():
            original = source / name
            sha = digest(original)
            if sha not in (expected, locks['grok_partial'][name]):
                raise ValueError('Unaudited interaction input: ' + name)
            text = original.read_text()
            if sha != expected:
                text = remove_partial(text)
            target = staged / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
            if digest(target) != expected:
                raise ValueError('Partial handoff cannot be normalized: ' + name)
        patch = (HERE / ('tes4_interactions_' + label + '.patch')).read_bytes()
        command = ['patch', '-p1', '--batch', '--forward', '--fuzz=0']
        subprocess.run(command + ['--dry-run'], input=patch, cwd=staged, check=True,
                       stdout=subprocess.DEVNULL)
        subprocess.run(command, input=patch, cwd=staged, check=True, stdout=subprocess.DEVNULL)
        shutil.copyfile(HERE / 'tes4_bindings.hpp', staged / HEADER)
        shutil.copyfile(HERE / 'reference_locks.hpp', staged / LOCK_HEADER)
        names = [*locks['base'], HEADER, LOCK_HEADER]
        record = {'schema': 1, 'base_revision': revision,
                  'tools_sha256': tools_identity(revision),
                  'source_sha256': {name: digest(staged / name) for name in names}}
        for name in names:
            shutil.copyfile(staged / name, source / name)
        stamp.write_text(json.dumps(record, indent=2) + '\n')
    return record


def verify(source):
    record = json.loads((source / STAMP).read_text())
    validate_tools(record)
    for name, expected in record['source_sha256'].items():
        if digest(source / name) != expected:
            if name == ACTOR_SOURCE and (source / '.openoblivion-tes4-animation.json').exists():
                from tes4_animation import verify as verify_animation
                successor = verify_animation(source)
                if successor['input_sha256'].get(name) == expected:
                    continue
            raise ValueError('Interaction source has changed: ' + name)
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
            parser.error('record requires --binary and existing camera build --manifest')
        binary, manifest = external(args.binary), external(args.manifest)
        build = json.loads(manifest.read_text())
        if build['base_revision'] != record['base_revision']:
            raise ValueError('Camera and interaction revisions disagree')
        build['tes4_interactions'] = record
        build['engine_sha256'] = digest(binary)
        build['engine_bytes'] = binary.stat().st_size
        if 'native_sha256' in build:
            if binary.name != 'libopenmw.so':
                raise ValueError('Android record requires the packaged libopenmw.so')
            build['native_sha256']['libopenmw.so'] = digest(binary)
        build['scope'] = ('Native camera filter, fixed static strips, TES4 names/base-container '
                          'snapshots and shared NPC skinning skeleton; full gameplay remains incomplete.')
        manifest.write_text(json.dumps(build, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
