# Latest continuation: 0.12-containers

Current private download, 2026-10-03: `0.12-containers`, versionCode 12,
QA `OO-ANDROID-012`. APK SHA256
`f588257abe91344ce187cb34ed81f40a9c6dd7278242c717b89f6991a7bfac00`
(661,254,187 bytes). Names, read-only base-container inspection, lock-state
reset, shared NPC skeleton attachment and GUI taps are documented in
[TES4_INTERACTIONS.md](TES4_INTERACTIONS.md). The older observations and
remaining animation/body research below remain historical evidence.

# What the phone preview can already play

Date: 2026-10-01. This is a read of the published Vilverin captures and the
pinned OpenMW 0.51 sources. It does not change the player body, the
34-unit step-up, the 62-unit step-down, or the 0.5 stair filter.

## Name label

`docs/media/android-vilverin-stairs.jpg` shows the word Bandit in a small
gold-bordered label above the NPC, directly under the "Drag right to look"
hint. The crosshair sits on that NPC. The engine tooltip is already on.

`docs/media/android-vilverin-interior.jpg` aims the crosshair at stone and
draws no name. ESM4 statics do not implement a tooltip. A chest, door, or
weapon in that room can still have one when the crosshair is on the object
and the record has a full name. That has not been photographed.

In game mode the label is centered horizontally and placed just above the
object's projected top (`tooltips.cpp`, the non-GUI branch). It is not a
full-width title bar. Default GUI scale is 1 and the default font size is
16. This APK does not override those settings. Tooltip delay applies to menu
hover, not to this world label. F11 hides the HUD and the label together.

The ray length is the loaded GMST `iMaxActivateDist`. OpenMW's Morrowind
default table lists 192. The value in the running Oblivion load order was
not measured for this note.

## Controls and HUD in the same shots

The overlay is MOVE, EXIT, JUMP, and USE, plus the look hint. USE covers the
minimap. The three attribute bars and the weapon and spell slots are the
Morrowind HUD for the template player, and they already render along the
lower left. Nothing on screen sends attack (left mouse), inventory (right
mouse), sneak (left ctrl, held), weapon ready (F), spell ready (R), journal
(J), wait (T), or the game menu (Escape). EXIT leaves the activity.

Space still activates. ESM4 doors teleport or disable themselves, and ESM4
books open the Morrowind book window. ESM4 NPCs and containers do not
override activate, so USE on the bandit or the chest does not open dialogue
or loot. Container base records do store item form-id and count pairs. The
Lua `ESM4Container` type does not expose that list.

## T-pose

The bandit in the stair capture is clothed and standing in the bind pose,
arms out. `ESM4NpcAnimation` loads the skeleton and parents body, head, hair,
armor, and clothing meshes to the object root. Its TES4 update says those
parts still need to be attached to bones, and it never adds an animation
source. The Morrowind keyframe loader accepts `NiSequenceStreamHelper` clips
only. Oblivion clips are `NiControllerSequence` data. No clip is attached, so
bone attachment by itself would still be a bind pose.

The deciding desktop log, before any loader work, is one Vilverin NPC:
skeleton bone count, and whether each inserted part has a skin whose bones
exist on that skeleton.

## Working tree after this pass

Version name `0.11-fit`, versionCode 11, was the previous served download and is archived.
Physics is the 0.9 library. APK SHA256
`6dede3d7b7c16633ea07a232aa5131f70f6182fcf9052f4bda6f6f5b538050a4`
(656,483,887 bytes). QA objective `OO-ANDROID-011`.

The closed overlay is the move stick plus USE (Space), JUMP (E), ATK
(left mouse, held), and MORE. The tray holds the Shift run toggle, sneak
(left ctrl while on), weapon (F), spell (R), inventory (right mouse),
journal (J), wait (T), the game menu (Escape), POV (Tab), and exit.
USE, JUMP, and attack sit above a 13% bottom gap so the minimap is not
under the thumb. The look hint is just above the move stick. Same-cell
doors stay open after USE. The measurement is in
[the Vilverin gate note](VILVERIN_GATE.md).

A player script draws a top bar when Lua has a record name. It does not print
record ids. TES4 actors are not in the 0.51 Lua type map, so the Bandit label
remains the engine tooltip. Build 0.10 appended GUI scale 1.25 and font size
20. The engine sanitized 20 to 18. The host no longer appends those two
settings.

## Still next

1. Bind TES4 actor and container display names in Lua, then the top bar can
   show them. Container inventory is loaded on the base record and is not
   exposed to Lua, so USE still does not open a chest.
2. Match inserted NPC parts to the male skeleton. That NIF has 142 named
   nodes, including `Bip01 Pelvis` and `Bip01 Spine`, and no Groin, Chest,
   Neck, Head, or Right Hand node. Not a new animation system, and not a new body.
3. Character radius, height, and step offset. A pass over the master, the
   default ini, and the player skeleton did not find them. Do not retune the
   body from this pass.

## Character body, measured 2026-10-01

Oblivion's live character controller is not in the files that were read.
`Oblivion.esm` has 382 GMSTs. None is a step height, a controller radius, or
`fJumpHeightMin`. `Oblivion_default.ini` `[HAVOK]` has no body size. Player
`00000007` uses `Characters\_Male\skeleton.NIF`. That skeleton's capsules are
layer-8 keyframed ragdoll limbs, parented to bones such as the spine and the
thighs. There is no character-proxy block and no scale field on those shapes.
The skeleton `BSBound` center is `0 0 66.2202` with extents
`23.0977 17.6446 66.2202`. That is a Gamebryo bound, not a controller.

The phone default is OpenMW shape type 0, an axis-aligned box
(`settings-default.cfg`: 0 box, 1 rotating box, 2 cylinder). The template
`BasicPlayer.dae` collision mesh, read as text, spans `-13.3072..13.3072` in
X and Y and `1.7012..140` in Z, which is half extents `13.3072, 13.3072,
69.1494` and center Z `70.8506`. The XY center is 0, so shape type 0 applies
to that mesh. Phone logs fail the Collada file (`basicplayer.dae`, code 3)
and then the embedded error marker. That marker's combined vertex bounds are
X and Z `-61.602..61.602` and Y `-9.950..9.951`, a 123.2 by 19.9 footprint.
The XY ratio is far outside the axis-aligned-box test, so the live body on
0.10 was the rotating marker box.

`tools/android/meshes/basicplayer.osgt` repeats the eight Collision corners
and nothing else. The packer rewrites the actor model keys from
`meshes/BasicPlayer.dae` to that file. The kf paths stay on the dae. This is
the template node the settings already named, loaded through a format the
phone already reads. It is not a recovered Oblivion capsule, and the step
constants and stair filter stay where they are. The next phone log's
`visual_bounds` is the check that this mesh, rather than the marker, loaded.
The host has no OSG, so that check is still ahead.
