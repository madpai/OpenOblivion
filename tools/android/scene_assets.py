#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Select a bounded classic TES4 visual test neighborhood into a private directory.

Independent plugin traversal; archive I/O uses the audited external Asset Lab API.
This is a packaging aid, not a complete dependency resolver or gameplay reader.
"""
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys
import zlib

EXTERIOR_WORLD = 0x3c
EXTERIOR_CENTER = (12, 21)
EXTERIOR_RADIUS = 2
TES4_CELL_UNITS = 4096


def in_exterior_grid(world, xy):
    return world == EXTERIOR_WORLD and xy is not None and all(
        abs(value - center) <= EXTERIOR_RADIUS for value, center in zip(xy, EXTERIOR_CENTER))


def subrecords(raw):
    pos, extended = 0, None
    while pos < len(raw):
        if pos + 6 > len(raw): raise ValueError('Truncated subrecord header')
        tag, size = struct.unpack_from('<4sH', raw, pos); pos += 6
        if tag == b'XXXX':
            if size != 4 or pos + 4 > len(raw): raise ValueError('Invalid extended subrecord')
            extended = struct.unpack_from('<I', raw, pos)[0]; pos += 4; continue
        if extended is not None: size, extended = extended, None
        if pos + size > len(raw): raise ValueError('Subrecord exceeds record')
        yield tag, raw[pos:pos+size]; pos += size
    if extended is not None: raise ValueError('Orphan extended size')


def visual_links(tag, fields):
    """Return visual paths/form dependencies, retaining repeated TES4 fields.

    This deliberately covers classic scene visuals only, not quests, scripts,
    load-order overrides or a complete inventory/gameplay dependency graph.
    """
    paths, links = [], set()
    for key, value in fields:
        if key in (b'MODL', b'MOD2', b'MOD3', b'MOD4') and value.rstrip(b'\0'):
            model = 'meshes/' + value.rstrip(b'\0').decode('cp1252')
            paths.append(model)
            if tag == b'NPC_' and key == b'MODL' and model.lower().endswith('.nif'):
                # Default TES4 idle is a sibling of the authored NPC skeleton.
                paths.append(model.replace('\\', '/').rsplit('/', 1)[0] + '/idle.kf')
        if key == b'ICON' and value.rstrip(b'\0'):
            if tag == b'LTEX': prefix = 'textures/landscape/'
            elif tag in (b'RACE', b'EYES'): prefix = 'textures/'
            else: continue
            paths.append(prefix + value.rstrip(b'\0').decode('cp1252'))
        if tag == b'SOUN' and key == b'FNAM' and value.rstrip(b'\0'):
            sound = value.rstrip(b'\0').decode('cp1252').replace('\\', '/')
            paths.append(sound if sound.lower().startswith('sound/') else 'sound/' + sound)
        direct = ((tag == b'NPC_' and key in (b'RNAM', b'HNAM', b'ENAM'))
                  or (tag == b'DOOR' and key in (b'SNAM', b'ANAM'))
                  or (tag == b'LTEX' and key == b'GNAM'))
        if direct:
            if len(value) != 4: raise ValueError('Invalid visual form reference')
            links.add(struct.unpack('<I', value)[0])
        if tag in (b'NPC_', b'CREA', b'CONT') and key == b'CNTO':
            if len(value) != 8: raise ValueError('Invalid inventory entry')
            links.add(struct.unpack_from('<I', value)[0])
        if tag in (b'LVLC', b'LVLI', b'LVLN') and key == b'LVLO':
            if len(value) not in (8, 12): raise ValueError('Invalid leveled visual entry')
            links.add(struct.unpack_from('<I', value, 4 if len(value) == 12 else 2)[0])
    links.discard(0)
    return paths, links


def visual_closure(records, roots):
    pending, seen, missing, wanted = list(roots), set(), set(), set()
    while pending:
        fid = pending.pop()
        if fid in seen: continue
        seen.add(fid)
        if len(seen) > 100000: raise ValueError('Visual dependency budget exceeded')
        if fid not in records:
            missing.add(fid); continue
        _, paths, links = records[fid]
        wanted.update(paths); pending.extend(links - seen)
    return wanted, seen, missing


def select(data, assetlab, output):
    from check_upstream import check
    check(assetlab, 'madpai/open-asset-lab')
    sys.path.insert(0, str(assetlab))
    from assetlab.importers.bsa import Archive
    output.mkdir(parents=True, exist_ok=True)
    plugin = (data / 'Oblivion.esm').read_bytes()
    if len(plugin) > 512*1024*1024 or plugin[:4] != b'TES4': raise ValueError('Expected bounded classic Oblivion master')
    selected_cells, records, refs = set(), {}, []

    def walk(pos, end, world=None, cell=None, depth=0):
        if depth > 16: raise ValueError('Group nesting budget exceeded')
        while pos < end:
            if pos + 20 > end: raise ValueError('Truncated TES4 header')
            tag, size = struct.unpack_from('<4sI', plugin, pos)
            if tag == b'GRUP':
                label, kind = struct.unpack_from('<Ii', plugin, pos+8)
                if size < 20 or pos+size > end: raise ValueError('Invalid group extent')
                walk(pos+20, pos+size, label if kind == 1 else world, label if kind == 6 else cell, depth+1)
                pos += size; continue
            flags, fid = struct.unpack_from('<II', plugin, pos+8)
            if pos+20+size > end or size > 32*1024*1024: raise ValueError('Record budget exceeded')
            raw = plugin[pos+20:pos+20+size]; pos += 20+size
            if flags & 0x40000:
                if len(raw) < 4: raise ValueError('Truncated compressed record')
                expected = struct.unpack_from('<I', raw)[0]
                if expected > 32*1024*1024: raise ValueError('Decompression budget exceeded')
                decoder = zlib.decompressobj(); raw = decoder.decompress(raw[4:], expected+1)
                if len(raw) != expected or not decoder.eof or decoder.unused_data: raise ValueError('Invalid compressed record')
            repeated = list(subrecords(raw))
            fields = dict(repeated)  # Singleton cell/reference fields only.
            if tag == b'CELL':
                editor = fields.get(b'EDID', b'').rstrip(b'\0').lower()
                xy = struct.unpack('<ii', fields[b'XCLC'][:8]) if b'XCLC' in fields else None
                # Pinned OpenMW TES4 scenes activate a radius-two (5x5) grid.
                if editor.startswith(b'vilverin') or in_exterior_grid(world, xy):
                    selected_cells.add(fid)
            if tag in (b'REFR', b'ACHR', b'ACRE') and b'NAME' in fields:
                # Persistent world references can belong to the world's
                # persistent CELL rather than their physical exterior cell.
                xy = None
                if world == EXTERIOR_WORLD and b'DATA' in fields:
                    if len(fields[b'DATA']) != 24: raise ValueError('Invalid reference transform')
                    xy = tuple(math.floor(value / TES4_CELL_UNITS) for value in struct.unpack_from('<ff', fields[b'DATA']))
                refs.append((cell, struct.unpack('<I', fields[b'NAME'])[0], in_exterior_grid(world, xy)))
            # All landscape texture definitions are small and prevent near-cell
            # blending/grass dependencies from being omitted by this simple slice.
            paths, links = visual_links(tag, repeated)
            # Keep definitions even when they need no visual file (for example
            # a leveled inventory item). Absence of a model is not a missing form.
            if tag not in (b'REFR', b'ACHR', b'ACRE', b'LAND', b'PGRD', b'CELL'):
                records[fid] = (tag, paths, links)
    walk(0, len(plugin))
    cell_bases = {base for cell, base, _ in refs if cell in selected_cells}
    position_bases = {base for _, base, visible in refs if visible}
    bases = cell_bases | position_bases
    roots = bases | {fid for fid, (tag, _, _) in records.items() if tag == b'LTEX'}
    wanted, followed, missing_forms = visual_closure(records, roots)
    archives = [Archive(data / ('Oblivion - ' + name + '.bsa')) for name in ('Meshes', 'Textures - Compressed', 'Misc', 'Sounds')]
    providers = {key: archive for archive in archives for key in archive.entries}
    # Runtime defaults may request common water/effect textures independently
    # of a scene model. Preserve these small shared texture directories.
    wanted.update(k for k in providers if k.startswith(('textures/water/', 'textures/effects/', 'textures/sky/')))
    pending = list(wanted); seen = set(); missing = []; packed = []
    while pending:
        name = pending.pop().replace('\\', '/').lower().lstrip('/')
        if name.startswith('meshes/meshes/'): name = name[7:]
        if name in seen: continue
        seen.add(name)
        if name not in providers:
            missing.append(name); continue
        content = providers[name].read(name)
        if name.endswith('.nif'):
            # Classic NiSourceTexture file paths and model links are readable
            # byte strings. Keep normal/glow companions even when implicit.
            for match in re.finditer(rb'[A-Za-z0-9_ .\\/\-:]+\.(?:dds|nif|kf)', content, re.I):
                value = match[0].decode('cp1252').replace('\\','/').lower()
                index = value.find('textures/') if '.dds' in value else value.find('meshes/')
                if index >= 0: pending.append(value[index:])
        if name.endswith('.dds'):
            for suffix in ('_n.dds', '_g.dds'):
                companion = name[:-4] + suffix
                if companion in providers: pending.append(companion)
        target = output / name
        if '..' in Path(name).parts or ':' in name: raise ValueError('Invalid selected asset path')
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(content)
        packed.append({'path': name, 'size': len(content), 'sha256': hashlib.sha256(content).hexdigest()})
    report = {'schema': 2, 'scope': 'Vilverin interiors and Tamriel cells 10..14,19..23 (native initial 5x5 grid); visual race/hair/eyes/inventory/leveled dependencies; door SOUN files; all LTEX textures/grass; shared effects',
              'cells': sorted(selected_cells), 'base_forms': len(bases), 'selected_files': sorted(packed, key=lambda f: f['path']),
              'position_only_base_forms': len(position_bases - cell_bases),
              'followed_forms': len(followed), 'missing_visual_forms': sorted(missing_forms),
              'missing_requests': sorted(missing)}
    (output.parent / 'scene-selection.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f"Selected {len(packed)} visual files, {sum(f['size'] for f in packed)//1024//1024} MiB; {len(missing)} unresolved requests", flush=True)
    return [(file, 'data/' + file.relative_to(output).as_posix()) for file in sorted(output.rglob('*')) if file.is_file()]
