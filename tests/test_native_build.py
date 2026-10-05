#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Original publication-receipt fixtures; no actual engine or game data."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/native'))
import prepare_android
import tes4_animation
import tes4_body
import tes4_movement
import tes4_player
import tes4_trees
import tes4_interactions

LIBRARIES = {'libopenmw.so', 'libSDL2.so', 'libGL.so', 'libopenal.so', 'libcollada-dom2.5-dp.so', 'libc++_shared.so'}


class NativeAnimationReceipt(unittest.TestCase):
    def test_chained_actor_hashes_allow_only_the_audited_successor(self):
        revision = next(iter(tes4_animation.REVISIONS))
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source, helper = root / 'source', root / 'tools'
            helper.mkdir(); source.mkdir()
            actor = tes4_animation.ACTOR
            files = {actor: b'Original changed actor fixture',
                     'components/nifosg/nifloader.cpp': b'Original loader fixture'}
            files.update({value: key.encode() for key, value in tes4_animation.HEADERS.items()})
            for path, data in files.items():
                out = source / path; out.parent.mkdir(parents=True, exist_ok=True); out.write_bytes(data)
            old_actor_hash = hashlib.sha256(b'Original previous actor fixture').hexdigest()
            inputs = {actor: old_actor_hash, 'components/nifosg/nifloader.cpp': 'a' * 64}
            (helper / 'tes4_animation.lock.json').write_text(json.dumps({'desktop': inputs}))
            predecessor = {'base_revision': revision,
                'tools_sha256': tes4_interactions.tools_identity(revision),
                'source_sha256': {actor: old_actor_hash}}
            predecessor['tools_sha256']['tools/native/tes4_interactions.py'] = tes4_interactions.PREVIOUS_TOOL
            prior = source / tes4_animation.PREDECESSOR
            prior.write_text(json.dumps(predecessor))
            identity = {'original-fixture-tool': 'b' * 64}
            record = {'schema': 1, 'base_revision': revision, 'tools_sha256': identity,
                'input_sha256': inputs, 'predecessor_sha256': tes4_animation.digest(prior),
                'source_sha256': {p: tes4_animation.digest(source / p) for p in files}}
            (source / tes4_animation.STAMP).write_text(json.dumps(record))
            with patch.object(tes4_animation, 'HERE', helper), \
                    patch.object(tes4_animation, 'tools_identity', return_value=identity):
                self.assertEqual(tes4_interactions.verify(source), predecessor)
                # A changed skin header must invalidate the whole chain.
                skin = source / tes4_animation.HEADERS['tes4_skin.hpp']
                original = skin.read_bytes(); skin.write_bytes(b'Unexpected skin source')
                with self.assertRaises(ValueError): tes4_interactions.verify(source)
                skin.write_bytes(original)
                # An edited predecessor receipt cannot be hidden by good outputs.
                prior.write_text(json.dumps(dict(predecessor, unexpected='edit')))
                with self.assertRaises(ValueError): tes4_animation.verify(source)

    def test_previous_tool_allowance_does_not_allow_other_changed_tools(self):
        revision = next(iter(tes4_animation.REVISIONS))
        record = {'base_revision': revision, 'tools_sha256': tes4_interactions.tools_identity(revision)}
        record['tools_sha256']['tools/native/tes4_interactions.py'] = tes4_interactions.PREVIOUS_TOOL
        tes4_interactions.validate_tools(record)
        record['tools_sha256']['tools/native/tes4_bindings.hpp'] = '0' * 64
        with self.assertRaises(ValueError): tes4_interactions.validate_tools(record)


class NativeBuildReceipt(unittest.TestCase):
    def fixture(self, root, *, missing_notice=False):
        source = root / 'source'
        scripts = source / 'source/buildscripts'
        engine = scripts / 'build/arm64/openmw-prefix/src/openmw'
        build = scripts / 'build/arm64/openmw-prefix/src/openmw-build'
        engine.mkdir(parents=True)
        (engine / '.openoblivion-native-source.json').write_text('{}')
        (build / 'resources').mkdir(parents=True)
        (build / 'resources/original.txt').write_text('Original public fixture resource\n')
        (build / 'defaults.bin').write_bytes(b'original fixture defaults')
        (build / 'libopenmw.so').write_bytes(b'original fixture engine')
        jni = source / 'source/app/src/main/jniLibs/arm64-v8a'
        jni.mkdir(parents=True)
        for name in LIBRARIES - {'libopenmw.so'}:
            (jni / name).write_bytes(('Original fixture ' + name).encode())
        (root / 'source-preparation.json').write_text('{}')
        (root / 'cache').mkdir()
        with zipfile.ZipFile(root / 'cache/fixture.zip', 'w') as archive:
            archive.writestr('original/LICENSE', 'Original fixture notice, GPL-3.0-only\n')
        lock = root / 'lock.json'
        lock.write_text(json.dumps({'donor_revision': 'original-fixture', 'archives': [],
            'engine_fetchcontent': [{'name': 'original', 'filename': 'fixture.zip', 'sha256': 'fixture',
                'notice_path': 'missing/LICENSE' if missing_notice else 'original/LICENSE',
                'notice_sha256': 'a' * 64}]}))
        return source, lock

    def test_complete_receipt_has_libraries_resources_and_notice(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source, lock = self.fixture(root)
            def record(source, binary, output):
                self.assertFalse((root / 'runtime/build-manifest.json').exists())
                return {'schema': 1, 'engine_sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}
            with patch.object(prepare_android, 'LOCK', lock), patch.object(prepare_android.subprocess, 'run'), \
                    patch.object(prepare_android, 'record_build', side_effect=record):
                prepare_android.stage_native(source, root, 1)
            result = json.loads((root / 'runtime/build-manifest.json').read_text())
            # In particular, notice-path iteration must never replace library names.
            self.assertEqual(set(result['native_sha256']), LIBRARIES)
            self.assertEqual(result['engine_sha256'], result['native_sha256']['libopenmw.so'])
            self.assertEqual(set(result['resources_sha256']), {'original.txt'})
            self.assertIn('Original fixture notice', (root / 'runtime/third-party-notices.txt').read_text())
            with patch.object(prepare_android, 'LOCK', lock), patch.object(prepare_android.subprocess, 'run'):
                with self.assertRaises(ValueError):
                    prepare_android.stage_native(source, root, 1)

    def test_failed_notice_assembly_never_publishes_a_receipt(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source, lock = self.fixture(root, missing_notice=True)
            with patch.object(prepare_android, 'LOCK', lock), patch.object(prepare_android.subprocess, 'run'):
                with self.assertRaises(KeyError):
                    prepare_android.stage_native(source, root, 1)
            self.assertFalse((root / 'runtime/build-manifest.json').exists())


class NativeBodyReceipt(unittest.TestCase):
    def test_tool_identity_covers_patch_header_lock_and_tool(self):
        for revision, name in tes4_body.REVISIONS.items():
            identity = tes4_body.tools_identity(revision)
            self.assertEqual(set(identity), {'tools/native/tes4_body.py', 'tools/native/tes4_body.lock.json',
                                             'tools/native/tes4_body_' + name + '.patch', 'tools/native/tes4_body.hpp'})

    def test_lock_matches_patch_targets_and_avoids_door_inputs(self):
        lock = json.loads((Path(tes4_body.HERE) / 'tes4_body.lock.json').read_text())
        doors = json.loads((Path(tes4_body.HERE) / 'tes4_doors.lock.json').read_text())
        for name in ('desktop', 'android'):
            patch_text = (Path(tes4_body.HERE) / ('tes4_body_' + name + '.patch')).read_text()
            targets = {line[6:] for line in patch_text.splitlines() if line.startswith('+++ b/')}
            self.assertEqual(targets, set(lock[name]))
            self.assertFalse(set(lock[name]) & set(doors[name]))
            self.assertIn('tes4OriginalBodyEnabled()', patch_text)

    def test_unrecorded_source_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                tes4_body.verify(Path(tmp))


class NativeMovementReceipt(unittest.TestCase):
    def test_lock_matches_patch_targets(self):
        lock = json.loads((Path(tes4_movement.HERE) / 'tes4_movement.lock.json').read_text())
        for name in ('desktop', 'android'):
            text = (Path(tes4_movement.HERE) / ('tes4_movement_' + name + '.patch')).read_text()
            self.assertEqual({l[6:] for l in text.splitlines() if l.startswith('+++ b/')}, set(lock[name]))
            self.assertIn('tes4MovementEnabled()', text)
        self.assertEqual(tes4_movement.PARENT, '.openoblivion-tes4-body.json')


class NativePlayerReceipt(unittest.TestCase):
    def test_lock_matches_patch_targets(self):
        lock = json.loads((Path(tes4_player.HERE) / 'tes4_player.lock.json').read_text())
        for name in ('desktop', 'android'):
            text = (Path(tes4_player.HERE) / ('tes4_player_' + name + '.patch')).read_text()
            self.assertEqual({l[6:] for l in text.splitlines() if l.startswith('+++ b/')}, set(lock[name]))
            self.assertIn('tes4ActorRecordFor', text)
        self.assertEqual(tes4_player.PARENT, '.openoblivion-tes4-movement.json')


class NativeTreesReceipt(unittest.TestCase):
    def test_lock_matches_patch_targets(self):
        lock = json.loads((Path(tes4_trees.HERE) / 'tes4_trees.lock.json').read_text())
        player = json.loads((Path(tes4_player.HERE) / 'tes4_player.lock.json').read_text())
        for name in ('desktop', 'android'):
            text = (Path(tes4_trees.HERE) / ('tes4_trees_' + name + '.patch')).read_text()
            self.assertEqual({l[6:] for l in text.splitlines() if l.startswith('+++ b/')}, set(lock[name]))
            self.assertIn('tes4TreesEnabled()', text)
            self.assertFalse(set(lock[name]) & set(player[name]))
        self.assertEqual(tes4_trees.PARENT, '.openoblivion-tes4-player.json')


if __name__ == '__main__':
    unittest.main()
