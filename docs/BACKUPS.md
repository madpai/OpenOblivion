# Project backups

GitHub holds the public source/history at
[madpai/OpenOblivion](https://github.com/madpai/OpenOblivion). A second local
backup stores a Git bundle, a source archive (including uncommitted public
work), and a SHA256 manifest. Both archives are verified before completing
the snapshot. Game installations, packed personal APKs, dependency caches and
raw QA evidence stay in the separate private workspace.

```sh
python3 tools/backup.py --destination /outside/openoblivion-backups
git clone /outside/openoblivion-backups/SNAPSHOT/history.bundle restored-project
```

`source.tar.gz` preserves worktree contents separately from committed history;
inspect `manifest.json` and its hashes before restoring it. Restore to a fresh
directory to compare any uncommitted work. The tool refuses destinations inside
the repository and runs the public-content guard over source, index and history.
Failed/inconsistent snapshots remain visibly marked `.partial-*`.

The development host has a daily systemd user timer, `openoblivion-backup.timer`,
with a persistent catch-up run when the user manager starts. It works while
that host/user session is running; it is not an offsite backup of private data.
Snapshots are retained without automatic deletion. GitHub publication remains
an explicit review/push action, rather than an unattended upload of worktree files.

To enable the repository's publication check in another checkout:

```sh
git config core.hooksPath tools/git-hooks
python3 tools/content_guard.py --history
```

The only binary documentation exception is the exact screenshot allowlist in
`docs/media/screenshots.json`, recording reviewed hashes, provenance and the
owner's publication instruction. Other images, game assets and APKs remain
blocked. CI repeats the guard, but the pre-push check catches mistakes locally.
