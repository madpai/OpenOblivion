# OpenOblivion

A project foundation for a native, open-source Oblivion runtime on Android
ARM64 and desktop Linux, with Vulkan rendering and persistent cooperative
multiplayer as primary design requirements.

The intended experience supports death, respawning, persistent progression,
alternate starts, cooperative PvE and custom modes. A later classic ruleset
should support faithful single-player behavior. **This checkout is a tested
research/tooling foundation, not a playable Oblivion engine.**

The compatibility foundation selected for the next prototype is **OpenMW**.
Its existing TES4/BSA/NIF work is substantially closer to the content-loading
problem than starting with an unrelated engine. Vulkan and multiplayer remain
separate unresolved integration work. See the [foundation decision](docs/decisions/0001-foundation.md)
and [upstream comparison](docs/research/FOUNDATION_COMPARISON.md).

## What works here

- A native read-only classic TES4 inspector, compiling a pinned, unchanged
  OpenMW reader slice. It checks container bounds, scans/decompresses record
  bodies and reports counts without content names or installation paths.
- A Vulkan physical-device and graphics-queue capability probe on Linux.
- Both executables cross-compile for Android `arm64-v8a`, API 29, NDK r28.
- Original generated fixtures, upstream revision/integrity checks and a
  public-content guard covering working files, staged blobs and Git history.
- A separate unchanged full OpenMW build and private interior/exterior scene
  probes, using the public Template and the owner's data with software OpenGL.
  See the [upstream reproduction recipe](tools/upstream/README.md).

Owner-supplied local `Oblivion.esm`: **1,167,017 records, 85,079 groups and
41,789 compressed records** scanned successfully. Separate upstream probes
rendered textured dungeon geometry and an exterior with terrain, water and
static meshes. These establish a content/viewer baseline; quests, original
animation, combat, multiplayer, Vulkan scenes, touch controls and phone
performance remain unproven. See [reproduction evidence](docs/research/REPRODUCTION.md).

## Build on Linux

Requirements: C++20 compiler, CMake >= 3.24, Ninja, Python >= 3.10, Git,
zlib development files and Vulkan development files. No game data is required
to build or run the public tests. The renderer-independent inspector can be
built with `-DOO_BUILD_VULKAN_PROBE=OFF`.

```sh
python3 tools/fetch_upstream.py --cache ../openoblivion-deps
cmake -S . -B build -G Ninja \
  -DOO_OPENMW_SOURCE="$PWD/../openoblivion-deps/openmw" \
  -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel 4
ctest --test-dir build --output-on-failure
python3 tools/content_guard.py --history
./build/openoblivion-vulkan-probe
./build/openoblivion-inspect "/your/Oblivion/Data/Oblivion.esm"
```

The dependency cache must stay outside this repository. `fetch_upstream.py`
fetches an immutable commit and refuses to replace an existing dirty or
wrong-revision checkout. CMake verifies all upstream tracked blobs at configure
and build time. Source includes and notices stay in that original checkout.

Keep raw logs, game data, screenshots and compiled content outside this
repository. The inspector accepts a single classic `.esm`/`.esp` file by
explicit path; installation discovery and load-order resolution are future work.
Use trusted owner files: container budgets are not a complete untrusted-file
parser sandbox. Extended `XXXX` subrecords are skipped by the upstream reader;
the subrecord count is not a complete semantic census.

## Cross-compile for Android

Set `OO_NDK_DIR` to an installed NDK r28 directory:

```sh
cmake -S . -B build-arm64 -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$OO_NDK_DIR/build/cmake/android.toolchain.cmake" \
  -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-29 \
  -DANDROID_STL=c++_static -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF \
  -DOO_OPENMW_SOURCE="$PWD/../openoblivion-deps/openmw"
cmake --build build-arm64 --parallel 4
```

These are native command-line probes. An APK, Android activity, Storage Access
Framework integration, touch controls and a Vulkan surface are not implemented.
Cross-compilation alone does not prove execution on a phone.

## Direction and contribution

Read the [charter](docs/PROJECT_CHARTER.md), [architecture](docs/ARCHITECTURE.md),
[multiplayer contract](docs/MULTIPLAYER.md), [Android plan](docs/ANDROID.md),
[format research](docs/research/FORMATS.md), [milestones](docs/ROADMAP.md) and
[handoff](docs/HANDOFF.md). Milestones have acceptance gates, not promised dates.

Original code is **GPL-3.0-only**; upstream files keep their own licenses.
The [license matrix](docs/research/LICENSE_MATRIX.md) records exact studied
revisions, notices, compatibility decisions and actual reuse. No Bethesda
or Havok game binaries/assets are distributed. Users supply their own classic
Oblivion installation. Original/public fixtures are generated from source.
