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

LIBRARIES = {'libopenmw.so', 'libSDL2.so', 'libGL.so', 'libopenal.so', 'libcollada-dom2.5-dp.so', 'libc++_shared.so'}


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


if __name__ == '__main__':
    unittest.main()
