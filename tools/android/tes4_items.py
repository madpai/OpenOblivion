#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Turn the classic master's items into host item records, and write the
leveled-list and inventory tables the phone overlay scripts roll from.
Generated at package time into private build output, never committed.

Each TES4 item becomes a host record named "oo4_" + the master FormID's low 24
bits (hex), keeping the original name, world model, inventory icon, weight and
value. The renderer maps equipped "oo4_" records back to the TES4 record for
the worn model. Host types are chosen by TES4 biped slot (see SLOT notes).
Effects, enchantments, scripts and item health are not carried yet.
"""
import struct
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scene_assets import subrecords

ITEM_TAGS = (b'ARMO', b'CLOT', b'WEAP', b'AMMO', b'MISC', b'KEYM', b'BOOK', b'ALCH', b'INGR', b'SLGM', b'SGST')
# TES4 biped flags
HEAD, HAIR, UPPER, LOWER, HAND, FOOT, RRING, LRING, AMULET, SHIELD = 0x1, 0x2, 0x4, 0x8, 0x10, 0x20, 0x40, 0x80, 0x100, 0x2000
NON_PLAYABLE = 0x40
# Host armor types: 0 helmet, 1 cuirass, 4 greaves, 5 boots, 6 left gauntlet, 8 shield.
# Host clothing types: 0 pants, 1 shoes, 2 shirt, 4 robe, 6 left glove, 8 ring, 9 amulet.
# TES4 gauntlets/gloves cover both hands in one item; the host left-hand slot holds them.
# TES4 hats are clothing in the head slot; the host has no clothing hat, so they
# become 0-rating helmets.
WEAPON_TYPES = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 9}  # blade1h, blade2h, blunt1h, blunt2h, staff, bow


def item_id(fid):
    return 'oo4_%06x' % (fid & 0xffffff)


def records(master):
    plugin = master.read_bytes()
    pos = 0
    while pos < len(plugin):
        tag, size = struct.unpack_from('<4sI', plugin, pos)
        if tag == b'GRUP':
            pos += 20
            continue
        flags, fid = struct.unpack_from('<II', plugin, pos + 8)
        raw = plugin[pos + 20:pos + 20 + size]
        pos += 20 + size
        if flags & 0x40000:
            raw = zlib.decompress(raw[4:])
        yield tag, fid, raw


def text(value):
    return value.split(b'\0', 1)[0].decode('cp1252', 'replace')


def armor_type(slots):
    if slots & SHIELD: return 8
    if slots & UPPER: return 1
    if slots & LOWER: return 4
    if slots & FOOT: return 5
    if slots & HAND: return 6
    return 0


def clothing_type(slots):
    if slots & UPPER and slots & LOWER: return 4
    if slots & UPPER: return 2
    if slots & LOWER: return 0
    if slots & FOOT: return 1
    if slots & HAND: return 6
    if slots & AMULET: return 9
    if slots & (RRING | LRING): return 8
    return None  # head/hair: hat


def sub(tag, data):
    return tag.encode() + struct.pack('<I', len(data)) + data


def zstr(value):
    return value.encode('cp1252', 'replace') + b'\0'


def host_record(tag, fid, fields):
    """(host tag, payload) for one TES4 item, or None when it has no host form."""
    name = text(fields.get(b'FULL', b'')) or text(fields.get(b'EDID', b''))
    model = text(fields.get(b'MOD2', b'')) or text(fields.get(b'MODL', b''))
    icon = text(fields.get(b'ICON', b''))
    head = sub('NAME', zstr(item_id(fid)))
    if model:
        head += sub('MODL', zstr(model))
    head += sub('FNAM', zstr(name))
    itex = sub('ITEX', zstr('textures\\menus\\icons\\' + icon)) if icon else b''
    data = fields.get(b'DATA', b'')
    if tag in (b'ARMO', b'CLOT'):
        slots, general = struct.unpack_from('<HB', fields.get(b'BMDT', b'\0\0\0\0'))
        if tag == b'ARMO':
            rating, value, health, weight = struct.unpack_from('<HIIf', data)
            kind = armor_type(slots)
        else:
            value, weight = struct.unpack_from('<If', data)
            rating, health, kind = 0, 100, clothing_type(slots)
        if tag == b'CLOT' and kind is not None:
            return 'CLOT', head + sub('CTDT', struct.pack('<ifHH', kind, weight, min(value, 0xffff), 0)) + itex
        if tag == b'CLOT':
            kind = 0
        return 'ARMO', head + sub('AODT', struct.pack('<ifiiii', kind, weight, value, health, 0, rating // 100)) + itex
    if tag in (b'WEAP', b'AMMO'):
        if tag == b'WEAP':
            kind, speed, reach, _flags, value, health, weight, damage = struct.unpack_from('<IffIIIfH', data)
            kind = WEAPON_TYPES.get(kind, 1)
        else:
            speed, _flags, value, weight, damage = struct.unpack_from('<fB3xIfH', data)
            kind, reach, health = 12, 1.0, 0
        d = min(damage, 255)
        return 'WEAP', head + sub('WPDT', struct.pack('<fihHffH6Bi', weight, value, kind, min(health, 0xffff),
                                                         speed, reach, 0, d, d, d, d, d, d, 0)) + itex
    if tag == b'BOOK':
        flags, _skill, value, weight = struct.unpack_from('<BbIf', data)
        return 'BOOK', (head + sub('BKDT', struct.pack('<fiiii', weight, value, flags & 1, -1, 0)) + itex
                        + sub('TEXT', fields.get(b'DESC', b'\0')))
    if tag in (b'ALCH', b'INGR'):
        weight = struct.unpack_from('<f', data)[0]
        value = struct.unpack_from('<i', fields.get(b'ENIT', b'\0' * 4))[0]
        if tag == b'ALCH':
            return 'ALCH', head + sub('ALDT', struct.pack('<fii', weight, value, 0)) + (
                sub('TEXT', zstr('textures\\menus\\icons\\' + icon)) if icon else b'')
        return 'INGR', head + sub('IRDT', struct.pack('<fi12i', weight, value, *([-1] * 12))) + itex
    if tag == b'SGST':
        _uses, value, weight = struct.unpack_from('<Bif', data)
    else:
        value, weight = struct.unpack_from('<if', data)
    return 'MISC', head + sub('MCDT', struct.pack('<fii', weight, value, 1 if tag == b'KEYM' else 0)) + itex


def scan(master):
    """Host records, leveled lists, NPC inventories, and which items are hidden."""
    host, lists, inventories, hidden = [], {}, {}, set()
    for tag, fid, raw in records(master):
        if tag in ITEM_TAGS:
            fields = dict(subrecords(raw))
            made = host_record(tag, fid, fields)
            if made:
                host.append(made)
            if tag in (b'ARMO', b'CLOT') and struct.unpack_from('<HB', fields.get(b'BMDT', b'\0\0\0\0'))[1] & NON_PLAYABLE:
                hidden.add(fid & 0xffffff)
        elif tag == b'LVLI':
            chance, flags, entries = 0, 0, []
            for sub_tag, value in subrecords(raw):
                if sub_tag == b'LVLD':
                    chance = value[0]
                elif sub_tag == b'LVLF':
                    flags = value[0]
                elif sub_tag == b'LVLO':
                    if len(value) >= 12:
                        level, item, count = struct.unpack_from('<h2xIh', value)
                    else:
                        level, item, count = struct.unpack_from('<hIh', value)
                    entries.append((level, item & 0xffffff, max(1, count)))
            lists[fid & 0xffffff] = (chance, flags, entries)
        elif tag == b'NPC_':
            rows = [struct.unpack_from('<Ii', value) for sub_tag, value in subrecords(raw) if sub_tag == b'CNTO']
            if rows:
                inventories[fid & 0xffffff] = [(item & 0xffffff, count) for item, count in rows]
    return host, lists, inventories, hidden


def lua(lists, inventories, hidden, known):
    def ok(fid):
        return fid in lists or fid in known
    out = ['-- Generated from the owner\'s Oblivion.esm; private build output.',
           '-- lists[FormID] = {chanceNone, flags, {level, FormID, count}, ...}',
           '-- inventories[NPC FormID] = {{FormID, count}, ...}; hidden = non-playable apparel',
           'return {', 'lists = {']
    for fid, (chance, flags, entries) in sorted(lists.items()):
        rows = ', '.join('{%d, %d, %d}' % e for e in entries if ok(e[1]))
        out.append('  [%d] = {%d, %d, %s},' % (fid, chance, flags, rows))
    out.append('},\ninventories = {')
    for fid, rows in sorted(inventories.items()):
        kept = ', '.join('{%d, %d}' % (item, count) for item, count in rows if ok(item))
        if kept:
            out.append('  [%d] = {%s},' % (fid, kept))
    out.append('},\nhidden = {' + ', '.join('[%d] = true' % fid for fid in sorted(hidden)) + '},\n}\n')
    return '\n'.join(out)


def build(master):
    """(host record payloads for the rules addon, Lua tables)."""
    host, lists, inventories, hidden = scan(master)
    known = {int(payload[12:18].decode(), 16) for _tag, payload in host}
    marker = ('MISC', sub('NAME', zstr('oo4_items')) + sub('FNAM', zstr('OpenOblivion items'))
              + sub('MCDT', struct.pack('<fii', 0, 0, 0)))
    return [marker, *host], lua(lists, inventories, hidden, known)
