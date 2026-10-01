# Milestones and acceptance gates

There are no promised delivery dates. Each stage preserves the last working
slice and resolves a concrete uncertainty before expanding scope.

| Milestone | Result | Acceptance / evidence | Current status |
|---|---|---|---|
| M0: founding research | License-aware foundation and reproducible native tools | Exact upstream pins, original tests, owner master scan, Linux/ARM64 builds, publication guard | Implemented locally; see reproduction |
| M1: existing desktop world | Reproduce OpenMW TES4 interior/exterior traversal before changing it | Build full upstream with documented dependencies; inspect static world/terrain/collision against owner installation; save private screenshots/traces | Partially reproduced: full build, real BSA/NIF agreement, interior/exterior screenshots; collision accuracy/typed catalogue boundary remain |
| M2: native Vulkan/mobile scene | One private TES4 scene plus an original public debug scene | Choose a licensed renderer slice, verify materials/axes/scale and collision; APK + touch + lifecycle; physical ARM64 phone frame time/memory evidence | Vulkan gate not implemented; OpenGL phone preview has visibility/look evidence and owner-reported basic movement/smooth stairs. Original movement fidelity, lifecycle and performance remain |
| M3: authoritative original co-op slice | Two players fight an original enemy, die and respawn | Headless authority, command validation, late join, no duplicate XP/loot, restart/reconnect and content mismatch rejection | Not implemented |
| M4: Oblivion dungeon co-op | Owner-supplied dungeon, animated enemy, melee/casting, inventory/equipment | Native NIF/KF/physics/record subset, server-owned combat/progression, private desktop + Android/LAN playtest | Not implemented |
| M5: persistent modes | Arena, Gatebound-like PvE and staged persistent Cyrodiil | Transactional saves/migrations, bounded Lua rules, instance/reset behavior, multi-hour soak and crash recovery | Not implemented |
| M6: broader/classic compatibility | Measured expansion of quests, dialogue, AI, magic, equipment and mods | Compatibility VM/conditions, representative mod corpus and explicit per-feature report; offline classic rules | Not implemented |

## M1 tasks in execution order

1. Full engine/tools now build without donor edits in an isolated container.
   Preserve this baseline and its recorded dependencies.
2. Record private install identity/load order. Validate one interior and
   exterior/terrain area; document missing features and exact renderer behavior.
   The owner now prioritizes actual player movement. Walking/stopping/ordinary
   collision/jump/look are reported working on the phone. Native 0.5 now has
   owner-reported smooth stairs with liked subtle stepping; swimming and a breath
   indicator are also observed. Next, measure original Oblivion walk/run speeds
   and jump behavior with fixed character stats, calibrate native movement, then
   repeat stair and water checks at those settings. Preserve the current stair
   feel until that comparison. Authored TES4 collision remains separate
   compatibility work; see [player movement priority](PLAYER_MOVEMENT.md).
3. Use original synthetic override/deletion/master-reference fixtures to verify
   typed data resolution. Cross-check bytes from one BSA/NIF against existing
   NifTools/Asset Lab readers with preserved diagnostics.
4. Establish an immutable scene/catalogue boundary and headless content path.
   Measure its dependency/memory cost before choosing a full fork or more slices.
5. Evaluate the Vulkan donor on the same scene and keep the original upstream
   view as a comparison. No blind merge of OpenMW, TES3MP and vsgopenmw.

## Features that do not count as completion

Static or frozen actors do not establish skeletal animation. Armor icons/stats
do not establish wearable meshes. A viewer does not establish quest/combat
compatibility. Network position sync does not establish server authority.
ARM64 compilation/emulation does not establish phone performance. Imported
packages matching a loader do not establish gameplay or publication rights.

## Risks with decisive experiments

| Risk | Decisive experiment |
|---|---|
| OpenMW reuse requires pervasive TES3 assumptions | Trace one TES4 interior/actor path and identify minimal adaptation boundaries |
| Vulkan migration drops essential behavior | Render identical owner scene/material/animation set through both paths |
| Original scripts assume one player and save reload | Classify a small dungeon quest/door script set by authority and state scope |
| Mobile world/texture costs exceed device budget | Measure sustained physical-device frame times/memory/thermals on bounded scenes |
| Multiplayer duplicates progress or loot | Kill/restart/reconnect at transaction/acknowledgement boundaries |
| Data/mod overrides desynchronize peers | Ordered manifests and reference-resolution fixtures; reject mismatch before join |
| License/dependency ambiguity blocks reuse | Exact-file audit; preserve notices or independently implement behavior |
