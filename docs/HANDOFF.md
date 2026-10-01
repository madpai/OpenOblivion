# Maintainer handoff

Founding checkpoint: 2026-09-30. This is a local repository with no remote
publication. Original project code is GPL-3.0-only; owner content stays private.

Personal sideload checkpoint: 2026-10-01. The user requested an asset-packed
test APK and a separate server like MegaMod's. The original Android launcher,
touch overlay and build/server tools are under `android/host` and `tools/android`.
They stage a pinned external OpenMW Android 0.51 baseline and a private visual
slice, not our new Vulkan/multiplayer runtime. The owner's APK/download root is
`/home/commander/openoblivion-private/sideload`, served only on Tailscale port
8735 by the user unit `openoblivion-sideload.service`. It is never a public
release. See [Android checkpoint](ANDROID.md) for the emulator graphics failure
and the owner's failed physical-phone views. The 0.2 diagnostic APK expands NPC
visual dependencies and logs camera/player positions; it is not a confirmed
phone rendering fix. The sideload page now includes screenshot uploads and
QA objective `OO-ANDROID-002`. Reports live in
`/home/commander/openoblivion-private/evidence/phone-qa`, outside downloads/Git.
Next compare phone screenshots and `OPENOBLIVION_PHONE_QA` samples with the
desktop loose-slice evidence to distinguish camera/spawn and rendering failures.

## Decisions and measured state

Read [ADR 0001](decisions/0001-foundation.md). Current OpenMW is selected as the
compatibility foundation. Its unchanged reader slice is compiled externally;
there is no vendored/merged engine, renderer, TES3MP server or Lua runtime.
Vulkan and strict authority are separate future integration work.

The native classic TES4 scan passes against the owner's 277,504,985-byte
master: 1,167,017 records / 85,079 groups / 41,789 compressed records. It uses
an independently authored reader-API loop because the pinned upstream
`ReaderUtils::readItem` can omit the final grouped record. Original fixtures
reproduce and cover this issue; no upstream file was patched.

Linux tools and Android ARM64 tools build. Eighteen tests pass in the normal
build; the founding fourteen also passed ASan/UBSan. The Vulkan probe enumerates
a desktop GPU; it does not render.
Six existing Asset Lab original-fixture tests were reproduced with the private
PyFFI environment and explicit NIFXMLPATH. Neither sibling checkout was edited.

Source/revisions/licenses: [license matrix](research/LICENSE_MATRIX.md),
[lock](research/upstreams.lock.json). Raw evidence is external; public results
are in [REPRODUCTION.md](research/REPRODUCTION.md). GitHub workflow is authored,
not remotely executed. No physical Android device was available through ADB;
the owner supplied a phone log and failure description.

## Continue here

M1 is in progress. Full upstream `openmw`, `esmtool`, `bsatool` and `niftest`
build in isolated Ubuntu; no donor source edits or host package installs.
One real static NIF agrees byte-for-byte between upstream/Asset Lab BSA readers
and passes upstream NIF parsing. See [build/probe recipe](../tools/upstream/README.md).
The later-game viewer requires a base game; use the audited public Template
alongside owner Oblivion content. Hydrate its LFS objects and verify their
committed size/hash. Do not silently patch the pinned reader to make tests pass.

Private interior/exterior probes now enter the requested cells, render and
exit cleanly. Screenshots were inspected: textured dungeon geometry and exterior
terrain/water/statics are present. Software llvmpipe was used. Template/UI,
COLLADA and some original texture/interpolator errors remain in the logs;
collision accuracy, motion and animation are not validated.

Next verify collision/traversal and typed override/master-reference fixtures,
then measure the content/scene boundary and use the same private scenes to
compare Vulkan donor work. Implement a small original
authoritative co-op slice before broad TES4 combat/quest conversion. See
[ROADMAP.md](ROADMAP.md) for acceptance gates and [MULTIPLAYER.md](MULTIPLAYER.md)
for ownership/persistence requirements.

## Tooling boundaries and authored limits

- `openoblivion-inspect`: read-only classic TES4 1.0/1.2, 20-byte headers,
  generic visited subrecords, count-only stdout; no load order/gameplay.
- Scanner limits are authored: 2 GiB input, 32 MiB record/declared inflation,
  64 nested groups and 2,000,000 each records/groups. They are not original
  engine limits. The independent envelope and reader must agree.
- `XXXX` extended payloads are skipped upstream. This is not complete field
  coverage or a hostile-file parser sandbox.
- Android API 29 is the initial build target, not a proven device support range.
- The public-content guard currently permits UTF-8 source/docs only; new public
  bitmap/binary fixtures need a reviewed provenance policy before admitting them.
- Dependency source must be clean and immutable; build in another directory.
  The fetcher refuses existing mismatched/dirty caches and never deletes them.
- Raw reports contain owner paths/hashes; `measure_scan.py` writes outside the
  checkout and refuses to overwrite an existing evidence directory.

## Verification

Use README.md commands. After source changes, run CTest and the content guard;
reader changes additionally need an owner scan. Keep CI free of game assets.
Before publishing, run the guard with `--history` and inspect exactly what is
being distributed, including dependency notices/source. No playable engine,
touch controls, original animation, network authority or persistence should be
reported as implemented until its corresponding gate passes.
