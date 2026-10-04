#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Read the classic master's Player record and write its starting stats for the
phone overlay script. Generated into private build output, never committed.

Derived values follow the original game's console readings for this record
(2026-10-03): health = 2 x Endurance, magicka = 2 x Intelligence,
fatigue = Strength + Willpower + Agility + Endurance.
"""
import argparse
from pathlib import Path
import struct
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scene_assets import subrecords

SKILLS = ('armorer', 'athletics', 'blade', 'block', 'blunt', 'handToHand', 'heavyArmor', 'alchemy',
          'alteration', 'conjuration', 'destruction', 'illusion', 'mysticism', 'restoration',
          'acrobatics', 'lightArmor', 'marksman', 'mercantile', 'security', 'sneak', 'speechcraft')
ATTRIBUTES = ('strength', 'intelligence', 'willpower', 'agility', 'speed', 'endurance', 'personality', 'luck')


def player_record(master):
    plugin = master.read_bytes()
    pos, end = 0, len(plugin)
    stack = [end]
    while pos < len(plugin):
        tag, size = struct.unpack_from('<4sI', plugin, pos)
        if tag == b'GRUP':
            pos += 20
            continue
        flags, fid = struct.unpack_from('<II', plugin, pos + 8)
        raw = plugin[pos + 20:pos + 20 + size]
        pos += 20 + size
        if tag == b'NPC_' and fid == 0x7:
            if flags & 0x40000:
                raw = zlib.decompress(raw[4:])
            return dict(subrecords(raw))
    raise ValueError('Player record 00000007 not found')


def stats(master):
    fields = player_record(master)
    data = fields[b'DATA']
    if len(data) < 33:
        raise ValueError('Unexpected Player DATA size')
    skills = dict(zip(SKILLS, data[:21]))
    attributes = dict(zip(ATTRIBUTES, data[25:33]))
    level = struct.unpack_from('<h', fields[b'ACBS'], 10)[0]
    return {'level': level, 'skills': skills, 'attributes': attributes,
            'health': 2 * attributes['endurance'], 'magicka': 2 * attributes['intelligence'],
            'fatigue': sum(attributes[a] for a in ('strength', 'willpower', 'agility', 'endurance'))}


def npc_table(master):
    """Every TES4 NPC_ base record: AI aggression/confidence and base health.
    The original console shows level-1 autocalc NPCs keep the record's health,
    fatigue (ACBS), skills and attributes (Vilverin bandits 0006C35E, 0006C356,
    0006C35B: health 16/20/20, fatigue 160/180/180, hand-to-hand 40/10/30,
    strength 35/55/55)."""
    plugin = master.read_bytes()
    pos, rows = 0, {}
    while pos < len(plugin):
        tag, size = struct.unpack_from('<4sI', plugin, pos)
        if tag == b'GRUP':
            pos += 20
            continue
        flags, fid = struct.unpack_from('<II', plugin, pos + 8)
        raw = plugin[pos + 20:pos + 20 + size]
        pos += 20 + size
        if tag != b'NPC_':
            continue
        if flags & 0x40000:
            raw = zlib.decompress(raw[4:])
        fields = dict(subrecords(raw))
        aidt = fields.get(b'AIDT', b'\0' * 12)
        data = fields.get(b'DATA', b'')
        health = struct.unpack_from('<I', data, 21)[0] if len(data) >= 25 else 0
        acbs = fields.get(b'ACBS', b'\0' * 16)
        fatigue = struct.unpack_from('<H', acbs, 6)[0]
        hand, strength, luck = (data[5], data[25], data[32]) if len(data) >= 33 else (0, 0, 0)
        blade, blunt, marksman = (data[2], data[4], data[16]) if len(data) >= 21 else (0, 0, 0)
        rows[fid & 0xffffff] = (aidt[0], aidt[1], health, fatigue, hand, strength, luck, blade, blunt, marksman)
    return rows


def npc_lua(rows):
    body = ',\n'.join(f'  [{fid}] = {{' + ', '.join(map(str, row)) + '}' for fid, row in sorted(rows.items()))
    return ('-- Generated from the owner\'s Oblivion.esm NPC records; private build output.\n'
            '-- [FormID & 0xffffff] = {aggression, confidence, health, fatigue, handToHand, strength, luck,'
            ' blade, blunt, marksman}\n'
            'return {\n' + body + '\n}\n')


def lua(values):
    def table(d):
        return '{' + ', '.join(f'{k} = {v}' for k, v in d.items()) + '}'
    return ('-- Generated from the owner\'s Oblivion.esm Player record; private build output.\n'
            f"return {{level = {values['level']}, health = {values['health']}, magicka = {values['magicka']}, "
            f"fatigue = {values['fatigue']},\n  attributes = {table(values['attributes'])},\n"
            f"  skills = {table(values['skills'])}}}\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('master', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--npcs', type=Path, help='Also write the NPC table here')
    args = parser.parse_args()
    args.output.write_text(lua(stats(args.master)))
    if args.npcs:
        args.npcs.write_text(npc_lua(npc_table(args.master)))


if __name__ == '__main__':
    main()
