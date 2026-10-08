# OpenOblivion

Research and reproduce before expanding the runtime. Read README.md,
docs/decisions/0001-foundation.md and docs/HANDOFF.md first.

- Public history contains code, tools, documentation and original fixtures only.
  Keep owner game files, extracts, screenshots, compiled content and raw reports
  outside this checkout. Never upload them through CI or release artifacts.
  On 2026-10-01 the owner explicitly authorized progress screenshots for the
  public GitHub README. Only the exact documentation captures recorded in
  docs/media/screenshots.json are approved exceptions; raw QA and game assets
  remain private. Preserve their provenance and the guard's hash checks.
- Before copying/adapting external code, update docs/research/LICENSE_MATRIX.md
  with exact revision, file license, notices, modifications and intended use.
  Unclear licenses mean research only until resolved. Preserve upstream notices.
- Original project code is GPL-3.0-only. Upstream keeps its own licenses.
- Fact, inference, unknown and future plans must remain distinct. A reader
  build is not gameplay; ARM64 compilation is not Android device validation;
  Vulkan enumeration is not rendering. Record measured evidence and limitations.
- Keep the TES4 compatibility layer separate from mode rules, rendering and
  authority. Do not make multiplayer a later patch to a single-player world.
- Run CTest and the public-content guard after changes. For reader changes,
  use original fixtures first, then an owner-supplied local installation.
- Never publish or push without a user instruction covering that action.
- **Feel rule (owner, 2026-10-06):** the engine must always feel like the original game. The only sanctioned creative
  liberties are for touch and mobile play (input mapping, on-screen controls, touch-sized menus). Any other difference is a
  bug or an unfinished measurement, not a design choice. Record every deviation, with its reason, in the deviation ledger in
  `docs/PARITY.md`; do not add one without writing it there.
- Player movement continues from `docs/HANDOFF.md`,
  `docs/research/HAVOK_COLLISION.md`, `docs/research/TES4_PLAYER_BODY.md` and
  `docs/research/TES4_AIRBORNE.md`. Fixed `OL_STATIC` strips load when
  `OPENOBLIVION_AUTHORED_COLLISION=1`; the measured classic player hull loads when
  `OPENOBLIVION_ORIGINAL_BODY=1`; the original ground speed (walk and run verified) is
  `OPENOBLIVION_TES4_MOVEMENT=1`; the original jump, gravity and air control are
  `OPENOBLIVION_TES4_AIRBORNE=1`; the level-ground support range (2.0 Havok units), hover and landing
  capture are `OPENOBLIVION_TES4_GROUNDED=1` (opt-in, off in the launcher until the owner feels it; the
  Android launcher reads `preview-user/config/openoblivion-grounded.txt`; mode 2 is an unfinished stair
  experiment, never ship it). Do not substitute an invented capsule for the hull, and
  do not tune the borrowed controller by feel: recover the law from the running original
  (read-only sampler plus a per-update replay, see the compendium technique note) and
  port it behind a switch with a paired same-binary probe. Still unmeasured: the original's
  stair (sliding) classification, behaviour on walkable slopes at 60 fps, step height and slope limit,
  other Acrobatics values, swimming and fall damage. The measured reference-to-hull float is not yet reproduced; the 0.5 camera filter is
  unchanged (a deliberate deviation: the original's stairs are a free fall per tread).
  Research first: `hub.py prior-art` / `diagnose` / `tried` in madpai/game-decomp-compendium.
