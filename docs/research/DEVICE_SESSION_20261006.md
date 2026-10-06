# First scripted device session and wireless debugging recipe

Date: 2026-10-06. Build `0.44-menu-exit`. Phone: Samsung Galaxy S24+ (SM-S926U), Android 16.
This is the first time a build was installed and exercised from the build host over adb instead of by hand.
Raw evidence (screenshots of game content, logcat) stays in the private workspace
(`~/openoblivion-private/evidence/device-20261006/`, 11 files) and is never committed. The owner has since paused
phone testing; the emulator gate in [ANDROID.md](../ANDROID.md) replaces it for now.

## Recipe: adb over Tailscale (worked on the first try once the prompt was accepted)

1. Build host: install Android `platform-tools` (adb 37.0.1 here), outside the checkout.
2. Phone: enable Developer options, then Wireless debugging. In Termux install `android-tools`, pair the phone with
   itself (`adb pair localhost:<pairing port>` with the code the screen shows), connect to it
   (`adb connect localhost:<port>`), then `adb tcpip 5555`. This makes adbd listen on TCP 5555 on every interface,
   including the Tailscale one.
3. Build host: `adb connect <phone tailnet address>:5555`. The first connection says `unauthorized`/`failed to
   authenticate` until the on-phone "Allow USB debugging?" prompt is accepted; then re-run `adb connect`.
4. Measured: direct Tailscale path, 23 ms round trip, about 6 MB/s for `adb push`/`install` (the 292 MB APK
   installs in under a minute).

Inference, not tested: `tcpip` mode should end at reboot or when Wi-Fi changes, so repeat step 2 after either.
Keep it on the tailnet only; adb authenticates by key, but a debug port is still an open door.
To disconnect: `adb disconnect <address>:5555`.

## What 0.44 did on the phone (measured)

- Installed with `adb install -r`; Android 16 showed two compatibility dialogs: the app is a **debuggable** build
  (the APK is built with Gradle `assembleDebug`) and its native libraries are **not 16 KB page aligned**.
- The game runs in the `:scene` process; `run-as org.openoblivion.preview` works because the build is debuggable.
- The journal opens and shows the real MQ02 entries. The overlay's own BACK button closes it. The **system BACK key
  does not**: `input keyevent 4` leaves the journal open. Cause (read from the code): `SDLActivity` forwards the key
  to the engine and consumes it, so `GameActivity.onBackPressed` never runs. Fixed in the Java host
  (`dispatchKeyEvent`), verified on the emulator, not yet in a phone build.
- Resource use while running the scene: about 1.6 GB resident memory and one CPU core at 100%. Inference: that is the
  single-threaded OSG setting (`OSG_THREADING=SingleThreaded`), so the frame rate is bound by one core; not measured
  as frame times.
- Visual observations: black bars around the 3D view (letterbox) and visible system bars; an empty brown/dark square
  at the bottom right of the HUD that nothing explains yet. All three reproduce on the emulator, so they are not
  phone-specific.

## Follow-ups (in the plan, [REVIEW_AND_PLAN.md](../REVIEW_AND_PLAN.md))

Ship a non-debuggable, 16 KB-aligned build; use the full display (immersive mode, correct aspect); find the HUD
square; measure frame times; then the phone batch acceptance of 0.40-0.44 when phone testing resumes.
