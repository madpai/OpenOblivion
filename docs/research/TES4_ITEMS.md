# TES4 items, loot and readied fists

Date: 2026-10-03. Step 5 of the owner-approved "make Vilverin playable" plan,
plus the owner's request that fists ready like a weapon.

## Items

`tools/android/tes4_items.py` reads the owner's master at package time and
writes one host item record per TES4 ARMO, CLOT, WEAP, AMMO, MISC, KEYM, BOOK,
ALCH, INGR, SLGM and SGST record (5,411 for Oblivion.esm) into the generated
`openoblivion_rules.omwaddon`, never committed. Each record is named
`oo4_` + the master FormID's low 24 bits and keeps the original name, world
model, inventory icon (`textures\menus\icons\…`, accepted by the player
receipt's icon-path hook), weight and value; book text is kept.

Host type by TES4 biped slot: upper → cuirass/shirt, lower → greaves/pants,
upper+lower clothing → robe, foot → boots/shoes, hand → left gauntlet/glove,
shield → shield, ring/amulet → ring/amulet. TES4 hats (clothing in the head
slot) become 0-rating helmets because the host has no clothing hat. These are
host bookkeeping choices, not TES4 behaviour.

Not carried yet: enchantments, magic effects (potions and ingredients have
none), scripts, item health/condition, non-playable hiding, gold as currency.

## Leveled lists and inventories

`openoblivion_tes4_items.lua` rolls NPC inventories through the master's LVLI
lists at the player's level, following the Construction Set's documented rules
(chance none; highest qualifying level unless "calculate from all levels";
"calculate for each item in count"). Not yet compared with the executable.
`tests/test_tes4_items.lua` covers the rules on synthetic lists.

## Who carries what

- The player receives the Player record's inventory once per character
  (Sack Cloth Shirt, Pants, Sandals, Wrist Irons) and equips it.
- Actor-bridge proxies receive their rolled inventory. Apparel is equipped,
  one item per TES4 body region (robes, then armor, then clothing). Weapons and
  everything else are held until death, then placed on the body, because the
  host AI would otherwise draw weapons the TES4 combat layer cannot use yet.
  This is a stand-in; TES4 NPCs fight with their weapons.
- Dead proxies are looted with the host container window.

## Rendering

The `tes4_player` renderer now draws worn models from the host inventory's
equipped `oo4_` items when the generated items are loaded, falling back to the
record inventory otherwise. Equipment changes rebuild the part set, so looted
armor leaves the corpse and equipped clothes appear on the player. Overlapping
regions are drawn once, in robe → armor → clothing order.

## Readied fists

Fists ready and holster like a weapon, as in the original. The host weapon
stance is the readied state (WEAPON button). Raising and lowering play the
original `handtohandequip.kf` / `handtohandunequip.kf`; attacking while
holstered readies instead of punching. Readied idle, walk, run and turn use
the original `handtohand*.kf` clips as the host "hh" stance groups. Bridge
actors show the same clips when the host AI readies them for combat. The 1.1×
unarmed speed bonus (fMoveNoWeaponMult) now applies only while holstered,
matching the speed formula's weapon-drawn input.

## First-person camera

Every `_1stperson` clip animates `Camera01`; the renderer now tracks it in
first person (it previously tracked `Bip01 Head`, which put the shirt in view).

## Evidence

Desktop, owner data, recorded binaries (`evidence/tes4-items-01`,
`tes4-loot-01`, `tes4-fp-*`, `tes4-ready-*`): player inventory shows the four
starting items with original icons and an outfit preview; five Vilverin
bandits roll and equip 3–5 apparel items each; a bandit killed in 13 punches
holds its rolled armor and mace in the loot window. Phone build
`0.32-loot-readied`.
