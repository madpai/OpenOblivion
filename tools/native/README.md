# Native stair camera integration

## TES4 interaction continuation

After applying the existing camera/static-strip integration, apply the name,
container, shared-skeleton and optional reference-lock reset patch to the
external engine tree. It accepts clean audited files or the exact interrupted
handoff hashes, and verifies an existing receipt on repeat application.

```sh
python3 tools/native/tes4_interactions.py apply --source /outside/native-desktop/source \
  --revision 46bd4599203ee52ffc0f3e8edb3fc159a0303a49
# Rebuild openmw in the existing container, then update its camera build receipt:
python3 tools/native/tes4_interactions.py record --source /outside/native-desktop/source \
  --binary /outside/native-desktop/build/openmw --manifest /outside/native-desktop/build-manifest.json
```

Android uses the engine tree beneath the donor build and revision
`f4bec41444214a7903bebd178389ca22ca13f646`. Rebuild `openmw`, recreate any
corrupted generated static archive before relinking, then strip debug info
into the private runtime's `libopenmw.so`. Record against that library and
the runtime's existing `build-manifest.json`. The packager validates the
interaction tools as well as all six packaged library hashes.
See [the measured scope](../../docs/research/TES4_INTERACTIONS.md).

This is a small, opt-in patch against audited OpenMW sources. It changes eye
presentation after physics updates the actor, before the existing camera sphere
casts. It does not change actor movement, collision geometry, heading, jump,
gravity or server authority. Healthy first-person tracking remains unchanged.

The original C++ filter is in `grounded_eye.hpp`; upstream camera patch context
is GPLv3 and attributed in NOTICE.md and the license matrix. The native switch
is `OPENOBLIVION_GROUNDED_EYE=1`. Filtering is limited to grounded zero-distance
third-person actor-root views, as used by the preview's missing-head fallback.
Jump intent, airborne/swimming state, cell changes, large position changes,
pauses, other camera modes and long frame gaps reset it. Native ceiling/wall
camera collision remains active.

## Android source build

Use the exact external donor checkout in `docs/research/upstreams.lock.json`.
Requirements include Git, Python, curl-compatible HTTPS access, unzip, GNU
make/GCC, CMake, envsubst, autotools/pkg-config and the usual host development
tools. NDK r26b is downloaded and hash checked by the preparation tool.
Build and dependency files stay outside the public checkout.

```sh
python3 tools/native/prepare_android.py \
  --donor /outside/research/openmw-android-andiweli \
  --work /outside/native-android --jobs 8 --build --grounded-eye
```

The tool locks nineteen archive inputs and three engine FetchContent inputs,
prepares an external donor worktree, builds host ICU and the donor engine
baseline, then applies/compiles the camera-only integration. It records source,
native library, resource/default and notice hashes in `runtime/build-manifest.json`.
The stale donor bzip2 URL uses upstream 1.0.8 with an original CMake adapter.
GL4ES skips an unused host configure; CMake policy compatibility is explicit.
Executable script modes are restored for Linux. These changes do not imply
byte-for-byte identity with the donor's released WSL binary or a fully hermetic
host toolchain. Keep the original donor checkout untouched.

To package the owner's private scene, add `--native-runtime /outside/native-android/runtime`
to the existing `tools/android/build_personal.py` command. It verifies the locked
build, replaces all six released libraries with the source-build set, and uses
that build's resources/defaults/notices. This produces version `0.5-native-stairs`,
enables native smoothing in the scene process and includes bounded read-only
stair QA. The rejected Lua smoothing experiment remains excluded. Without this
option the packager retains the released 0.3 baseline behavior.

## Desktop comparison

Use a separate checkout of desktop pin
`46bd4599203ee52ffc0f3e8edb3fc159a0303a49`; do not edit the reader cache.

```sh
python3 tools/native/integration.py apply --source /outside/native-desktop/source \
  --revision 46bd4599203ee52ffc0f3e8edb3fc159a0303a49
# Build the full engine using the existing isolated upstream build recipe.
python3 tools/native/integration.py record --source /outside/native-desktop/source \
  --binary /outside/native-desktop/build/openmw \
  --output /outside/native-desktop/build-manifest.json
```

Add `--native-manifest /outside/native-desktop/build-manifest.json` to the
player probe, and toggle `--native-grounded-eye` for a comparison using the
same binary. Do not combine it with the pre-physics Lua `--grounded-eye` option.
Original fixtures support `--movement-surface stairs|ramp|wall|ceiling`.
The wall route deliberately fails the walking-response gate because the wall
correctly blocks the body; assess its clearance separately. Probe completion,
movement acceptance, camera metrics and device validation remain separate.

## Authored static collision

`authored_strips.hpp` expands a Gamebryo triangle strip. Degenerate steps are
omitted. `authored_collision_desktop.patch` and
`authored_collision_android.patch` teach the external Bullet loader to use a
fixed `OL_STATIC` `bhkNiTriStripsShape` when `OPENOBLIVION_AUTHORED_COLLISION=1`.
MOPP bytes are not executed. The rigid-body translation is not applied. Every
other shape, including clutter, ragdolls and phantoms, stays on the render-mesh
fallback. The player cylinder, step constants and camera filter are unchanged.

```sh
python3 tools/native/authored_collision.py \
  --source /outside/native-desktop/source \
  --revision 46bd4599203ee52ffc0f3e8edb3fc159a0303a49
```

The Android 0.51 tree uses revision `f4bec41444214a7903bebd178389ca22ca13f646`.
Apply it to that engine source, not to the donor Android project root. The
script refuses a second apply.

Rebuild the desktop loader inside `openoblivion-research-build:founding`,
with the source mounted at `/source` and the existing build at `/work/build`.
Override the image entrypoint; the image's default command is the full
upstream build. The host has no OpenSceneGraph headers. Link Bullet as the
image's float64 libraries.

On Android, rebuild with `cmake --build <openmw-build> --target openmw`.
The top-level Makefile does not compile the loader object when that path is
named directly. If `ld.lld` reports `R_AARCH64_ABS32` out of range in
`utilpackage.cpp.o`, strip debug info from the new loader object, delete
`libcomponents.a`, and link again. The phone packager strips the library.
