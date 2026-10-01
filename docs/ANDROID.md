# Android platform plan

An optional personal APK/launcher now exists under `android/host`, using the
audited external OpenMW Android 0.51 runtime and OpenGL ES. See
[personal build instructions](../tools/android/README.md). The user-requested
private APK bundles a bounded owner-data scene slice and installs it without
manual file copying. Public APKs must still contain no game data.

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
**0.7-controls** keeps the 0.5 motor and stair filter. USE is the lower-right
button and JUMP is above it, matching this engine's Space and E bindings. The
top button pulses always-run and starts on run. Swimming and the meter are observations;
depletion/recovery and drowning remain untested.

The private download is 0.7-controls; 0.6 is withdrawn, 0.5 remains the stair comparison, and the complete working 0.3 APK/page/notes are archived
for recovery/comparison. The rejected 0.4 Lua-filter APK remains withheld.
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
