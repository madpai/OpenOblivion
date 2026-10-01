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
