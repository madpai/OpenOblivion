#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Make an emulator-only APK: the phone APK plus x86_64 native libraries.

The Android emulator on an x86_64 host runs arm64 code through a translation layer whose GLES
proxy crashes inside GL4ES (null call target in libndk_translation_proxy_libGLESv2.so, seen on
Android 14 and 16 images, software and host GPU). A native x86_64 build of the same engine
source avoids the translation. This tool leaves every other byte of the phone APK (dex,
resources, assets, payload, arm64 libraries) as built and only adds lib/x86_64/*.so, then
zip-aligns and signs with the SDK debug key. The result is for emulators and is never served to
the phone: its signature differs, so installing it over the phone build needs an uninstall.

Usage:
  make_emulator_apk.py --apk phone.apk --libs <dir with the six x86_64 .so> --output emulator.apk
                       --sdk ~/android/sdk [--keystore ~/.android/debug.keystore]
"""
import argparse
import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

LIBRARIES = ['libopenmw.so', 'libc++_shared.so', 'libSDL2.so', 'libGL.so', 'libopenal.so', 'libcollada-dom2.5-dp.so']
SIGNATURE_SUFFIXES = ('.SF', '.RSA', '.DSA', '.EC')


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def newest_build_tools(sdk):
    versions = sorted((p for p in (sdk / 'build-tools').iterdir() if (p / 'apksigner').exists()),
                      key=lambda p: [int(x) for x in p.name.split('.') if x.isdigit()])
    if not versions:
        raise SystemExit('No build-tools with apksigner under ' + str(sdk))
    return versions[-1]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--apk', required=True, type=Path)
    parser.add_argument('--libs', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--sdk', required=True, type=Path)
    parser.add_argument('--keystore', type=Path, default=Path.home() / '.android/debug.keystore')
    args = parser.parse_args()
    missing = [n for n in LIBRARIES if not (args.libs / n).is_file()]
    if missing:
        raise SystemExit('Missing x86_64 libraries: ' + ', '.join(missing))
    tools = newest_build_tools(args.sdk)
    unsigned = args.output.with_suffix('.unsigned.apk')
    aligned = args.output.with_suffix('.aligned.apk')
    with zipfile.ZipFile(args.apk) as source, zipfile.ZipFile(unsigned, 'w') as out:
        for info in source.infolist():
            name = info.filename
            if name.startswith('lib/x86_64/'):
                raise SystemExit('Input APK already has x86_64 libraries; use the phone APK')
            if name.startswith('META-INF/') and (name.endswith(SIGNATURE_SUFFIXES) or name == 'META-INF/MANIFEST.MF'):
                continue  # the old v1 signature; v2/v3 blocks vanish when the archive is rewritten
            out.writestr(info, source.read(name), compress_type=info.compress_type)
        for name in LIBRARIES:
            out.write(args.libs / name, 'lib/x86_64/' + name, compress_type=zipfile.ZIP_DEFLATED)
    subprocess.run([str(tools / 'zipalign'), '-f', '-p', '4', str(unsigned), str(aligned)], check=True)
    unsigned.unlink()
    subprocess.run([str(tools / 'apksigner'), 'sign', '--ks', str(args.keystore), '--ks-pass', 'pass:android',
                    '--key-pass', 'pass:android', '--out', str(args.output), str(aligned)], check=True)
    aligned.unlink()
    subprocess.run([str(tools / 'apksigner'), 'verify', str(args.output)], check=True)
    print('emulator APK: %s sha256=%s' % (args.output, digest(args.output)))
    for name in LIBRARIES:
        print('  lib/x86_64/%s sha256=%s' % (name, digest(args.libs / name)))


if __name__ == '__main__':
    sys.exit(main())
