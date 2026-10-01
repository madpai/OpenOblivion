# Foundation comparison

Snapshot: 2026-09-30. **Fact** means read source/documentation or a reproduced
result; **Inference** is an engineering choice; **Unknown** requires a test.
No FPS or gameplay claims are inferred from videos or repository descriptions.

| Project | Fact / source | Inference for OpenOblivion | Unknown / next decisive check |
|---|---|---|---|
| OpenMW | [0.49 release](https://openmw.org/2025/openmw-0-49-0-released/) describes experimental later-game walking alongside a base game. Pinned development 0.52.0 source builds unchanged; private interior/exterior screenshots reproduce textured static geometry/terrain with the public Template. | Strongest compatibility starting point. | Collision accuracy, animation/gameplay coverage, Vulkan migration and mobile costs. |
| OpenMW Example Suite | [Pinned template](https://gitlab.com/OpenMW/example-suite/-/tree/a41b44d9403ff3f8a1505c1b4bc152c4dd623b64) supplies required base-game records/assets; locked LFS data materialized and verified externally. | Use for the upstream viewer bootstrap while measuring TES3 assumptions. | A template player/UI is not native TES4 gameplay; current COLLADA/UI/animation warnings need investigation. |
| vsgopenmw | [Pinned README](https://github.com/vsgopenmw-dev/vsgopenmw/blob/2830e7e2b4f18ef08ee24eff45a13568ec917061/vsgopenmw-readme.md) targets TES3 and replaces OSG rendering with VSG; [build guide](https://github.com/vsgopenmw-dev/vsgopenmw/blob/2830e7e2b4f18ef08ee24eff45a13568ec917061/vsgopenmw-build.md) describes Termux/Linux-style Android operation. The studied head has a 2026-09-08 commit. | Useful renderer donor; do not label it abandoned based on old commentary. | Current native Android surface/touch support, TES4 behavior and VSG merge/feature parity. |
| TES3MP | [Pinned README](https://github.com/TES3MP/TES3MP/blob/49be5b6405d6ab427e06ed350cf76c715a1f3bdd/README.md) states 0.8.1/OpenMW 0.47 and extensive multiplayer synchronization with server Lua. | Learn supported player behavior and persistent state handling. | Strict server-owned combat/XP and newer TES4 integration are not established by synchronization alone. |
| TES3MP CoreScripts | [config.lua](https://github.com/TES3MP/CoreScripts/blob/3e397a11eaf7d0d4ff08df4bb9925e67748b4db8/scripts/config.lua) has death/respawn/penalty options; [player state](https://github.com/TES3MP/CoreScripts/blob/3e397a11eaf7d0d4ff08df4bb9925e67748b4db8/scripts/player/base.lua) separates login, character, location and stats. | Adapt design lessons; MIT allows specific audited reuse. | Transactional reward guarantees, script sandboxing and trust boundaries needed here. |
| xyzz Android port | [Pinned README](https://github.com/xyzz/openmw-android/blob/bfd613230ebe57170cbe4966aa8938d54afa6efa/README.md) says no longer developed; build separates native libraries and Java launcher. GitHub marks it archived. | Study lifecycle/input/build lessons, not a current platform guarantee. | Modern scoped storage, Vulkan, current NDK and maintenance on selected devices. |
| MegaMod / Asset Lab | Current local source has native Vulkan/Android survival experience and a classic BSA v103/NIF 20.0.0.4 static importer. Six original Oblivion-path tests reproduced. | Reuse provenance, native-loader agreement, host-owned rules and measured playtest discipline. | Static/frozen art is not KF animation, wearable equipment, quests or a persistent TES4 world. |
| NifTools | Niflib/NifSkope have source licenses and format implementations; NifSkope warns of mixed dependencies, including Havok-related Windows tooling. | Prefer existing decoders/knowledge over another broad NIF rewrite. | Exact per-block, KF/controller and collision-shape behavior on required owner assets. |
| xEdit / xOBSE | xEdit's [TES4 definitions](https://github.com/TES5Edit/TES5Edit/blob/9fb016884bec138ea6c7b872cec831537d464c3e/Core/wbDefinitionsTES4.pas) cover record/script/condition structures. xOBSE documents commands and game forms; inspected license grant remains unclear. | Use as corroborating behavior/format references; xOBSE code is not admitted for reuse. | Script VM semantics, native extension compatibility, license resolution for any exact copied file. |
| TESUnity | [Pinned README](https://github.com/ColeDeanShepherd/TESUnity/blob/f4d5e19f68da380da9da745356c7904f3428b9d6/README.md) requires Morrowind and uses Unity. NIF schema containing an Oblivion version is not an Oblivion gameplay claim. | Viewer reference, weaker fit for a native open-source runtime. | No reproduced classic TES4 gameplay or target platform evidence here. |

## Exact source locations studied

- [OpenMW reader](https://github.com/OpenMW/openmw/blob/46bd4599203ee52ffc0f3e8edb3fc159a0303a49/components/esm4/reader.cpp),
  [traversal helper](https://github.com/OpenMW/openmw/blob/46bd4599203ee52ffc0f3e8edb3fc159a0303a49/components/esm4/readerutils.hpp),
  [ESM store](https://github.com/OpenMW/openmw/blob/46bd4599203ee52ffc0f3e8edb3fc159a0303a49/apps/openmw/mwworld/esmstore.cpp).
- [vsgopenmw build dependencies](https://github.com/vsgopenmw-dev/vsgopenmw/blob/2830e7e2b4f18ef08ee24eff45a13568ec917061/CMakeLists.txt).
- [Asset Lab scope](https://github.com/madpai/open-asset-lab/blob/e5f9dcb29f67ed6346954e66ee6d0af575f832fc/docs/OBLIVION_IMPORT.md),
  [original fixtures](https://github.com/madpai/open-asset-lab/blob/e5f9dcb29f67ed6346954e66ee6d0af575f832fc/tests/test_oblivion.py).
- [MegaMod architecture](https://github.com/madpai/megamod-showdown/blob/b6f54ea71c92953441751a28b0f93375e53bf1bc/docs/ENGINE_ARCHITECTURE.md).

Other audited candidate licenses/revisions are in [LICENSE_MATRIX.md](LICENSE_MATRIX.md).
SDL, ENet, Bullet and VSG are candidates, not installed runtime subsystems.

## Research exclusions

No leaked proprietary engine source, Havok binaries, DRM bypass or extracted
game assets were imported. Historical Oblivion multiplayer names found in
discussion/search were not accepted as implementations without a verified
source repository and license. Remastered multiplayer projects do not establish
classic native engine compatibility.
