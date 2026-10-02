# Personal Android scene preview

This is an original small Android host around a separately audited OpenMW
Android 0.51 release. It is an experimental reproduction package, not the
OpenOblivion simulation, multiplayer server or Vulkan renderer.

The source tree contains no donor Java files, native libraries, game assets or
APK. All those inputs and outputs are staged outside the checkout. The user
explicitly requested a personal asset-packed APK and private sideload server;
that does not authorize a public game-data release.

## Inputs and build

Use the exact donor checkout and release recorded in
[the license matrix](../../docs/research/LICENSE_MATRIX.md) and
[upstream lock](../../docs/research/upstreams.lock.json). Release and native
engine SHA256 checks are mandatory; all tracked donor/template/Asset Lab
files are verified before staging. Java bridge files are unchanged external
inputs. The independently authored Java host uses the JNI class names and
resource namespace expected by that bridge, with a distinct application ID
`org.openoblivion.preview`.

Requires Python 3.11+, Java 17, Gradle 8.9, SDK platform 35, Android Gradle
Plugin 8.5.2, the materialized public Template and the owner's classic Data
directory. The released native runtime was built with NDK r26b/API 21;
the host requires API 29 and targets API 32 for this historical SDL baseline.
No claim of 16 KiB-page compatibility or physical-device performance is made.

```sh
python3 tools/android/build_personal.py \
  --donor /outside/research/openmw-android-andiweli \
  --upstream-apk /outside/upstream-0.51.0-11.apk \
  --template /outside/research/example-suite \
  --assetlab /outside/open-asset-lab \
  --data /owner/Oblivion/Data \
  --work /outside/android-preview-build \
  --sdk /path/android/sdk --gradle /path/gradle-8.9/bin/gradle
```

The packager includes the whole master, public Template, engine resources,
and a visual neighborhood: all Vilverin interiors and Tamriel cells
10..14,19..23, matching the pinned runtime's initial 5x5 active exterior grid.
Persistent world references are also selected by their physical position;
their owning persistent CELL need not be in this neighborhood.
The packaging-only TES4 traversal follows reference base forms
and model paths, including repeated race head/body parts, NPC race/hair/eyes,
inventory and leveled item/actor links, then readable NIF texture links and
implicit normal/glow companions. All landscape texture definitions, their
grass models and common effects are included. This is a bounded scene slice, not a complete plugin/mod
dependency resolver. Reports list unresolved requests; SpeedTree and some
unused expansion terrain paths remain unsupported/unbundled. Sound, voices,
DLC plugins and game executables are excluded.

First launch streams and verifies each payload entry into private app storage,
rejects traversal/unknown entries and insufficient space, and marks completion
only after all hashes match. A separate scene process protects the launcher
from native runtime crashes. Touch movement/look/use/jump controls cancel held
keys on focus loss/pause. The launcher provides a selectable scene log.
The native scene path remains experimental; installing successfully does not
prove world rendering, collision or gameplay.

The 0.2 diagnostic build includes original read-only Lua that logs cell,
player position, camera/tracked position, pitch/yaw and collision state after
1, 3, 8, 15 and 25 simulation seconds. Look for `OPENOBLIVION_PHONE_QA` in the
scene log. It does not change the camera, spawn, collision or gameplay rules.
The user's 0.1 phone report loaded the cell but showed incorrect interior/
exterior views and Collada player-model failures. The expanded visual bundle
fixes missing NPC dependencies. The later 0.3 report establishes phone visibility
after repairing camera tracking.

Build 0.3 adds a separately authored preview camera workaround. If first-person
tracking stays more than 512 units from the player for 0.25 seconds, it selects
native third-person actor-root tracking with zero orbit distance. This retains
the engine's look/movement and collision paths while avoiding a missing
Camera/Head bone. Healthy tracking is left alone. Camera mode and measured
camera/player distance appear in the diagnostic log; activation prints
`OPENOBLIVION_CAMERA_REPAIR`. This repairs a reproduced camera condition, not
the Collada loader, original animation or RPG gameplay. The owner's 0.3 phone
screenshots show textured interiors, an NPC and exterior ground/ruins. Its
exterior log confirms activation, four samples at 124 units above the player
and changing look angles. Horizontal player coordinates stay constant in those
samples, so movement/collision still require a separate test. The visible NPC
is in a T-pose; this is not animation evidence.

The opt-in desktop stair eye-height experiment is in
`camera_stairs_candidate.omwscripts` and is excluded from the personal
packager. Controlled original stairs improve, but real Vilverin ascent exposes
a frame-timing regression. The private experimental 0.4 APK is withheld, and the
working phone baseline 0.3 is archived. See [movement research](../../docs/PLAYER_MOVEMENT.md).

Personal preview **0.11-fit** (versionCode 11) is the served package. It keeps the 0.9 movement and strip collision. The closed overlay is documented in [TOUCH_ACTIONS.md](../../docs/TOUCH_ACTIONS.md). The name bar is in [LOOK_NAME.md](../../docs/LOOK_NAME.md). The hall-gate measurement is in [VILVERIN_GATE.md](../../docs/research/VILVERIN_GATE.md). `0.10-touch-name` and `0.9-authored-collision` are archived.

Personal preview **0.9-authored-collision** uses the native engine with fixed
`OL_STATIC` strip collision enabled. USE is the
lower-right button and JUMP is above it. The top button holds Shift for run
and starts on run. A player script pins always-run off so Shift is not inverted
into a walk. Walk speed, jump, the player cylinder, and the stair filter are
unchanged from 0.5. `0.8-run` is archived.

The subsequent native candidate **0.5-native-stairs** is built through
[tools/native](../native/README.md). Add `--native-runtime /outside/native-android/runtime`
to the packager command to use its verified six-library set and exact build
resources/defaults/notices. The host enables the native post-physics filter and
bounded read-only stair sampling; the rejected Lua filter remains excluded.
Without that option the released 0.3 path remains available. The current
private download offers 0.11-fit for owner QA. It uses the
native engine with the static-collision switch on, the collapsed touch overlay,
the template collision box, and the name bar. 0.10, 0.9, 0.8-run, and 0.5 remain archived, and 0.3 is preserved separately.

The packager recreates the generated APK while retaining compilation caches,
then rejects excessive unused ZIP space. This prevents incremental APK updates
from retaining a replaced large payload as hundreds of MiB of dead bytes.

## Private server

Copy the verified APK into an external private directory. Create `download.json`
with `build`, `validation`, and `downloads` (each has `name`, `size`, `sha256`).
Optional `qa_id` and `qa_objective` describe the current device test.
Allowlist `openoblivion-personal-preview.apk`, `SHA256SUMS.txt` and
`source-notes.txt`. Then run:

```sh
python3 tools/android/sideload.py --root /outside/sideload \
  --bind YOUR_TAILSCALE_IPV4 --port 8735 --uploads /outside/evidence/phone-qa
```

The service rejects non-Tailscale bind addresses and serves only those filenames,
with HEAD, SHA256 ETags and single-range/resume support. It streams in 1 MiB
blocks, has no directory listing, and leaves sibling services alone. The page
shows a QA objective/checklist, gallery picker, device/build fields and a scene
log box. It uploads at most four PNG/JPEG/WebP screenshots (20 MiB each) per
report. A raw image POST to `/upload` returns an opaque ID; a JSON POST to
`/report` links those IDs with notes/logs. Invalid IDs, foreign browser origins,
oversized bodies and unsupported content are rejected. Two uploads can be
handled concurrently; image signatures are checked, not fully decoded.

The upload directory must be outside both the checkout and download root. It
has mode 0700; images/receipts/reports have mode 0600 and server-generated names.
Uploads are not served by any download route. Receipts preserve the tested
build, page APK hash and current server build/hash separately so an older
download is not silently attributed to a newer APK. Keep all payloads/reports
and the private server manifest outside Git. A hardened service with read-only
home protection needs a write exception for this evidence directory.

Original fixture tests exercise dependency closure and the complete HTTP
upload/report flow, including private-file boundaries and download ranges:
`python3 tests/test_android_preview.py`. Owner/device evidence stays external.
