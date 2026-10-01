# Maintainer handoff

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
and the owner's failed physical-phone views. The current download is
`0.3-camera-repair`, with screenshot uploads and QA objective `OO-ANDROID-004`.
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
and look working. The latest clarification says stair ascent/descent works, but
each tread produces an uncomfortable vertical view jolt in both directions.
The earlier catching/slowing answer is historical. Actual player travel remains
the priority. The grounded eye-height experiment is explicitly opt-in for
desktop research
and excluded from the phone packager. Original native stair comparisons reduce
view jolts, but real Vilverin ascent worsens the measured variation; the current
Lua frame hook precedes physics/camera tracking. Do not deploy the private
experimental 0.4 APK or claim smooth stairs. The working 0.3 download is retained
and archived. See [player movement](PLAYER_MOVEMENT.md) for evidence and the
remaining post-physics presentation/collision work.
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

Linux tools and Android ARM64 tools build. Twenty-seven Python tests and the
Lua eye-height trajectory suite pass in the normal build; the founding fourteen
also passed ASan/UBSan. The Vulkan probe enumerates
a desktop GPU; it does not render.
Six existing Asset Lab original-fixture tests were reproduced with the private
PyFFI environment and explicit NIFXMLPATH. Neither sibling checkout was edited.

Source/revisions/licenses: [license matrix](research/LICENSE_MATRIX.md),
[lock](research/upstreams.lock.json). Raw evidence is external; public results
are in [REPRODUCTION.md](research/REPRODUCTION.md). The first GitHub run passes the Linux build/tests; the
Android runner setup is being corrected to use its explicit SDK-manager path. No physical Android device was available through ADB;
the owner supplied failing 0.1/0.2 evidence and visible 0.3 scene screenshots/logs.

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
passes, and the separate phone preview verifies visibility/look only.

Next resolve the post-physics eye-height timing and reproduce both stair
directions before asking for another phone build test.
Audit authored TES4 collision separately and change the motor only when native
trajectories identify a physical defect. The native movement trace distinguishes
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
