#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_upstream


class UpstreamTests(unittest.TestCase):
    def test_pin_and_hidden_worktree_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            def git(*args):
                return subprocess.check_output(['git', '-C', directory, *args], text=True).strip()
            git('init', '-q')
            path = Path(directory) / 'original.txt'
            path.write_text('original\n')
            git('add', 'original.txt')
            git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'original')
            sha = git('rev-parse', 'HEAD')
            with patch.object(check_upstream.json, 'loads', return_value={'OpenMW/openmw': {'revision': sha}}):
                self.assertEqual(check_upstream.check(directory), sha)
                git('update-index', '--assume-unchanged', 'original.txt')
                path.write_text('modified\n')
                with self.assertRaisesRegex(ValueError, 'Modified upstream file'):
                    check_upstream.check(directory)
            with self.assertRaisesRegex(ValueError, 'revision differs'):
                check_upstream.check(directory)


if __name__ == '__main__':
    unittest.main()
