#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Back up public source/history to a verified external local snapshot."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile

from content_guard import check


def backup(root, destination):
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if destination == root or root in destination.parents:
        raise ValueError('Backups must be outside the repository')
    errors = check(root, history=True)
    if errors:
        raise ValueError('Public content guard rejected backup: ' + repr(errors))
    def git(*args):
        return subprocess.check_output(['git','-C',str(root),*args], stderr=subprocess.STDOUT)
    head = git('rev-parse','HEAD').decode().strip()
    names = sorted(set(n.decode() for n in git('ls-files','--cached','--others','--exclude-standard','-z').split(b'\0') if n))
    files = {name:(root/name).read_bytes() for name in names if (root/name).is_file()}
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(destination,0o700)
    snapshot = Path(tempfile.mkdtemp(prefix='.partial-',dir=destination))
    bundle = snapshot/'history.bundle'
    git('bundle','create',str(bundle),'--all')
    git('bundle','verify',str(bundle))
    archive = snapshot/'source.tar.gz'
    with tarfile.open(archive,'w:gz') as out:
        for name, data in files.items():
            info=tarfile.TarInfo(name); info.size=len(data)
            info.mode=0o755 if os.access(root/name,os.X_OK) else 0o644
            out.addfile(info,io.BytesIO(data))
    with tarfile.open(archive,'r:gz') as saved:
        for name,data in files.items():
            if saved.extractfile(name).read()!=data:
                raise ValueError('Source archive verification failed: '+name)
    if git('rev-parse','HEAD').decode().strip()!=head:
        raise ValueError('HEAD changed while backing up; partial snapshot retained')
    for name,data in files.items():
        if (root/name).read_bytes()!=data:
            raise ValueError('Source changed while backing up; partial snapshot retained')
    def digest(path):
        with path.open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()
    manifest={'schema':1,'created_at':datetime.now(timezone.utc).isoformat(),'head':head,
              'scope':'Public project source and all Git refs; excludes private game data/APKs/raw QA',
              'files':{name:hashlib.sha256(data).hexdigest() for name,data in files.items()},
              'archives':{p.name:{'bytes':p.stat().st_size,'sha256':digest(p)} for p in (bundle,archive)}}
    (snapshot/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    for path in snapshot.iterdir():
        path.chmod(0o600)
        with path.open('rb') as stream: os.fsync(stream.fileno())
    final=destination/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+head[:10])
    snapshot.rename(final)
    return final


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps({'backup':str(backup(args.root,args.destination))}))
