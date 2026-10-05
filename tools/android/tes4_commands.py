#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Read the script command table from the owner's Oblivion.exe.

The executable keeps one 40-byte record per script command (long name, short
name, opcode, help text, needs-parent flag, parameter count, parameter table,
three handlers, flags). Opcodes run 0x1000..0x1171 on the Steam build; a
condition record's function number is the opcode minus 0x1000. Each parameter
record is {type name, type id, optional}. Only names, opcodes and parameter
types are read; no executable code is copied. The output stays private (it
is written beside other build output, never committed).

  tes4_commands.py --exe Oblivion.exe --output commands.json
"""
import argparse
import json
from pathlib import Path
import struct
import sys

IMAGE_BASE = 0x400000
# (RVA, size in file, file offset) of .text, .rdata and .data on the audited build.
SECTIONS = ((0x1000, 0x626e00, 0x400), (0x628000, 0xd9a00, 0x627200), (0x702000, 0x30c00, 0x700c00))
# Anchor: the record of the SetStage command, found by its name's address.
ANCHOR_NAME = b'SetStage\0'
ENTRY = struct.Struct('<IIIIHHIIIII')

PARAM_TYPES = {
    0: 'String', 1: 'Integer', 2: 'Float', 3: 'ObjectID', 4: 'ObjectReferenceID', 5: 'ActorValue', 6: 'Actor',
    7: 'SpellItem', 8: 'Axis', 9: 'Cell', 10: 'AnimationGroup', 11: 'MagicItem', 12: 'Sound', 13: 'Topic',
    14: 'Quest', 15: 'Race', 16: 'Class', 17: 'Faction', 18: 'Sex', 19: 'Global', 20: 'Furniture', 21: 'Object',
    22: 'VariableName', 23: 'Stage', 24: 'MapMarker', 25: 'ActorBase', 26: 'Container', 27: 'Worldspace',
    28: 'CrimeType', 29: 'Package', 30: 'CombatStyle', 31: 'MagicEffect', 32: 'Birthsign', 33: 'FormType',
    34: 'WeatherID', 35: 'NPC', 36: 'Owner', 37: 'EffectShader',
}


def file_offset(va):
    rva = va - IMAGE_BASE
    for start, size, offset in SECTIONS:
        if start <= rva < start + size:
            return offset + rva - start
    return None


def read_table(data):
    def cstr(va):
        offset = file_offset(va)
        if offset is None:
            return None
        return data[offset:data.index(b'\0', offset)].decode('latin1')

    def entry(offset):
        return dict(zip(('name', 'short', 'opcode', 'help', 'parent', 'nparams', 'params', 'exec', 'parse', 'eval',
                         'flags'), ENTRY.unpack_from(data, offset)))

    def valid(offset):
        if offset < 0 or offset + ENTRY.size > len(data):
            return False
        row = entry(offset)
        name = cstr(row['name']) if file_offset(row['name']) else None
        return (name is not None and name.isprintable() and name[:1].isalpha()
                and 0x1000 <= row['opcode'] < 0x4000 and row['nparams'] < 20)

    # The name string lives in .rdata; its address is referenced by the first field of one record.
    anchor_name = data.find(ANCHOR_NAME)
    if anchor_name < 0:
        raise ValueError('SetStage is not in this executable')
    rdata_start, rdata_size, rdata_offset = SECTIONS[1]
    name_va = IMAGE_BASE + rdata_start + anchor_name - rdata_offset
    data_start, data_size, data_offset = SECTIONS[2]
    pointer = struct.pack('<I', name_va)
    at = data.find(pointer, data_offset, data_offset + data_size)
    if at < 0:
        raise ValueError('No command record points at SetStage')
    first = last = at
    while valid(first - ENTRY.size):
        first -= ENTRY.size
    while valid(last + ENTRY.size):
        last += ENTRY.size
    commands = []
    for offset in range(first, last + ENTRY.size, ENTRY.size):
        row = entry(offset)
        params = []
        for index in range(row['nparams']):
            base = file_offset(row['params'])
            type_name_va, type_id, optional = struct.unpack_from('<III', data, base + 12 * index)
            params.append({'type': PARAM_TYPES.get(type_id, str(type_id)), 'id': type_id,
                           'optional': bool(optional) or '(optional)' in (cstr(type_name_va) or '').lower()})
        commands.append({'name': cstr(row['name']), 'short': cstr(row['short']) or '', 'opcode': row['opcode'],
                         'parent': bool(row['parent']), 'params': params})
    return commands


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    commands = read_table(args.exe.read_bytes())
    args.output.write_text(json.dumps(commands, indent=1))
    print(f'{len(commands)} commands, opcodes {commands[0]["opcode"]:#x}..{commands[-1]["opcode"]:#x}', file=sys.stderr)


if __name__ == '__main__':
    main()
