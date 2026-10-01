# Look name

Phone-readable title for the object under the center of the view. It is the OpenMW “what am I looking at” name, drawn as a top bar. It does not move the player, change collision, the stair camera filter, run/walk, or the body, and it does not activate anything.

## What it shows

A player script reads the center look target. The bar shows the record name after trimming surrounding space. It does not show the record id. A form id on a TES4 static would cover the view, and this 0.51 Lua API has no display name for TES4 actors. Those actor names stay on the engine tooltip: `docs/media/android-vilverin-stairs.jpg` already draws Bandit above that NPC. The bar hides when the ray misses, the hit has no object, the name is empty, or the hit is past the activation distance. `camera.showCrosshair(true)` runs once so the aim point stays visible.

The bar is top center, 400×56 pixels with 24 px text, sized for the forced 960×540 framebuffer. The HUD layer has `pick="true"` (`files/data/mygui/openmw_layers.xml`), so a widget there can take clicks. The script inserts `OpenOblivionLookName` after HUD with `interactive = false`. That calls `Layer::insert`, which sets MyGUI pick off, so the bar does not consume input.

The target log is one line, and only when the target changes: `OPENOBLIVION_LOOK_NAME name=<name> id=<id>`, or `OPENOBLIVION_LOOK_NAME cleared`.

## Distance

The ray starts at `camera.getPosition()` and follows `camera.viewportToWorldVector` at viewport `(0.5, 0.5)`, the same center OpenMW uses in `World::getFocusObject`. Its length is `iMaxActivateDist` plus `camera.getThirdPersonDistance()` plus telekinesis, in game units. Focus distance is the hit distance from the camera minus that camera pullback. A hit is rejected when focus distance is greater than `iMaxActivateDist`, unless the object allows telekinesis. Telekinesis magnitude is feet times `ceil(21.33333333)`, matching `World::feetToGameUnits` and `Constants::UnitsPerFoot`. The player is ignored. Nothing is activated.

`iMaxActivateDist` is read with `core.getGMST`, the same `ESM::GameSetting` store as `World::getMaxActivationDistance` (`apps/openmw/mwworld/worldimp.cpp`). Oblivion.esm does not contain that GMST: its GMST group at file offset 764 holds 382 records and no editor id `iMaxActivateDist`. The phone loads `template.omwgame` before `Oblivion.esm`; that file’s TES3 GMST `iMaxActivateDist` is INTV `0xC0` (192) at file offset 20776. If `getGMST` returns nil, the script uses that measured 192. The game binary does not substitute a number: `Store::find` throws. OpenCS lists 192 at `apps/opencs/model/world/defaultgmsts.cpp:1955`, and that file is not the running game. `fAutoDoorActivateDistance` in Oblivion.esm is 150 and is not this distance.

Morrowind NPC and creature records refuse the telekinesis extension, as do unlocked teleport doors with no trap. ESM4 classes in this tree do not override `allowTelekinesis`, so they keep the default (allowed). This build also has no Lua type package for ESM4 actors.

## Ray

`nearby.castRenderingRay` is used, not `nearby.castRay`. The rendering ray is what OpenMW’s own focus uses, so it can hit visible objects that have no physics body. It is legal in a player `onFrame` handler: `LuaManager::synchronizedUpdate` sets `mProcessingInputEvents` around input and `onFrame` (`apps/openmw/mwlua/luamanagerimp.cpp`). The same call throws from `onUpdate` (`apps/openmw/mwlua/nearbybindings.cpp`). The script therefore does not use `onUpdate`.

## API limit

`object.type.record(object).name` is used when that type binding exists. In this 0.51 tree, `record()` is bound for Morrowind object types and for ESM4 doors and terminals. Other ESM4 types, including weapons, armor, books, containers, and activators, have a type table but no `record()`. ESM4 NPCs and creatures are not in the Lua type map, so `object.type` is nil. The bar stays hidden for those hits. The engine tooltip still draws a TES4 NPC name. The phone settings raise GUI scale to 1.25 and font size to 20 so that existing label, the bars, and the minimap are easier to read on the 960×540 framebuffer. Those two numbers are a touch-comfort choice, not recovered Oblivion settings.

## Packing

`tools/android/look_name.omwscripts` is `PLAYER: scripts/openoblivion_look_name.lua`. `MainActivity` adds `content=look_name.omwscripts` on both the native and non-native config paths, next to the other `qa` scripts. It is not gated on the stair-camera build. `tools/android/build_personal.py` packs both files under `qa/` and records them in `preview_tools_sha256`, the same way as phone QA.
