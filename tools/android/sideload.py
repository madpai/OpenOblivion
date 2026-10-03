#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Private Tailscale APK downloads and owner screenshot/QA reports."""
import argparse
from datetime import datetime, timezone
from email.utils import format_datetime
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
from pathlib import Path
import re
import threading
from urllib.parse import urlsplit
import uuid
import hashlib

MAX_SCREENSHOT = 20 * 1024 * 1024
MAX_REPORT = 1024 * 1024


def stamp():
    return datetime.now(timezone.utc).isoformat()


def save_screenshot(directory, body):
    if body.startswith(b'\x89PNG\r\n\x1a\n'):
        suffix = '.png'
    elif body.startswith(b'\xff\xd8\xff'):
        suffix = '.jpg'
    elif body[:4] == b'RIFF' and body[8:12] == b'WEBP':
        suffix = '.webp'
    else:
        raise ValueError('Use a PNG, JPEG or WebP screenshot')
    identity = uuid.uuid4().hex
    path = directory / (identity + suffix)
    with path.open('xb') as stream:
        stream.write(body)
    path.chmod(0o600)
    receipt = {'schema': 1, 'kind': 'screenshot', 'id': identity, 'file': path.name,
               'size': len(body), 'sha256': hashlib.sha256(body).hexdigest(), 'received_at': stamp()}
    metadata = directory / (identity + '.json')
    metadata.write_text(json.dumps(receipt, indent=2) + '\n'); metadata.chmod(0o600)
    return {'id': identity, 'bytes': len(body)}


def save_report(directory, body, current_sha, current_build):
    try:
        data = json.loads(body)
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError('Invalid report JSON') from None
    if not isinstance(data, dict):
        raise ValueError('Expected a report object')
    fields = {'device': 120, 'android': 80, 'tested_build': 160, 'scene': 20, 'result': 30,
              'notes': 8000, 'log': 131072, 'page_apk_sha256': 64, 'qa_objective': 80}
    report = {}
    for key, limit in fields.items():
        value = data.get(key, '')
        if not isinstance(value, str) or len(value) > limit:
            raise ValueError('Invalid report field: ' + key)
        report[key] = value
    if report['scene'] not in ('interior', 'exterior', 'both', 'other'):
        raise ValueError('Choose a scene')
    if report['result'] not in ('empty', 'sky-only', 'falling', 'crash', 'geometry', 'other'):
        raise ValueError('Choose what happened')
    shots = data.get('screenshots', [])
    if not isinstance(shots, list) or len(shots) > 4:
        raise ValueError('At most four screenshots per report')
    receipts = []
    for identity in shots:
        if not isinstance(identity, str) or not re.fullmatch('[0-9a-f]{32}', identity):
            raise ValueError('Invalid screenshot ID')
        file = directory / (identity + '.json')
        if not file.is_file() or file.is_symlink():
            raise ValueError('Unknown screenshot ID')
        receipt = json.loads(file.read_text())
        if receipt.get('kind') != 'screenshot':
            raise ValueError('ID is not a screenshot')
        receipts.append(receipt)
    if not receipts and not report['notes'].strip() and not report['log'].strip():
        raise ValueError('Include a screenshot, notes or a scene log')
    identity = uuid.uuid4().hex
    report.update({'schema': 1, 'kind': 'qa-report', 'id': identity, 'received_at': stamp(),
                   'screenshots': receipts, 'server_apk_sha256': current_sha, 'server_build': current_build})
    file = directory / (identity + '.json')
    with file.open('x') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')
    file.chmod(0o600)
    return {'id': identity, 'screenshots': len(receipts)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--bind', required=True)
    parser.add_argument('--port', type=int, default=8735)
    parser.add_argument('--uploads', required=True, type=Path, help='Private evidence directory outside the download root')
    args = parser.parse_args()
    if ipaddress.ip_address(args.bind) not in ipaddress.ip_network('100.64.0.0/10'):
        parser.error('Bind must be a private Tailscale IPv4 address')
    root = args.root.resolve(strict=True)
    repository = Path(__file__).resolve().parents[2]
    if root == repository or repository in root.parents:
        parser.error('Personal APKs must be served from outside the public checkout')
    uploads = args.uploads.expanduser().resolve()
    if uploads == repository or repository in uploads.parents or uploads == root or root in uploads.parents:
        parser.error('Uploads must be outside the repository and download root')
    uploads.mkdir(parents=True, exist_ok=True, mode=0o700)
    uploads.chmod(0o700)
    upload_slots = threading.BoundedSemaphore(2)
    manifest = json.loads((root / 'download.json').read_text())
    entries = {entry['name']: entry for entry in manifest['downloads']}
    for name in entries:
        if Path(name).name != name or (root / name).is_symlink() or not (root / name).is_file():
            parser.error('Invalid allowlisted download')
    apk = entries['openoblivion-personal-preview.apk']
    replacements = {
        'SIZE': f"{apk['size'] / 1024 / 1024:.0f} MB",
        'BUILD': manifest['build'], 'VALIDATION': manifest['validation'],
        'HASH': apk['sha256'], 'QA_ID': manifest.get('qa_id', 'OO-ANDROID-002'),
        'QA_OBJECTIVE': manifest.get('qa_objective', 'Verify visible dungeon geometry and exterior ground, then check look and movement.'),
    }
    page_text = Path(__file__).with_name('sideload.html').read_text()
    for key, value in replacements.items():
        page_text = page_text.replace('@@' + key + '@@', html.escape(value))
    complete = manifest.get('asset_set')
    asset_section = ''
    if complete:
        name = complete['name']
        if name not in entries or not name.endswith('.zip'):
            parser.error('Complete APK set must be an allowlisted ZIP download')
        entry = entries[name]
        asset_section = ('<section class="panel"><h2>Complete installed assets</h2><p><a class="download" href="/'
            + html.escape(name, quote=True) + '">Download full APK set — '
            + f"{entry['size'] / 1024**3:.2f} GiB" + '</a></p><p>Build '
            + html.escape(complete['build']) + '. Includes the installed archives, expansions, music, voices and videos.</p>'
            + '<p>This optional package uses the same preview engine as the single APK. '
              'Both packages start at the same Vilverin interior or exterior. '
              'The full set supplies scenery, textures and models for exploring farther from Vilverin. '
              'You can try walking into surrounding areas and report missing artwork, collision problems or crashes. '
              'That wider phone exploration remains unverified. It does not add completed quests or combat; '
              'the smaller APK already includes the gate fix, NPC idle and nearby door sounds.</p>'
            + '<p>Unzip on a computer, connect your Android phone with USB debugging enabled and '
              'Android platform-tools (adb) available, then run <b>install.cmd</b> on Windows or '
              '<b>sh install.sh</b> on Linux/macOS. The script installs every signed APK together. '
              'Opening base.apk alone will not install the full set.</p>'
            + '<p>Allow about 18 GB free for downloading, installing and unpacking. '
              'Complete assets support further testing; original gameplay and audio/video playback remain incomplete.</p>'
            + '<p class="muted">SHA256: <code>' + html.escape(entry['sha256']) + '</code></p></section>')
    page_text = page_text.replace('@@ASSET_SET@@', asset_section)
    page = page_text.encode()


    class Handler(BaseHTTPRequestHandler):
        server_version = 'OpenOblivionSideload/1'
        def do_HEAD(self): self.serve(False)
        def do_GET(self): self.serve(True)
        def respond_json(self, code, data):
            body = json.dumps(data).encode()
            self.send_response(code); self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body))); self.send_header('Cache-Control', 'no-store')
            self.end_headers(); self.wfile.write(body)
        def do_POST(self):
            path = urlsplit(self.path).path
            if path not in ('/upload', '/report'):
                self.respond_json(404, {'error': 'Not found'}); return
            origin = self.headers.get('Origin')
            if origin and origin != f'http://{args.bind}:{args.port}':
                self.respond_json(403, {'error': 'Use the private sideload page to upload'}); return
            if self.headers.get('Transfer-Encoding') or self.headers.get('Content-Encoding', 'identity') != 'identity':
                self.respond_json(400, {'error': 'Encoded uploads are not supported'}); return
            try:
                size = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                size = 0
            limit = MAX_SCREENSHOT if path == '/upload' else MAX_REPORT
            if size <= 0 or size > limit:
                self.respond_json(413, {'error': 'Upload is empty or exceeds the size limit'}); return
            if path == '/report' and self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                self.respond_json(415, {'error': 'Report must use JSON'}); return
            if not upload_slots.acquire(blocking=False):
                self.respond_json(503, {'error': 'Uploads are busy; try again shortly'}); return
            try:
                self.connection.settimeout(30)
                body = self.rfile.read(size)
                if len(body) != size:
                    raise ValueError('Upload was interrupted; try again')
                result = (save_screenshot(uploads, body) if path == '/upload'
                          else save_report(uploads, body, apk['sha256'], manifest['build']))
                self.respond_json(201, result)
                self.log_message('Saved private %s id=%s', path[1:], result['id'])
            except ValueError as error:
                self.respond_json(400, {'error': str(error)})
            except OSError:
                self.respond_json(500, {'error': 'Could not store the upload; please retry'})
            finally:
                upload_slots.release()
        def serve(self, body):
            path = urlsplit(self.path).path
            if path == '/':
                self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Content-Length', str(len(page))); self.end_headers()
                if body: self.wfile.write(page)
                return
            name = path.removeprefix('/')
            if name not in entries:
                self.send_error(404); return
            entry = entries[name]
            file = root / name
            if file.is_symlink() or file.stat().st_size != entry['size']:
                self.send_error(503, 'Download changed; restart the service after verification'); return
            size = entry['size']; start, end = 0, size - 1; partial = False
            etag = '"' + entry['sha256'] + '"'
            range_header = self.headers.get('Range')
            if range_header and self.headers.get('If-Range', etag) == etag:
                match = re.fullmatch(r'bytes=(\d*)-(\d*)', range_header)
                if match and (match[1] or match[2]):
                    start = int(match[1]) if match[1] else max(0, size - int(match[2]))
                    end = min(size-1, int(match[2])) if match[1] and match[2] else size-1
                    partial = True
                if not partial or start > end or start >= size:
                    self.send_response(416); self.send_header('Content-Range', f'bytes */{size}')
                    self.send_header('Content-Length', '0'); self.end_headers(); return
            self.send_response(206 if partial else 200)
            mime = ('application/vnd.android.package-archive' if name.endswith('.apk')
                    else 'application/zip' if name.endswith('.zip') else 'text/plain; charset=utf-8')
            self.send_header('Content-Type', mime)
            self.send_header('Accept-Ranges', 'bytes'); self.send_header('ETag', etag)
            self.send_header('Last-Modified', format_datetime(datetime.fromtimestamp(file.stat().st_mtime, timezone.utc), usegmt=True))
            self.send_header('Content-Length', str(end-start+1))
            self.send_header('X-Content-Type-Options', 'nosniff')
            if name.endswith(('.apk', '.zip')): self.send_header('Content-Disposition', 'attachment; filename="' + name + '"')
            if partial: self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
            self.end_headers()
            if not body: return
            try:
                with file.open('rb') as stream:
                    stream.seek(start); remaining = end-start+1
                    while remaining:
                        block = stream.read(min(1024*1024, remaining))
                        if not block: break
                        self.wfile.write(block); remaining -= len(block)
            except (BrokenPipeError, ConnectionResetError):
                pass
    server = ThreadingHTTPServer((args.bind, args.port), Handler)
    server.daemon_threads = True
    print(f'Private sideload server: http://{args.bind}:{args.port}/', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
