#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from content_guard import check, reason


class ContentGuardTests(unittest.TestCase):
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

