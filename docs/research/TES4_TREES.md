# TES4 trees

Date: 2026-10-04. Build `0.40-trees`. Trees were the biggest missing part of
the outdoors: OpenMW's scene loader logs "Ignoring SpeedTree data file" and
draws nothing for a `.spt` model, so every forest was empty.

## What the owner's data shows (measured 2026-10-04)

- Oblivion.esm has 142 TREE records (Shivering Isles adds more). Each has
  `MODL` (a `.spt` path without a directory, e.g. `TreeYewForest.spt`), `MODB`
  (bound radius), `ICON` (leaf texture), `SNAM` (seed), `CNAM` (eight floats of
  leaf and wind settings) and `BNAM` (two floats: billboard width and height).
  Every `MODB` equals `BNAM` × 1.2071, so `BNAM` is the real size.
- The 113 base-game `.spt` files (139 with Shivering Isles) are 1.3–2.3 KB.
  They hold parameters for a procedural generator: texture paths, Bezier
  splines for branch profiles, a collision-object block. They do not hold
  meshes. The generator (SpeedTree 4) is third-party and not reproduced.
- No `.spt` defines a collision object (the block is all zeros). Seven trees
  (`TreeYewForest`, `TreeCottonwoodSU`, `TreeCPSnowGum`, `TreeSnowGumFree`,
  `TreeCamoranParadise01/02/04`) have a small NIF at `meshes/trees/<name>.nif`
  holding only a Havok trunk shape.
- All 142 records have a pre-rendered picture of the finished tree at
  `textures/trees/billboards/<spt basename>.dds` (512×512 or 256×256, mostly
  DXT3, 52 DXT5, 7 DXT1) with a leaf-shaped alpha cut-out. This is the image the
  original engine shows for distant trees.

## What `tes4_trees` does

The `tes4_trees` receipt (after `tes4_player`) is opt-in with
`OPENOBLIVION_TES4_TREES=1` (set by the Android host; probes take
`--tes4-trees`). It changes three engine files:

- `components/esm4/loadtree.cpp` reads `BNAM` and records (width, height) per
  model name in a small registry (`tes4_trees.hpp`).
- `components/resource/scenemanager.cpp`: where the loader used to return an
  empty node for `.spt`, it builds two crossed vertical quads of that size with
  the billboard picture, alpha-tested at 0.5, rooted at the reference origin.
- `components/resource/bulletshapemanager.cpp`: a `.spt` model gets no collision
  shape of its own (otherwise the engine would turn the two quads into walls);
  where `meshes/trees/<name>.nif` exists it is loaded as the trunk shape.

Trees are lit by the sun and ambient only (`simpleLighting` user value skips
point lights), as the original's trees are; without it a billboard's large
bounds picked up the blue Ayleid glow lights near the Imperial City and turned a
yew blue.

## Pitfall recorded for later work

The desktop engine (pin 46bd459) takes its shader material from
`SceneUtil::Material`; the Android donor (f4bec41) from `osg::Material`. A
material of the other kind is silently ignored and the shader's
`material.*` uniforms stay unset, which showed as an additive blue. The header
chooses by `__has_include(<components/sceneutil/material.hpp>)`.

## Limits (facts vs stand-ins)

- Stand-in, not parity: flat billboards instead of 3D trunks, branches and leaf
  cards; two crossed planes rather than a camera-facing sprite; no wind or
  rustle (`CNAM`), no leaf curvature, no tree shadows or canopy shadow.
- Collision: only the seven trees above have a trunk shape, and only if the
  authored-collision loader accepts their Havok layer. A probe walking straight
  at a `TreeYewForest` trunk was not stopped, so even those do not collide yet.
  Whether the other trees collide in the original is unmeasured.
- Brightness has not been compared with the original; the billboards are dark
  by design and look dim at dusk.
- Evidence: desktop probes `trees-yew3` and `trees-a` (private). Phone
  acceptance is pending.

## Reproduce

```sh
python3 tools/native/tes4_trees.py apply --source /outside/native-desktop/source \
  --revision 46bd4599203ee52ffc0f3e8edb3fc159a0303a49
# rebuild openmw, then record:
python3 tools/native/tes4_trees.py record --source ... --binary ... --manifest ...
python3 tools/upstream/probe_scene.py ... --tes4-trees --phone-overlay \
  --movement-position X Y Z --movement-heading DEGREES   # replaces the sewer-exit start
```
