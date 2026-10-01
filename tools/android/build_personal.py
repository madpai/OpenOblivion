#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Stage a private, self-contained ARM64 scene APK from audited external inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from check_upstream import check
from scene_assets import select


def digest(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def outside(path):
    path = path.expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError('Game data, donor files and build outputs must stay outside the public checkout')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--donor', required=True, type=Path)
    parser.add_argument('--upstream-apk', required=True, type=Path)
    parser.add_argument('--template', required=True, type=Path)
    parser.add_argument('--data', required=True, type=Path)
    parser.add_argument('--assetlab', required=True, type=Path, help='Audited external BSA reader checkout')
    parser.add_argument('--work', required=True, type=Path, help='Private staging/build directory')
    parser.add_argument('--sdk', required=True, type=Path)
    parser.add_argument('--gradle', required=True, type=Path)
    parser.add_argument('--native-runtime', type=Path, help='External audited native source-build runtime directory')
    args = parser.parse_args()
    work, data, template, donor, apk = map(outside, (args.work, args.data, args.template, args.donor, args.upstream_apk))
    lock = json.loads((ROOT / 'docs/research/upstreams.lock.json').read_text())['Andiweli/OpenMW-Android']
    check(donor, 'Andiweli/OpenMW-Android')
    check(template, 'OpenMW/example-suite')
    if digest(apk) != lock['release_sha256']:
        raise ValueError('Upstream APK hash does not match the audited release')
    work.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(work, 0o700)
    host = work / 'host'
    shutil.copytree(ROOT / 'android/host', host, dirs_exist_ok=True)
    stage = work / 'payload-source'
    stage.mkdir(exist_ok=True)
    jni = host / 'app/src/main/jniLibs/arm64-v8a'
    jni.mkdir(parents=True, exist_ok=True)
    native_hashes = {}
    with zipfile.ZipFile(apk) as archive:
        names = ['libc++_shared.so', 'libopenal.so', 'libSDL2.so', 'libGL.so', 'libcollada-dom2.5-dp.so', 'libopenmw.so']
        for name in names:
            content = archive.read('lib/arm64-v8a/' + name)
            sha = hashlib.sha256(content).hexdigest()
            if name == 'libopenmw.so' and sha != lock['libopenmw_sha256']:
                raise ValueError('Released native engine differs from its source-side hash')
            (jni / name).write_bytes(content)
            native_hashes[name] = sha
        for name in archive.namelist():
            for prefix, destination in [('assets/libopenmw/resources/', 'resources/'), ('assets/libopenmw/openmw/', 'base/')]:
                if name.startswith(prefix) and not name.endswith('/'):
                    relative = Path(destination + name[len(prefix):])
                    if relative.is_absolute() or '..' in relative.parts:
                        raise ValueError('Invalid upstream archive path')
                    out = stage / relative
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_bytes(archive.read(name))
    native_build = None
    if args.native_runtime:
        runtime = outside(args.native_runtime)
        native_build = json.loads((runtime / 'build-manifest.json').read_text())
        native_lock = ROOT / 'docs/research/android-native.lock.json'
        if (native_build.get('schema') != 1 or native_build.get('engine_kind') != 'openoblivion-native-integration'
                or native_build.get('base_revision') != lock['engine_base_revision']
                or native_build.get('donor_revision') != lock['revision']
                or native_build.get('dependency_lock_sha256') != digest(native_lock)):
            raise ValueError('Native source-build provenance differs from the audited Android baseline')
        for name, sha in native_build['tools_sha256'].items():
            if name not in ('tools/native/integration.py', 'tools/native/grounded_eye.hpp', 'tools/native/camera_grounded_eye.patch') or digest(ROOT / name) != sha:
                raise ValueError('Native integration source tools have changed')
        if set(native_build['native_sha256']) != set(native_hashes):
            raise ValueError('Native source build must contain the exact six open-source runtime libraries')
        for name, sha in native_build['native_sha256'].items():
            if digest(runtime / name) != sha:
                raise ValueError('Native source library hash mismatch: ' + name)
            shutil.copyfile(runtime / name, jni / name)
        native_hashes = native_build['native_sha256']
        resources = outside(Path(native_build['resources']))
        for name, sha in native_build['resources_sha256'].items():
            path = Path(name)
            if path.is_absolute() or '..' in path.parts or digest(resources / path) != sha:
                raise ValueError('Native source resource mismatch: ' + name)
        # Use the resources produced by this exact engine build, without
        # carrying obsolete files from the released resource tree.
        shutil.rmtree(stage / 'resources')
        shutil.copytree(resources, stage / 'resources')
        defaults = outside(Path(native_build['defaults']))
        if digest(defaults) != native_build['defaults_sha256']:
            raise ValueError('Native source defaults mismatch')
        shutil.copyfile(defaults, stage / 'base/defaults.bin')
    java = host / 'app/src/main/java/org/libsdl/app'
    java.mkdir(parents=True, exist_ok=True)
    bridge = donor / 'source/app/src/main/java/org/libsdl/app'
    java_hashes = {}
    for source in sorted(bridge.glob('*.java')):
        shutil.copyfile(source, java / source.name)
        java_hashes[source.name] = digest(source)
    assets = host / 'app/src/main/assets'
    assets.mkdir(parents=True, exist_ok=True)
    notices = assets / 'licenses'; notices.mkdir(exist_ok=True)
    for source, name in [(donor / 'LICENSE', 'OpenMW-Android-GPL.txt'), (donor / 'source/3rdparty-licenses.txt', 'donor-third-party.txt'),
                         (template / 'LICENSE', 'Template-LICENSE.txt'), (template / 'AUTHORS.md', 'Template-AUTHORS.md'),
                         (ROOT / 'LICENSE', 'OpenOblivion-GPL.txt'), (ROOT / 'NOTICE.md', 'OpenOblivion-NOTICE.md')]:
        shutil.copyfile(source, notices / name)
    if native_build:
        if digest(runtime / 'third-party-notices.txt') != native_build['notices_sha256']:
            raise ValueError('Native source notices mismatch')
        shutil.copyfile(runtime / 'third-party-notices.txt', notices / 'native-source-third-party.txt')
    shutil.copyfile(template / 'settings.cfg', stage / 'template-settings.cfg')
    paths = [(file, 'template/' + file.relative_to(template / 'game_template/data').as_posix())
             for file in sorted((template / 'game_template/data').rglob('*')) if file.is_file()]
    paths += [(file, file.relative_to(stage).as_posix()) for file in sorted(stage.rglob('*')) if file.is_file()]
    # Original read-only camera/player diagnostics; no donor scripts modified.
    paths += [(ROOT / 'tools/android/phone_qa.omwscripts', 'qa/phone_qa.omwscripts'),
              (ROOT / 'tools/android/scripts/openoblivion_phone_qa.lua', 'qa/scripts/openoblivion_phone_qa.lua'),
              (ROOT / 'tools/android/look_name.omwscripts', 'qa/look_name.omwscripts'),
              (ROOT / 'tools/android/scripts/openoblivion_look_name.lua', 'qa/scripts/openoblivion_look_name.lua'),
              (ROOT / 'tools/android/run_gate.omwscripts', 'qa/run_gate.omwscripts'),
              (ROOT / 'tools/android/scripts/openoblivion_run_gate.lua', 'qa/scripts/openoblivion_run_gate.lua'),
              (ROOT / 'tools/android/camera_repair.omwscripts', 'qa/camera_repair.omwscripts'),
              (ROOT / 'tools/android/scripts/openoblivion_preview_camera.lua', 'qa/scripts/openoblivion_preview_camera.lua')]
    if native_build:
        # Read-only QA sampling, without the rejected pre-physics Lua filter.
        paths += [(ROOT / 'tools/android/native_stair_qa.omwscripts', 'qa/native_stair_qa.omwscripts'),
                  (ROOT / 'tools/android/scripts/openoblivion_stair_qa.lua', 'qa/scripts/openoblivion_stair_qa.lua')]
    selection = work / 'scene-data'
    if selection.exists():
        if selection.is_symlink(): raise ValueError('Selection directory must not be a symlink')
        shutil.rmtree(selection)
    paths += select(data, outside(args.assetlab), selection)
    game_names = ['Oblivion.esm']
    paths += [(data / name, 'data/' + name) for name in game_names]
    files = [{'path': name, 'size': file.stat().st_size, 'sha256': digest(file)} for file, name in paths]
    identity = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    manifest = {'schema': 1, 'id': identity, 'unpacked_bytes': sum(f['size'] for f in files), 'files': files}
    manifest_path = assets / 'payload-manifest.json'
    payload = assets / 'payload.zip'
    # Reuse only a byte-verified previous payload, never stale game/source changes.
    cache = work / 'payload-cache.json'
    previous = json.loads(cache.read_text()) if cache.exists() else {}
    if previous.get('id') != identity or not payload.is_file() or digest(payload) != previous.get('zip_sha256'):
        print('Packing private visual assets (no voices, DLC or game binaries)', flush=True)
        with zipfile.ZipFile(payload, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as out:
            for file, name in paths:
                if name == 'data/Oblivion.esm': print('Packing private master and scene dependencies', flush=True)
                out.write(file, name)
        if payload.stat().st_size > 1900 * 1024 * 1024:
            raise ValueError('Payload too large for this single-APK test budget')
        cache.write_text(json.dumps({'id': identity, 'zip_sha256': digest(payload)}) + '\n')
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    provenance = {'schema': 1, 'purpose': 'Personal owner-data scene preview, never a public release',
                  'donor': lock, 'java_sha256': java_hashes, 'native_sha256': native_hashes,
                  'payload_id': identity, 'payload_bytes': payload.stat().st_size,
                  'unpacked_bytes': manifest['unpacked_bytes'], 'template_revision': check(template, 'OpenMW/example-suite')}
    provenance['native_source_build'] = native_build
    provenance['host_source_sha256'] = {file.relative_to(ROOT / 'android/host').as_posix(): digest(file)
                                       for file in sorted((ROOT / 'android/host').rglob('*')) if file.is_file()}
    provenance['preview_tools_sha256'] = {file.relative_to(ROOT).as_posix(): digest(file) for file in
        (Path(__file__).resolve(), ROOT / 'tools/android/scene_assets.py',
         ROOT / 'tools/android/phone_qa.omwscripts', ROOT / 'tools/android/scripts/openoblivion_phone_qa.lua',
         ROOT / 'tools/android/look_name.omwscripts', ROOT / 'tools/android/scripts/openoblivion_look_name.lua')}
    for file in (ROOT / 'tools/android/camera_repair.omwscripts', ROOT / 'tools/android/scripts/openoblivion_preview_camera.lua'):
        provenance['preview_tools_sha256'][file.relative_to(ROOT).as_posix()] = digest(file)
    (assets / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    (host / 'local.properties').write_text('sdk.dir=' + str(args.sdk.resolve()) + '\n')
    result = host / 'app/build/outputs/apk/debug/app-debug.apk'
    # AGP's incremental ZIP writer can leave the old large payload as dead
    # space. Recreate only this generated APK; keep compilation caches.
    if result.is_symlink(): raise ValueError('Generated APK must not be a symlink')
    result.unlink(missing_ok=True)
    subprocess.run([str(args.gradle.resolve()), '--no-daemon', '--console=plain',
                    '-PooNativeGroundedEye=' + ('true' if native_build else 'false'), 'assembleDebug'], cwd=host, check=True)
    with zipfile.ZipFile(result) as built:
        if result.stat().st_size > sum(entry.compress_size for entry in built.infolist()) + 16*1024*1024:
            raise ValueError('APK contains excessive unused ZIP space; regenerate the APK')
        print('Checking APK CRCs and exact native hashes', flush=True)
        bad = built.testzip()
        if bad:
            raise ValueError('APK CRC failed: ' + bad)
        for name, sha in native_hashes.items():
            if hashlib.sha256(built.read('lib/arm64-v8a/' + name)).hexdigest() != sha:
                raise ValueError('Packaged native library changed: ' + name)
    output = work / 'openoblivion-personal-preview.apk'
    shutil.copyfile(result, output)
    if digest(output) != digest(result):
        raise ValueError('APK changed while copying')
    provenance['apk_sha256'] = digest(output)
    provenance['apk_bytes'] = output.stat().st_size
    (work / 'build-manifest.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps({'apk': str(output), 'bytes': provenance['apk_bytes'], 'sha256': provenance['apk_sha256']}))


if __name__ == '__main__':
    main()
