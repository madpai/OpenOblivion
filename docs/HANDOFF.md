# Maintainer handoff

Founding checkpoint: 2026-09-30. This is a local repository with no remote
publication. Original project code is GPL-3.0-only; owner content stays private.

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

Linux tools and Android ARM64 tools build. Fourteen tests pass in normal and
ASan/UBSan builds. The Vulkan probe enumerates a desktop GPU; it does not render.
Six existing Asset Lab original-fixture tests were reproduced with the private
PyFFI environment and explicit NIFXMLPATH. Neither sibling checkout was edited.

Source/revisions/licenses: [license matrix](research/LICENSE_MATRIX.md),
[lock](research/upstreams.lock.json). Raw evidence is external; public results
are in [REPRODUCTION.md](research/REPRODUCTION.md). GitHub workflow is authored,
not remotely executed. No physical Android device was available.

## Continue here

M1 is the next goal: reproduce full upstream TES4 world viewing in an isolated
build environment. The host lacks several engine development dependencies.
System configuration failed at yaml-cpp; the upstream bundled-dependency route
got past that but failed at missing Boost headers/config. A container build can
resolve host dependency drift without modifying the user's installed system.
Do not change or silently patch the pinned reader to make a baseline pass.

After an upstream scene works, measure its content/scene boundary and use the
same private scene to compare Vulkan donor work. Implement a small original
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

