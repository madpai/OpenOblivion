#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Compile original KF/skin fixtures against the recorded Linux native engine."""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--build', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--image', default='openoblivion-research-build:founding')
    parser.add_argument('--inside', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.inside:
        lines = Path('/work/build/build.ninja').read_text().splitlines()
        start = next(i for i, line in enumerate(lines) if line.startswith('build niftest:'))
        link = next(line.split('=', 1)[1].strip() for line in lines[start + 1:]
                    if line.startswith('  LINK_LIBRARIES ='))
        # RecordPtrT has a different Debug layout. Match the Release library;
        # fixture require() checks remain active even with NDEBUG.
        subprocess.run(['/usr/bin/c++', '-std=c++20', '-DNDEBUG', '-I/source', '-I/work/build',
                        '-I/source/components/nifosg', '-I/source/apps/openmw/mwrender',
                        '/evidence/fixture.cpp', '-o', '/evidence/fixture', *shlex.split(link)],
                       check=True, cwd='/work/build')
        subprocess.run(['/evidence/fixture'], check=True)
        return
    if not args.source or not args.build or not args.output:
        parser.error('--source, --build and --output are required')
    from tes4_animation import digest, external, verify
    from tes4_interactions import verify as verify_interactions
    source, build, output = map(external, (args.source, args.build, args.output))
    receipt = verify(source)
    verify_interactions(source)
    if receipt['base_revision'] != '46bd4599203ee52ffc0f3e8edb3fc159a0303a49':
        raise ValueError('These linker fixtures require the audited desktop build')
    output.mkdir(mode=0o700)
    here = Path(__file__).resolve().parent
    shutil.copyfile(here / 'tes4_kf_fixtures.cpp', output / 'fixture.cpp')
    command = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
               '-v', f'{source}:/source:ro', '-v', f'{build}:/work/build:ro',
               '-v', f'{here}:/tools:ro', '-v', f'{output}:/evidence',
               '--entrypoint', 'python3', args.image, '/tools/run_kf_fixtures.py', '--inside']
    result = subprocess.run(command, capture_output=True, text=True)
    (output / 'stdout.txt').write_text(result.stdout)
    (output / 'stderr.txt').write_text(result.stderr)
    (output / 'receipt.json').write_text(json.dumps({'native_integration': receipt,
        'runner_sha256': digest(Path(__file__)), 'fixture_sha256': digest(output / 'fixture.cpp'),
        'returncode': result.returncode}, indent=2) + '\n')
    print(result.stdout, end='')
    result.check_returncode()


if __name__ == '__main__':
    main()
