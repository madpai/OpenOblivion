# Havok collision and the movement gap

Date: 2026-10-01. This is a movement-blocking investigation. It does not change
the player motor, the stair filter, or the phone build. Oblivion movement is
still the borrowed OpenMW controller on collision generated from visible
meshes. Tuning that controller further, including walk/run speed, is blocked
until the collision surface and the player body match the serialized Havok
semantics closely enough to measure.

No Havok binary, MOPP cooker, or decompiled game code is included or required
for the first step below.

## What the phone just showed

Private report `93db9dd902434ef2bf0e54dc7234dca9` is build `0.8-run`. The log
contains `OPENOBLIVION_RUN_GATE`, so the settings pin ran. Across 357 grounded
moving samples spanning 25.7 simulation seconds, horizontal speed has median
149.9 and maximum 165.1. Nothing exceeds 200. The earlier 0.7 log, report
`472a8828bfc742a4bac5fc80c653b358`, has the same walk band, median 150.9.
The borrowed gait control is not producing a second speed. Oblivion's normal
travel mode is run. That speed is not recoverable by another key binding while
the body is still walking on the wrong surface.

## Two different physics models

Oblivion stores gameplay collision in `bhk*` blocks and moves the live player
with a Havok character body. The pinned OpenMW 0.52 loader does not use those
blocks. For a NIF at version 10.0.1.0 or later it sets
`mGenerateCollision` when `BSXFlags` bit 2 is set, with the explicit comment
that this uses rendered geometry instead of Bethesda Havok data
(`components/nifbullet/bulletnifloader.cpp` at the locked desktop revision
`46bd4599203ee52ffc0f3e8edb3fc159a0303a49`). The same branch is in the Android
0.51 base. The NIF reader in `components/nif/physics.cpp` does parse
`bhkCollisionObject`, `bhkRigidBody`, `bhkMoppBvTreeShape`, and
`bhkNiTriStripsShape`, and nothing in the Bullet loader consumes them.

The live actor in that runtime is a vertical Bullet cylinder built from the
rendered bounds (`mwphysics/actor.cpp`), or a box when the bounds are not
roughly round. Step-up is the constant 34, step-down is 62, and the maximum
slope is 46 degrees (`components/misc/constants.hpp`,
`mwphysics/constants.hpp`). Extra stair hacks in the stepper exist for bad
Morrowind assets. None of these numbers is an Oblivion record. There is no
collision-layer filter.

## What this scene actually serializes

A header census of the private Vilverin visual slice read 1,245 of 1,319 NIF
headers. Seventy-four headers did not match this reader, so the counts are a
lower bound. Parsed versions are 20.0.0.4 with user version 11 or 10 and
Bethesda version 11.

| Block | Files | Blocks |
|---|---:|---:|
| `bhkCollisionObject` | 896 | 1,132 |
| `bhkRigidBody` | 609 | 1,266 |
| `bhkRigidBodyT` | 317 | 491 |
| `bhkMoppBvTreeShape` | 237 | 238 |
| `bhkNiTriStripsShape` | 240 | 241 |
| `bhkPackedNiTriStripsShape` | 0 | 0 |
| `bhkConvexVerticesShape` | 415 | 531 |
| `bhkBoxShape` | 214 | 524 |
| `bhkCapsuleShape` | 114 | 675 |
| `bhkListShape` | 102 | 102 |
| `bhkConvexTransformShape` | 62 | 195 |
| `bhkBlendCollisionObject` | 26 | 625 |
| `bhkSPCollisionObject` | 8 | 8 |

Three hundred eighteen parsed files have no `bhk*` block. All six stair-named
meshes in the slice (`arnhallstairs01`, `arnhallstairsentrance01`,
`arnhalluturnstairs02`, `arwhallstairs01`, `arwhallstairsbridge01`,
`arpitstairs02`) use the same chain: `BSXFlags`, visible `NiTriStrips`, and
`bhkCollisionObject` / `bhkRigidBody` / `bhkMoppBvTreeShape` /
`bhkNiTriStripsShape`. This slice does not use packed strip shapes. That is
not a claim about every Oblivion mesh.

The MOPP block is an acceleration structure around the strip shape. Bullet
already builds a BVH from triangles. The MOPP byte code does not have to be
executed, and the proprietary cooker does not have to be shipped, if the child
strip vertices and triangles are translated. That translation is the missing
static-world path.

Open-source NIF tooling uses a factor of 7 when it writes packed Havok
vertices (`bhkScaleFactor = 7` in niftools `MaxNifTools.ini`; PyFFI stores
packed vertices as `nif / 7`). That factor does not apply to these stairs.
Their collision vertices live in `NiTriStripsData` referenced by
`bhkNiTriStripsShape`, and the measured extents are already in the same units
as the visible mesh. Multiplying by 7 makes the collision about seven times
too large. `bhkMoppBvTreeShape.scale` is 1 and the strip shape scale is
`(1, 1, 1, 0)` on all six.

## Layers, materials, and the player body

`nif.xml` from niftools defines `OblivionLayer` as the byte in `HavokFilter`,
which OpenMW already stores as `HavokFilter::mLayer`. The values that matter
for walking are separate from the surface material:

- `OL_STATIC` (1), `OL_ANIM_STATIC` (2), `OL_TERRAIN` (13), and `OL_STAIRS`
  (19) are world surfaces a character is expected to stand on.
- `OL_CLUTTER` (4) is a dynamic rigid body, not part of the static stair mesh.
- `OL_NONCOLLIDABLE` (15), `OL_TRIGGER` (12), and the pick layers
  (`OL_CAMERA_PICK` 24 through `OL_PATH_PICK` 27) are present in the file and
  must not become solid player collision.
- `OL_CHAR_CONTROLLER` (20) is the live character body.
- `OblivionHavokMaterial` value 15 is `OB_HAV_MAT_STONE_STAIRS`. That is a
  material id inside the shape, not the same field as `OL_STAIRS`.

The six stair bodies were then decoded with the 20.0.0.4 layout used by the
pinned reader. Each one is the same kind of static body:

| Mesh | Visible verts / tris | Collision verts / tris | Layer | Material | Motion | Quality |
|---|---:|---:|---|---|---|---|
| `arnhallstairs01` | 889 / 1,612 | 402 / 624 | `OL_STATIC` | stone | fixed | fixed |
| `arnhallstairsentrance01` | 667 / 1,252 | 312 / 480 | `OL_STATIC` | stone | fixed | fixed |
| `arnhalluturnstairs02` | 4,083 / 7,984 | 2,108 / 3,495 | `OL_STATIC` | stone | fixed | fixed |
| `arwhallstairs01` | 1,390 / 2,618 | 756 / 1,288 | `OL_STATIC` | stone | fixed | fixed |
| `arwhallstairsbridge01` | 1,965 / 3,602 | 1,026 / 1,714 | `OL_STATIC` | stone | fixed | fixed |
| `arpitstairs02` | 903 / 1,613 | 487 / 782 | `OL_STATIC` | stone | fixed | fixed |

World-object layer and rigid-body layer are both 1. The strip subshape filters
are also layer 1. None of these stairs uses `OL_STAIRS` or the stone-stairs
material. Mass is 0. Friction and restitution are both 0.3. Collision-object
flags are 1. On four stairs the collision bounds match the visible bounds on
every axis, so the unit scale is 1. The U-turn and pit meshes differ by a few
percent on some axes because the collision mesh is not the render mesh, not
because of a factor of 7. The collision meshes have about half as many
triangles as the visible meshes.

`HkMotionType::Motion_Fixed` (7) and `Quality_Fixed` (1) are the static
architecture combination described by the Construction Set physics notes.
`Motion_Dynamic` and `Quality_Moving` are clutter. `bhkBlendCollisionObject`
in this slice is the ragdoll path (625 blocks in 26 files), not the live
player. `bhkSPCollisionObject` is a phantom used for trigger volumes. Neither
is required to test stair contact.

The live player capsule is not one of these static meshes. Oblivion constructs
it at runtime on `OL_CHAR_CONTROLLER`. Its radius, height, and step offset are
not in the stair NIFs and are not recovered here. OpenMW's cylinder, 34-unit
step-up, and 62-unit ground sweep are Morrowind controller constants. Changing
them before the ground mesh is the authored one would tune contact against the
decorative render surface.

## What is required, and what is not

Required before another movement tune:

1. Static triangle collision from these `bhkNiTriStripsShape` blocks, in the
   stored units, for fixed `OL_STATIC` bodies. The MOPP bytes stay unused.
2. A layer filter so later pick, trigger, and non-collidable shapes do not
   become floors. These six stairs do not need a special stair layer.
3. A measured comparison on one of these stairs: the authored triangles
   versus the current render-mesh collision, then the same player trace on
   both.

Not required for that comparison:

- Executing or rebuilding MOPP.
- Packed strips, until a mesh outside this slice needs them.
- Clutter simulation, ragdolls, constraints, or phantom triggers.
- A new player capsule or a new step height. Those are the second change,
  after the trace shows what the authored surface does to the current body.
- Walk/run speed constants. The GMST read already in
  [player movement](../PLAYER_MOVEMENT.md) stays on record. Applying it on the
  render-mesh collision would mix two unmeasured differences.

## Static loader measurement

The bounded loader is now in the external Bullet NIF loaders behind
`OPENOBLIVION_AUTHORED_COLLISION=1`. See
[tools/native](../../tools/native/README.md). It accepts only a root
`bhkCollisionObject` whose body is fixed, quality-fixed, layer `OL_STATIC` on
both the world filter and the body filter, and whose shape is a
`bhkMoppBvTreeShape` over `bhkNiTriStripsShape` or that strip shape directly.
Strip scale and MOPP scale must be 1. The root Gamebryo transform must be
identity. Triangles are built in the stored units and added as one compound
child at the origin. The rigid-body translation is not applied. MOPP bytes are
not executed. Anything else, including a non-identity root, keeps the
render-mesh fallback. The player cylinder, the 34/62 step constants and the
camera filter were not changed.

The desktop 0.52 loader was rebuilt and run on the six stair NIFs. Bullet's
triangle count omits degenerate strip steps, the same rule the render-mesh
path already uses. The earlier table counted every step (`length - 2`), so
those larger numbers remain the serialized counts. The counts Bullet keeps are:

| Mesh | Render triangles | Authored triangles | Compound children | Child origin |
|---|---:|---:|---:|---|
| `arnhallstairs01` | 866 | 213 | 1 | 0,0,0 |
| `arnhallstairsentrance01` | 700 | 165 | 1 | 0,0,0 |
| `arnhalluturnstairs02` | 4,632 | 1,522 | 1 | 0,0,0 |
| `arwhallstairs01` | 1,486 | 575 | 1 | 0,0,0 |
| `arwhallstairsbridge01` | 2,066 | 751 | 1 | 0,0,0 |
| `arpitstairs02` | 756 | 268 | 1 | 0,0,0 |

With the switch off, the same files produce the render counts and several
compound children, also at the origin. Four stairs have the same Bullet AABB
either way: `arnhallstairs01`, `arnhallstairsentrance01`, `arwhallstairs01`
and `arwhallstairsbridge01`. The U-turn mesh is larger on the authored shape
by about 32 units on X and Y. The pit mesh differs on its lower Z bound
(-31.7 render, -11.8 authored). That matches the earlier finding that those
two collision meshes are not the render mesh.

A 20 by 20 downward ray grid on each shape's own AABB shows the surfaces are
not the same. On `arwhallstairs01`, where the AABBs match, 245 rays hit both
shapes. The median absolute height difference is 2.32 units, 188 rays differ
by more than 1, 19 differ by more than 16, and the maximum is 372.73. The
bridge median is 2.44 (maximum 29.3). `arnhallstairs01` median is 0.55
(maximum 12.4). The entrance median is 0 (maximum 6.86). The pit median is 0
(maximum 2.84). The U-turn grid is not paired, because its AABBs differ.
Contact changes. This is a shape trace, not a character-controller recording.

The Android 0.51 loader compiles with the same switch. Linking
`libopenmw.so` first failed on a debug relocation in the existing
`utilpackage.cpp.o` (`R_AARCH64_ABS32` out of range). Stripping debug info
from the new loader object, which the phone package strips anyway, let the
link succeed. The cylinder and the stair filter are unchanged. Preview
`0.9-authored-collision` is the phone package that carries this library.

## Smallest next steps

1. The stair report and this static loader comparison are done.
2. The character body is still unknown. Radius, height and step offset are
   not in these NIFs. Do not invent them, and do not change the cylinder or
   the step constants until a source for those values is identified. Repeat
   the stair trace with that body before tuning speed.
3. Oblivion's normal run speed comes after the body is standing on the
   authored surface. The 0.8 log already shows that another key binding does
   not create that speed.

Inference, not a measurement: the render mesh is a likely source of tread
snags because it is denser than the Havok mesh and has no stair layer. The
owner's liked 0.5 stair feel was camera smoothing on top of that surface. It
is not evidence that the physical steps match Oblivion.
