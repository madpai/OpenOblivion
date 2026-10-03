# Complete private installed-data packaging

Checkpoint: 2026-10-03. The owner's request covers a complete asset package and
the 1:1 Android port. Packaging is a separate acceptance gate from gameplay.
The earlier single APK contains only the Vilverin visual slice.

Current continuation: **0.21-installed-fit**, versionCode 21,
5,569,251,666 bytes, SHA256
`037ce9eadcae74bd5d2ddf362e1e159c6c7ae4d52b08e0549ce9ac74ad01f985`.
It uses the same complete Data snapshot and installation structure, with the
native idle and embedded gate changes described in [TES4_ANIMATION.md](TES4_ANIMATION.md)
and [TES4_DOORS.md](TES4_DOORS.md). Native audio is enabled as described in
[TES4_AUDIO.md](TES4_AUDIO.md). The preview player model serialization fix is
documented in [PLAYER_COLLISION_MODEL.md](PLAYER_COLLISION_MODEL.md).
Its extracted payload contains **824 files / 5,955,596,757 bytes**, including
all 73 original Data files.
The earlier 0.13 measurements below establish the original packaging/storage
checkpoint. All packages remain private; the smaller single APK is 0.20-fit.
Use the smaller APK for the gate test. The full set uses the same engine and
supplies artwork for broader exploration; it does not add completed quests or
combat. Broader phone exploration remains unverified. The preceding 0.18/0.19
audio packages are retained privately for recovery.

Both downloads use the same Vilverin interior/exterior starting buttons and
include the gate fix, NPC idle and nearby door sounds. The full set is useful
for exploratory rendering and collision tests while walking farther from
Vilverin: check whether surrounding terrain, architecture, textures and models
load, and report missing artwork or crashes. These are proposed phone tests,
not verified additional playable regions. For the current gate-passage retest,
the smaller single APK is sufficient.

## Measured content and format boundary

The supplied classic Data directory contains **73 files / 5,820,258,458 bytes**:
all base and installed expansion BSAs/plugins, loose music, videos, shaders,
textures and installation text. Independently streaming raw DEFLATE level 6
over each file produces 5,496,260,389 bytes before ZIP metadata or runtime files.
Even the base-only subset produces 4,403,875,283 compressed bytes.

The installed Android ZIP writer (`com.android:zipflinger:8.5.2`) rejects a
ZIP32 central-directory offset above 4,294,967,295. A complete ordinary ZIP
payload already exceeds that boundary. ZIP64 is permitted for the outer
download archive, not for the signed APK components used here. Do not quietly
omit voices/videos or increase an APK budget to claim complete content.

Android supports installing split APKs as one application; its official
[adb documentation](https://developer.android.com/tools/adb) describes
`install-multiple`. This checkpoint uses a base APK and five asset-only APKs,
with the same package, version and signing certificate. It is an **adb APK
set**, not a bundletool `.apks` or Play delivery bundle.

## Original implementation

`tools/android/payload.py` inventories every supplied Data file, rejects links,
ambiguous paths and executable modules, and partitions whole files into ZIP32
payloads bounded at 1,500 MiB before compression. Missing required classic
archives fail the build. Archive bytes and loose-file bytes remain unchanged;
there is no texture conversion, audio re-encoding or BSA rebuilding.

`build_personal.py --all-assets --native-runtime ...` uses the existing audited
native runtime/template and includes the complete Data inventory. A schema-2
manifest lists every source-file size/hash, each payload part, archive order
and the measured classic plugin list. Every packaged entry is streamed and
compared to the independent source manifest before signing. Build receipts
record host/tool/native/SDK identities.

`split_assets.py` builds and signs asset-only splits using SDK 35 tools and the
existing private debug certificate. Each split must verify v2 signing, match
the base signer/version, pass alignment and CRC checks. The private download
ZIP contains all six APKs, checksums, a manifest, instructions and Windows/
POSIX `adb install-multiple -r` scripts. It never enters public Git or CI.

The launcher opens assets from the installed APK set, verifies each extracted
file, rejects missing parts before writing files, checks available storage and
marks completion only after all entries agree. Obsolete loose scene extracts
are deleted after verification so they cannot override the newly installed
BSAs. The launcher scrolls on short landscape displays. The existing schema-1
single-APK format remains supported.

Configuration explicitly loads the six base archives, then installed expansion
archives. It enables `Oblivion.esm` and installed `DLCShiveringIsles.esp` /
`Knights.esp`. Other supplied plugins are preserved but not automatically
enabled: this tool does not recover or guess a mod load order.

## Scope and continuation

The complete payload has **824 files / 5,955,596,775 extracted bytes**, including
the template, engine resources and original diagnostic/interaction scripts.
All game files remain private. Game EXE/DLL files outside Data are not assets
and are excluded. Allow about 18 GB free for a downloaded set, its installed
APK copies and extracted files, plus more when upgrading existing content.

Desktop Vilverin interior and exterior probes load the full installed archive /
classic expansion list and finish with inspected captures. This confirms those
scenes with the complete content configuration. It does not establish every
worldspace, expansion quest, asset format or override rule.

The founding `0.13-installed-assets` set is **5,569,203,949 bytes**, SHA256
`c75804511bc434951e66acf9cb1933bb19e7b515c6d62708706122dfcbcd2474`.
An isolated Android 14 x86_64 emulator with ARM64 translation installs all six
signed APKs together. First-launch extraction finishes in about 94 seconds.
An independent on-device SHA256/size walk agrees for every one of the 824 files
and all 73 original Data files. The ready marker, all configured archives/
plugins, removal of an obsolete loose-file fixture and enabled scene buttons
are checked. A base-only install correctly reports the missing splits.
The final bundle also passes an independent check of every nested APK hash.
All 13 public CTest groups and the publication/history guard pass.

These are emulator installation/storage/UI checks, not Android world-rendering
acceptance. No physical phone is connected through adb. The separate desktop
captures show the selected scenes; the Android runtime library is unchanged.

At the 0.13 packaging checkpoint, the Android runtime library and movement
constants were unchanged. The 0.15 continuation adds default NPC idle; full
locomotion/attack/facial animation, quests, combat, inventory transfer, save
compatibility, audio/video playback and original menus remain incomplete. Physical-phone acceptance remains separate from
emulator installation/storage checks. See [the parity ledger](../PARITY.md).

Private evidence: `openoblivion-private/evidence/full-content-package-20261003`
and `installed-data-desktop-13{a,b}`. Keep raw manifests, hashes of owner data,
screenshots and APKs there; publish only these measured scope statements.
