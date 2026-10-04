# TES4 faces and hair

Date: 2026-10-04. Phone build `0.34-faces`.

## What the original does

An NPC's head is the race head mesh (`Characters\<Race>\HeadHuman.nif`; the
human races share it) with a face texture, plus ears, mouth, teeth, tongue and eyes from the race's head-part
list, plus the NPC's hair record. The Construction Set bakes one face texture
per NPC next to the master (`textures\faces\oblivion.esm\<FormID>_0.dds`,
256×256; `_1` and `_2` are 32×32 tint swatches). Runtime FaceGen also morphs the
head shape from the NPC's FGGS/FGGA coefficients (`.egm`, not done yet) and can
build a texture from FGTS and the race `.egt` tint modes (not done yet).

## What the renderer does now

`tes4_player.hpp` builds a look per attached part:

- Head (race head part 0): the race head texture multiplied by the NPC's baked
  FaceGen map ×2. The baked maps (`textures\faces\oblivion.esm\<FormID>_0.dds`)
  are not skins: they are grey-blue tint maps centred on mid-grey (mean about
  0.45 to 0.65) with eyebrows and lips as darker or lighter detail, with a
  constant alpha of 127, as a Gamebryo detail map (×2 modulate) is used. Using
  them directly as the face made heads grey, and the alpha made the host
  alpha-test the whole head away (first attempt). The two images are decoded
  (DXT1/3/5 in software) and combined into an opaque RGBA texture, cached per
  pair. The Player has no baked face, so uses the race texture opaque. The
  ×2 modulate is the interpretation that fits the data; not yet compared with
  an original face.
- Body pieces: the RACE record gives each piece (upper, legs, hands, feet) its
  skin texture, so a Dark Elf has ash-grey skin all over, not Imperial brown.
- Ears, mouth, teeth, tongue: the race's own texture. Males use head part 1
  (ears) and females 2. A head part the female list leaves empty (the race
  shares one head mesh) comes from the male list; using the empty female list
  made female bandits headless.
- Hair: the HAIR record's model and texture (the NIF's own texture names do not
  exist in the archives), with the NPC's hair colour (HCLR) multiplied into the
  materials.
- Hair meshes are unskinned and authored in head space; the original attaches
  them to the head bone. The renderer parents them to `Bip01 Head` with the
  inverse of the bone's bind pose so they follow the head (they used to sit at
  the character's feet, which is what the teal "blob" in third person was).
  The skeleton's node map is built lazily, so it is read through
  `getNodeMap()`, not `mNodeMap`, while parts attach.
- Worn armor and clothing for a female actor use the female biped model, else
  the male one (many items have a single model).

## Evidence and limits

Desktop probes (`tes4-face-*`, owner data): baked faces apply to the Vilverin
bandit bases (`0006c355`, `0006c357`, `0006c35a`, `0006c35d`); the player, which
has no baked face, uses the race head. Not done: EGM shape morphs, FGTS texture
building (needed for the player and runtime NPCs), EYES records (the engine does
not load them, so eyes keep the race texture), the NPC `TPLT` template face,
and aging textures. Hair tint depends on the host material path; verify against
the original on a hair colour that is not black.
