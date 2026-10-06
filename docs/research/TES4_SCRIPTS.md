# TES4 scripts, quests and dialogue

Date: 2026-10-04/05. Builds `0.41-quests`, `0.42-voices` and `0.43-object-scripts`. Until now the port had no
quest state, no journal and no way to talk to anyone: NPC activation opened the
host's empty Morrowind dialogue window. This note records what exists, how it
was checked, and what is still a guess.

## What the owner's data holds (measured 2026-10-04)

- Oblivion.esm: 390 QUST, 3,817 DIAL, 19,278 INFO (1.97 MB of response text),
  2,393 SCPT, 7,599 further result scripts (5,718 in INFO, 1,881 in quest
  stages). Every script keeps its source (SCTX) beside the bytecode (SCDA).
- Oblivion.exe keeps one 40-byte record per script command: long and short name,
  opcode, needs-a-reference flag, and a parameter table (type id and optional
  flag per parameter). 370 commands, opcodes 0x1000–0x1171. A condition's
  function number is the opcode minus 0x1000 (GetIsID is 72, GetStage 58).
  `tools/android/tes4_commands.py` reads the table from the owner's executable;
  the table itself is never committed.
- Dialogue conditions: 48,531 CTDA records over 92 functions; GetIsID alone is
  40%, and 14 functions cover 94.6%.

## Pipeline

1. `tes4_script.py` compiles script source to Lua using the exact parameter lists
   of the command table. Identifiers (quests, factions, objects, cells) are
   resolved to FormIDs at compile time. Extra words after a command are ignored,
   as the original compiler did.
2. `tes4_gamedata.py` writes the private overlay data: `scripts/tes4data/`
   `quests.lua`, `index.lua`, `actors.lua`, `frag_NNN.lua` (result scripts, 128 per
   file), `script_NNN.lua` (object and quest scripts, 32 per file) and `dial_NNN.lua`
   (dialogue). 204 files, about 17 MB, none committed.
3. `openoblivion_tes4_script.lua` (runtime, pure Lua), `openoblivion_tes4_commands.lua`
   (commands), `openoblivion_tes4_dialogue.lua` (dialogue engine) run the data.
   `openoblivion_tes4_game.lua` (global script) connects them to the world;
   `openoblivion_tes4_ui.lua` (player script) draws messages, the conversation
   window and the journal. `openoblivion_actor_bridge.lua` routes activation of a
   bridged NPC to the conversation window.

## Verification

- Statement structure: for all 7,945 scripts and result scripts that have both
  source and bytecode, the compiler's statement-level opcode sequence (Begin, If,
  Set, command opcodes, reference prefix 0x1C, End, ...) equals the bytecode's.
  Two scripts differ because their source lacks an End/Endif.
- Fixtures: `tests/test_tes4_script.py` (compiler), `test_tes4_script_rt.lua`
  (stages, journal, conditions, commands, save/load), `test_tes4_dialogue.lua`.
- End to end on the owner's data (LuaJIT, mock world): starting a new game sets
  MQ02 stage 0, which chains to stages 10, 20 and 25 with their journal text.
  Arriving in Chorrol and then at Weynon Priory advances MQ02 to 30 and 40
  through the real `MQ02Script`. Jauffre greets with "Hello. I'm Brother Jauffre.
  Can I help you?", offers "I brought you the Amulet of Kings." and "The Emperor
  sent me to find you.", takes the amulet, tells the story of the Dragonfires and
  Martin, and starts MQ03.
- Desktop engine probes (`--movement-ui dialogue|journal`) show the conversation
  window with Jauffre and the journal with the real MQ02 entries.

## Rules implemented and their status

| Rule | Status |
|---|---|
| Responses tried in file order; first passing wins | Documented CS behaviour, not compared with the executable |
| Random flag: random among passing random responses | Documented, not measured |
| Say-once responses skipped after use | Documented |
| Topic list = type "topic" with a passing response, once learned if any AddTopic/add-topic names it, never if only reachable as a choice | **Inference**; the real list rule is unmeasured |
| `GetInCell` of a "dummy cell for GetInCell" = the city worldspace of the same name, or the exterior cells within two of the location's map marker | **Approximation**; the original's rule is unknown |
| `SetStage` starts a quest that is not running | Inferred (MQ02 is never started otherwise) |
| Quest scripts run every 5 s | **Verified source**: INI setting `fQuestScriptDelayTime`, shipped default 5.0 in `Oblivion_default.ini`. There is no object-script delay setting, so the 0.25 s object tick stays unverified |
| Unloaded references are 1e9 units away | Choice, so "near X" triggers do not fire |
| Unimplemented commands return 0 and are logged once | Choice; some conditions therefore pass wrongly |

## Voices

Verified 2026-10-06 against the executable (its format string for the file base name and the `mp3`/`wav`/`lip` type
strings next to `Data\Sound\Voice`) and independently by the bsa-rs documentation example; see
[EXECUTABLE_RECON.md](EXECUTABLE_RECON.md). Lip-sync `.lip` files exist in the original and are not used by the port yet.

A response's recorded line is `sound/voice/oblivion.esm/<race>/<m|f>/<quest>_<topic>_<INFO id,
8 hex digits>_<response number>.mp3` in the voice archives (measured: e.g. the Breton male
folder holds `mq02_greeting_0001dc44_1.mp3`). The speaker's race name comes from the NPC record's
race, the quest from the response's QSTI. The global script plays a conversation's lines one after
another with the engine's `say` (the FFmpeg decoder is linked into libopenmw); a file the archives
lack is logged and skipped. Playback is confirmed only as file resolution on the desktop; hearing
it needs the phone.

## Scripts on placed references

3,042 base records carry a script (`baseScripts` in the index). When a reference becomes active the
global script attaches its base record's script: variables are shared with `Ref.var` reads and writes,
`OnLoad` runs once, `GameMode` runs every 0.25 s with the elapsed time as `GetSecondsPassed`, a bridged
NPC's death runs `OnDeath`, and activating a scripted door, container, activator, light or item runs
its `OnActivate`. As in the original, that block replaces the normal activation unless the script calls
`Activate` on itself (a block that fails to run falls back to the normal activation so no object is
locked by a bug). Implemented object commands: GetSelf, GetActionRef, IsActionRef, Activate, Enable,
Disable, GetDisabled, GetDead, MoveToMarker, KillActor, GetPos, GetActorValue (health, magicka, fatigue
and the eight attributes), GetLevel. A bridged NPC's script talks to the host actor that stands in
for it. `OnHit`, `OnEquip`, `OnAdd`, `OnTrigger*`, package events and spell-effect blocks are not
dispatched.

## Leaving menus (0.44)

A phone report said the journal could not be closed. On the desktop engine a click on the 22 px
"Close" text works but is easy to miss; Escape also closes the journal override. 0.44 therefore adds,
independent of the menu's own widgets: a BACK button in the touch overlay (drawn while any menu is
open, sends Escape), the Android back key doing the same, big Close/Goodbye buttons, and a tap on
any unused part of the journal page closing it. Taps are logged (`OPENOBLIVION_UI tap ...`) so View
Scene Log shows whether a phone tap reached the UI. Desktop probes `--movement-ui journal-wait` and
`dialogue-wait` keep a menu open for an xdotool click (image `openoblivion-research-build:xdotool`,
the founding image plus xdotool).

## Not done

Presentation and AI commands are counted stubs (PlayGroup, Say, StartCombat, packages, lock state,
PlaceAtMe, SetOpenState, ...); lip sync, facial animation, persuasion, barter and training are absent;
disposition is a plain modifier; faction reaction, crime and fame are no-ops. Plugins other than
Oblivion.esm (Shivering Isles, Knights) are not read. The conversation window and journal are a plain
list UI, not the original's.

## Reproduce

```sh
python3 tools/android/tes4_commands.py --exe Oblivion.exe --output commands.json
# build_personal.py and the desktop probe call tes4_gamedata.build() themselves when
# Oblivion.exe sits beside Data; the overlay then carries scripts/tes4data.
python3 tools/upstream/probe_scene.py ... --phone-overlay --start WeynonPrioryHouse \
  --movement-position 150 -100 -100 --movement-ui dialogue
```
