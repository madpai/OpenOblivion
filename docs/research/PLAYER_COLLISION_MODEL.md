# Phone gate blockage: preview player model loading

Date: 2026-10-03. Owner report `bd8b99b04a83457c9a79d1714694c736`
identifies `0.18-audio`; its download SHA agrees with the served build. The
private screenshot shows both hall-gate leaves open. The log records successful
Open/Close/Open playback and one async physics worker, but also:

```text
AsciiInputIterator::readProperty(): Unmatched property only., expecting UniqueID
InputStream::readObject(): Unsupported wrapper class Collision
Failed to load 'meshes/basicplayer.osgt'
```

The engine substitutes its embedded error marker for a failed model. That
marker is about 123.203 units wide; the authored frame opening is about 111
units at mid height. The intended preview template body is 26.6144 units wide.
The log records movement attempts after Open stopping at the doorway. This is
a player-model loading defect separate from the animated leaf boxes.

## Cause and correction

The original OSGT had only one Generator value and additional `#` prose lines
after the header. OSG's ASCII stream reads two Generator values and then object
data; it does not skip those prose lines. Both mistakes are removed. The
vertices, twelve triangles, Collision node name, settings rewrite and all body
dimensions remain unchanged. Provenance prose now lives in
[the mesh README](../../tools/android/meshes/README.md).

The corrected file SHA256 is
`c49ec7218f55f3b100e79010b5cb609b27a7fad17d0c81ad42fa6f562851f7ea`.
Its bounds remain X/Y −13.3072..13.3072, Z 1.7012..140.0, taken from the
already-audited example-suite Collision mesh. This is the preview template
body; original Oblivion controller dimensions and motor equivalence remain
unmeasured. No native source/binary, movement constant or 0.5 camera-filter
constant changes.

Earlier Python checks extracted the correct vertex numbers without decoding
the file. Earlier desktop gate probes loaded the healthy template DAE. Those
checks did not establish Android OSGT loading. The new CTest fixture uses the
actual OSG reader, checks the loaded hierarchy, eight vertices, twelve decoded
triangles and all six bound coordinates. All **15 CTest groups** pass.

## Measured before/after evidence

The preserved 0.18 model reproduces the exact parser errors with OSG 3.6.5.
The corrected model loads. An independently written, private JNI harness links
the exact unchanged ARM64 OSG static libraries used by the current native
Android build. On the isolated Android 14 emulator with native ARM64
translation, it rejects the old file and passes every hierarchy/triangle/bounds
check on the corrected file (`ARM64_OSG old=1 fixed=0`). This exercises native
model decoding without requesting a GL scene. It is not physical-phone passage
acceptance or an emulator rendering claim.

The bounded Vilverin native before/after probes use the Android settings
rewrite, the exact supplied OSGT and **one async physics worker**. With the old
file, leaf closed/open/closed collision checks pass, but the player stays at
local Y −13.625809 after opening. With the corrected file, the player is
blocked at Y −18.278564 while closed and crosses to Y +373.571655 after Open.
Full installed-data traversal with the corrected model passes too. Desktop
uses double-precision Bullet; physical Android movement still needs the owner
retest. The gate/frame geometry and animation are unchanged between controls.

Private evidence is retained under `evidence/tes4-player-model-20261003`, with
`tes4-player-model-old-20a`, `tes4-player-model-fixed-20b` and
`tes4-player-model-full-20c` scene runs. Raw report, screenshot, captures,
native harness and APKs remain outside public Git/CI.

Reproduce the decoder check through the ordinary public CMake/CTest build.
For native scene comparison, use the recorded engine and the prior
[door reproduction command](TES4_DOORS.md), adding:

```sh
--door-traversal \
--player-collision-model tools/android/meshes/basicplayer.osgt \
--async-physics-threads 1
```

Use a fresh private output directory and `--scene-data` for the actual bounded
payload, or `--installed-data` for the full source Data. A supplied model failing
to load now fails the probe independently of visual gate success.

## Private packages and acceptance

| Package | Bytes | SHA256 |
|---|---:|---|
| 0.20-fit single APK, versionCode 20 | 667,756,891 | `42953ccdabe775a2cb720629446a240179fee059fea47a9433cb3a0d5fb348d8` |
| 0.21-installed-fit complete ZIP, versionCode 21 | 5,569,251,666 | `037ce9eadcae74bd5d2ddf362e1e159c6c7ae4d52b08e0549ce9ac74ad01f985` |

The single payload has 4,192 files / 869,962,749 bytes, ID
`3739014dc9c27e9074faf268ac0f640ef567153613894b0b9c0397bfd42d41ef`.
The complete payload has 824 files / 5,955,596,757 bytes, ID
`75eee5118205024fd00c48ec4fd965b2ee6fdb2243d6bf0ddc7aaeb14d0e87d4`.
All 73 supplied Data files / 5,820,258,458 original bytes remain unchanged.
Native library SHA remains
`d2b097d80b2d6a6c0997490216a530432f87399740a1598e01916a9cae0c9222`.
The prior 0.18/0.19 packages remain private recovery checkpoints.

Signatures, alignment, payload/native identities and the full ZIP's CRCs and
six nested APK hashes pass. The isolated emulator upgrades 0.19 → 0.20 → 0.21,
verifies all 4,192/824 extracted file hashes and all one/six installed APK
hashes, and reaches the ready launcher. Preparation takes about 22.23/92.80
seconds on this test setup. These are installation/storage/UI checks; the
historical emulator GLES translation crash still prevents scene acceptance.

Use the smaller 0.20 APK for the gate retest. The optional complete set supplies
artwork for exploration beyond the bounded slice using the same engine; it
does not add completed quests or combat. Wider exploration needs phone testing.
The full set retains its six-APK computer installation and about 18 GB free-space
requirement. The original audio/door/idle limitations remain.

Phone QA objective **OO-ANDROID-020**: open the gate, walk through, turn around
and walk back. Check nearby Open/Close audio, closed-leaf blocking, stairs and
jump. The screenshot proves visible opening on 0.18; corrected phone passage
and audible audio acceptance remain pending. The complete 1:1 port is incomplete.
