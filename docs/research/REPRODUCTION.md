# Reproduction evidence

Date: 2026-09-30. All game files, raw reports and binaries remain outside the
public checkout. Counts below are a reviewed summary. This is an M0 tooling
checkpoint, not playable Oblivion or multiplayer evidence.

## Revisions and builds

| Item | Reproduced result |
|---|---|
| OpenMW source | `46bd4599203ee52ffc0f3e8edb3fc159a0303a49`; unchanged checkout, all tracked blobs verified |
| Linux inspector/probe | GCC 16.2.1, CMake 4.4.3, Ninja; Debug build succeeded |
| Android inspector/probe | NDK `28.0.13004108`, Clang 19, `arm64-v8a`, API 29, static libc++; Release cross-build succeeded; ELF identity checked |
| Public tests | 14 original/guard cases in 3 CTest suites passed |
| Address/undefined behavior sanitizers | Same 14 cases / 3 suites passed with ASan+UBSan |
| Content guard | Prospective working content and empty initial history passed; staged/history checks repeated after local snapshot |
| Linux Vulkan probe | NVIDIA GeForce RTX 3060 Ti, Vulkan 1.4.351, graphics queue available; no rendering/surface test |
| Full upstream host configure | System dependency route stopped at yaml-cpp. Bundled-source route progressed through OSG/MyGUI/Bullet/Recast/yaml configuration, then stopped at missing Boost headers/config |
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

## Limits and next decisive evidence

The inspector visits generic subrecords; it does not resolve a complete load
order or simulate any record. Its wrapper bounds container sizes and declared
decompression allocation, not every hostile payload. It currently targets
trusted classic owner installations.

Next: isolate the full desktop upstream build and reproduce one private
Oblivion interior/exterior scene. Record rendering/collision/animation scope
and actual dependencies before accepting a full runtime fork. Vulkan scene
rendering, a native Android app and authoritative co-op remain separate gates.

