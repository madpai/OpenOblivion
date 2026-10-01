# Reproduction evidence

Date: 2026-09-30. All game files, raw reports and binaries remain outside the
public checkout. Counts below are a reviewed summary. This is an M0 tooling
checkpoint and partial M1 reproduction, not playable Oblivion or multiplayer evidence.

## Revisions and builds

| Item | Reproduced result |
|---|---|
| OpenMW source | `46bd4599203ee52ffc0f3e8edb3fc159a0303a49`; unchanged checkout, all tracked blobs verified |
| Linux inspector/probe | GCC 16.2.1, CMake 4.4.3, Ninja; Debug build succeeded |
| Android inspector/probe | NDK `28.0.13004108`, Clang 19, `arm64-v8a`, API 29, static libc++; Release cross-build succeeded; ELF identity checked |
| Public tests | 15 original/guard cases in 3 CTest suites passed, including template LFS identity checks |
| Address/undefined behavior sanitizers | Original 14 cases / 3 suites passed with ASan+UBSan before the tooling continuation |
| Content guard | Working, staged and committed-history checks passed at the local checkpoint |
| Linux Vulkan probe | NVIDIA GeForce RTX 3060 Ti, Vulkan 1.4.351, graphics queue available; no rendering/surface test |
| Full upstream build | Pinned unchanged source built in isolated Ubuntu 24.04: `openmw`, `esmtool`, `bsatool`, `niftest`; GCC 13, CMake 3.28, Boost 1.83, OSG 3.6.5, SDL 2.30 |
| GitHub CI | Workflow authored for Linux tests/content history and ARM64 compilation; no remote run or publication occurred |
| Physical Android | No ADB device connected; no phone run, touch or frame-time evidence |

## Owner master file

Input: owner-supplied classic `Oblivion.esm`, 277,504,985 bytes, HEDR 1.0.
Source hash is recorded only in the private evidence. The native scan reports:

- **1,167,017 records including the TES4 header**.
- **85,079 groups**.
- **41,789 compressed records** processed through the existing reader.
- **4,572,485 visited subrecords excluding the header**; extended `XXXX`
  payloads are skipped by upstream, so this is not all semantic fields.
- Independent envelope totals agree with the upstream-reader traversal.

The public `tools/measure_scan.py` run took **2.9546 seconds** and reported
**23,016 KiB peak child RSS** on the Linux host. This includes process startup
and the private measurement launcher; it is a scanner measurement, not a
rendering/runtime memory profile or phone result. A separate direct subprocess
scan reported 3.0038 seconds / 13,032 KiB; launch context affects peak RSS.

To reproduce with a fresh private output directory:

```sh
python3 tools/measure_scan.py \
  --executable ./build/openoblivion-inspect \
  --plugin "/your/Oblivion/Data/Oblivion.esm" \
  --output ../openoblivion-private/evidence/new-scan
```

The tool refuses an output directory inside the checkout or an existing
evidence directory. It stores private input/executable identity, stdout,
stderr and metrics. A failed scan exits nonzero; do not commit its raw report.

## Original-fixture coverage

The inspector's 9 cases cover HEDR 1.0/1.2, nested groups, record types and
subrecord counts, compressed decoding, corrupt compressed streams, truncated
files/groups, unknown/later formats, invalid signatures/sizes, nesting and
decompression budgets, and suppression of input paths/content names in stdout.
Single grouped-record fixtures also prevent recurrence of the upstream
traversal-helper final-record omission.

Four publication-guard cases cover asset extensions/renamed binary signatures,
private directories, a prohibited staged blob hidden by a clean working file,
deleted content remaining in history, and symlinks. One upstream-lock case
checks the pinned revision and a modified file hidden by assume-unchanged.

## Existing Asset Lab reproduction

At Asset Lab `e5f9dcb29f67ed6346954e66ee6d0af575f832fc`, all **6** original
Oblivion-path tests passed without changes to its checkout: BSA compression/
bounds/path cases, rigid compilation, and NIF static geometry/controller
refusal/freeze/exclusion cases.

The system Python run initially passed 3 and skipped 3 because PyFFI was absent.
The existing private decoder environment initially failed those 3 because the
installed wheel lacked `nif.xml`. Setting `NIFXMLPATH` to its already-pinned
schema submodule made all six pass. This documents the real environment
requirement rather than treating skipped tests as decoder validation.

This reproduction does not prove KF animation, worn armor, original Havok
behavior, full plugin semantics or gameplay. PyFFI/schema distribution rights
and bundled binary exclusions are tracked separately in the license matrix.

## Full upstream and independent asset agreement

The full OpenMW development 0.52.0 build succeeded without donor source edits
in a Docker environment. The host-only attempts lacked yaml-cpp/Boost; the
isolated dependency environment resolved that issue without installing host
packages. The source was mounted read-only. Ubuntu base image digest,
upstream-selected MyGUI 3.4.3/Recast revisions and build recipe are recorded in
[standalone reproduction tools](../../tools/upstream/README.md) and the license
matrix; the exact image ID/package inventory and build log remain private.
Both downloaded archives match upstream's SHA-512 pins. Every extracted file
was compared against its archive: **2,246 MyGUI files and 164 Recast files**,
with no differences. The final build recipe also completed against this cache.

Upstream `bsatool` extracted one owner static clutter NIF, and `niftest` read
it without errors. An independent Asset Lab BSA read produced **identical
11,661 bytes**. The member name/hash, model and diagnostics remain private.
This is one archive/member agreement, not blanket NIF, KF or physics coverage.

The scene harness uses software Mesa llvmpipe, OpenGL 4.5, LLVM 20.1.2/Mesa
25.2.8. Loading Oblivion alone reproduced a Morrowind fallback-script error
and missing `gamehour` global before any cell was entered. The
[official setup](https://openmw.org/2025/openmw-0-49-0-released/) requires a
base game alongside later-game content. The external public Example Suite
provides it; its LFS objects must be materialized, not mistaken for game data
when the checkout contains pointer text. No upstream code was patched to
hide those startup failures.

Both **Vilverin** and **VilverinExterior** then entered their requested cells,
produced private 800x600 screenshots and exited zero via the original probe
script. Image inspection confirms textured dungeon geometry in the interior
and terrain, water, rocks and other static meshes outside. The first completed
interior probe took 16.9597 seconds wall time; the exterior took 17.7911 seconds.
Those durations include container startup/loading and the seven-second
simulation window; they are not frame-time/FPS results.

The viewer logs still report missing template UI/weather assets, a template
COLLADA body load failure, missing character textures and unsupported trap/
butterfly interpolators. Generated collision/navmesh entries are visible, but
collision accuracy and movement were not validated. Sky/player/UI behavior
includes the template/Morrowind bootstrap. This evidence does not establish
original NPC animation, gameplay, faithful world materials or Vulkan rendering.

## Limits and next decisive evidence

The inspector visits generic subrecords; it does not resolve a complete load
order or simulate any record. Its wrapper bounds container sizes and declared
decompression allocation, not every hostile payload. It currently targets
trusted classic owner installations.

Next: complete the private interior/exterior and collision checks, then measure
the immutable scene/content boundary before accepting a full runtime fork. Vulkan scene
rendering, a native Android app and authoritative co-op remain separate gates.
