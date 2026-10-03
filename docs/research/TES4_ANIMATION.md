# TES4 transform clips and default NPC idle

Checkpoint: 2026-10-03. Native Linux and Android ARM64 builds now decode
`NiControllerSequence` KF roots, resolve string-palette bone names and preserve
valid constant transform channels. An original bounded evaluator handles
float and compressed cubic spline channels, including the NIF WXYZ rotation
layout and missing-channel sentinels. The legacy sequence-helper loader remains.
External source pins, notices and exact integration inputs are registered in
[the license matrix](LICENSE_MATRIX.md).

## Measured decoding

The owner's third-person idle and forward-walking clips use version 20.0.0.4.
The unchanged native renderer loaded zero tracks from either root. The new
adapter loads **73 transform tracks from each**. Idle includes 23 compressed
spline transform tracks, 50 ordinary transform tracks and two float tracks;
the two float tracks are explicitly outside this transform adapter.

Independent PyFFI parsing and a separately written float64 de Boor evaluator
cross-check 1,525 compressed channel samples across 23 tracks. Maximum absolute
component error is **0.0000007321**, below the 0.00002 comparison tolerance.
Both clips produce 8,906 finite sampled poses over 61 times per track. Idle has
25 changing tracks and forward walking has 66. These are decoder measurements,
not an original-executable playback or locomotion comparison.

Original in-memory native fixtures cover constant defaults, invalid-value
sentinels, palette bounds/fallback, duplicate targets, truncated spline data,
analytic packed channels, controller cloning, data lifetime and legacy fallback.
The public math fixtures additionally check analytic cubic/linear curves,
endpoints, packed offsets and bounds. All 14 CTest groups pass. No game clips
or proprietary implementation are included in these fixtures.

## Live actor connection

The renderer selects `idle.kf` beside the NPC's authored skeleton. TES4 NPCs
now register with the existing non-actor animation update path. This supplies
the preview's idle clock; it does not supply TES4 actor statistics or AI.
Clips use independent cloned controllers per actor.

The first live probe proved the clock but still showed a T-pose. Inspection
found that the previous empty attachment filter copied a part's private
skeleton. An original TES4 selector now copies the renderable's local subtree,
allowing skinned parts to resolve the actor's animated bones. Inspected private
captures show the clothed bandit with lowered arms and the original idle pose.
The human skeleton lacks the clip's nine tail targets; those targets are
reported and skipped rather than mapped to invented bones.

Full-data and bounded-APK-slice Vilverin probes each observe five NPCs, at least
13 clock samples per actor, and two natural loop wraps without starting an
animation from the probe. The camera-only observation driver chooses a clear
view through a collision ray and records three private captures. It is excluded
from the shipped APK. The same-binary container window/capture/close regression also passes. Movement
constants remain unchanged; motor parity remains a separate acceptance gate.

## Reproduction and receipts

Apply the existing interaction integration first, then:

```sh
python3 tools/native/tes4_animation.py apply --source /outside/native-desktop/source \
  --revision 46bd4599203ee52ffc0f3e8edb3fc159a0303a49
# Rebuild the native engine, then record its existing build manifest.
python3 tools/native/tes4_animation.py record --source /outside/native-desktop/source \
  --binary /outside/native-desktop/build/openmw --manifest /outside/native-desktop/build-manifest.json
python3 tools/native/run_kf_fixtures.py --source /outside/native-desktop/source \
  --build /outside/native-desktop/build --output /outside/evidence/kf-fixtures
```

The Android engine revision is `f4bec41444214a7903bebd178389ca22ca13f646`.
Build it, strip debug information into the private runtime's `libopenmw.so`,
and record against its runtime manifest. The packager checks animation tools
and all native libraries. Receipts keep the predecessor interaction receipt,
exact input/output hashes and the narrow actor-file successor chain. Edited
headers or predecessor receipts fail validation.

Use `tools/upstream/probe_scene.py --tes4-animation` with the recorded Linux
build and private installation; `--scene-data` can test the selected loose
slice. The fixture runner uses the same Release components library to avoid
the reader's different Debug pointer layout. Its explicit checks remain active.

## Private test packages and limits

The single APK is **0.14-idle**, versionCode 14: 661,308,211 bytes, SHA256
`1de755cda143598c31df5fad55e1edeb37ce8a9f47295145937177afa8cf0cc4`.
Its 4,170 payload files / 863,696,567 extracted bytes include the byte-identical
original idle beside the bounded Vilverin models. Every payload hash verifies.
The complete installed-data set is **0.15-installed-idle**, versionCode 15:
5,569,234,535 bytes, SHA256
`c56f5b551f4f99a05137daa22c63e7013562957fc5ecb940337793cddddbaf0c`.
It retains all 73 original Data files and the six-APK installation procedure.
An isolated Android 14 emulator upgrades from the single APK to the full set;
all 824 extracted files match their sizes/hashes, and all six installed APKs
match their package hashes. The ready marker and enabled launcher are checked.
Full-set extraction takes about 93 seconds in this emulator. These are
installation/storage/UI measurements, not world-rendering acceptance.

Native Android library SHA256:
`933510d7a30ec17541ba9eb071ca748af31fd5f739d3c329496772cf60db2230`.
Desktop engine SHA256:
`8ee1ced888724883cddf9c52bb780cff2c27b44209192e46176c6f4cd91e2d27`.
The existing private signer, player motor, collision box, fixed static strips
and 0.5 stair filter are retained.

This checkpoint implements transform decoding and default third-person NPC
idle. Locomotion/attack selection, first-person hands, facial/morph tracks,
equipment/body-slot masking, special idle rules, actor physics, embedded door
sequences, combat, scripts/quests and save compatibility remain required work.
Android installation and storage checks are separate from physical-phone idle
rendering acceptance, which is pending. See [the parity ledger](../PARITY.md).

Private evidence: `tes4-animation-20261003`,
`tes4-animation-native-fixtures-14`, and `tes4-animation-desktop-14{a,b,c,d,e}`.
The earlier failed clock and bind-pose probes are retained; only the final
full-data/slice probes establish the live checkpoint. All raw files stay private.
