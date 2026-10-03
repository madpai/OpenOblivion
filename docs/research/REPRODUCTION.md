# Reproduction evidence

Latest native continuation, 2026-10-03: [TES4_ANIMATION.md](TES4_ANIMATION.md)
records original TES4 transform sequence/default/spline decoding, live NPC idle
and a corrected shared-skin attachment. Both native builds and 14 public CTest
groups pass. Full-data and bounded-slice desktop probes observe five NPCs
through two loops; private captures show the clothed idle pose. The single APK
and complete six-APK set carry this native library, with verified signatures,
payload hashes and emulator installation/storage checks. Physical-phone idle
acceptance and full 1:1 gameplay remain pending. Older measurements below are
historical checkpoints with their own scope.

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


## Personal Android sideload baseline 0.1 (2026-10-01)

Original launcher/touch host plus unchanged external Andiweli OpenMW Android
0.51 baseline, source `7c97200966c9cb35a76b74d16d5c76f1a8939612`. See
[license matrix](LICENSE_MATRIX.md) for the release/native hashes and dependency
limits. This is separate from the unchanged desktop 0.52 reproduction.

- APK: 440,107,222 bytes (about 420 MiB), SHA256
  `d374efdce1d5c512d6ec76cef3cb0d41f11079c6011309533230dfb108be252b`. Android APK Signature Scheme v2 verifies.
- Packaged ZIP CRCs and all six unchanged native library hashes pass. The
  payload manifest verifies every extracted entry on first launch. Owner files
  stay outside Git; the APK is a personal test, not a public release.
- Visual selection: 1,287 extracted files (157 MiB), four Vilverin interiors
  plus nine Tamriel exterior cells; whole master/public Template/runtime
  resources included. 47 unresolved requests are recorded privately, primarily
  unsupported SpeedTree and unavailable/unused expansion landscape paths. This
  is a bounded scene slice; distant exploration may encounter missing resources.
- Android 14 Google APIs x86_64 emulator, `libndk_translation.so` ARM64 bridge,
  software graphics: APK install, cold asset verification and launcher pass.
  World loading fails in `libndk_translation_proxy_libGLESv2.so`, null function
  target; OSG single-threading does not resolve it. An experimental ANGLE
  preference did not select an installed ANGLE package and was removed.
  Template-only control gets further and reports Collada model load errors.
  No physical phone rendering, movement, collision, frame-time or lifecycle
  claim is established. Logs/screenshots remain private.
- Tailscale-only HTTP service: HEAD, byte/suffix ranges, If-Range behavior,
  rejected traversal/unlisted files/invalid ranges and a complete APK download
  with matching SHA256 pass. Existing sibling servers keep their ports.

Evidence directory: `/home/commander/openoblivion-private/evidence/android-preview`.
Personal artifact root: `/home/commander/openoblivion-private/sideload`. The
user service is enabled for the current user's sessions (`Linger=no`); the
host and Tailscale must remain online. Stop with
`systemctl --user stop openoblivion-sideload.service`. No remote push occurred.

## Phone QA and diagnostic build 0.2 (2026-10-01)

The owner reported incorrect views in both scenes, with mostly sky outside.
Their phone log reaches Vilverin under GL4ES/OpenGL 2.1 and contains Collada
sky/player model failures, missing NPC visual files and missing attachment
nodes. It does not show a native crash. A loaded cell is not a visibility pass.
Camera/spawn failure is a hypothesis; no camera coordinates were in that log.

The independently authored scene packager now preserves repeated model and
inventory subrecords and follows NPC race/hair/eyes, inventory/leveled forms,
race head/body paths and landscape grass. All **32 NPC mesh paths** reported
missing are present in the new private selection. It contains 3,079 files
(407 MiB), follows 3,208 forms with no missing form IDs, and records 57 unresolved
asset requests. Unsupported SpeedTree and unavailable expansion terrain/grass
remain among those requests; this is still a scene slice, not a full resolver.

Build `0.2-scene-diagnostics`, versionCode 2: **636,600,299 bytes**, SHA256
`54f999707f2ed86fc360f025259b3d9a08cf8d756eeef66e76f12a4ff0ef83b0`.
APK v2 signature, ZIP CRCs and unchanged native hashes pass. The payload declares
840,121,235 unpacked bytes. Original read-only Lua logs player/camera positions,
orientation and collision state at five intervals without changing gameplay.
The template/native runtime remains unchanged; Collada loading is not fixed.

The Android 14 emulator upgrades from 0.1 to 0.2 successfully. The new payload
ID matches the installer's completion marker; installed diagnostic Lua matches
its source hash, configuration registers it, and the launcher reaches assets
ready. This verifies update/unpacking/configuration, not emulator world rendering.

Desktop 0.52 probes register the private loose slice and mount **only the owner
master**, without full game archives supplying omitted dependencies. Both exit
zero and produce inspected screenshots: textured interior walls/doorway and
exterior terrain/water/statics are visible. Phone diagnostic Lua also emits
samples there. Wall times: 16.8712 seconds interior, 17.2646 exterior. These are
desktop content/diagnostic checks, not Android rendering, FPS or movement proof.
Evidence is under `evidence/android-preview-slice-{interior,exterior}-02` in the
private workspace.

The sideload page now includes objective `OO-ANDROID-002`, explicit visibility
pass/fail criteria, a gallery picker and phone/build/result/notes/log fields.
Original HTTP fixtures and a live private round trip verify screenshot/report
storage, build identity, upload limits, invalid IDs, origin rejection, download
ranges and refusal to serve uploaded evidence. Test uploads are removed after
verification. Real phone reports stay in `evidence/phone-qa`, outside downloads
and Git. Four CTest suites (18 tests) and the history content guard pass.

## Camera origin reproduction and repair candidate 0.3 (2026-10-01)

The owner's follow-up 0.2 QA submission contains screenshots of a flat green
interior and a sky-only exterior. Its exterior log records three camera/tracked
positions at the world origin while the player is in the loaded exterior cell.
Touch look changes pitch/yaw. The two saved reports contain duplicate evidence;
both are retained privately. No physical device is connected to ADB.

In the pinned 0.51 camera implementation, first-person tracking selects a Camera
or Head node. When neither exists, tracked position becomes zero. The failed
Collada player model therefore strands the view at the origin. An original
desktop fault option deliberately selects a missing player model, without
changing upstream files. The control reproduces **the same green blank interior**
and zero camera position with a normally placed player.

An independent preview Lua fallback switches sustained lost first-person
tracking to native actor-root tracking at zero orbit distance. It activates
after 0.25 seconds with tracked/player distance over 512 units. Desktop fault
tests then show textured interior/exterior geometry and camera distance
**124 units** above the player. A healthy control retains first-person mode and
does not activate the fallback. A two-second movement/turning fault test moves
38.9528 units in the interior; the final loose-slice exterior test moves
306.4249 units while the camera follows at 124 units. Collision fidelity and
physical-phone behavior are not established by these bounded desktop tests.

The bundle now matches the runtime's initial **5x5 exterior grid** and includes
persistent world references selected by position rather than only CELL ownership.
An original fixture covers in-grid persistent placement, out-of-grid exclusion
and exclusion of another world. All **38 missing owner mesh paths** from the
follow-up log are selected. The selection contains 3,417 files (429 MiB), four
interiors plus 25 exterior cells, 3,300 followed forms, six additional base forms
selected by position, and 62 unresolved asset requests. Unsupported SpeedTree,
template/weather and unavailable expansion assets remain outside this fix.

Build `0.3-camera-repair`, versionCode 3: **653,815,486 bytes**, SHA256
`e0054ec93aeeb2909ef66b940c4d2734933c1dbcc2e8a3bf694cb0485c656f24`.
Payload declares 863,651,520 unpacked bytes. Signature, ZIP CRCs and unchanged
native library hashes pass. The packager now recreates the generated APK and
checks unused ZIP-space overhead: an incremental package initially retained
about 600 MiB of dead bytes after replacing its payload, and was rejected before
deployment. Compilation caches remain reusable.

The Android 14 emulator upgrades from 0.2 to 0.3 successfully. Its completion
marker matches payload ID
`87eb3d8206bab322a63008de3d83a82777a232deb7bbe6319945e8393a6a8b11`;
installed camera/diagnostic Lua matches the original sources, configuration
registers the fallback and the launcher reaches assets ready. This establishes
upgrade/unpacking/configuration, not Android scene rendering.

The existing private service now serves 0.3 and objective `OO-ANDROID-003`.
A complete HTTP APK download matches the hash/size above; the live page build,
objective, suffix range and new ETag checks pass. The verified 0.2 download and
manifest are archived in `sideload-history/0.2`; real phone submissions are
retained. The new objective requires visible scenery, look and five-second
movement in both scenes, with screenshots and updated camera logs.

Private evidence: `evidence/camera-origin-control-interior-03`,
`camera-root-repair-{interior,exterior}-03`, `camera-healthy-control-interior-03`,
`camera-root-motion-interior-03`, and `camera-final-slice-exterior-03` under the
private workspace. The latest exterior probe uses only the selected loose data
and owner master, verifies movement/camera bounds and exits zero. Model-loader
errors and unsupported animation remain; the new APK requires another phone
visibility/touch report. Nineteen original tests pass in four CTest suites.

## Phone visibility and camera tracking confirmed on 0.3 (2026-10-01)

The owner submitted a new report at 14:52 UTC, selecting build
`0.3-camera-repair` and result "Geometry visible" for both scenes. The report's
page/server APK hashes match the served 0.3 artifact. Three screenshot receipts
match their private files' sizes and SHA256 hashes. Inspected images show a
textured interior stairway with a clothed NPC, a textured chamber with lighting
and props, and exterior textured ground/ruins. The NPC is in a T-pose; frozen
appearance does not establish skeletal animation. No raw owner image/log is
added to the public repository.

Only the exterior log is attached. It records `OPENOBLIVION_CAMERA_REPAIR`
activation and four `OPENOBLIVION_PHONE_QA` samples at 1, 3, 8 and 15 simulation
seconds. All show mode 2, camera/tracked position 124 units above the player and
collision enabled. Pitch/yaw change; yaw ranges from -1.00390625 to
2.24021649 radians. Horizontal player coordinates stay constant across all
four samples. This verifies the repaired phone camera and look control plus
scene visibility, **not horizontal movement or collision fidelity**. The two
interior views support scene visibility; they do not provide a timed motion
trace. Device/model and Android version were omitted.

Player/sky Collada failures, missing Groin attachment, unsupported controllers,
a path interpolator and template/weather resources remain. The log shows no
new game-mesh "Resource not found" failures for this exterior run. No FPS,
thermal, lifecycle, original gameplay, Vulkan or multiplayer claim is made.

Private evidence remains in `evidence/phone-qa`; the derived, original analysis
is `evidence/android-preview/phone-03-analysis.json`. The APK is unchanged.
The page records this visibility/look checkpoint and advances to
`OO-ANDROID-004`, testing movement/release, stairs/ground and jump. Each scene
gets a separate report before the next launch, retaining its own latest log.

## Native-player movement priority and trajectory probe (2026-10-01)

The owner's subsequent chat playtest reports walking, stopping, ordinary
collision, jumping and looking working. Stairs bounce and forward travel also
catches/slows at each step. The owner explicitly prioritizes actual in-game
player movement over viewer work. This is qualitative phone evidence, recorded
privately in `evidence/android-preview/phone-04-chat-analysis.json`; no stair
fix, comprehensive collision fidelity or phone timing claim is established.

An independently authored desktop probe now drives the stock native player's
walk, release, jump and landing controls, capturing position, ground state and
expected walk speed at up to 20 samples per simulation second. It changes no
camera path. Optional placement teleports once before the timed test; normal
movement then uses upstream physics. Raw traces, source/configuration hashes,
observed cell and engine identity are recorded privately.

The initial exterior control covers 728.75 horizontal units over 4.902843
sampled walking seconds, 99.09% of requested distance. Stopping drift after
a 0.2-second grace period is 0.3308 units. The jump rises 113.2647 units and
ends grounded. These measure one bounded desktop route, not original game
movement fidelity or a physical-phone benchmark.

The default interior route is obstructed (25.7 units over about five seconds,
3.47% of requested distance); its jump is blocked too. Turning at the same
spawn faces a stone door. Neither run is a stair reproduction. Two initial
stair placements also fail to provide a valid ascent/descent comparison: one
falls and resets to the entry location, producing a large discontinuity;
the other is obstructed. Screenshots/traces are preserved, not counted as
successful stair traversal. General native collision accuracy stays unverified.

Original trajectory fixtures reject vertical-only and camera-only "walking",
stopping drift, an unlanded jump, incomplete/non-finite data and respawn/teleport
discontinuities. Trace completion is separate from horizontal response,
stopping and jump/landing acceptance. Authored diagnostic thresholds and
route-clearance limitations are documented in [PLAYER_MOVEMENT.md](../PLAYER_MOVEMENT.md).

Both pinned 0.51 and 0.52 loaders explicitly generate Bethesda collision from
rendered geometry rather than the authored Havok shape data. Private inspection
of two Ayleid stair models finds separate MOPP/triangle-strip collision trees
with fewer vertices than the visible meshes. This is a verified compatibility
gap and a candidate contributor to snagging; causal proof on the owner's stair
route remains outstanding. No upstream source, solver or native library is
changed in this checkpoint. The current 0.3 APK is retained; a camera-only
smoothing workaround is not implemented.

Private evidence: `evidence/player-movement-{interior,exterior}-01`,
`player-movement-stairs-descent-01`, `player-movement-stair-{ascent,descent}-02`
and the validated exterior repeat. Analysis revisions preserve original metrics
and reject the invalid stair reset. This checkpoint did not change collision.
The later static-strip loader and its shape comparison are in
[Authored static collision](#authored-static-collision-2026-10-01) below.

Twenty-four original tests pass in five CTest suites. The Linux tools rebuild
with verified unchanged upstream source. The validated exterior repeat retains
the three movement gates with no discontinuities; its raw trace is private.


## Stair eye-height experiment and publication checkpoint (2026-10-01)

The owner clarified that walking up/down stairs works; the primary complaint
is a vertical view jolt at every tread, in both directions. This supersedes
interpreting the earlier catching/slowing answer as a demonstrated blocked
traversal defect. Smooth player travel remains the priority.

An original source-generated cell has twenty 16-unit rises and 24-unit treads,
with clear landings. No owner data is loaded in these fixture runs. Native
controls/physics solve the trajectory. At the unchanged 0.52 desktop pin,
raw/experimental comparisons cover the same 320-unit rise and show:

| Original route | Raw view velocity variation | Filtered | Reduction | Walk/stop/jump |
| --- | ---: | ---: | ---: | --- |
| Ascent | 2214.55 | 484.60 | 78.1% | pass |
| Descent | 2092.43 | 449.61 | 78.5% | pass |

Variation is total absolute change in vertical velocity per walking second,
measured from the up-to-20-Hz view trace; it is an authored diagnostic, not a
perceptual comfort score. Walking requested-distance ratios are 0.998..1.000,
ground states remain true, stopping drift is zero and jumps land. Eye offsets
stay about -18..+18 units in these runs. Original Lua fixtures cover both
stair directions, flat/ramp cadence and jump/fall/teleport/pause reset behavior.

Identified Vilverin entrance routes now reproduce physical ascent/descent.
Both raw and experimental routes pass walking/stopping/jump/landing. Descent
view variation falls from 2413.96 to 704.33 (70.8%); ascent rises from 1206.67
to 3008.31. **The real ascent regression prevents deployment.** OpenMW invokes
Lua `onFrame` before physics and native camera tracking update, confirmed in
`apps/openmw/engine.cpp` and `apps/openmw/mwlua/luamanagerimp.cpp` at the locked
0.52 revision. An out-of-phase height offset is the current inference; this
requires post-physics presentation work rather than claiming a solved motor.

A healthy first-person scene control remains mode 1 with no fallback activation;
the exterior movement/turn control moves 308.97 units, changes yaw and retains
native collision. The private experimental 0.4 APK builds, passes CRC/native
hash checks, but is withheld. The live phone download stays at 0.3. The default
packager and camera repair source remain the working baseline; the experiment
requires explicit `--grounded-eye`. Its original fixture/analysis tools are
public, while generated meshes/plugins, trajectories and images remain private.

Private evidence: `original-stair-{ascent,descent}-{raw,smoothed}-04b`,
`player-entrance-stairs-{ascent,descent}-{raw,smoothed}-04`,
`player-look-control-04b`, `player-healthy-tracking-control-04b`.
Initial origin-centered ascent fixtures did not activate missing-head recovery
until too late and are excluded from camera comparisons. A healthy-template
movement attempt on the original fixture fell and is not traversal evidence;
the separate healthy scene control establishes unchanged tracking only.

The owner authorized public publication to `madpai/OpenOblivion` and explicitly
requested progress screenshots. Three reviewed, unedited 0.3 phone captures
are pinned in `docs/media/screenshots.json`. This narrow documentation
exception is checked independently for worktree, index and historical trees;
arbitrary images, extracted artwork, game files and personal APKs stay blocked.
Source/history snapshots are described in [BACKUPS.md](../BACKUPS.md).


First public CI run: Linux build and all six CTest suites pass at `61702ec`.
Android setup fails before compilation because `sdkmanager` is absent from PATH.
The runner-image's [pinned installation script](https://github.com/actions/runner-images/blob/57b93f2cf7eda14a6a71f3175d15218626cdbd4c/images/ubuntu/scripts/build/install-android-sdk.sh#L38)
locates it at `$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager`; the workflow
now uses that explicit path while retaining the exact NDK version. This is
runner setup work, separate from phone/runtime validation.


The [corrected public CI run](https://github.com/madpai/OpenOblivion/actions/runs/36896855361)
at `a09dd1244b36c3acdc10a895e47e414e9d82da9d` passes both Linux build/fixture
checks and Android ARM64 cross-compilation. All three published README images
were fetched back and matched to the approved size/SHA256 ledger. The daily
backup service completes successfully; recovery verifies the Git bundle with
clone/`git fsck` and checks every archived source file. No phone stair fix or
new public binary release is claimed.

## Native post-physics stair checkpoint (2026-10-01)

An independently authored C++ height filter and small audited GPLv3 camera
patch are compiled in a separate desktop checkout of the existing 0.52 pin.
Integrated engine SHA256:
`4e4c0778bb47fe0000d19c4d21a3efa29ed63c357a8342c58aea860aed7b7eb9`.
Same-binary enable/disable comparisons improve view vertical-velocity variation
77.5% on original ascent stairs, 59.5% on actual Vilverin ascent and 75.9% on
actual descent. Walking response, stopping and jump/landing pass. Independent
ramp/descent, blocked-wall, low-ceiling, look and healthy-tracking controls
pass their applicable gates. See [movement details](../PLAYER_MOVEMENT.md) for
sampled limits and evidence identifiers. No physical solver is replaced.

The canonical `tools/native/prepare_android.py --build --grounded-eye` completes
against Andiweli source `7c97200966c9cb35a76b74d16d5c76f1a8939612`, engine base
`f4bec41444214a7903bebd178389ca22ca13f646`, NDK r26b/API21/Clang17, GNU make and
host CMake 4.4.3. Nineteen archive inputs and three engine FetchContent inputs
are hash-locked, with inspected notices. The stale bzip2 URL, implicit unused
GL4ES host configure, script modes and old CMake-policy minimum are repaired
in an external build recipe; reader and donor research checkouts remain clean.
This establishes a repeatable source/dependency recipe, not bit-identical donor
release output or a fully hermetic host toolchain.

Native Android libopenmw SHA256:
`00e91be09c6af4fb3d5460be1b387f7242854a3c2c0b355d34924e82d307cab0`.
All six runtime libraries are AArch64; dynamic dependencies resolve to bundled
or Android system libraries. The receipt records source/patch/tool, native,
349 resource/default and actual notice hashes. Receipt fixture tests cover
complete library/resource/notice inventories and prevent failed notice assembly
from publishing a canonical receipt. Eight CTest suites pass: 29 Python tests,
the Lua trajectories and 3,817 C++ trajectory assertions. Full history content
checks also pass.

Personal **0.5-native-stairs / versionCode5** APK: 656,467,659 bytes, SHA256
`c767a984092f26eeb5c3b75e19c26cbeebf75d8f5b83e35cb52e882b9da23156`.
Its v2 signature, CRCs, all six native hashes and compiled enable flag pass.
Private payload ID:
`1b6deaaec72018f75240ea4ebeced49adee1a1cbfbbcc328584bf55dab5dddcf`;
863,652,035 unpacked bytes. Emulator upgrade, verified payload readiness and
`native_stair_qa.omwscripts` configuration pass. The source-built engine loads
its libraries and begins content loading, then the emulator repeats the known
null target in `libndk_translation_proxy_libGLESv2.so` before camera creation.
No emulator scene/filter runtime pass is claimed. Subsequent physical-phone
evidence is recorded in the following checkpoint.

The complete privately served 0.5 download matches its APK hash and page QA
objective `OO-ANDROID-005`. Complete 0.3 is retained separately for recovery.
The rejected pre-physics Lua 0.4 APK remains withheld. Private native logs,
runtime receipts, APK and emulator images are under `native-android` and
`android-native-preview-build`, outside public Git/download evidence routes.
No game assets or public binary release are added by this source checkpoint.

## Native 0.5 phone feedback and movement priority (2026-10-01)

Private `OO-ANDROID-005` report `505b52e80f8a4869a9068a5b1e53eeee` was received
2026-10-01 19:13:02 UTC. Its tested/server build is `0.5-native-stairs` and both
page/server APK hashes match the 0.5 hash above. Device/model and Android fields
are blank; notes and screenshot attachments are empty. The selector says
interior, but the actual log loads VilverinExterior and neighboring exterior
cells. Treat the selected label and recorded scene separately.

At 15:10:59.202 the log records `OPENOBLIVION_NATIVE_GROUNDED_EYE` enabled; at
15:11:03.770 it records missing-head actor-root fallback activation. Five phone
samples include changing horizontal player coordinates and pitch/yaw, mode 2
and camera collision enabled. There are 400 bounded stair-QA samples spanning
26.397 simulation seconds from initialization; those exterior samples do not
identify a controlled interior ascent/descent route. No phone percentage
improvement or timing/performance result is inferred from them.

The owner's subsequent chat feedback describes stairs as very smooth with
almost realistic stepping they like. They also observe swimming working and
a breath indicator appearing. This is physical-phone qualitative evidence,
separate from the native desktop metrics. Water transitions, breath
depletion/recovery, drowning and original Oblivion movement fidelity remain
unverified; existing Collada/animation limitations remain.

At this checkpoint the liked 0.5 stair feel stayed in place and the runtime
was unchanged. The later control correction and the current engine follow-up
are in the next section and in [player movement](../PLAYER_MOVEMENT.md).

## Phone controls 0.8 (2026-10-01)

The 0.7 log, report `472a8828bfc742a4bac5fc80c653b358`, stays near 151 units
per second while moving. That is the borrowed walk speed. The Caps Lock pulse
changed the button label and not the gait. Preview 0.8 holds Shift for run and
a player script pins `alwaysRun` off, because the borrowed control formula
treats Shift as the opposite of that saved setting. `smoothControllerMovement`
is pinned off so a controller axis cannot replace the Shift state. USE and
JUMP are unchanged from the fixed 0.7 mapping. The private sideload objective
is `OO-ANDROID-008`.

The follow-up report `93db9dd902434ef2bf0e54dc7234dca9` is the same 0.8 build.
`OPENOBLIVION_RUN_GATE` is present. Grounded moving speed over 25.7 simulation
seconds has median 149.9 and maximum 165.1, with no sample above 200. The
Shift hold did not create a run gait.

## Authored static collision (2026-10-01)

`tools/native/authored_collision.py` patches the audited 0.51 and 0.52
`bulletnifloader.cpp` files. With `OPENOBLIVION_AUTHORED_COLLISION=1`, the
desktop loader builds one identity compound child from fixed `OL_STATIC`
strip data. Degenerate strip steps are omitted. On the six stair NIFs the
authored counts are 213, 165, 1,522, 575, 751 and 268 triangles. The render
path on the same files is 866, 700, 4,632, 1,486, 2,066 and 756. A 20 by 20
downward ray grid on `arwhallstairs01` has median absolute height difference
2.32. The cylinder, step constants and camera filter were not changed. The phone
package `0.9-authored-collision` (versionCode 9, QA `OO-ANDROID-009`) carries
the same switch. Its APK SHA256 is
`281685ea5663bc4d0783c940b915a3805daa49e44e0b29aecf66370dec9664b9`
and the stripped `libopenmw.so` SHA256 is
`77a6b4baeb3db3e67aab6d02be080b7b67adf4215e1a2c0c7344ddab09713c0e`.
Linking required stripping debug info from the new loader object after
`ld.lld` reported an out-of-range `R_AARCH64_ABS32` debug relocation in the
existing `utilpackage.cpp.o`. Detail is in [HAVOK_COLLISION.md](HAVOK_COLLISION.md).

## Phone controls 0.7 (2026-10-01)

Owner testing of private preview 0.6 reported that the USE and JUMP labels no
longer matched the buttons, and that the run control left the player walking
after one press. This engine binds Space to activate and E to jump. Holding
Shift inverts the always-run setting. Preview 0.7 restores USE on the lower
button and JUMP above it, and pulses the always-run control instead of holding
Shift. It starts on run. The 0.5 movement motor and stair filter are unchanged.
0.6 is withdrawn. The private sideload objective is `OO-ANDROID-007`. The APK
stays outside this repository.
