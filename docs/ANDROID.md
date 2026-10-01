# Android platform plan

Confirmed: native inspector and Vulkan capability probe compile for
`arm64-v8a`, API 29, NDK `28.0.13004108`, Clang 19, static libc++. These are
command-line executables, not an APK. No device run occurred in this checkpoint.

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
recovery, followed by one private TES4 scene. APK contents must pass the
no-game-data check. Emulator evidence proves UI/lifecycle behavior; a physical
phone run is required for device performance claims.

