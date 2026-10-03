# Embedded TES4 doors and moving collision

Checkpoint: 2026-10-03. The Vilverin hall gate now plays its original embedded
Open and Close clips through USE. Its two authored keyframed boxes follow the
leaves, and the door remains visible and holds the final pose. This is a
measured door slice toward the active 1:1 Android goal.

## Implementation and reproduction

The original KF adapter now also accepts an explicitly selected
NiControllerSequence. An active classic NiControllerManager owns separate,
immutable clip holders in scene-template metadata. Each object clones its
controllers and assigns its own existing non-actor playback clock. Managed
nodes survive scene optimization, so renderer and collision retain the same
NIF record-index paths. Root-KF decoding and NPC idle retain their previous
behavior and receipt ancestry.

TES4 doors register the object clock. The global-script `ESM4Door` interface
provides `hasSequence`, `isSequencePlaying` and a queued `playSequence` request.
The packaged activation handler requests Open/Close, with Forward/Backward
and the previous hide toggle available for unsupported meshes. Repeated USE
during an active clip is ignored. Teleport-door handling stays on its existing
path. These preview semantics do not establish original activation parity.

The separate collision adapter accepts active, zero-mass keyframed
`OL_ANIM_STATIC` `bhkRigidBodyT` boxes. Their primitive extents and body offsets
use the measured classic factor of seven. The offset stays inside a local
compound shape; its parent child follows the authored NiNode transform.
Compound cloning preserves scale bookkeeping before adding already-scaled
children, preventing the first update from scaling their offsets twice.
Unsupported shape trees retain the existing render-mesh fallback. The fixed
`OL_STATIC` strip helper, body model, movement settings and 0.5 stair filter
are unchanged.

Apply after the recorded camera/static-strip, interaction and animation patches:

```sh
python3 tools/native/tes4_doors.py apply --source /outside/native/source \
  --revision 46bd4599203ee52ffc0f3e8edb3fc159a0303a49
# Rebuild openmw, then record the exact resulting binary:
python3 tools/native/tes4_doors.py record --source /outside/native/source \
  --binary /outside/native/build/openmw --manifest /outside/native/build-manifest.json
python3 tools/native/run_kf_fixtures.py --fixture doors \
  --source /outside/native/source --build /outside/native/build \
  --output /outside/evidence/original-door-fixtures
```

Android uses engine base `f4bec41444214a7903bebd178389ca22ca13f646` inside the
audited donor tree. Strip the rebuilt library into the private runtime, record
against that library and its manifest, then run the personal packager. The
door receipt locks eight exact input files, two original headers, patch/tool
identities and both predecessor receipts. Earlier receipts remain intact;
verification permits only their specifically recorded successor changes.
See the [license audit](LICENSE_MATRIX.md).

## Measured evidence

- Original native fixtures pass for separate groups, inactive managers, classic
  version bounds, duplicate-name rejection, scene/controller cloning, box
  offsets/extents/margins, scaled compound cloning and reference isolation.
  Previous KF/default/spline/skin fixtures also pass. All 14 public CTest groups
  pass. Linux and Android ARM64 native engines compile.
  The final desktop binary also passes the NPC-idle and container-window/Close
  scene regressions.
- The owner's gate has two 1.366666675-second sequences, four transform tracks
  per sequence and two keyframed box bodies. An unchanged independent PyFFI
  parse plus an original float64 Hermite evaluator agrees with **488 native
  effective poses**, maximum component error **1.23114e-7**, tolerance 2e-5.
  Both original box parameter sets also agree. Missing channels preserve the
  target's authored bind transform.
- Full-installed-data and bounded-slice desktop tests activate the actual
  packaged handler. Both clocks advance, finish and hold their end times.
  An extra mid-clip activation is consumed without hiding the gate. Private
  captures show closed, open and closed-again leaves.
- A fixed 31-ray cross-section has **21 gate hits closed, zero fully open,
  and 21 closed again**. The current player body, walking through the ordinary
  controls, stops at local Y **-18.278564** while the gate is closed, remains
  grounded, then crosses beyond local Y **+374** after opening. This proves
  traversal for the current body; it does not measure the original capsule.

Raw reports, the original mesh and all new captures remain private under
`openoblivion-private/evidence/tes4-doors-*`. No additional public screenshot
exception is used.

## Private packages and remaining acceptance

The single Vilverin APK is **0.16-doors**, versionCode 16, **661,325,407 bytes**,
SHA256 `09c62b589c1fe73d15cd13654323668901c02d9a6c6c9d338c40911902eb05e7`.
The complete installed-data APK set is **0.17-installed-doors**, versionCode 17,
**5,569,251,696 bytes**, SHA256
`1a10afc36929493cead6bc4f2257b26fdae8d87b3c720e847c644cfa9cb79054`.
It includes every supplied Data file unchanged, in six signed APKs; see
[installation instructions](INSTALLED_ASSETS.md). The previous 0.14/0.15
packages remain private recovery checkpoints.

An isolated Android 14 emulator upgrades from the previous full set to 0.16,
then to 0.17. All **4,170 single-package payload files** and **824 full-set
payload files** match their source hashes; the installed one/six APK hashes,
ready markers and launcher controls also pass. Preparing the complete payload
takes **96.83 seconds** in this run. This measures installation, storage and
launcher behavior; the emulator's historical GLES translation failure remains
unresolved, so these checks do not establish Android scene rendering.

Physical-phone gate rendering/traversal and NPC idle acceptance remain pending.
The desktop scene runs with audio disabled. Original-executable timing,
mid-swing reversal, closing obstruction/contact behavior, locks/keys/traps,
reference/save persistence and other authored collision shapes remain parity
work. Loot transfer, actor locomotion/AI/combat, first-person hands, quests,
dialogue and the other areas in [the parity ledger](../PARITY.md) are incomplete.
