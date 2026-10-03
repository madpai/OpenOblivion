# The player as an Oblivion character

Date: 2026-10-03. The preview player was the template game's actor: a
Morrowind-style body (`BasicPlayer.dae`, which Android cannot load) without
TES4 animation. With `OPENOBLIVION_TES4_PLAYER=1` the `tes4_player` receipt
(after `tes4_movement`) renders it from the master's Player record instead.

## What it does

- Finds the master's `Player` NPC (`00000007`, "Bendu Olo", Imperial male) by
  editor ID; the load order renumbers its FormID because the template loads
  first.
- Third person: `Characters\_Male\skeleton.nif`, the bare body (TES4 race
  records carry body textures, not meshes, so `UpperBody`, `LowerBody`, `Hand`
  and `Foot` come from the skeleton folder), the race head parts and hair.
- First person: Oblivion's own `_1stperson\skeleton.nif` with only upper body
  and hands, so the camera tracks a real head bone and the preview camera
  fallback no longer triggers.
- 22 original locomotion clips per view (idle, walk, run, turn, sneak, swim).
  TES4 KF sequence names repeat across files (`walkforward.kf` and
  `sneakforward.kf` are both "Forward"), so each clip is renamed by file to the
  host group (`walkfastforward.kf` → `runforward`, `sneakidle.kf` →
  `idlesneak`, …). `Bip01 Head` is aliased as `Head` for the host camera.
- Template body parts are skipped for this player. Mechanics, inventory and the
  measured collision hull are unchanged; speed stays the TES4 formula.

## Outfit and stats (0.30)

- The Player record's starting inventory is worn: Sack Cloth Shirt, Pants and
  Sandals and Wrist Irons (the original reference shows the same outfit). Each
  item's BMDT slot bits hide the bare body piece it covers.
- Starting stats are read from the owner's master at package time
  (`tools/android/tes4_stats.py`, values never committed) and applied by an
  overlay player script, which also exposes TES4 skills as interface
  `TES4Stats`. The original console reports, for this record: health 80,
  magicka 100, fatigue 150, level 1, Strength 50, Endurance 40, Speed 40, i.e.
  health = 2 x Endurance, magicka = 2 x Intelligence, fatigue = Strength +
  Willpower + Agility + Endurance. The record's base health (45) is not the
  player's health.

## Evidence

Desktop, same recorded binary, owner data: the player loads with 22 groups in
both views (`evidence/tes4-player-*`); a third-person capture shows the Imperial
body mid-stride with the original walk clip. Vilverin walk 116.4 units/s (TES4
formula), gate traversal, NPC idle and stair fixture regressions pass. Run
requests 355.6 units/s. Android ARM64 builds and is packaged as
`0.29-tes4-player`; phone rendering is pending.

## Not yet

Face textures/FaceGen (the head is untextured-dark), a real TES4 inventory
and equipping (the worn outfit is cosmetic), weapon/hand-to-hand/jump/attack clips, race skin
texture overrides, female/beast players, and a bare body under NPC armour
(NPCs still attach only what they wear).
