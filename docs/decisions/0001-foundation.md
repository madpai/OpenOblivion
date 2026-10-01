# ADR 0001: OpenMW compatibility foundation with staged integration

Status: accepted for the reader/next world-viewer prototype; full runtime fork
selection remains gated by viewer and rendering evidence. Date: 2026-09-30.

## Problem

We need Oblivion content compatibility, Android/Vulkan presentation and
persistent cooperative simulation. No studied project proves all three in
one ready-to-use foundation. Recreating mature content readers would add work
before the core multiplayer uncertainties have been tested.

## Decision

Use the pinned current OpenMW source as the **compatibility foundation**.
Compile an unchanged reader slice now. Reproduce its desktop Oblivion world
view next, then expose a narrow immutable-content boundary and evaluate
Vulkan presentation against actual scenes. Keep upstream mergeability visible.

Study vsgopenmw for renderer migration and resource/animation handling. Its
documentation targets TES3; it is not accepted as a proven Oblivion/Android
foundation. Study TES3MP/CoreScripts for behavior and persistence, without
assuming their older engine/protocol or actor authority meets our requirements.
Reuse individual audited pieces only when a concrete slice needs them.

Use GPL-3.0-only for original OpenOblivion code to permit practical GPLv3 reuse.
Preserve external licenses and notices. Unknown-license code remains research
only. No game/physics binaries are bundled.

## Evidence

- OpenMW explicitly announced experimental later-game world walking in 0.49;
  current source has ESM4 stores/readers, TES4 BSA handling and NIF support.
- The pinned reader compiles with a small standard-library/zlib dependency
  closure for Linux and Android ARM64. The owner's classic master scan agrees
  with an independent container count: 1,167,017 records / 85,079 groups.
- Existing Asset Lab imports demonstrate bounded static artwork conversion,
  not the full TES4 world/quest/runtime semantics needed here.
- The Vulkan fork and TES3MP have separate scopes and ancestry. A combined
  fork would inherit integration risk before establishing a working TES4 slice.
- Full desktop OpenMW configuration is not yet reproduced: it currently stops
  at missing yaml-cpp. The reader build does not answer renderer/runtime costs.

Exact links and revisions: [comparison](../research/FOUNDATION_COMPARISON.md),
[license matrix](../research/LICENSE_MATRIX.md), [reproduction](../research/REPRODUCTION.md).

## Alternatives

| Foundation | Benefit | Reason it is not selected as the initial complete runtime |
|---|---|---|
| Current OpenMW | Existing Bethesda content/runtime knowledge | Selected compatibility base; Vulkan and authority integration remain work |
| vsgopenmw | Existing Vulkan migration | Documented TES3 scope; TES4/native Android behavior unproven here |
| TES3MP | Playable persistent Morrowind multiplayer | OpenMW 0.47 ancestry and distributed/client synchronization assumptions |
| MegaMod + Asset Lab | Local Android/Vulkan and cooperative-survival experience | Current Oblivion importer loses skin/KF/physics/plugin semantics |
| New runtime from scratch | Full design control | Discards working compatibility knowledge before measuring integration costs |
| Unity viewer | Faster visual experiments in that engine | Does not supply a native open-source runtime or demonstrated Oblivion gameplay |

## Consequences and revisit gate

Do not fork every system or build a generic ECS/plugin framework now. Keep a
source ledger for copied code, small upstream-facing fixes, original fixtures
and private integration evidence. The direct reader loop works around a
reproduced upstream traversal-helper omission without changing upstream files.

Revisit the full runtime choice after M1/M2: one interior/exterior scene,
terrain/static collision and native Vulkan on ARM64. Compare observed reuse
cost, dependencies, memory and frame times. A replacement renderer or a larger
fork must be justified by those results, not by a preference for originality.

