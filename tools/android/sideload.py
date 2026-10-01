#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Serve an allowlisted personal APK on a Tailscale address with download resume."""
import argparse
from datetime import datetime, timezone
from email.utils import format_datetime
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--bind', required=True)
    parser.add_argument('--port', type=int, default=8735)
    args = parser.parse_args()
    if ipaddress.ip_address(args.bind) not in ipaddress.ip_network('100.64.0.0/10'):
        parser.error('Bind must be a private Tailscale IPv4 address')
    root = args.root.resolve(strict=True)
    repository = Path(__file__).resolve().parents[2]
    if root == repository or repository in root.parents:
        parser.error('Personal APKs must be served from outside the public checkout')
    manifest = json.loads((root / 'download.json').read_text())
    entries = {entry['name']: entry for entry in manifest['downloads']}
    for name in entries:
        if Path(name).name != name or (root / name).is_symlink() or not (root / name).is_file():
            parser.error('Invalid allowlisted download')
    apk = entries['openoblivion-personal-preview.apk']
    page = ('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OpenOblivion personal test</title><style>body{font:18px system-ui;max-width:720px;margin:40px auto;padding:0 20px;background:#141c21;color:#eae9df}a{color:#bce5f0} .download{display:inline-block;padding:18px;background:#276174;color:white;border-radius:8px;font-weight:bold}code{overflow-wrap:anywhere;font-size:13px}li{margin:12px 0}</style>
<h1>OpenOblivion Preview</h1><p>Personal ARM64 scene test with your Oblivion assets included.</p>
<p><a class="download" href="/openoblivion-personal-preview.apk">Download APK — SIZE</a></p>
<ol><li>Keep Tailscale connected while downloading. Download resume is supported.</li>
<li>Open the APK and allow installation from your browser when Android asks.</li>
<li>Open <b>OpenOblivion Preview</b>. Let the bundled assets install once, then choose Vilverin interior or exterior.</li>
<li>Use the left pad to move and drag the right side to look. Exit returns to the launcher.</li></ol>
<p>Android 10 or newer, ARM64. Allow about 3 GB of free storage for download, installation and unpacking.</p>
<p>Early world-view test using OpenMW Android 0.51 and OpenGL ES. Original quests, combat, multiplayer and Vulkan are still under development. The bundled visual assets cover Vilverin and nearby exterior cells; distant areas may have missing textures. Voices, sound and DLC are omitted.</p>
<p>VALIDATION</p><p>Build BUILD<br>SHA256: <code>HASH</code></p>
<p>For your own installation only. Keep this asset-packed APK private.</p>
<p><a href="/SHA256SUMS.txt">Checksums</a> · <a href="/source-notes.txt">Runtime source and attribution</a></p></html>'''
            .replace('SIZE', f"{apk['size'] / 1024 / 1024:.0f} MB")
            .replace('VALIDATION', html.escape(manifest['validation']))
            .replace('BUILD', html.escape(manifest['build']))
            .replace('HASH', html.escape(apk['sha256']))).encode()

    class Handler(BaseHTTPRequestHandler):
        server_version = 'OpenOblivionSideload/1'
        def do_HEAD(self): self.serve(False)
        def do_GET(self): self.serve(True)
        def serve(self, body):
            path = urlsplit(self.path).path
            if path == '/':
                self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8')
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
            self.send_header('Content-Type', 'application/vnd.android.package-archive' if name.endswith('.apk') else 'text/plain; charset=utf-8')
            self.send_header('Accept-Ranges', 'bytes'); self.send_header('ETag', etag)
            self.send_header('Last-Modified', format_datetime(datetime.fromtimestamp(file.stat().st_mtime, timezone.utc), usegmt=True))
            self.send_header('Content-Length', str(end-start+1))
            self.send_header('X-Content-Type-Options', 'nosniff')
            if name.endswith('.apk'): self.send_header('Content-Disposition', 'attachment; filename="' + name + '"')
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
