#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Original in-memory fixtures; no samples from Bethesda data."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

EXE = sys.argv.pop(1)


def sub(tag, body):
    return struct.pack('<4sH', tag, len(body)) + body


def record(tag, body, flags=0):
    return struct.pack('<4s4I', tag, len(body), flags, 1, 0) + body


def header(version=1.0):
    return record(b'TES4', sub(b'HEDR', struct.pack('<fII', version, 1, 2)))


def group(body, kind=0):
    return struct.pack('<4sI4siHH', b'GRUP', 20 + len(body), b'WEAP', kind, 0, 0) + body


class InspectTests(unittest.TestCase):
    def invoke(self, blob):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'original-fixture.esp'
            path.write_bytes(blob)
            return subprocess.run([EXE, str(path)], capture_output=True, text=True, timeout=5)

    def success(self, blob):
        result = self.invoke(blob)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def reject(self, blob, message):
        result = self.invoke(blob)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(message, result.stderr)

    def test_classic_header_only_and_12(self):
        for version in (1.0, 1.2):
            result = self.success(header(version))
            self.assertEqual(result['records_including_header'], 1)
            self.assertAlmostEqual(result['header_version'], version)

    def test_nested_groups_and_subrecord_counts(self):
        body = sub(b'EDID', b'OpenOblivionOriginal\0') + sub(b'DATA', struct.pack('<II', 7, 9))
        blob = header() + group(group(record(b'WEAP', body), kind=2))
        result = self.success(blob)
        self.assertEqual(result['record_types'], {'TES4': 1, 'WEAP': 1})
        self.assertEqual(result['groups'], 2)
        self.assertEqual(result['scanned_subrecords_excluding_header'], 2)

    def test_compressed_record_is_decoded(self):
        body = sub(b'EDID', b'OriginalCompressedRecord\0') + sub(b'DATA', bytes(range(20)))
        compressed = struct.pack('<I', len(body)) + zlib.compress(body)
        result = self.success(header() + group(record(b'WEAP', compressed, 0x40000)))
        self.assertEqual(result['compressed_records'], 1)
        self.assertEqual(result['scanned_subrecords_excluding_header'], 2)

    def test_corrupt_compression_is_rejected(self):
        self.reject(header() + group(record(b'WEAP', struct.pack('<I', 16) + b'not-zlib', 0x40000)), 'decompress')

    def test_file_and_header_bounds(self):
        self.reject(b'TES4', 'size bounds')
        self.reject(header()[:-1], 'size bounds')
        self.reject(header() + b'WEAP', 'Truncated')
        self.reject(header() + group(record(b'WEAP', b''))[:-1], 'Group exceeds')

    def test_group_depth_and_decompression_budgets(self):
        nested = record(b'WEAP', sub(b'EDID', b'Original\0'))
        for _ in range(65):
            nested = group(nested)
        self.reject(header() + nested, 'nesting budget')
        body = struct.pack('<I', 32 * 1024 * 1024 + 1) + zlib.compress(b'original')
        self.reject(header() + group(record(b'WEAP', body, 0x40000)), 'Decompressed record')

    def test_later_formats_and_unknown_versions_rejected(self):
        self.reject(header(1.7), 'plugin version')
        blob = header()
        self.reject(blob[:20] + b'\0' * 4 + blob[20:], 'later game formats')
        self.reject(b'BAD!' + blob[4:], 'classic TES4 plugin')

    def test_invalid_signature_and_record_size(self):
        self.reject(header() + group(record(b'BAD!', sub(b'EDID', b'Original\0'))), 'signature')
        blob = header() + group(record(b'WEAP', sub(b'EDID', b'Original\0')))
        bad = bytearray(blob)
        struct.pack_into('<I', bad, len(header()) + 20 + 4, 0xffffffff)
        self.reject(bad, 'Record exceeds')

    def test_reports_no_input_paths_or_content_names(self):
        blob = header() + group(record(b'WEAP', sub(b'EDID', b'PrivateContentNameMustNotLeak\0')))
        result = self.invoke(blob)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('PrivateContentNameMustNotLeak', result.stdout)
        self.assertNotIn('original-fixture', result.stdout)


if __name__ == '__main__':
    unittest.main()

