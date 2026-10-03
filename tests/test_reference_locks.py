#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Load three original synthetic classic references through the native reader."""
from pathlib import Path
import struct
import subprocess
import sys
import tempfile


def sub(tag, payload):
    return tag + struct.pack('<H', len(payload)) + payload


def record(tag, fid, payload):
    return struct.pack('<4sIIII', tag, len(payload), 0, fid, 0) + payload


header = record(b'TES4', 0, sub(b'HEDR', struct.pack('<fII', 1.0, 3, 0x800)))
body = sub(b'NAME', struct.pack('<I', 0x100))
locked = sub(b'XLOC', struct.pack('<B3xI4x', 15, 0x1234))
references = b''.join(record(b'REFR', 0x800 + i, body + (locked if i == 1 else b''))
                      for i in range(3))
fixture = header + struct.pack('<4sI4siI', b'GRUP', 20 + len(references), b'REFR', 0, 0) + references
with tempfile.TemporaryDirectory(prefix='openoblivion-reference-locks-') as tmp:
    path = Path(tmp) / 'original-reference-locks.esp'
    path.write_bytes(fixture)
    subprocess.run([sys.argv[1], str(path)], check=True)
