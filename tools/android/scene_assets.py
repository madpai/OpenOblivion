#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Select a bounded classic TES4 visual test neighborhood into a private directory.

Independent plugin traversal; archive I/O uses the audited external Asset Lab API.
This is a packaging aid, not a complete dependency resolver or gameplay reader.
"""
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import zlib


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
            fields = dict(subrecords(raw))
            if tag == b'CELL':
                editor = fields.get(b'EDID', b'').rstrip(b'\0').lower()
                xy = struct.unpack('<ii', fields[b'XCLC'][:8]) if b'XCLC' in fields else None
                if editor.startswith(b'vilverin') or (world == 0x3c and xy and abs(xy[0]-12)<=1 and abs(xy[1]-21)<=1):
                    selected_cells.add(fid)
            if tag in (b'REFR', b'ACHR', b'ACRE') and b'NAME' in fields:
                refs.append((cell, struct.unpack('<I', fields[b'NAME'])[0]))
            # All landscape texture definitions are small and prevent near-cell
            # blending/grass dependencies from being omitted by this simple slice.
            paths = []
            for key in (b'MODL', b'MOD2', b'MOD3', b'MOD4'):
                if key in fields: paths.append('meshes/' + fields[key].rstrip(b'\0').decode('cp1252'))
            if tag == b'LTEX' and b'ICON' in fields:
                paths.append('textures/landscape/' + fields[b'ICON'].rstrip(b'\0').decode('cp1252'))
            if paths: records[fid] = (tag, paths)
    walk(0, len(plugin))
    bases = {base for cell, base in refs if cell in selected_cells}
    wanted = set()
    for fid, (tag, paths) in records.items():
        if fid in bases or tag == b'LTEX': wanted.update(paths)
    archives = [Archive(data / ('Oblivion - ' + name + '.bsa')) for name in ('Meshes', 'Textures - Compressed', 'Misc')]
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
    report = {'schema': 1, 'scope': 'Vilverin interiors and Tamriel cells 11..13,20..22; all LTEX textures; shared effects',
              'cells': sorted(selected_cells), 'base_forms': len(bases), 'selected_files': sorted(packed, key=lambda f: f['path']),
              'missing_requests': sorted(missing)}
    (output.parent / 'scene-selection.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f"Selected {len(packed)} visual files, {sum(f['size'] for f in packed)//1024//1024} MiB; {len(missing)} unresolved requests", flush=True)
    return [(file, 'data/' + file.relative_to(output).as_posix()) for file in sorted(output.rglob('*')) if file.is_file()]
