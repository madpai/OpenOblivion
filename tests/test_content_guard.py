#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from content_guard import approved_images, check, reason


class ContentGuardTests(unittest.TestCase):
    def test_only_exact_reviewed_screenshot_passes(self):
        # Original synthetic signature bytes, not a copied game image.
        image = b'\xff\xd8\xfforiginal-test'
        name = 'docs/media/fixture.jpg'
        entry = dict(path=name, kind='runtime-screenshot', scope='documentation',
                     bytes=len(image), sha256=hashlib.sha256(image).hexdigest(),
                     publication_authorization='Original fixture', provenance='Original synthetic bytes')
        images = approved_images(json.dumps(dict(schema=1, screenshots=[entry])))
        self.assertIsNone(reason(name, image, images=images))
        self.assertIsNotNone(reason(name, image))
        self.assertIsNotNone(reason(name, image+b'changed', images=images))
        self.assertIsNotNone(reason('docs/media/other.jpg', image, images=images))
        self.assertIsNotNone(reason(name, image, symlink=True, images=images))
        entry['path'] = 'docs/media/game.dds'
        with self.assertRaises(ValueError):
            approved_images(json.dumps(dict(schema=1, screenshots=[entry])))

    def test_staged_media_manifest_cannot_be_hidden_by_worktree(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(['git', 'init', '-q', directory], check=True)
            root=Path(directory); (root/'docs/media').mkdir(parents=True)
            image=b'\xff\xd8\xfforiginal-test'; name='docs/media/fixture.jpg'
            entry=dict(path=name,kind='runtime-screenshot',scope='documentation',bytes=len(image),
                       sha256='0'*64,publication_authorization='Fixture',provenance='Original synthetic bytes')
            ledger=root/'docs/media/screenshots.json'
            ledger.write_text(json.dumps(dict(schema=1,screenshots=[entry])))
            (root/name).write_bytes(image)
            subprocess.run(['git','-C',directory,'add','.'],check=True)
            entry['sha256']=hashlib.sha256(image).hexdigest()
            ledger.write_text(json.dumps(dict(schema=1,screenshots=[entry])))
            self.assertTrue(any('index:' in why for _,why in check(root)))

    def test_extensions_case_and_renamed_game_data(self):
        self.assertIsNotNone(reason('docs/Oblivion.ESM', b'text'))
        self.assertIsNotNone(reason('fixtures/innocent.txt', b'BSA\0original'))
        self.assertIsNotNone(reason('fixtures/renamed.txt', b'Gamebryo File Format'))
        self.assertIsNotNone(reason('Data Files/readme.txt', b'text'))
        self.assertIsNotNone(reason('fixtures/text.txt', b'a\0b'))
        self.assertIsNone(reason('tests/test_original.py', b'# Original fixture generator\n'))

    def test_staged_blob_cannot_be_hidden_by_worktree(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(['git', 'init', '-q', directory], check=True)
            path = Path(directory) / 'notes.txt'
            path.write_bytes(b'TES4original-test-magic')
            subprocess.run(['git', '-C', directory, 'add', 'notes.txt'], check=True)
            path.write_text('safe worktree\n')
            self.assertTrue(any('index:' in why for _, why in check(directory)))

    def test_history_remembers_deleted_game_data(self):
        with tempfile.TemporaryDirectory() as directory:
            def git(*args):
                subprocess.run(['git', '-C', directory, *args], check=True, capture_output=True)
            git('init', '-q')
            path = Path(directory) / 'bad.txt'
            path.write_bytes(b'BSA\0original-test-magic')
            git('add', 'bad.txt')
            git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'test only')
            git('rm', 'bad.txt')
            git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'delete')
            self.assertFalse(check(directory))
            self.assertTrue(any('history:' in why for _, why in check(directory, history=True)))

    def test_symlink_rejected_without_reading_target(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(['git', 'init', '-q', directory], check=True)
            (Path(directory) / 'link.txt').symlink_to('/does-not-exist')
            self.assertTrue(check(directory))


if __name__ == '__main__':
    unittest.main()
