# Android platform plan

An optional personal APK/launcher now exists under `android/host`, using the
audited external OpenMW Android 0.51 runtime and OpenGL ES. See
[personal build instructions](../tools/android/README.md). The user-requested
private APK bundles a bounded owner-data scene slice and installs it without
manual file copying. Public APKs must still contain no game data.

Gate-fit correction: the owner's 0.18 phone report shows open leaves but failed
passage. A malformed OSGT player model loaded the oversized error-marker body.
`0.20-fit` corrects the serialization, and `0.21-installed-fit` carries the same
fix in the complete set. Actual Android ARM64 OSG loading and native desktop
before/after traversal pass; physical-phone passage confirmation is pending.
Use the smaller APK for the gate test. The optional full set supplies artwork
outside the bounded scene, using the same engine and gameplay implementation.
See [the collision-model evidence](research/PLAYER_COLLISION_MODEL.md).

Complete installed-data checkpoint, 2026-10-03: the separate private
`0.21-installed-fit` package carries every supplied Data file in a signed
APK set. The 5.57 GB download contains six APKs and computer install scripts;
the complete Data does not fit one signed APK. Android emulator installation,
all 824 extracted file hashes/sizes, the complete archive/plugin configuration,
obsolete loose-file removal and launcher controls pass. Native NPC idle and
embedded gate clips with moving collision are described in
[TES4_ANIMATION.md](research/TES4_ANIMATION.md) and
[TES4_DOORS.md](research/TES4_DOORS.md). Native audio is enabled in
[TES4_AUDIO.md](research/TES4_AUDIO.md); `0.20-fit` is the smaller single-APK option.
See [installed assets](research/INSTALLED_ASSETS.md) for exact content, checksum
and installation instructions. Full content availability does not establish
phone rendering, original audio/video playback or gameplay parity.

Android 14 x86_64 emulator with ARM64 translation: APK installation, SHA256
verified asset unpacking and the launcher passed. The world-load attempt
crashed in `libndk_translation_proxy_libGLESv2.so` with a null function target;
single-threaded OSG rendering did not fix it. A template-only control reached
world initialization but reported Android Collada model load failures. This
does not establish phone scene rendering or touch movement. No physical device
was connected to ADB.

The owner's subsequent physical-phone test of build 0.1 reaches Vilverin under
GL4ES/OpenGL 2.1 but reports an incorrect interior and mostly sky outside. Its
log confirms Collada sky/player model failures and missing NPC race/body/hair/
worn-item models. Build 0.2 expands visual dependencies and includes all 32 NPC
mesh paths reported missing. Original read-only Lua now samples player/camera
positions, orientation and collision state. Desktop 0.52 checks of that loose
visual slice show textured interior geometry and exterior terrain/water/statics.
That did not establish that the phone view was fixed; its follow-up report
provided the camera coordinates needed to diagnose the blank views.

The 0.2 private sideload page added QA objective `OO-ANDROID-002`, a gallery upload
picker and device/build/log fields. Its pass condition requires visible world
geometry and working look/movement. Empty interiors or sky without ground fail.
Reports and screenshots stay outside the checkout and are not downloadable
through the service.

The follow-up 0.2 report contains two failing screenshots and exterior camera
samples at `(0, 0, 0)` while the player is in the loaded cell. Pitch/yaw change
with touch look. The pinned engine's first-person camera needs a Camera/Head
bone; absent tracking returns the origin. Deliberately omitting the player model
on desktop reproduces the same blank interior and zero camera positions.

Build 0.3 conditionally switches lost first-person tracking to the native
actor-root camera at zero orbit distance. Desktop fault tests recover textured
interior/exterior views and keep the camera 124 units above the player during
bounded movement/turning. Healthy first-person tracking remains unchanged.
The visual bundle now covers the initial 5x5 exterior grid and persistent
references selected by position; all 38 missing owner mesh paths in the follow-up
log are selected. The Collada loader remains unresolved. This is a preview
workaround. Objective `OO-ANDROID-003` requested scenery, look and movement
screenshots/logs in both scenes.
The emulator upgrade verifies the payload ID, installed scripts/configuration
and ready launcher. The complete served APK matches the build SHA256.

The owner's 0.3 phone submission now establishes **scene visibility**: two
screenshots show textured interior stairway/chamber geometry, props and a clothed
NPC; a third shows textured exterior ground and ruins. The NPC is in a T-pose.
Only the exterior log is supplied. It records fallback activation and four
samples at 1, 3, 8 and 15 simulation seconds with camera/tracked positions
124 units above the player, mode 2, changing pitch/yaw and collision enabled.
The logged horizontal player coordinates never change, so look/tracking pass
but traversal and collision fidelity remain unverified. Device/model and
Android version were left blank; no performance claim is established.

Build 0.3 is the archived working phone baseline. The owner's subsequent chat
playtest reports walking, stopping, ordinary collision, jumping and look working.
The 0.3 clarification says stairs are traversable, but the view bounces at each
tread uphill and downhill. The earlier catching/slowing answer remains
historical evidence; the subsequent 0.5 feedback is recorded below.

An unshipped eye-height experiment reduces measured jolts on original desktop
stairs while walk/stop/jump still pass. Its real Vilverin ascent comparison is
worse, exposing a frame-timing problem: Lua `onFrame` executes before physics
and camera tracking update. It is explicitly opt-in via `--grounded-eye` in the
desktop probe, and is excluded from the personal packager. The experimental
0.4 APK was built privately but is withheld; that checkpoint retained 0.3.
See [player movement](PLAYER_MOVEMENT.md). General collision accuracy, animation,
lifecycle and performance remain unmeasured.

Private preview **0.5-native-stairs** now uses a source-built Android engine
with the independently authored post-physics C++ height filter. Nineteen
native archive inputs, three engine FetchContent inputs and NDK r26b are
hash-locked; external donor and reader checkouts stay unchanged. The canonical
native build command completes, including the baseline and camera integration.
See [native build recipe](../tools/native/README.md) and
[dependency inventory](research/android-native.lock.json).

The same-binary desktop comparison improves actual Vilverin ascent/descent
view variation by 59.5%/75.9%; walking, stopping, jump/landing and separate
ramp/wall/ceiling/look/healthy-tracking controls pass. Eight CTest suites include
29 Python fixtures, the original Lua trajectories and 3,817 C++ trajectory
assertions. These remain desktop/source evidence.

All six compiled libraries are AArch64 with resolved bundled/system dependency
names. APK signature/CRCs/native hashes pass; versionCode 5 and the compiled
native-enable flag are verified. Android 14 emulator upgrade, hash-verified
payload readiness and native stair-QA configuration pass. Native libraries load
and the engine begins content loading, then scene rendering hits the same
confirmed `libndk_translation_proxy_libGLESv2.so` null-function target as the
released baseline, before camera construction. This is not Android scene or
filter-runtime validation from the emulator.

The subsequent `OO-ANDROID-005` physical-phone report, received
2026-10-01 19:13 UTC, matches the served 0.5 APK SHA256. It logs native grounded-eye
enablement, missing-head fallback activation and changing player/look positions.
The selector says interior, but the log begins in VilverinExterior and records
exterior travel. It contains 400 bounded movement/view samples and no attached
screenshots; device/model and Android version are blank. This verifies phone
activation and sampled movement, not a controlled stair or performance comparison.

The owner separately reports very smooth stairs with subtle stepping they like,
swimming working and a breath indicator appearing. Preserve the current feel.
One-to-one speed, jump and stair collision is not the current target. Preview
**0.9-authored-collision** keeps the 0.5 motor and stair filter and turns on
fixed `OL_STATIC` strip collision. USE is the lower-right
button and JUMP is above it, matching this engine's Space and E bindings. The
top button holds Shift for run after always-run is pinned off, and starts on
run. The 0.7 log stayed at walk speed. Swimming and the meter are observations;
depletion/recovery and drowning remain untested.

The current package is **0.18-audio** (versionCode 18), QA
`OO-ANDROID-018`. It retains the original Vilverin gate Open/Close clips and two
authored moving collision boxes. Desktop full-data and bounded-slice tests
verify visible leaves, held end poses, closed/open/closed collision and player
traversal. It retains original TES4 transform KF decoding and NPC idle with live
shared skinning. Five desktop NPCs advance through two loops and the clothed
pose is inspected. Native audio is now enabled and the bounded slice includes
22 original door sound files. Full-data and bounded-slice desktop mixes identify
both gate samples. Phone gate, idle and audio acceptance remain pending; sound
distance/volume behavior still uses placeholders. See [audio evidence](research/TES4_AUDIO.md).
The motor, stair filter, strip loader, template collision box, container
inspection and touch overlay remain. Locomotion, combat and live loot transfer
are still incomplete. See [door evidence](research/TES4_DOORS.md).

The complete installation option is **0.19-installed-audio**, versionCode 19,
with all 73 supplied Data files in six signed APKs. Unzip on a computer and run
the included adb install script. See [installed assets](research/INSTALLED_ASSETS.md).
The previous 0.16 single APK and 0.17 full set are retained privately for recovery.
Earlier 0.11/0.10/0.9/0.8 checkpoints are archived; 0.6/0.7 are withdrawn,
0.5 remains the stair comparison and 0.3 remains the phone visibility baseline.
The rejected 0.4 Lua-filter APK remains withheld.
Native 0.5 keeps the original movement and camera collision paths and adds
bounded read-only QA samples. It remains OpenGL, with animation, general TES4
collision accuracy, Vulkan and multiplayer unresolved.

Confirmed: native inspector and Vulkan capability probe compile for
`arm64-v8a`, API 29, NDK `28.0.13004108`, Clang 19, static libc++. These are
command-line executables, separate from the preview APK. The founding probes
were not executed on an Android device.

## Native app boundary

Build the simulation/content logic once for Linux, the headless server and
Android. The Android host owns activity lifecycle, file grants, touch events,
audio lifecycle and the native window. SDL is a candidate for desktop input/
windowing and Android hosting; evaluate existing port code before choosing
SDL versus a small native activity/JNI host. Desktop launcher Qt dependencies
must not become prerequisites of the mobile game.

Use the [Storage Access Framework](https://developer.android.com/training/data-storage/shared/documents-files)
to let users select their own installation tree and retain the granted access.
A content URI is not a POSIX filename. Bethesda readers need seekable random
access: adapt granted descriptors when the provider supports seeking, otherwise
explicitly stage selected files into a private app cache. Handle revoked grants,
missing masters, interrupted copies and insufficient storage. Never copy
archives onto the render/input thread or package them into a public APK.

## Vulkan and lifecycle

Require a usable graphics queue, Android surface/swapchain support and the
actual mesh/material texture features the renderer uses. Capability enumeration
alone does not establish this. On pause/window loss, stop presentation safely;
preserve simulation/session identity under policy, rebuild surface/swapchain on
resume and cancel stale uploads. Test rotation, background/foreground,
screen off, permission revocation, device loss and interruption during loading.

Decode on bounded worker queues, enforce source/decompressed/GPU memory
budgets, stream cell resources and progressively upload textures. Measure
resident memory, loading stalls, frame-time percentiles and thermal behavior
on the selected phone before fixing quality defaults or world radius. Current
32 MiB record/2 GiB file scanner limits are tooling budgets, not mobile runtime
memory targets or recovered game constants.

## Touch interface

Provide distinct pointer capture for movement, look, attack/block/cast,
interact, jump and inventory. Commands pass through the same action/input
boundary as desktop. Handle multi-touch, finger reassignment, safe insets,
UI interception, cancel events and stuck controls after focus loss. Configure
size/position/sensitivity and left/right-handed placement. Camera prediction
is local; progression is authoritative. Menus do not pause a multiplayer world.

The first app gate is an original scene with working touch controls and surface
recovery, followed by one private TES4 scene. Public APK contents must pass the
no-game-data check; personal asset-packed tests stay outside the repository and
public releases. Emulator evidence proves UI/lifecycle behavior; a physical
phone run is required for device performance claims.
