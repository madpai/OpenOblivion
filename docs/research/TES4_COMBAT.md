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

## Weapons (2026-10-04, build `0.35-weapons`)

Weapon damage is transcribed from `Oblivion.exe` 0x547070 (reads the same
effective-skill helper 0x547b90 and fatigue helper 0x547f00 as hand-to-hand;
decoded from the disassembly, not yet compared with a live original swing):

    damage = (weapon damage × fDamageWeaponMult)
           × (fDamageWeaponConditionBase + fDamageWeaponConditionMult × condition)
           × (fDamageSkillBase + fDamageSkillMult × effective skill / 100)
           × (fDamageStrengthBase + fDamageStrengthMult × min(Strength, 100) / 100)
           × fatigue factor

Values: master overrides fDamageWeaponMult 0.5, condition 0.5 + 0.5, skill mult
1.5, strength 0.75 + 0.5 (the executable supplies skill base 0.2). The weapon's
skill is Blade, Blunt or Marksman by weapon type; condition is the item's
health fraction. An Iron Longsword (damage 10) in the starting player's hands
(blade 5, strength 50, luck 50) deals 1.375, which the desktop fight logs
(`tes4-weap-01`) reproduce; `tests/test_tes4_combat.lua` covers the formula.
Weapon reach is fCombatDistance (128) × the weapon's reach plus the same body
allowance as hands (an inference).

Not done: fatigue cost per swing (fFatigueAttackWeaponBase 7 and Mult 0.1 exist
but their use is not decoded), power attacks (the executable's direction
bonuses, master 2.5 to 3), sneak attack ×4, armor reduction, weapon wear
(fDamageToWeaponPercentage), blocking, staggers, bows and staves.

## Animations and rendering

TES4 ships complete one-hand, two-hand, staff and bow clip sets. The renderer
loads the equipped weapon's family only (so a rebuild on equipment change), as
host groups with the weapon short group suffixed (`1h` blade one-hand, `1b`
blunt one-hand, `2c`/`2b` two-hand, `2w` staff, `bow`): readied idle, walk, run
and turn clips, plus `tes4equip`, `tes4unequip`, `tes4attackright/left/power`,
`tes4blockidle`, `tes4stagger` and `tes4recoil`. The weapon mesh sits on the
skeleton's `Weapon` node in the hand while drawn and on `SideWeapon` (one-hand)
or `BackWeapon` (two-hand, staff, bow) otherwise; first person shows it only
when drawn. The weapon moves between nodes when the draw state changes, not at
the original's `Attach`/`Detach` animation keys.

Bandits wield the strongest melee weapon they were rolled and fight with its
clips, reach and damage; their weapon skills come from the NPC record
(blade, blunt, marksman at level 1).

## Armor (2026-10-04, build `0.36-armor`)

One worn piece contributes (`Oblivion.exe` 0x547370):
`rating × (fArmorRatingBase + (fArmorRatingMax − fArmorRatingBase) × effective
armor skill / 100) × (fArmorRatingConditionBase + fArmorRatingConditionMult ×
condition)`, with the executable's defaults 0.35, 1.0, 0.0 and 1.0 (no master
overrides). The actor's total sums the worn slots and is capped at
`fMaxArmorRating` (0x60e540; master 85, exe 90). Armor ratings are stored ×100
in ARMO (an Iron Cuirass is 10.00); generated host records keep the rounded
value in `baseArmor`, and carry the heavy-armor flag (BMDT general flag 0x80)
in the otherwise unused `enchantCapacity` so the rules layer can pick the
Heavy or Light Armor skill. NPC armor skills come from the NPC record.

Applying the total to damage as "blocks that percentage, up to the cap" is the
documented rule and is **not** decoded from the executable's damage routine.
The rounding the executable applies inside the piece routine is not
reproduced. Desktop check (`tes4-armor-4`): an iron set (rating 10.7 at the
starting armor skill) cuts an Iron Mace hit from 2.07 to 1.85.

Armor wear (fDamageToArmorPercentage), the armor-weight class skill gain and
magic armor are not modelled.

