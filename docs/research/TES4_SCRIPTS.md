# TES4 scripts, quests and dialogue

Date: 2026-10-04. Build `0.41-quests` (first version). Until now the port had no
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
| Quest scripts run every 5 s | The original's delay is a game setting, not read yet |
| Unloaded references are 1e9 units away | Choice, so "near X" triggers do not fire |
| Unimplemented commands return 0 and are logged once | Choice; some conditions therefore pass wrongly |

## Not done

Object scripts are compiled but not attached to references (OnActivate, OnLoad,
GameMode of placed objects); most presentation commands (PlayGroup, Say,
MoveTo, StartCombat, packages) are counted stubs; voice files, lip sync,
persuasion, barter and training are absent; disposition is a plain modifier;
faction reaction, crime and fame are no-ops. Plugins other than Oblivion.esm
(Shivering Isles, Knights) are not read. The conversation window and journal are
a plain list UI, not the original's.

## Reproduce

```sh
python3 tools/android/tes4_commands.py --exe Oblivion.exe --output commands.json
# build_personal.py and the desktop probe call tes4_gamedata.build() themselves when
# Oblivion.exe sits beside Data; the overlay then carries scripts/tes4data.
python3 tools/upstream/probe_scene.py ... --phone-overlay --start WeynonPrioryHouse \
  --movement-position 150 -100 -100 --movement-ui dialogue
```
