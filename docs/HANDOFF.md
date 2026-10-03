# Maintainer handoff

Door continuation, 2026-10-03: the Vilverin gate now plays original embedded
Open/Close clips through USE, with two authored keyframed boxes following its
leaves. Desktop full-data and bounded-slice tests verify closed/open/closed
collision and ordinary player traversal. Native fixtures, the prior KF suite,
all 14 CTest groups and both native builds pass. Current packages are
`0.16-doors` and `0.17-installed-doors`; see [TES4_DOORS.md](research/TES4_DOORS.md)
for receipts, reproduction, hashes and remaining parity work. The earlier
0.14/0.15 idle packages are recovery checkpoints. Phone gate/idle acceptance
remains pending. The complete 1:1 port goal remains active.

Final door binaries also pass desktop NPC-idle and container-window regressions.
An isolated Android 14 emulator verifies the 0.16 single APK and 0.17 six-APK
upgrade, all extracted payload hashes and the ready launcher. These are
installation/storage/UI checks; the existing emulator GLES translation failure
still prevents scene-rendering acceptance. No physical phone is connected.

The following animation and interaction entries record earlier checkpoints.

Animation continuation, 2026-10-03: default TES4 NPC idle now advances and
skins the attached body/clothing. Both native engines build; transform decoding
is cross-checked independently; full-data and bounded-slice desktop probes
observe five NPCs through two loops and inspect the clothed pose. Public CTest
now has 14 groups. See [TES4_ANIMATION.md](research/TES4_ANIMATION.md) for exact
source receipts, reproduction, package hashes and remaining original-animation
work. Current private packages are `0.14-idle` (single Vilverin APK) and
`0.15-installed-idle` (complete installed-data APK set). Previous 0.12/0.13 are
retained for recovery. No movement/body/stair constants were changed. Physical
phone idle acceptance remains pending; the 1:1 goal remains active.

Current continuation, 2026-10-03: the owner now prioritizes a 1:1 classic
Oblivion Android port and explicitly authorizes source/docs publishing and
private sideload APK updates. [PARITY.md](PARITY.md) supersedes the older
statement below that one-to-one gameplay was not the current target.
The interrupted native binding declarations and container UI are completed
as a measured inspection checkpoint. At that point the inherited door sequence
hook used the fallback; the continuation above implements the embedded gate path.
See [TES4_INTERACTIONS.md](research/TES4_INTERACTIONS.md) for native names,
container/window verification, reference lock reset, shared-skeleton scope,
build receipts and remaining work. Movement constants remain unchanged.

Complete-content continuation: `--all-assets` now produces the private
`0.13-installed-assets` signed APK set. Every supplied Data file is included
byte for byte; all 824 extracted files / 73 original Data files verify on an
isolated Android emulator after `adb install-multiple`. The 5.57 GB download
exceeds a single signed APK, so unzip on a computer and run the included
install script with the phone connected. The smaller `0.12-containers` single
APK remains the direct-install choice. See [INSTALLED_ASSETS.md](research/INSTALLED_ASSETS.md)
for the complete package hash, content/format boundary, verified desktop full
archive/expansion configuration and remaining phone/gameplay acceptance.
The full set's native library and movement constants are unchanged.

Founding checkpoint: 2026-09-30. The owner authorized publication to
https://github.com/madpai/OpenOblivion on 2026-10-01. Original project code is
GPL-3.0-only; owner content stays private.

Personal sideload checkpoint: 2026-10-01. The user requested an asset-packed
test APK and a separate server like MegaMod's. The original Android launcher,
touch overlay and build/server tools are under `android/host` and `tools/android`.
They stage a pinned external OpenMW Android 0.51 baseline and a private visual
slice, not our new Vulkan/multiplayer runtime. The owner's APK/download root is
`/home/commander/openoblivion-private/sideload`, served only on Tailscale port
8735 by the user unit `openoblivion-sideload.service`. It is never a public
release. See [Android checkpoint](ANDROID.md) for the emulator graphics failure
and the owner's earlier failed physical-phone views. At that checkpoint the served download was
`0.12-containers` (versionCode 12), QA objective `OO-ANDROID-012`. Its APK
SHA256 is `f588257abe91344ce187cb34ed81f40a9c6dd7278242c717b89f6991a7bfac00`
(661,254,187 bytes). It adds TES4 names, base-container inspection, shared
NPC skeleton attachment and correct optional lock reset. It keeps the 0.5 stair filter, the fixed `OL_STATIC`
strip collision, and the 0.9 movement library. The closed overlay is the
stick plus USE, JUMP, ATK, and MORE. Actor models use the template Collision
box in `basicplayer.osgt`. Same-cell doors stay open until used again. See
[the Vilverin gate note](research/VILVERIN_GATE.md) and
[preview play](research/PREVIEW_PLAY.md). `0.11-fit`, `0.10-touch-name` and
`0.9-authored-collision` are archived.
The 0.9 package keeps the 0.5 stair filter and adds fixed `OL_STATIC` strip collision.
USE is the lower-right button, JUMP
is above it, and run is a held Shift with always-run pinned off. It starts on
run. Run speed is still the borrowed walk. `0.8-run` is archived.
`0.6-run-toggle` and `0.7-controls` are withdrawn.
`0.5-native-stairs` remains archived for the stair comparison.
The complete working 0.3 APK/page/notes are archived privately. Native 0.5
builds the Android engine from hash-locked sources and applies the small audited
post-physics camera patch. Same-binary desktop Vilverin comparisons improve
view variation by 59.5% uphill and 75.9% downhill; movement/control fixtures
pass. APK integrity/signature and emulator upgrade/payload checks pass.
The emulator scene retains its confirmed GLES translation crash before camera
construction. The subsequent phone upload confirms native filter enablement,
actor-root fallback and movement/look in exterior cells. The owner now reports
very smooth stairs with liked subtle stepping, plus swimming and a visible
breath indicator. Original movement speed/jump fidelity remains uncalibrated.
APK signature, emulator upgrade/payload configuration and the complete served
download checksum pass. Reports live in
`/home/commander/openoblivion-private/evidence/phone-qa`, outside downloads/Git.
The follow-up 0.2 report shows camera/tracked positions at the origin, with a
normally positioned player. The missing Camera/Head bone condition reproduces
the blank view on desktop. Build 0.3 adds a conditional native actor-root camera
fallback at zero orbit distance and includes the initial 5x5 exterior grid plus
persistent references by position. Desktop fault/motion and healthy controls
pass. The owner's 0.3 submission now shows textured interiors and exterior
ground/ruins on the phone. Exterior logs verify fallback activation, 124-unit
camera tracking and touch look. The four samples have identical horizontal
player coordinates; that log does not verify traversal/collision. A clothed NPC is
visible in a T-pose; original animation and Collada loading remain unresolved.
The owner subsequently reports walking, stopping, ordinary collision, jumping
and look working. The 0.3 clarification says stair ascent/descent works, but
each tread produces an uncomfortable vertical view jolt in both directions.
The earlier catching/slowing answer is historical. Actual player travel remains
the priority. The grounded eye-height experiment is explicitly opt-in for
desktop research
and excluded from the phone packager. Original native stair comparisons reduce
view jolts, but real Vilverin ascent worsens the measured variation; the current
Lua frame hook precedes physics/camera tracking. Do not deploy the private
experimental 0.4 APK or attribute the 0.5 phone result to that Lua experiment.
The working 0.3 baseline is retained
and archived. See [player movement](PLAYER_MOVEMENT.md) for evidence and the
original movement calibration and separate collision work.
The previous 0.2 APK is archived privately, and real QA submissions are retained.
See `OPENOBLIVION_CAMERA_REPAIR` and mode/distance in `OPENOBLIVION_PHONE_QA` logs.

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

Linux tools and Android ARM64 tools build. Twenty-nine Python tests, the
Lua eye-height trajectory suite and 3,817 native C++ trajectory assertions
pass in the normal build; the founding fourteen
also passed ASan/UBSan. The Vulkan probe enumerates
a desktop GPU; it does not render.
Six existing Asset Lab original-fixture tests were reproduced with the private
PyFFI environment and explicit NIFXMLPATH. Neither sibling checkout was edited.

Source/revisions/licenses: [license matrix](research/LICENSE_MATRIX.md),
[lock](research/upstreams.lock.json). Raw evidence is external; public results
are in [REPRODUCTION.md](research/REPRODUCTION.md). GitHub CI now passes Linux build/tests and Android ARM64 cross-compilation
at `7599b1b` ([run](https://github.com/madpai/OpenOblivion/actions/runs/36912085741)). This is compile/test
evidence, separate from Android runtime/device validation. No physical Android device was available through ADB;
the owner supplied failing 0.1/0.2 evidence, visible 0.3 scene screenshots/logs
and the subsequent 0.5 native runtime log/comfort feedback. The latest report
is `505b52e80f8a4869a9068a5b1e53eeee`, received 2026-10-01 19:13 UTC. It is
labeled interior, but its log records exterior travel; no screenshots or device
details are attached. See the reproduction ledger for scope.

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
collision accuracy and animation are not validated. Bounded desktop motion
passes; phone evidence includes visibility/look and subsequent owner-reported
basic movement/stair comfort, with no original movement calibration yet.

The post-physics camera candidate now passes desktop stair comparisons in both
directions, and the owner now likes the 0.5 stair feel. One-to-one movement,
including stair collision, is not the current target: several published
movement settings are absent from the master, and the character body dimensions
are still unknown. The desktop loader can use fixed `OL_STATIC` strip shapes
when `OPENOBLIVION_AUTHORED_COLLISION=1`; the `arwhallstairs01` ray grid changes
contact, and the cylinder was not retuned. See
[HAVOK_COLLISION.md](research/HAVOK_COLLISION.md). The 0.8 phone log stayed at
walk speed, median 149.9 and maximum 165.1, so another run binding is not the
next change. Phone preview 0.9 carries that library. Its APK SHA256 is
`281685ea5663bc4d0783c940b915a3805daa49e44e0b29aecf66370dec9664b9`.
Keep 0.5 as the stair
comparison and 0.3 as the recovery baseline. Check swim transitions and breath
behavior separately; the owner's observation does not prove drowning.
Use `tools/native/README.md` for the canonical source build and its exact receipt.
The source build lives under `/home/commander/openoblivion-private/native-android`,
desktop integration under `native-desktop`, and private candidate APK staging
under `android-native-preview-build`. Reader/donor research pins remain clean.
The fixed `OL_STATIC` strip loader is measured. Do not repeat that patch.
The next physical change is the character body, and only after its radius,
height, and step offset are recovered rather than invented. Change the motor
only when a native trajectory identifies a defect. The native movement trace distinguishes
horizontal travel,
stopping, jump/landing and respawn discontinuities. Typed override/master-reference
fixtures and the content/scene boundary remain required; use the same scenes to
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
- The public-content guard permits UTF-8 source/docs and three exact approved
  README screenshots. Additional images require recorded publication
  authorization, provenance and reviewed hashes; game binaries remain blocked.
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


## Public repository and backups

The owner explicitly authorized this public GitHub repository and selected
README progress screenshots. The screenshot manifest is a narrow guard
exception; APKs/game data/raw QA stay private. The local pre-push hook and CI
check index, worktree and each historical tree. The GitHub bootstrap commit is
preserved when merging the existing local founding history.

Verified source archives/Git bundles are in the private `backups` directory.
`openoblivion-backup.timer` runs daily with persistent catch-up; the host user
manager must be running. A recovery test clones the bundle, runs `git fsck`
and checks every archived source hash. See [BACKUPS.md](BACKUPS.md).
