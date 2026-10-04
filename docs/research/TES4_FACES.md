# TES4 faces and hair

Date: 2026-10-04. Phone build `0.34-faces`.

## What the original does

An NPC's head is the race head mesh (`Characters\<Race>\HeadHuman.nif`) with a
face texture, plus ears, mouth, teeth, tongue and eyes from the race's head-part
list, plus the NPC's hair record. The Construction Set bakes one face texture
per NPC next to the master (`textures\faces\oblivion.esm\<FormID>_0.dds`,
256×256; `_1` and `_2` are 32×32 tint swatches). Runtime FaceGen also morphs the
head shape from the NPC's FGGS/FGGA coefficients (`.egm`, not done yet) and can
build a texture from FGTS and the race `.egt` tint modes (not done yet).

## What the renderer does now

`tes4_player.hpp` builds a look per attached part:

- Head (race head part 0): the NPC's baked face texture when the master has one,
  else the race head texture. Baked faces carry a constant alpha of 127 that the
  original ignores; the host alpha-tests it away (the head vanished in the first
  attempt), so skin textures are used opaque. The copy of the image has its DXT3
  or DXT5 alpha blocks rewritten (or alpha bytes if the GPU path decompressed it).
- Ears, mouth, teeth, tongue and eyes: the race's own texture for that part.
  The NIF's own paths (for example `textures/facegen/ears/human/earshuman.dds`)
  do not exist in the archives. Males use head part 1 (ears) and females 2.
  Head parts come from the female list for female NPCs (they previously always
  used the male list).
- Hair: the HAIR record's model and its texture (the NIF's texture names do not
  exist either, for example `grey_mane.dds`), with the NPC's hair colour (HCLR)
  multiplied into the materials.

Texture swaps use the host's `overrideTexture` helper (and a copy of it for
skin), applied to the nodes each part adds. Baked faces are only known for the
master's NPCs.

## Evidence and limits

Desktop probes (`tes4-face-*`, owner data): baked faces apply to the Vilverin
bandit bases (`0006c355`, `0006c357`, `0006c35a`, `0006c35d`); the player, which
has no baked face, uses the race head. Not done: EGM shape morphs, FGTS texture
building (needed for the player and runtime NPCs), EYES records (the engine does
not load them, so eyes keep the race texture), the NPC `TPLT` template face,
and aging textures. Hair tint depends on the host material path; verify against
the original on a hair colour that is not black.
