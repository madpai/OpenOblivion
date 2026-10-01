#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Prepare a locked, external copy of the audited Android native build recipe."""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request
import tarfile
import zipfile
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from check_upstream import check
from integration import external, digest
from integration import apply as apply_camera, record_build

LOCK = ROOT / 'docs/research/android-native.lock.json'


def fetch(entry, cache):
    target = cache / entry['filename']
    if target.exists():
        if digest(target) != entry['sha256']:
            raise ValueError('Cached source hash mismatch: ' + entry['name'])
        return
    temporary = target.with_suffix(target.suffix + '.partial')
    with urllib.request.urlopen(entry['url'], timeout=120) as response, temporary.open('wb') as out:
        while chunk := response.read(1024 * 1024):
            out.write(chunk)
    if digest(temporary) != entry['sha256']:
        raise ValueError('Downloaded source hash mismatch: ' + entry['name'])
    temporary.rename(target)


def recipe(original, lock, cache):
    text = original
    for entry in lock['archives']:
        pattern = r'(ExternalProject_Add\(' + re.escape(entry['name']) + r'\s)(.*?)(\n\))'
        match = re.search(pattern, text, re.S)
        if not match:
            raise ValueError('Missing audited dependency: ' + entry['name'])
        block = re.sub(r'(?m)^\s*#?\s*URL_HASH[^\n]*\n', '\n', match[2])
        block, count = re.subn(r'(?m)^\s*URL\s*(?:https?://\S+\s*)+',
            '\n        URL ' + (cache / entry['filename']).as_uri()
            + '\n        URL_HASH SHA256=' + entry['sha256'] + '\n', block, count=1)
        if count != 1:
            raise ValueError('Unexpected source declaration: ' + entry['name'])
        if entry['name'] == 'bzip2':
            block = block.replace('        CONFIGURE_COMMAND',
                '        PATCH_COMMAND python3 ' + str(ROOT / 'tools/native/bzip2_cmake.py')
                + ' <SOURCE_DIR>\n\n        CONFIGURE_COMMAND', 1)
        if entry['name'] == 'gl4es':
            # It is built through ndk-build; an implicit host-CMake configure
            # serves no purpose and breaks on modern CMake.
            block = block.replace('        BUILD_COMMAND', '        CONFIGURE_COMMAND ""\n\n        BUILD_COMMAND', 1)
        text = text[:match.start(2)] + block + text[match.end(2):]
    return text.replace('set(COMMON_CMAKE_ARGS\n',
                        'set(COMMON_CMAKE_ARGS\n        -DCMAKE_POLICY_VERSION_MINIMUM=3.5\n', 1)


def prepare(donor, work):
    check(donor, 'Andiweli/OpenMW-Android')
    lock = json.loads(LOCK.read_text())
    work.mkdir(parents=True, exist_ok=True, mode=0o700)
    cache = work / 'cache'
    cache.mkdir(exist_ok=True)
    entries = lock['archives'] + lock['engine_fetchcontent'] + [dict(lock['ndk'], name='ndk')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        # Inspect every result; failure prevents recipe preparation/building.
        futures = [pool.submit(fetch, entry, cache) for entry in entries]
        errors = []
        for future in futures:
            try:
                future.result()
            except Exception as error:
                errors.append(str(error))
        if errors:
            raise ValueError('\n'.join(errors))
    source = work / 'source'
    if not source.exists():
        subprocess.run(['git', '-C', str(donor), 'worktree', 'add', '--detach', str(source),
                        lock['donor_revision']], check=True)
    if subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() != lock['donor_revision']:
        raise ValueError('External build source has a different revision')
    scripts = source / 'source/buildscripts'
    identity_path = work / 'source-preparation.json'
    identity = json.loads(identity_path.read_text()) if identity_path.exists() else None
    modified = {}
    for name in ('CMakeLists.txt', 'build.sh'):
        relative = 'source/buildscripts/' + name
        original = subprocess.check_output(['git', '-C', str(source), 'show', 'HEAD:' + relative], text=True)
        desired = recipe(original, lock, cache) if name == 'CMakeLists.txt' else original.replace(
            'cmake ../.. \\\n', 'cmake ../.. \\\n\t-DCMAKE_POLICY_VERSION_MINIMUM=3.5 \\\n', 1)
        current = (scripts / name).read_text()
        if current not in (original, desired) and (not identity or
                identity.get('recipe_sha256', {}).get(name) != digest(scripts / name)):
            raise ValueError('Unrecorded build recipe change: ' + name)
        (scripts / name).write_text(desired)
        modified[name] = digest(scripts / name)
    for path in [scripts / 'build.sh', *(scripts / 'include').glob('*.sh')]:
        path.chmod(path.stat().st_mode | 0o111)
    downloads = scripts / 'downloads'
    downloads.mkdir(exist_ok=True)
    ndk_link = downloads / lock['ndk']['filename']
    if ndk_link.exists():
        if digest(ndk_link) != lock['ndk']['sha256']:
            raise ValueError('Existing NDK archive differs')
    else:
        ndk_link.symlink_to(cache / lock['ndk']['filename'])
    identity = {'schema': 1, 'donor_revision': lock['donor_revision'], 'lock_sha256': digest(LOCK),
                'recipe_sha256': modified, 'tool_sha256': digest(Path(__file__)),
                'bzip2_adapter_sha256': digest(ROOT / 'tools/native/bzip2_cmake.py')}
    identity_path.write_text(json.dumps(identity, indent=2) + '\n')
    # The donor host-ICU helper otherwise downloads without enforcing a hash.
    # Use unzip to retain executable file modes from this verified ZIP.
    host = scripts / 'build/icu-host-build'
    host.mkdir(parents=True, exist_ok=True)
    if not (host / 'Makefile').exists():
        subprocess.run(['unzip', '-q', '-o', str(cache / 'libicu.zip')], cwd=host, check=True)
        subprocess.run(['./icu-release-70-1/icu4c/source/configure', '--disable-tests', '--disable-samples',
                        '--disable-icuio', '--disable-extras', 'CC=gcc', 'CXX=g++'], cwd=host, check=True)
    host_link = host / 'release-70-1.zip'
    if not host_link.exists():
        host_link.symlink_to(cache / 'libicu.zip')
    return source, host


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--donor', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--build', action='store_true', help='Compile the donor baseline after preparation')
    parser.add_argument('--grounded-eye', action='store_true', help='Then compile the audited native camera integration')
    args = parser.parse_args()
    if not 1 <= args.jobs <= 32:
        parser.error('Jobs must be 1..32')
    if args.grounded_eye and not args.build:
        parser.error('--grounded-eye requires --build')
    source, host = prepare(external(args.donor), external(args.work))
    if args.build:
        subprocess.run(['make', '-j' + str(args.jobs)], cwd=host, check=True)
        subprocess.run(['bash', 'buildscripts/build.sh', '--arch', 'arm64', '--jobs', str(args.jobs), '--release'],
                       cwd=source / 'source', check=True)
        if args.grounded_eye:
            stage_native(source, external(args.work), args.jobs)
    print('Verified native Android recipe: ' + str(source))


def stage_native(source, work, jobs):
    scripts = source / 'source/buildscripts'
    engine = scripts / 'build/arm64/openmw-prefix/src/openmw'
    build = scripts / 'build/arm64/openmw-prefix/src/openmw-build'
    stamp = engine / '.openoblivion-native-source.json'
    if not stamp.exists():
        baseline = work / 'baseline-engine.json'
        baseline.write_text(json.dumps({'schema': 1, 'engine_base_revision': json.loads(LOCK.read_text())['engine_base_revision'],
            'engine_sha256': digest(build / 'libopenmw.so'), 'lock_sha256': digest(LOCK)}, indent=2) + '\n')
        apply_camera(engine, json.loads(LOCK.read_text())['engine_base_revision'])
    # ExternalProject's completed stamp does not track edits inside its source.
    subprocess.run(['cmake', '--build', str(build), '--target', 'openmw', '--parallel', str(jobs)], check=True)
    runtime = work / 'runtime'
    if (runtime / 'build-manifest.json').exists():
        raise ValueError('Runtime already recorded; preserve it and use a fresh runtime destination')
    runtime.mkdir(exist_ok=True)
    import shutil
    jni = source / 'source/app/src/main/jniLibs/arm64-v8a'
    library_names = ['libopenmw.so', 'libc++_shared.so', 'libSDL2.so', 'libGL.so', 'libopenal.so', 'libcollada-dom2.5-dp.so']
    for name in library_names:
        shutil.copyfile(build / name if name == 'libopenmw.so' else jni / name, runtime / name)
    llvm = scripts / 'toolchain/ndk/toolchains/llvm/prebuilt/linux-x86_64/bin'
    subprocess.run([str(llvm / 'llvm-strip'), str(runtime / 'libopenmw.so')], check=True)
    notices = bytearray(b'OpenOblivion native Android source build: external dependency notices\n')
    lock = json.loads(LOCK.read_text())
    for entry in lock['archives'] + lock['engine_fetchcontent']:
        archive = work / 'cache' / entry['filename']
        notices.extend(('\n\n=== ' + entry['name'] + ' / source SHA256 ' + entry['sha256'] + ' ===\n').encode())
        notice_hashes = entry.get('notice_sha256', {})
        names = list(notice_hashes) if isinstance(notice_hashes, dict) else [entry['notice_path']]
        if entry['name'] == 'libjpeg-turbo':
            names.append('libjpeg-turbo-1.5.3/README.ijg')
        if zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive) as stream:
                for name in names:
                    notices.extend(('\n--- ' + name + ' ---\n').encode() + stream.read(name))
        else:
            with tarfile.open(archive) as stream:
                for name in names:
                    notices.extend(('\n--- ' + name + ' ---\n').encode() + stream.extractfile(name).read())
    # Preserve bundled engine/library licenses as well as the archive's project grant.
    for root in (engine / 'extern', scripts / 'toolchain/ndk/sources/cxx-stl/llvm-libc++'):
        if root.is_dir():
            for path in sorted(root.rglob('*')):
                if path.is_file() and path.name.casefold().startswith(('license', 'licence', 'copying', 'copyright')):
                    notices.extend(('\n--- ' + path.relative_to(root).as_posix() + ' ---\n').encode() + path.read_bytes())
    (runtime / 'third-party-notices.txt').write_bytes(notices)
    manifest = runtime / ('.build-manifest-' + uuid.uuid4().hex + '.partial')
    record = record_build(engine, runtime / 'libopenmw.so', manifest)
    record.update(native_sha256={name: digest(runtime / name) for name in library_names},
                  dependency_lock_sha256=digest(LOCK), donor_revision=json.loads(LOCK.read_text())['donor_revision'],
                  source_preparation=json.loads((work / 'source-preparation.json').read_text()),
                  resources=str(build / 'resources'), defaults=str(build / 'defaults.bin'),
                  resources_sha256={p.relative_to(build / 'resources').as_posix(): digest(p)
                                    for p in sorted((build / 'resources').rglob('*')) if p.is_file()},
                  defaults_sha256=digest(build / 'defaults.bin'))
    record['notices_sha256'] = digest(runtime / 'third-party-notices.txt')
    manifest.write_text(json.dumps(record, indent=2) + '\n')
    manifest.rename(runtime / 'build-manifest.json')


if __name__ == '__main__':
    main()
