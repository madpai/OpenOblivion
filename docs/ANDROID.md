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
That does not establish that the phone view is fixed; the Android Collada loader
failure and a possible camera/spawn issue remain under investigation.

The private sideload page now has QA objective `OO-ANDROID-002`, a gallery upload
picker and device/build/log fields. Its pass condition requires visible world
geometry and working look/movement. Empty interiors or sky without ground fail.
Reports and screenshots stay outside the checkout and are not downloadable
through the service. Use those reports to compare the new camera-position logs
with desktop evidence before selecting a renderer, model or spawn fix.

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
