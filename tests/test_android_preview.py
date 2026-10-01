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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/android'))
import scene_assets
import sideload


class SceneDependencies(unittest.TestCase):
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
            sha = hashlib.sha256(content).hexdigest()
            (root / 'download.json').write_text(json.dumps({
                'build': 'fixture-build', 'validation': 'Unverified fixture',
                'downloads': [{'name': apk_name, 'size': len(content), 'sha256': sha}]}))
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
