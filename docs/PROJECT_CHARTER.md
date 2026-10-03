# Project charter

OpenOblivion aims to load an owner's classic The Elder Scrolls IV: Oblivion
installation in a native Android ARM64/desktop Linux runtime. On 2026-10-03,
the owner made a 1:1 classic Oblivion Android port the primary objective.
Original controls, movement, animation, UI, combat, quests, dialogue, AI,
audio and save behavior need measured parity. Linux provides reference and
development checks. Vulkan, cooperative play and persistent server-owned
progression remain additional requirements. Oblivion Remastered is a separate
unresearched target. See [the parity ledger](PARITY.md).

The planned first multiplayer experience is a small cooperative dungeon: alternate
start, movement, combat, shared enemies, death, respawn and durable rewards.
Persistent Cyrodiil, arena survival and Gatebound-like PvE build on this slice.
A classic single-player ruleset remains possible by running the same authority
locally with different death, time, quest and save policies.

## Engineering commitments

1. Study and reproduce existing implementations before adding a subsystem.
2. Reuse compatible source with immutable revision and intact attribution.
3. Prefer a small tested content/gameplay slice over a broad unsupported claim.
4. Record fact, inference, unknown and authored tuning separately.
5. Keep compatibility semantics separate from generic simulation and mode rules.
6. Define ownership, persistence, late join and reset behavior with each mechanic.
7. Validate both original fixtures and private owner content; measure actual
   rendering/device behavior before making performance or compatibility claims.

## Repository boundary

Public: engine/tools/docs, original fixture generators and carefully reviewed
open-licensed source. Private: ESM/ESP data, BSA archives, NIF/DDS/KF files,
voices/music/effects, executables/DLLs, physics binaries, extracted artwork,
screenshots, compiled donor packages and raw owner reports. User paths and
content names also remain outside public generated evidence.

No content-serving protocol downloads an installation from the server. Each
client supplies its own files. Code licensing does not grant asset rights.
Mod compatibility and original-game progression are measured features, not
consequences of successfully reading a record header.

## Founding scope

This first checkpoint selects a compatibility foundation, records licensing,
reproduces a native reader and establishes builds/tests/content safeguards.
It does not declare completion of the long-term engine objective. The original
request ended during the license-matrix list; any continuation can extend this
charter without discarding the reproduced work.
