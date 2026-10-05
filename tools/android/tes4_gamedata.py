#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Turn the owner's Oblivion.esm quests, scripts and dialogue into Lua data (private build output).

Written beside the other generated overlay files and never committed:

  scripts/tes4data/quests.lua     every quest: stages, journal text, conditions, result fragment ids
  scripts/tes4data/index.lua      script chunk table, globals' initial values, exterior cell grid -> CELL
  scripts/tes4data/frag_NNN.lua   compiled result scripts (quest stages, dialogue results), 128 per file
  scripts/tes4data/script_NNN.lua compiled object/quest scripts, 32 per file
  scripts/tes4data/dial_NNN.lua   dialogue topics and responses, grouped by topic

The script compiler (tes4_script.py) needs the executable's command table
(tes4_commands.py), so a build reads both files from the owner's installation.
"""
import re
import struct

import tes4_master
from tes4_script import CommandTable, Resolver, compile_fragment, compile_script, lua_string

FRAGMENTS_PER_CHUNK = 128
SCRIPTS_PER_CHUNK = 32
TOPICS_PER_CHUNK = 64


class Raw(str):
    """Lua source inserted verbatim by lua()."""


def lua(value, indent=0):
    pad = '  ' * (indent + 1)
    if value is None:
        return 'nil'
    if isinstance(value, Raw):
        return str(value)
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        text = repr(value)
        return text if ('.' in text or 'e' in text or 'n' in text) else text + '.0'
    if isinstance(value, str):
        return lua_string(value)
    if isinstance(value, (list, tuple)):
        if not value:
            return '{}'
        inline = all(isinstance(x, (int, float, bool, type(None))) for x in value)
        if inline:
            return '{' + ', '.join(lua(x) for x in value) + '}'
        return '{\n' + ''.join(pad + lua(x, indent + 1) + ',\n' for x in value) + '  ' * indent + '}'
    if isinstance(value, dict):
        if not value:
            return '{}'
        rows = []
        for key in sorted(value, key=lambda k: (isinstance(k, str), k)):
            name = f'[{key}]' if isinstance(key, int) else (key if re.fullmatch(r'[A-Za-z_]\w*', key) and key not in LUA_WORDS
                                                              else f'[{lua_string(key)}]')
            rows.append(pad + f'{name} = {lua(value[key], indent + 1)},\n')
        return '{\n' + ''.join(rows) + '  ' * indent + '}'
    raise TypeError(type(value))


LUA_WORDS = {'and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 'function', 'if', 'in', 'local', 'nil',
             'not', 'or', 'repeat', 'return', 'then', 'true', 'until', 'while', 'goto'}


def text(raw):
    return raw.rstrip(b'\0').decode('latin1')


def condition(raw):
    """CTDA: type/flags byte, compare value (or GLOB FormID), function, two parameters."""
    flags, value, function, parameter1, parameter2 = struct.unpack_from('<B3xfIII', raw, 0)
    if flags & 0x04:  # compare against a global's value
        value = struct.unpack_from('<I', raw, 4)[0]
    return [function, flags, round(value, 6) if not flags & 0x04 else value, parameter1, parameter2]


class MasterResolver(Resolver):
    def __init__(self, forms, scripts, quest_scripts):
        self.forms = forms
        self.scripts = scripts
        self.quest_scripts = quest_scripts

    def form(self, word):
        return self.forms.get(word.lower())

    def quest_script(self, quest):
        source = self.scripts.get(self.quest_scripts.get(quest))
        if not source:
            return None
        return {m.group(2).lower(): ('long' if m.group(1).lower() == 'int' else m.group(1).lower())
                for m in re.finditer(r'(?im)^\s*(short|long|int|float|ref)\s+(\w+)', source)}


class GameData:
    def __init__(self, master, commands):
        self.master = master
        self.table = CommandTable.load(commands) if not isinstance(commands, CommandTable) else commands
        self.forms = {}
        self.scripts = {}  # SCPT FormID -> source
        self.script_names = {}
        self.quest_scripts = {}
        self.worlds = {}  # lower-case EDID -> (FormID, lower-case FULL name)
        self.markers = {}  # lower-case EDID of a map marker reference -> (x, y)
        self.warnings = []
        self.fragments = []  # Lua function expressions, 1-based ids
        self.fragment_sources = []
        self.script_modules = []  # (formid, expression)
        self.stats = {}

    # -- first pass: names and sources ------------------------------------
    def index(self):
        for record in tes4_master.records(self.master):
            editor = record.editor_id()
            if editor:
                self.forms[editor.lower()] = (record.formid, record.type.decode())
            if record.type == b'WRLD':
                self.worlds[(editor or '').lower()] = (record.formid, (record.full_name() or '').lower())
            elif record.type == b'REFR' and editor and editor.lower().endswith('mapmarker') and record.first(b'DATA'):
                self.markers[editor.lower()] = struct.unpack_from('<2f', record.first(b'DATA'), 0)
            if record.type == b'SCPT':
                self.scripts[record.formid] = text(record.first(b'SCTX', b''))
                self.script_names[record.formid] = editor
            elif record.type == b'QUST' and record.first(b'SCRI'):
                self.quest_scripts[record.formid] = struct.unpack('<I', record.first(b'SCRI'))[0]
        self.resolver = MasterResolver(self.forms, self.scripts, self.quest_scripts)

    # -- compilation ------------------------------------------------------
    def fragment(self, source, name):
        """Compile a result script and return its 1-based id, or None when it is empty."""
        source = source.strip()
        if not re.sub(r';[^\n]*', '', source).strip():
            return None
        self.fragment_sources.append(source)
        result = compile_fragment(source, self.table, self.resolver, name)
        self.warnings += result.warnings
        self.fragments.append(result.expr)
        return len(self.fragments)

    def script(self, formid):
        name = self.script_names.get(formid) or hex(formid)
        result = compile_script(self.scripts[formid], self.table, self.resolver, name)
        self.warnings += result.warnings
        self.script_modules.append((formid, result.expr))
        return result

    # -- quests -----------------------------------------------------------
    def quests(self):
        quests = {}
        for record in tes4_master.records(self.master, {b'QUST'}):
            data = record.first(b'DATA', b'\0\0')
            quest = {'id': record.editor_id(), 'name': record.full_name() or '', 'flags': data[0], 'priority': data[1]}
            if record.first(b'SCRI'):
                quest['script'] = struct.unpack('<I', record.first(b'SCRI'))[0]
            quest_conditions = []
            stages, entry, stage = {}, None, None
            for tag, raw in record.subs:
                if tag == b'INDX':
                    stage = struct.unpack('<H', raw)[0]
                    stages.setdefault(stage, [])
                    entry = None
                elif tag == b'QSDT' and stage is not None:
                    entry = {'flags': raw[0]}
                    stages[stage].append(entry)
                elif entry is not None and tag == b'CTDA':
                    entry.setdefault('cond', []).append(condition(raw))
                elif entry is not None and tag == b'CNAM':
                    entry['log'] = text(raw)
                elif entry is not None and tag == b'SCTX':
                    fid = self.fragment(raw.decode('latin1'), f'{quest["id"]} stage {stage}')
                    if fid:
                        entry['result'] = fid
                elif stage is None and tag == b'CTDA':
                    quest_conditions.append(condition(raw))
            if quest_conditions:
                quest['cond'] = quest_conditions
            if stages:
                quest['stages'] = stages
            quests[record.formid] = quest
        self.stats['quests'] = len(quests)
        return quests

    def object_scripts(self):
        for formid in sorted(self.scripts):
            self.script(formid)
        self.stats['scripts'] = len(self.script_modules)

    def functions(self):
        """Condition function number -> {command name, needs a reference, parameter types}."""
        rows = {}
        for opcode, command in self.table.by_opcode.items():
            types = [name for name, _ in command.params[:2]]
            rows[opcode - 0x1000] = [command.lua, command.parent] + [t if t in ('ActorValue', 'Axis', 'Sex') else None
                                                                      for t in types]
        return rows

    def globals(self):
        values = {}
        for record in tes4_master.records(self.master, {b'GLOB'}):
            raw = record.first(b'FLTV')
            values[record.formid] = struct.unpack('<f', raw)[0] if raw else 0.0
        return values

    def cells(self):
        """Exterior grid -> CELL per worldspace, and the places that "dummy" CELLs stand for.

        Shipped scripts test `GetInCell Chorrol` against interior-flagged placeholder cells whose
        FULL name says "dummy cell for GetInCell". The engine's rule for them is not known; this
        maps a placeholder to the worldspace with the same name (cities), or else to the exterior
        grid cells within two of its map marker (landmarks such as Weynon Priory). An
        approximation to check against the original game.
        """
        grid, world = {}, None
        areas = {}
        dummies = []
        for record in tes4_master.records(self.master, {b'WRLD', b'CELL'}):
            if record.type == b'WRLD':
                world = record.formid
                continue
            raw = record.first(b'XCLC')
            if raw and len(raw) >= 8 and world is not None:
                x, y = struct.unpack_from('<ii', raw, 0)
                grid.setdefault(world, {})[f'{x},{y}'] = record.formid
            elif (world is None and record.first(b'DATA', b'\0')[0] & 1 and not record.first(b'XCLL')
                  and len(record.subs) <= 3 and record.editor_id()):
                dummies.append(record)
        tamriel = self.worlds.get('tamriel', (0x3C, ''))[0]
        for record in dummies:
            name = record.editor_id().lower()
            match = next((formid for edid, (formid, full) in self.worlds.items()
                          if edid == name + 'world' or (full and full == name)), None)
            if match:
                areas[record.formid] = {'world': match}
            elif name + 'mapmarker' in self.markers:
                x, y = self.markers[name + 'mapmarker']
                gx, gy = int(x // 4096), int(y // 4096)
                areas[record.formid] = {'world': tamriel, 'cells': {f'{gx + dx},{gy + dy}': True
                                                                      for dx in range(-2, 3) for dy in range(-2, 3)}}
        return grid, areas

    # -- actors -----------------------------------------------------------
    def actors(self):
        """NPC_ base records as seen by conditions: race, class, sex, level, factions."""
        rows = {}
        for record in tes4_master.records(self.master, {b'NPC_'}):
            acbs = record.first(b'ACBS', b'\0' * 16)
            row = {'level': struct.unpack_from('<h', acbs, 8)[0]}
            if struct.unpack_from('<I', acbs, 0)[0] & 1:
                row['female'] = True
            if record.first(b'RNAM'):
                row['race'] = struct.unpack('<I', record.first(b'RNAM'))[0]
            if record.first(b'CNAM'):
                row['class'] = struct.unpack('<I', record.first(b'CNAM'))[0]
            factions = [[struct.unpack_from('<I', raw)[0], struct.unpack_from('<b', raw, 4)[0]]
                        for raw in record.all(b'SNAM') if len(raw) >= 5]
            if factions:
                row['factions'] = factions
            rows[record.formid] = row
        self.stats['actors'] = len(rows)
        return rows

    # -- dialogue ---------------------------------------------------------
    @staticmethod
    def speakers(conditions):
        """NPC base IDs a response is restricted to by GetIsID conditions, or None when it is generic."""
        groups, current = [], []
        for c in conditions:
            current.append(c)
            if not c[1] & 1:
                groups.append(current)
                current = []
        if current:
            groups.append(current)
        for group in groups:
            ids = [c[3] for c in group if c[0] == 72 and c[1] & 0xE3 == 0 and c[2] == 1.0]
            if ids and len(ids) == len(group):
                return ids
        return None

    def dialogue(self, output):
        data_dir = output / 'scripts' / 'tes4data'
        topics, current = {}, None
        for record in tes4_master.records(self.master, {b'DIAL', b'INFO'}):
            if record.type == b'DIAL':
                raw = record.first(b'DATA', b'\0')
                current = {'id': record.editor_id(), 'name': record.full_name() or '', 'type': raw[0],
                           'quests': [struct.unpack('<I', q)[0] for q in record.all(b'QSTI')], 'infos': []}
                topics[record.formid] = current
                continue
            info = {'id': record.formid}
            raw = record.first(b'DATA', b'\0\0\0')
            info['flags'] = raw[2] if len(raw) > 2 else 0
            info['next'] = raw[1] if len(raw) > 1 else 0
            if record.first(b'QSTI'):
                info['quest'] = struct.unpack('<I', record.first(b'QSTI'))[0]
            conditions = [condition(raw) for raw in record.all(b'CTDA')]
            if conditions:
                info['cond'] = conditions
                speakers = self.speakers(conditions)
                if speakers:
                    info['speakers'] = speakers
            responses = []
            for tag, raw in record.subs:
                if tag == b'TRDT':
                    emotion, value = struct.unpack_from('<Ii', raw, 0)
                    responses.append({'emotion': emotion, 'value': value, 'n': raw[12]})
                elif tag == b'NAM1' and responses:
                    responses[-1]['text'] = text(raw)
            if responses:
                info['r'] = responses
            added = [struct.unpack('<I', raw)[0] for raw in record.all(b'NAME')]
            if added:
                info['add'] = added
            choices = [struct.unpack('<I', raw)[0] for raw in record.all(b'TCLT')]
            if choices:
                info['choices'] = choices
            source = record.first(b'SCTX')
            if source:
                fid = self.fragment(source.decode('latin1'), f'INFO {record.formid:#x}')
                if fid:
                    info['result'] = fid
            if current is not None:
                current['infos'].append(info)
        # Topics only a script or response can hand out are listed once learned; the rest are always known.
        learned, choice_only = set(), set()
        for topic in topics.values():
            for info in topic['infos']:
                learned.update(info.get('add', ()))
                choice_only.update(info.get('choices', ()))
        for source in list(self.scripts.values()) + self.fragment_sources:
            for name in re.findall(r'(?i)\baddtopic\s+(\w+)', source):
                found = self.forms.get(name.lower())
                if found:
                    learned.add(found[0])
        # chunk the infos; large topics are split so no Lua file grows past a few hundred responses
        slices, chunk_of = [], {}
        for formid, topic in sorted(topics.items()):
            infos = topic['infos']
            for start in range(0, max(len(infos), 1), 200):
                part = infos[start:start + 200]
                slices.append((formid, start, part))
        chunks, current_chunk, size = [], [], 0
        for formid, start, part in slices:
            current_chunk.append({'dial': formid, 'from': start, 'infos': part})
            size += len(part) + 1
            chunk_of.setdefault(formid, [])
            if size >= 300:
                chunks.append(current_chunk)
                for entry in current_chunk:
                    if len(chunks) not in chunk_of[entry['dial']]:
                        chunk_of[entry['dial']].append(len(chunks))
                current_chunk, size = [], 0
        if current_chunk:
            chunks.append(current_chunk)
            for entry in current_chunk:
                if len(chunks) not in chunk_of[entry['dial']]:
                    chunk_of[entry['dial']].append(len(chunks))
        for number, entries in enumerate(chunks, 1):
            (data_dir / f'dial_{number:03d}.lua').write_text(
                '-- Generated from the owner\'s Oblivion.esm; private build output.\nreturn function(rt)\n  return '
                + lua(entries, 1) + '\nend\n')
        speaker_topics, generic_topics = {}, []
        for formid, topic in topics.items():
            generic = False
            for info in topic['infos']:
                if 'speakers' in info:
                    for npc in info['speakers']:
                        speaker_topics.setdefault(npc, set()).add(formid)
                else:
                    generic = True
            if generic:
                generic_topics.append(formid)
        listing = {formid: {'id': topic['id'], 'name': topic['name'], 'type': topic['type'],
                            'chunks': chunk_of.get(formid, []), 'learned': formid in learned or None,
                            'choice': formid in choice_only or None}
                   for formid, topic in topics.items()}
        self.stats.update(topics=len(topics), responses=sum(len(t['infos']) for t in topics.values()),
                          dialogue_chunks=len(chunks))
        return listing, {npc: sorted(ids) for npc, ids in speaker_topics.items()}, sorted(generic_topics)

    # -- output -----------------------------------------------------------
    @staticmethod
    def chunk(entries, header='return function(rt)\n  local C, N = rt.C, rt.N\n  return {\n', footer='  }\nend\n'):
        body = ''.join(f'  [{key}] = {expr},\n' for key, expr in entries)
        return header + body + footer

    def write(self, output):
        data_dir = output / 'scripts' / 'tes4data'
        data_dir.mkdir(parents=True, exist_ok=True)
        quests = self.quests()
        listing, speaker_topics, generic_topics = self.dialogue(output)
        self.object_scripts()
        chunk_of_script = {}
        for number, start in enumerate(range(0, len(self.script_modules), SCRIPTS_PER_CHUNK), 1):
            entries = self.script_modules[start:start + SCRIPTS_PER_CHUNK]
            (data_dir / f'script_{number:03d}.lua').write_text(self.chunk(entries))
            for formid, _ in entries:
                chunk_of_script[formid] = number
        fragment_chunks = 0
        for number, start in enumerate(range(0, len(self.fragments), FRAGMENTS_PER_CHUNK), 1):
            entries = [(start + i + 1, expr) for i, expr in enumerate(self.fragments[start:start + FRAGMENTS_PER_CHUNK])]
            (data_dir / f'frag_{number:03d}.lua').write_text(self.chunk(entries))
            fragment_chunks = number
        (data_dir / 'quests.lua').write_text('-- Generated from the owner\'s Oblivion.esm; private build output.\nreturn '
                                             + lua(quests) + '\n')
        cells, areas = self.cells()
        index = {'fragmentsPerChunk': FRAGMENTS_PER_CHUNK, 'fragmentChunks': fragment_chunks,
                 'scriptChunk': chunk_of_script, 'globals': self.globals(), 'cells': cells, 'areas': areas,
                 'scriptOfQuest': {fid: q['script'] for fid, q in quests.items() if 'script' in q},
                 'functions': self.functions(), 'topics': listing, 'speakerTopics': speaker_topics,
                 'genericTopics': generic_topics,
                 'greeting': next((fid for fid, topic in listing.items() if topic['id'] == 'GREETING'), None)}
        (data_dir / 'actors.lua').write_text('-- Generated from the owner\'s Oblivion.esm; private build output.\nreturn '
                                             + lua(self.actors()) + '\n')
        (data_dir / 'index.lua').write_text('-- Generated from the owner\'s Oblivion.esm; private build output.\nreturn '
                                            + lua(index) + '\n')
        self.stats.update(fragments=len(self.fragments), warnings=len(self.warnings))
        return self.stats


def build(master, executable, output):
    """Generate the overlay's tes4data from the owner's master and executable. Returns statistics."""
    import json
    import tempfile
    from pathlib import Path
    import tes4_commands
    with tempfile.TemporaryDirectory() as tmp:
        commands = Path(tmp) / 'commands.json'
        commands.write_text(json.dumps(tes4_commands.read_table(Path(executable).read_bytes())))
        data = GameData(Path(master), commands)
        data.index()
        stats = data.write(Path(output))
    stats['warnings_list'] = data.warnings
    return stats
