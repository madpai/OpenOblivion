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
11..13,20..22. The packaging-only TES4 traversal follows reference base forms
and model paths, then readable NIF texture links and implicit normal/glow
companions. All available landscape texture definitions and common effects
are included. This is a bounded scene slice, not a complete plugin/mod
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

## Private server

Copy the verified APK into an external private directory. Create `download.json`
with `build`, `validation`, and `downloads` (each has `name`, `size`, `sha256`).
Allowlist `openoblivion-personal-preview.apk`, `SHA256SUMS.txt` and
`source-notes.txt`. Then run:

```sh
python3 tools/android/sideload.py --root /outside/sideload \
  --bind YOUR_TAILSCALE_IPV4 --port 8735
```

The service rejects non-Tailscale bind addresses and serves only those filenames,
with HEAD, SHA256 ETags and single-range/resume support. It streams in 1 MiB
blocks, has no directory listing or upload endpoint, and leaves sibling services
alone. Keep all payloads/reports and the private server manifest outside Git.
