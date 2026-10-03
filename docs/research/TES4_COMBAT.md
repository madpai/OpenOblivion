# TES4 actor bridge and hand-to-hand combat

Date: 2026-10-03. Steps 3–4 of the owner-approved "make Vilverin playable" plan.

## Why a bridge

The host engine loads TES4 NPCs as animated objects: no collision, no stats, no
AI, no death. Rather than rebuild an actor system, the phone overlay's
`openoblivion_actor_bridge.lua` replaces each active TES4 NPC with a host actor
proxy (a runtime record copied from the template player) and disables the
original. The proxy's otherwise unused `head` field carries the TES4 NPC's
record ID, so the `tes4_player` renderer draws that NPC's skeleton, body, worn
(leveled) equipment, hair and original animations. The host supplies
collision, pathfinding, the combat AI and death.

## Measured facts (original executable and console)

- Level-1 NPC stats equal their record values: Vilverin bandits `0006C35E`,
  `0006C356`, `0006C35B` show health 16/20/20, fatigue 160/180/180 (ACBS),
  hand-to-hand 40/10/30 and Strength 35/55/55 in the original console.
- Vilverin's bandits have AI aggression 100.
- Hand-to-hand damage, from `Oblivion.exe` 0x547280 (with 0x547b90, 0x547f00):
  effective skill = clamp(skill + Luck × 0.4 − 20, 0, 100);
  r = (effective skill / 100) × (min(Strength,100) / 100 × 0.75) × fatigue factor;
  fatigue factor = fFatigueBase − (1 − fatigue ratio) × fFatigueMult;
  health damage = fHandHealthMin + (fHandHealthMax − fHandHealthMin) × min(r, 1);
  fatigue damage = health × fHandFatigueDamageMult + fHandFatigueDamageBase.
  Executable defaults are used unless Oblivion.esm overrides them (fFatigueBase
  1.0, fFatigueMult 0.5, fHandHealthMax 15, fHandFatigueDamageMult 0.5,
  fHandFatigueDamageBase 1.0, fHandReachMult 0.6). The starting player hits for
  1.26 health / 1.63 fatigue; a hand-to-hand 40, Strength 35 bandit for 2.47.
- Hand reach is fCombatDistance 128 × fHandReachMult 0.6 = 76.8.

## Inferences and stand-ins (not original behaviour)

- Reach is treated as edge-to-edge distance (the host AI measures that way).
  `openoblivion_rules.omwaddon` sets the host fHandToHandReach to 0.6 so the AI
  closes to the TES4 reach.
- Detection: an actor with aggression ≥ 80 attacks a player within 1500 units
  in line of sight. TES4 disposition, factions and sneak detection are not
  implemented yet.
- Attacks alternate the original right/left hand-to-hand clips; damage applies
  on the clip's `Hit` key. No power attacks, blocking, staggers, misses or
  difficulty scaling yet. Fatigue reaching zero does not knock down.
- Death plays the original `idleanims/deathidle.kf` posed-dead clip, since TES4
  uses ragdolls.

## Evidence

Desktop, owner data, same recorded binary (`evidence/tes4-fight-*`): a bandit
engages at sight, chases, hits the player for 2.42 per hit (fatigue reduced
from full); the player's hits do 1.26; the bandit dies after 13 hits and lies
down. Phone build `0.31-bandit-fights`.
