#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Sign asset-only APK splits and package a private complete installation set.

The outer download ZIP may use ZIP64. Each signed Android APK is ZIP32.
This is an adb-installable APK set, not a bundletool APKS/Play bundle.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

from payload import digest

ROOT = Path(__file__).resolve().parents[2]


def outside(path):
    path = path.expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError('Private APK sets must stay outside the public checkout')
    return path


def run(args):
    return subprocess.check_output([str(arg) for arg in args], text=True, stderr=subprocess.STDOUT)


def certificate(apksigner, apk):
    verified = run([apksigner, 'verify', '--verbose', '--print-certs', apk])
    match = re.search(r'^Signer #1 certificate SHA-256 digest: ([0-9a-f]{64})$', verified, re.M)
    if (not match or 'Number of signers: 1' not in verified
            or 'Verified using v2 scheme (APK Signature Scheme v2): true' not in verified):
        raise ValueError('Expected one verified v2 APK signer')
    return match[1]


def build(base, part_directory, sdk, output, keystore):
    base, part_directory, output, keystore = map(outside, (base, part_directory, output, keystore))
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    manifest = json.loads((part_directory / 'payload-manifest.json').read_text())
    if manifest.get('schema') != 2 or manifest.get('content_scope') != 'installed-data':
        raise ValueError('Expected complete installed-data payload manifest')
    sdk = sdk.expanduser().resolve()
    bt = sdk / 'build-tools/35.0.0'
    aapt, signer, align = (bt / name for name in ('aapt2', 'apksigner', 'zipalign'))
    badging = run([aapt, 'dump', 'badging', base])
    match = re.search(r"package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'", badging)
    if not match or match[1] != 'org.openoblivion.preview':
        raise ValueError('Unexpected base package')
    package, code, version = match.groups()
    expected_signer = certificate(signer, base)
    with zipfile.ZipFile(base) as apk:
        if json.loads(apk.read('assets/payload-manifest.json')) != manifest:
            raise ValueError('Base APK and payload manifest differ')
        first = manifest['parts'][0]
        if digest(part_directory / first['asset']) != first['sha256']:
            raise ValueError('Base payload changed')
        with apk.open('assets/' + first['asset']) as stream:
            import hashlib
            if hashlib.file_digest(stream, 'sha256').hexdigest() != first['sha256']:
                raise ValueError('Base payload differs from its manifest')
    shutil.copyfile(base, output / 'base.apk')
    apks = [output / 'base.apk']
    for index, part in enumerate(manifest['parts'][1:], 1):
        asset = part['asset']
        if Path(asset).name != asset or not asset.endswith('.zip'):
            raise ValueError('Invalid payload part name')
        source = part_directory / asset
        if source.stat().st_size != part['size'] or digest(source) != part['sha256']:
            raise ValueError('Payload part changed: ' + asset)
        name = f'assets_{index:03d}'
        xml = output / (name + '.xml')
        xml.write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{package}" split="{name}" android:versionCode="{code}" android:versionName="{version}">
    <uses-sdk android:minSdkVersion="29" android:targetSdkVersion="32" />
    <application android:hasCode="false" />
</manifest>
''')
        unsigned, aligned, signed = (output / (name + suffix) for suffix in ('.unsigned.apk', '.aligned.apk', '.apk'))
        for generated in (unsigned, aligned, signed):
            if generated.is_symlink():
                raise ValueError('Generated split output must not be a symbolic link')
            generated.unlink(missing_ok=True)
        run([aapt, 'link', '--manifest', xml, '-I', sdk / 'platforms/android-35/android.jar', '-o', unsigned])
        with zipfile.ZipFile(unsigned, 'a', compression=zipfile.ZIP_STORED, allowZip64=False) as apk:
            apk.write(source, 'assets/' + asset)
        run([align, '-f', '4', unsigned, aligned])
        run([signer, 'sign', '--ks', keystore, '--ks-key-alias', 'androiddebugkey',
             '--ks-pass', 'pass:android', '--key-pass', 'pass:android',
             '--v1-signing-enabled', 'false', '--v2-signing-enabled', 'true', '--v3-signing-enabled', 'false',
             '--v4-signing-enabled', 'false', '--out', signed, aligned])
        if certificate(signer, signed) != expected_signer:
            raise ValueError('Asset split signer differs from base')
        run([align, '-c', '4', signed])
        split_badging = run([aapt, 'dump', 'badging', signed])
        if f"split='{name}'" not in split_badging or f"versionCode='{code}'" not in split_badging:
            raise ValueError('Unexpected signed split identity')
        with zipfile.ZipFile(signed) as apk:
            if apk.testzip():
                raise ValueError('Signed asset split failed CRC check')
        apks.append(signed)
        for temporary in (xml, unsigned, aligned):
            temporary.unlink()
    entries = [{'name': file.name, 'size': file.stat().st_size, 'sha256': digest(file)} for file in apks]
    receipt = {'schema': 1, 'format': 'adb-apk-set', 'package': package, 'version_code': int(code),
               'version_name': version, 'certificate_sha256': expected_signer, 'payload_id': manifest['id'],
               'unpacked_bytes': manifest['unpacked_bytes'], 'content_scope': manifest['content_scope'], 'apks': entries}
    receipt['tools_sha256'] = {name: digest(ROOT / name) for name in
                               ('tools/android/payload.py', 'tools/android/split_assets.py')}
    receipt['sdk_tools_sha256'] = {file.name: digest(file) for file in
                                   (aapt, signer, align, sdk / 'platforms/android-35/android.jar')}
    (output / 'package-manifest.json').write_text(json.dumps(receipt, indent=2) + '\n')
    (output / 'SHA256SUMS.txt').write_text(''.join(f"{e['sha256']}  {e['name']}\n" for e in entries))
    arguments = ' '.join(e['name'] for e in entries)
    (output / 'install.sh').write_text('#!/bin/sh\nset -eu\ncd -- "$(dirname -- "$0")"\nadb install-multiple -r ' + arguments + '\n')
    (output / 'install.sh').chmod(0o700)
    (output / 'install.cmd').write_text('@echo off\r\ncd /d "%~dp0"\r\nadb install-multiple -r ' + arguments + '\r\n')
    (output / 'README.txt').write_text(
        'OpenOblivion private complete installed-data APK set\n\n'
        'Unzip this whole download on your computer. Connect your ARM64 Android 10+\n'
        'phone with USB debugging enabled and Android platform-tools (adb) available.\n'
        'Run install.cmd on Windows, or sh install.sh on Linux/macOS. Install every\n'
        'APK together; opening base.apk alone cannot install the complete package.\n'
        'Then open OpenOblivion Preview and keep it open during asset verification.\n'
        'Allow about 18 GB free for the download, APK installation and extracted data.\n\n'
        'All files in the supplied classic Data directory are preserved, including\n'
        'base/expansion archives, plugins, music, voices, videos and shaders.\n'
        'Game EXE/DLL files are excluded. Packaged content does not implement quests,\n'
        'combat, animation, original menus, audio/video playback or save parity.\n'
        'Only Oblivion.esm and installed Shivering Isles/Knights plugins are enabled;\n'
        'other packaged plugins require an explicitly verified load order.\n\n'
        'This is an adb APK set, not a bundletool .apks file. Source/attribution:\n'
        'https://github.com/madpai/OpenOblivion (base APK contains dependency notices).\n'
        'For this owner installation only. Keep the entire package private.\n')
    bundle = output / 'openoblivion-installed-assets.zip'
    with zipfile.ZipFile(bundle, 'w', compression=zipfile.ZIP_STORED) as archive:
        for file in [*apks, *[output / name for name in ('package-manifest.json', 'SHA256SUMS.txt', 'install.sh', 'install.cmd', 'README.txt')]]:
            archive.write(file, file.name)
    receipt['download'] = {'name': bundle.name, 'size': bundle.stat().st_size, 'sha256': digest(bundle)}
    (output / 'build-manifest.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, type=Path)
    parser.add_argument('--parts', required=True, type=Path)
    parser.add_argument('--sdk', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--keystore', type=Path, default=Path.home() / '.android/debug.keystore')
    args = parser.parse_args()
    print(json.dumps(build(args.base, args.parts, args.sdk, args.output, args.keystore), indent=2))
