# Maintainer handoff

Armor, 2026-10-04: served `0.36-armor`. Worn armor reduces incoming physical
damage by its capped rating (decoded piece rating; the percentage rule itself
is documented, not decoded). See TES4_COMBAT.md. Next: blocking (no block
GMSTs found by name in the executable, decode the damage routine), power
attacks, fatigue per swing, bows, detection.

Weapons, 2026-10-04: served `0.35-weapons`. Looted melee weapons can be
equipped and are drawn and sheathed on the skeleton's weapon nodes, with the
original one-hand/two-hand clip sets, damage from the decoded exe formula
(0x547070) and bandits that fight with their weapons; baked face maps are
tints (×2 detail), now composited onto race skins; race body skins and female
fallbacks fixed. See [TES4_COMBAT.md](research/TES4_COMBAT.md) and
[TES4_FACES.md](research/TES4_FACES.md). Next: blocking, power attacks,
fatigue cost per swing, armor reduction, then bows, detection/disposition,
FaceGen shapes (EGM) and trees.

Faces, 2026-10-04: served `0.34-faces`. NPC heads use baked face textures
(forced opaque), race head-part textures and hair records with hair colour; see
[TES4_FACES.md](research/TES4_FACES.md). The desktop probe takes
`--movement-face*` options to put a camera in front of the nearest actor.
Next: EGM shape morphs and FGTS texture building (player face), weapons in TES4
combat, blocking, detection/disposition.

First-person fix, 2026-10-04: served `0.33-first-person-fix` after the owner's
0.32 screenshot showed stretched clothing in first person with fists readied.
See the first-person section of [TES4_ITEMS.md](research/TES4_ITEMS.md).
Desktop probes now take `--movement-pitch`.

Loot and readied fists, 2026-10-03: served `0.32-loot-readied`. TES4 items are
generated host records (`tools/android/tes4_items.py`), NPC inventories roll
through TES4 leveled lists, corpses are lootable, the renderer draws equipped
items, fists ready like a weapon with the original clips, and first person
views from `Camera01`. See [TES4_ITEMS.md](research/TES4_ITEMS.md). The
launcher can take private artwork (`build_personal.py --launcher-art`); the
owner's icon resembles the official emblem, so artwork is never committed.
Next: weapons in TES4 combat, blocking, TES4 detection/disposition, face
textures, gold/barter; then trees.

Bandit fights, 2026-10-03: served `0.31-bandit-fights`. TES4 NPCs become host
actor proxies (`tools/android/overlay`, actor bridge) drawn by the `tes4_player`
renderer; hand-to-hand damage is transcribed from the executable and NPC stats
come from the master (verified against the original console). See
[TES4_COMBAT.md](research/TES4_COMBAT.md) for facts vs stand-ins. Player stats
and outfit: [TES4_PLAYER.md](research/TES4_PLAYER.md). Next: weapons
(Vilverin loot), blocking, TES4 detection/disposition, face textures, and a TES4
inventory; then trees.

Oblivion player, 2026-10-03 (owner approved the "make Vilverin playable" plan:
TES4 player, stats/inventory, measured melee, bandit AI, looting; trees and
water in parallel). Step 1 landed as `tes4_player` (after `tes4_movement`),
served as `0.29-tes4-player`; see [TES4_PLAYER.md](research/TES4_PLAYER.md).
The private original reference game must be started from its `game/`
folder (`original-reference-20261003/launch_reference.sh`); launching elsewhere
crashed at `oblivion+0x18dc7c` looking for `Data\Menus\strings.xml`.
Next: step 2, TES4 stats/inventory and the Player's starting clothes on the body.

Sky and default run, 2026-10-03: served build `0.28-sky-run`. Android's COLLADA
loader rejects every template `.dae`, so the sky lost its atmosphere layer.
`tools/android/overlay/meshes/sky_atmosphere.osgt` is the CC0 template mesh
converted with plain OSG classes; desktop probes render it identically to the
`.dae` (`evidence/tes4-sky-{dae,osgt}-02`, mean pixel difference 0.005).
Running is the default as in Oblivion (overlay run gate pins always-run on;
WALK holds Shift), which also removes the lost-first-Shift-press problem.
Overlay files (`tools/android/overlay`, see its README) ship in the APK and
override payload copies without changing the payload ID. Next: the same
COLLADA failure leaves the player without `BasicPlayer.dae` animations; then
jump height (`fJumpHeightMin/Max`) from the original executable.

Run/sneak and start, 2026-10-03: the owner reported sneak doing nothing and no
walk/run difference. The player had no locomotion animation states, so the
borrowed engine always used walk speed. `tes4_movement` (after `tes4_body`)
applies the original executable's speed formula to the player (walk 116.6,
run 355.6, sneak 70 units/s on desktop). Phone build `0.27-run-sneak` also
starts at the original prologue sewer exit by default, and fixes menu tap
scaling and overlay redraw (0.26). See [TES4_MOVEMENT.md](research/TES4_MOVEMENT.md).

Phone-only complete data, 2026-10-03: the served build is `0.25-download-assets`,
a single APK that downloads and verifies the full installed Data from the
sideload server on first launch (see [ANDROID.md](ANDROID.md)). The payload
parts live in the sideload root next to the APK and are allowlisted in
`download.json`. 0.22/0.23 are archived in `sideload-history/0.23-installed-body`.

Measured player body, 2026-10-03: the original classic controller hull was
read from the owner's running executable (Proton, isolated display, read-only
process sampling). It is an 18-vertex eight-sided prism with pointed ends:
radius 20.25, height 128, convex radius 0.70 units, centre 71.0 above the
reference. It is unchanged by jump/sneak and rotates with heading. The native
`tes4_body` receipt (after doors) gives the player that hull under
`OPENOBLIVION_ORIGINAL_BODY=1`. It also judges the hull's walkable support
under its centre, because the cone's edge contacts otherwise triggered the
inherited 10-unit stair hack (3x climb speed). Same-binary desktop runs:
stair variation is −31%/−34%/−43% (fixture up/down, Vilverin). Vilverin height
tracks the original's own samples (RMS 5.23 vs 8.44). Gate, ramp, wall,
ceiling, jump, idle and container checks pass. All 16 CTest groups pass.
Packages `0.22-body` (single, versionCode 22) and `0.23-installed-body`
(complete set, 23) enable it; `0.20-fit`/`0.21-installed-fit` are recovery.
Not reproduced: the original's ~3 unit lower reference/float, its own stepping, gait and
run speed. The private reference game hung on `coc ICMarketDistrict` under
software rendering and was stopped. Relaunching with the recorded Proton command
now crashes at startup (null read at `oblivion+0x18dc7c`) although the isolated
ini is unchanged; diagnose that before the next measurement, and measure in
Vilverin rather than the Imperial City. See [TES4_PLAYER_BODY.md](research/TES4_PLAYER_BODY.md).
Next: phone acceptance of 0.22 stairs/gate, then original walk/run speed and
jump impulse from the same sampler.

Gate-fit correction, 2026-10-03: the owner's 0.18 screenshot shows open leaves;
report `bd8b99b04a83457c9a79d1714694c736` records the player OSGT loader failure
and failed passage. The model's malformed Generator header and unsupported
comment lines reproduce the exact parser errors. Correct serialization retains
all template vertices, triangles and dimensions. The real Android ARM64 OSG
libraries reject the old file and accept the corrected one in an isolated
emulator harness. Bounded-slice before/after native traversal reproduces the
blockage and passes after correction; full-data traversal passes too, with one
async physics worker. All 15 CTest groups pass, including a real OSG reader
regression. Native binaries, motor and camera constants are unchanged.
Packages are `0.20-fit` and `0.21-installed-fit`; 0.18/0.19 are retained for
recovery. Phone passage still requires a retest. See
[PLAYER_COLLISION_MODEL.md](research/PLAYER_COLLISION_MODEL.md) for hashes,
reproduction and the remaining original-controller gap. The full 1:1 goal
remains incomplete.

Audio continuation, 2026-10-03: native audio initialization is enabled and the
bounded Vilverin scene includes 22 original door sound files. The handler emits
opening/closing audio at the door. Full-data and bounded-slice desktop wave
captures identify both original samples with correlation above 0.997; the same
gate collision and ordinary traversal checks pass. No native library, movement
or sound-distance constants change. Packages are `0.18-audio` and
`0.19-installed-audio`; see [TES4_AUDIO.md](research/TES4_AUDIO.md) for hashes,
reproduction and remaining attenuation/lifecycle/phone work. The preceding
0.16/0.17 door packages remain recovery checkpoints. All 14 CTest groups pass.
Android 14 emulator upgrades to 0.18 then 0.19, verifies all 4,192/824 payload
hashes, installed APK hashes and ready launchers. The complete ZIP and six
nested APKs verify independently. Audible phone and scene acceptance remain
pending; the emulator's historical GLES translation failure still applies.
The complete 1:1 port remains incomplete and its goal remains active.

The following door, animation and interaction entries record earlier checkpoints.

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
