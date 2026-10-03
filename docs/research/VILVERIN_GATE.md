# Vilverin hall gate

Continuation, 2026-10-03: [embedded door playback](TES4_DOORS.md) now loads
the original Open/Close sequences and two authored keyframed boxes. Desktop
closed/open/closed captures, collision cross-sections and ordinary player
traversal pass. Private packages 0.16/0.17 include this implementation; phone
acceptance and original reversal/obstruction/persistence remain. The note
below records the earlier static-renderer diagnosis.

Date: 2026-10-01. Phone report `0bfee3b28dba483f988193d20f6acac5` is build
`0.10-touch-name`. The player came down the Vilverin hall stairs and stopped
at `(-4936.99, 144.41, -447)` while the center ray read `Gate`,
`FormId:0x20228cc`. That log has no activation line. The thirteen-button
overlay covered the right half of the screen, including USE.

## The records

`0x000228CC` is DOOR `ARNHallGateDoor01`, model
`Dungeons\AyleidRuins\Interior\ARNHallGateDoor01.NIF`. Reference `0x00066EC0`
in cell Vilverin (`0x0001663A`) sits at `(-4928, 64, -384)` with yaw `-π`.
The reference has no teleport destination and no lock. The static on the same
spot, `0x00066EBF`, is `ARNHallDoorFrame01` at z `-448` with the same yaw.

The stopped point is on `ARNHallStairs01` (reference `0x000491B5` at
`(-4928, 384, -320)`, same yaw). The gate leaf's transformed bounds are about
76 units further along the hall. The stair mesh's own bounds contain the
stopped point. A cross-section of that stair, in stored units, is about 200
units wide at the stop and about 152 units wide nearer the gate.

## What is solid

`ARNHallGateDoor01` has BSX integer data 11. OpenMW's collision test is
`mData & 2`, and 11 includes that flag. The root has no collision object.
Each leaf carries a `bhkBoxShape` on a `bhkRigidBodyT`, layer 2
(`OL_ANIM_STATIC`), motion 6 (keyframed), quality 2, mass 0. Those bodies
are not fixed `OL_STATIC` strips, so the authored-strip loader leaves them
and the render mesh stays. Multiplying the box half-extents by 7 reproduces
the visible slabs. Strip vertices are a different field and stay in mesh
units. The phone log shows `NiControllerManager` and
`NiMultiTargetTransformController` unhandled on this file, and no authored
triangle count. The sequences are named Open and Close, each 1.367 seconds.
The stored Open keys yaw the two leaves about Z to about +87.9 and −87.3
degrees. Those keys are not played, so the leaves stay in the closed bind
pose. The text keys name `DRSMetalOpen02` and `DRSMetalClose02`.

A 0.5-unit raster of the closed render mesh reported a 14-unit gap. That
figure leaks between the overlapping leaves. A 0.25-unit flood fill has no
connected through-path: width 0 at mid height, and about 1.5 at the bottom
edge. Holes in one leaf do not continue through the other leaf. A body 26
units wide does not walk through that closed leaf, and the 123-unit marker
does not either. The hall frame `ARNHallDoorFrame01` does take the strip
path: the phone logged 30 triangles, and the strip scale is `(1, 1, 1)`.
Those vertices were not multiplied by 7. The collision opening is 111 units
at mid height and 126.75 at the floor. The 123-unit-wide error-marker body
fits the floor slice and does not fit the mid-height slice. The 26.6-unit
template collision box fits both.

`ARNHallStairs01` is already on that same strip path (213 triangles in the
phone log). Its landing cross-section is wider than both bodies. The frame,
not the stair treads, is the opening that rejects the marker body once the
leaf is out of the way.

## What USE does

Same-cell ESM4 doors have no C++ animation. The 0.51 activation handler hid
the object for five seconds and then showed it again. Load doors still
teleport; this hall gate is not one of them. The packer now rewrites that
handler so a same-cell door toggles: the first USE hides the closed mesh and
it stays hidden until the next USE. The Open and Close sequences are still
not played, so the leaf disappears instead of swinging. The rewrite is in
`same_cell_doors_stay_open` and is applied to the staged
`activationhandlers.lua` after the resource hash check. A successful USE logs
`OPENOBLIVION_DOOR`.

The closed overlay is now the move stick plus USE, JUMP, ATK, and MORE.
The other controls, including the old always-on cluster, are on the MORE
tray. See [touch actions](../TOUCH_ACTIONS.md).

## Still outside this package

ESM4 NPCs and creatures are not in the Lua type map. `ESM4Npc::getName`
already returns `mFullName`, which is why the engine tooltip can say Bandit,
and why the name bar cannot. ESM4 container inventory is a list of form id
and count. The Lua container type has no accessor for it, and no activation
handler opens a chest. `ESM4Npc::insertObjectPhysics` does not add a body.
The male skeleton loads far enough to log `NiBSBoneLODController` and
`bhkBlendController`. `meshes/characters/_male/skeleton.nif` has 370 blocks
and 142 named nodes, including `Bip01 Pelvis`, `Bip01 Spine`, and
`Bip01 Spine1`. It has no node named Groin, Chest, Neck, Head, or Right Hand.
Part attachment still asks for those Morrowind names, which is the Groin
error in the phone log. The beast skeleton is the same kind of mismatch:
426 blocks, 160 names, and no Groin node.
