#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Original fixtures for private scene packaging and QA evidence boundaries."""
import hashlib
from http.server import ThreadingHTTPServer
import http.client
import json
from pathlib import Path
import stat
import struct
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from types import ModuleType

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/android'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import scene_assets
import sideload
import payload
import zipfile


class InstalledPayload(unittest.TestCase):
    def test_complete_inventory_and_bounded_parts_preserve_original_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); data = root / 'Data'; data.mkdir()
            names = ['Oblivion.esm', *payload.BASE_ARCHIVES, 'Knights.esp', 'Knights.bsa',
                     'DLCShiveringIsles.esp', 'Music/Explore/original.mp3', 'Video/original.bik',
                     'Shaders/original.sdp', 'Textures/original.dds', 'OriginalMod.esp']
            for index, name in enumerate(names):
                path = data / name; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(bytes([index]) * (index + 1))
            paths, archives, plugins = payload.installed_data(data)
            self.assertEqual({name.removeprefix('data/') for _, name in paths}, set(names))
            self.assertEqual(archives, [*payload.BASE_ARCHIVES, 'Knights.bsa'])
            self.assertEqual(plugins, ['Oblivion.esm', 'DLCShiveringIsles.esp', 'Knights.esp'])
            groups = payload.partition(paths, limit=24)
            self.assertGreater(len(groups), 1)
            recovered, parts = {}, []
            for index, group in enumerate(groups):
                self.assertLessEqual(sum(file.stat().st_size for file, _ in group), 24)
                out = root / f'part-{index}.zip'
                receipt = payload.write_zip(out, group)
                parts.append(receipt)
                self.assertEqual(receipt['sha256'], hashlib.sha256(out.read_bytes()).hexdigest())
                with zipfile.ZipFile(out) as archive:
                    self.assertIsNone(archive.testzip())
                    for name in archive.namelist():
                        self.assertNotIn(name, recovered)
                        recovered[name] = archive.read(name)
            self.assertEqual(recovered, {name: file.read_bytes() for file, name in paths})
            manifest = {'parts': parts, 'files': [{'path': name, 'size': file.stat().st_size,
                        'sha256': hashlib.sha256(file.read_bytes()).hexdigest()} for file, name in paths]}
            payload.verify_parts(root, manifest)
            broken = json.loads(json.dumps(manifest)); broken['files'][0]['sha256'] = '0' * 64
            with self.assertRaises(ValueError): payload.verify_parts(root, broken)
            broken = json.loads(json.dumps(manifest)); broken['files'].pop()
            with self.assertRaises(ValueError): payload.verify_parts(root, broken)
            with self.assertRaises(ValueError): payload.partition(paths, limit=2)
            with self.assertRaises(ValueError): payload.validate_paths([paths[0], paths[0]])
            with self.assertRaises(ValueError): payload.validate_paths([(paths[0][0], 'data/../escape')])

    def test_incomplete_ambiguous_and_executable_installations_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            with self.assertRaises(ValueError): payload.installed_data(data)
            for name in ['Oblivion.esm', *payload.BASE_ARCHIVES]: (data / name).write_bytes(b'original')
            invalid = data / 'unexpected.dll'; invalid.write_bytes(b'original fixture')
            with self.assertRaises(ValueError): payload.installed_data(data)
            invalid.unlink()
            link = data / 'linked-file'; link.symlink_to(data / 'Oblivion.esm')
            with self.assertRaises(ValueError): payload.installed_data(data)
            link.unlink()
            (data / 'oblivion.esm').write_bytes(b'ambiguous original fixture')
            with self.assertRaises(ValueError): payload.installed_data(data)


class SceneDependencies(unittest.TestCase):
    def test_persistent_reference_selected_by_world_position(self):
        # Independent synthetic classic records and a tiny archive substitute.
        def sub(tag, data): return tag + struct.pack('<H', len(data)) + data
        def record(tag, fid, data=b''): return struct.pack('<4sIIII', tag, len(data), 0, fid, 0) + data
        def group(kind, label, data): return struct.pack('<4sIIiI', b'GRUP', len(data)+20, label, kind, 0) + data
        def reference(fid, base, x, y):
            return record(b'REFR', fid, sub(b'NAME', struct.pack('<I', base))
                          + sub(b'DATA', struct.pack('<6f', x*4096, y*4096, 0, 0, 0, 0)))
        persistent = group(6, 10, reference(20, 1, 12.5, 21.5) + reference(21, 2, 15.5, 21.5))
        target = record(b'CELL', 11, sub(b'XCLC', struct.pack('<ii', 12, 21)))
        other_world = group(1, 0x777, group(6, 12, reference(22, 3, 12.5, 21.5)))
        plugin = (record(b'TES4', 0) + group(1, 0x3c, persistent + target) + other_world
                  + record(b'STAT', 1, sub(b'MODL', b'fixture/inside.nif\0'))
                  + record(b'STAT', 2, sub(b'MODL', b'fixture/outside.nif\0'))
                  + record(b'STAT', 3, sub(b'MODL', b'fixture/other-world.nif\0')))
        class FixtureArchive:
            def __init__(self, _):
                self.entries = {name: None for name in ('meshes/fixture/inside.nif',
                                'meshes/fixture/outside.nif', 'meshes/fixture/other-world.nif')}
            def read(self, _): return b'Original fixture mesh bytes.'
        module = ModuleType('assetlab.importers.bsa'); module.Archive = FixtureArchive
        import check_upstream
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / 'Oblivion.esm').write_bytes(plugin)
            previous_path = sys.path[:]
            try:
                with patch.dict(sys.modules, {'assetlab.importers.bsa': module}), patch.object(check_upstream, 'check'):
                    selected = scene_assets.select(root, root / 'fixture-archive-api', root / 'slice')
            finally:
                sys.path[:] = previous_path
            self.assertEqual([name for _, name in selected], ['data/meshes/fixture/inside.nif'])
            report = json.loads((root / 'scene-selection.json').read_text())
            self.assertEqual(report['position_only_base_forms'], 1)
            self.assertEqual(report['cells'], [11])

    def test_repeated_race_and_inventory_fields_survive_dependency_closure(self):
        def sub(tag, value): return tag + struct.pack('<H', len(value)) + value
        def form(value): return struct.pack('<I', value)
        raw = (sub(b'RNAM', form(2)) + sub(b'HNAM', form(3)) + sub(b'ENAM', form(4))
               + sub(b'CNTO', form(5) + form(1)) + sub(b'CNTO', form(6) + form(1)))
        race = sub(b'MODL', b'fixture/head.nif\0') + sub(b'MODL', b'fixture/ears.nif\0')
        records = {}
        for fid, tag, fields in [(1, b'NPC_', list(scene_assets.subrecords(raw))),
                                  (2, b'RACE', list(scene_assets.subrecords(race))),
                                  (3, b'HAIR', [(b'MODL', b'fixture/hair.nif\0')]),
                                  (4, b'EYES', [(b'ICON', b'fixture/eyes.dds\0')]),
                                  (5, b'ARMO', [(b'MODL', b'fixture/boots.nif\0')]),
                                  (6, b'CLOT', [(b'MODL', b'fixture/shirt.nif\0')])]:
            paths, links = scene_assets.visual_links(tag, fields)
            records[fid] = (tag, paths, links)
        wanted, seen, missing = scene_assets.visual_closure(records, {1})
        self.assertEqual(seen, set(range(1, 7)))
        self.assertFalse(missing)
        self.assertEqual(wanted, {'meshes/fixture/head.nif', 'meshes/fixture/ears.nif',
                                 'meshes/fixture/hair.nif', 'textures/fixture/eyes.dds',
                                 'meshes/fixture/boots.nif', 'meshes/fixture/shirt.nif'})

    def test_npc_skeleton_includes_default_idle_without_changing_equipment(self):
        paths, links = scene_assets.visual_links(b'NPC_', [(b'MODL', b'Characters\\Fixture\\Skeleton.NIF\0')])
        self.assertEqual(paths, ['meshes/Characters\\Fixture\\Skeleton.NIF', 'meshes/Characters/Fixture/idle.kf'])
        self.assertFalse(links)
        paths, _ = scene_assets.visual_links(b'ARMO', [(b'MODL', b'Fixture\\Armor.NIF\0')])
        self.assertEqual(paths, ['meshes/Fixture\\Armor.NIF'])

    def test_scene_door_audio_follows_both_sound_records(self):
        paths, links = scene_assets.visual_links(b'DOOR',
            [(b'SNAM', struct.pack('<I', 2)), (b'ANAM', struct.pack('<I', 3))])
        records = {1: (b'DOOR', paths, links)}
        for fid, filename in ((2, b'FX\\FixtureOpen.wav\0'), (3, b'Sound/FX/FixtureClose.wav\0')):
            sound_paths, sound_links = scene_assets.visual_links(b'SOUN', [(b'FNAM', filename)])
            records[fid] = (b'SOUN', sound_paths, sound_links)
        wanted, seen, missing = scene_assets.visual_closure(records, {1})
        self.assertEqual(wanted, {'sound/FX/FixtureOpen.wav', 'Sound/FX/FixtureClose.wav'})
        self.assertEqual(seen, {1, 2, 3})
        self.assertFalse(missing)
        with self.assertRaises(ValueError):
            scene_assets.visual_links(b'DOOR', [(b'SNAM', b'\0')])

    def test_leveled_variants_cycles_and_missing_forms(self):
        fields = [(b'LVLO', struct.pack('<hIh', 1, 2, 1)),
                  (b'LVLO', struct.pack('<hHIhH', 2, 0, 3, 1, 0))]
        paths, links = scene_assets.visual_links(b'LVLC', fields)
        self.assertEqual(links, {2, 3})
        wanted, seen, missing = scene_assets.visual_closure(
            {1: (b'LVLC', paths, links), 2: (b'LVLI', ['meshes/fixture.nif'], {1})}, {1})
        self.assertEqual(wanted, {'meshes/fixture.nif'})
        self.assertEqual(seen, {1, 2, 3})
        self.assertEqual(missing, {3})
        with self.assertRaises(ValueError):
            scene_assets.visual_links(b'NPC_', [(b'CNTO', b'bad')])


class PrivateQAHTTP(unittest.TestCase):
    def test_upload_report_and_download_privacy(self):
        # Temporary original data only. Intercept binding so CI needs no tailnet.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'downloads'; root.mkdir()
            uploads = Path(directory) / 'evidence'
            apk_name = 'openoblivion-personal-preview.apk'
            content = b'Original download protocol fixture.'
            (root / apk_name).write_bytes(content)
            bundle = 'openoblivion-installed-assets.zip'; (root / bundle).write_bytes(b'Original APK-set fixture.')
            sha = hashlib.sha256(content).hexdigest()
            (root / 'download.json').write_text(json.dumps({
                'build': 'fixture-build', 'validation': 'Unverified fixture',
                'asset_set': {'name': bundle, 'build': 'fixture-full-set'},
                'downloads': [{'name': apk_name, 'size': len(content), 'sha256': sha},
                              {'name': bundle, 'size': 25, 'sha256': hashlib.sha256((root / bundle).read_bytes()).hexdigest()}]}))
            ready = threading.Event(); servers = []
            def bind(_address, handler):
                server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
                servers.append(server); ready.set(); return server
            argv = ['sideload.py', '--root', str(root), '--uploads', str(uploads),
                    '--bind', '100.64.0.1', '--port', '8735']
            with patch.object(sys, 'argv', argv), patch.object(sideload, 'ThreadingHTTPServer', bind):
                thread = threading.Thread(target=sideload.main, daemon=True); thread.start()
                self.assertTrue(ready.wait(5), 'Server failed to start')
                server = servers[0]
                def request(method, path, body=None, headers=None):
                    connection = http.client.HTTPConnection(*server.server_address, timeout=5)
                    connection.request(method, path, body=body, headers=headers or {})
                    response = connection.getresponse()
                    result = (response.status, dict(response.headers), response.read())
                    connection.close(); return result
                try:
                    page = request('GET', '/')[2]
                    self.assertIn(b'Current QA objective', page)
                    self.assertIn(b'Send screenshots', page)
                    self.assertIn(b'Complete installed assets', page)
                    self.assertIn(bundle.encode(), page)
                    self.assertIn(b'install.cmd', page)
                    status, headers, body = request('GET', '/' + bundle)
                    self.assertEqual(status, 200)
                    self.assertEqual(headers['Content-Type'], 'application/zip')
                    self.assertEqual(body, b'Original APK-set fixture.')
                    status, headers, body = request('GET', '/' + apk_name, headers={'Range': 'bytes=2-7'})
                    self.assertEqual((status, body), (206, content[2:8]))
                    self.assertEqual(headers['Content-Range'], f'bytes 2-7/{len(content)}')
                    self.assertEqual(request('GET', '/' + apk_name, headers={'Range': 'bytes=999-'})[0], 416)
                    # Generate a tiny original PNG; no public bitmap fixture.
                    import zlib
                    def chunk(tag, data):
                        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data))
                    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
                           + chunk(b'IDAT', zlib.compress(b'\0\x20\x40\x60')) + chunk(b'IEND', b''))
                    status, _, body = request('POST', '/upload', png, {'Content-Type': 'image/png'})
                    self.assertEqual(status, 201); image_id = json.loads(body)['id']
                    shot = uploads / (image_id + '.png')
                    self.assertEqual(shot.read_bytes(), png)
                    self.assertEqual(stat.S_IMODE(shot.stat().st_mode), 0o600)
                    self.assertEqual(stat.S_IMODE(uploads.stat().st_mode), 0o700)
                    report = {'scene': 'both', 'result': 'empty', 'tested_build': 'older-phone-build',
                              'log': 'Original fixture log', 'screenshots': [image_id], 'page_apk_sha256': 'b'*64}
                    status, _, body = request('POST', '/report', json.dumps(report), {'Content-Type': 'application/json'})
                    self.assertEqual(status, 201)
                    saved = json.loads((uploads / (json.loads(body)['id'] + '.json')).read_text())
                    self.assertEqual(saved['tested_build'], 'older-phone-build')
                    self.assertEqual(saved['page_apk_sha256'], 'b'*64)
                    self.assertEqual(saved['server_apk_sha256'], sha)
                    self.assertEqual(saved['screenshots'][0]['sha256'], hashlib.sha256(png).hexdigest())
                    for path in ['/' + shot.name, '/../evidence/' + shot.name, '/evidence/', '/download.json']:
                        self.assertEqual(request('GET', path)[0], 404)
                    self.assertEqual(request('POST', '/upload', b'<svg/>')[0], 400)
                    self.assertEqual(request('POST', '/upload', png, {'Origin': 'https://foreign.example'})[0], 403)
                    self.assertEqual(request('POST', '/upload', b'', {'Content-Length': str(sideload.MAX_SCREENSHOT+1)})[0], 413)
                    self.assertEqual(request('POST', '/report', '{}', {'Content-Type': 'text/plain'})[0], 415)
                    for invalid in [dict(report, screenshots=['../escape']), dict(report, screenshots=['a'*32]),
                                    dict(report, notes='x'*8001), dict(report, log=3), []]:
                        self.assertEqual(request('POST', '/report', json.dumps(invalid), {'Content-Type': 'application/json'})[0], 400)
                finally:
                    server.shutdown(); server.server_close(); thread.join(5)


if __name__ == '__main__':
    unittest.main()
