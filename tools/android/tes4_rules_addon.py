#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Write openoblivion_rules.omwaddon: host game settings set to the classic
TES4 values the bridged actors need. Generated at package time.

- fHandToHandReach 0.6: the host AI closes to fHandToHandReach x fCombatDistance
  (edge to edge); Oblivion.esm sets fHandReachMult 0.6 with fCombatDistance 128.
"""
import argparse
from pathlib import Path
import struct

SETTINGS = {'fHandToHandReach': 0.6}


def sub(tag, data):
    return tag.encode() + struct.pack('<I', len(data)) + data


def record(tag, data):
    return tag.encode() + struct.pack('<III', len(data), 0, 0) + data


def build(extra=()):
    """The addon bytes; extra = (tag, payload) host records (tes4_items)."""
    header = sub('HEDR', struct.pack('<fi32s256sI', 1.3, 0, b'OpenOblivion contributors',
                                     b'TES4 rules for the host actors', len(SETTINGS) + len(extra)))
    out = record('TES3', header)
    for name, value in SETTINGS.items():
        out += record('GMST', sub('NAME', name.encode() + b'\0') + sub('FLTV', struct.pack('<f', value)))
    for tag, payload in extra:
        out += record(tag, payload)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.parse_args().output.write_bytes(build())


if __name__ == '__main__':
    main()
