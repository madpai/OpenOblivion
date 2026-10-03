# License matrix

Research snapshot: 2026-09-30. Original OpenOblivion code is **GPL-3.0-only**.

## TES4 animation integration audit (2026-10-03)

Before modifying renderer sources, inspected OpenMW's GPLv3 grant and the exact
desktop base `46bd4599203ee52ffc0f3e8edb3fc159a0303a49`. Intended integration:
an original NiControllerSequence/KF adapter, constant-transform defaults and
bounded compact/float spline sampling. No proprietary code is adapted.
`components/nifosg/nifloader.cpp` is blob
`8bfa8de264049a9bb2d3ced5ce81831e3a607aab`; `controller.cpp` is
`d88f617005f3cfc0a69ae516601aeaa85ca1ccbf`; `controller.hpp` is
`8daf9545ae56cd4ee5db3883e0c45a11ae1c5d95`. The adapter uses their public
controller/reader interfaces; these files have no narrower file-level grant.
Patch context remains OpenMW GPLv3. Equivalent Android base
`f4bec41444214a7903bebd178389ca22ca13f646`, with the audited donor integration,
has inspected blobs `88b728d456ecd92cbbd0bf318721d7f0cfd23a0e`,
`116a25684678232ab8f87a74c6ec0262a7930a7f`, and
`cceec279b2fab21272a52a58826133621b68821e` respectively. Integration receipts
must also lock actual file SHA256s; the nested Android sources are inside the
donor worktree, so its Git HEAD is not the engine revision.

NPC source integration extends the previously audited GPLv3
`apps/openmw/mwrender/esm4npcanimation.cpp` after shared-skinning attachment.
The input SHA256s are `d8d0b696c70ad1ef7d8876701994b442f8d03f3a923b1c10df38a12b30b0ebaf`
on desktop and the Android value in `tools/native/tes4_animation.lock.json`.
It selects `idle.kf` beside the authored skeleton and uses the existing
animation clock; no movement constants or proprietary implementation are copied.
The animation receipt retains the previous interaction receipt and validates
the exact input/output hash chain for this shared source file.
`apps/openmw/mwclass/esm4npc.hpp` is also audited under OpenMW GPLv3, desktop
blob `ded76ffe46dfe7904c0142ee9096d889954a0d29`; both exact input SHA256s are
in the animation lock. Its original registration omission is repaired through
`useAnim()` so the existing non-actor clock advances; this does not implement
TES4 AI, actor statistics or physical locomotion.

Skin attachment uses the same GPLv3 SceneManager/RigGeometry interfaces at
desktop pin `46bd4599203ee52ffc0f3e8edb3fc159a0303a49`. Inspected blobs:
`attach.cpp` `17cdbf5be6642feb805e6702b9e03ac9911dacb8`,
`riggeometry.cpp` `f5fbb8d2dce5f1f18d2f2929eb0d0b8189154674`,
`riggeometry.hpp` `64f8ac3ce237c46bfb94539e9bb0a4f57525a5de`, and
`components/resource/scenemanager.hpp` `4e2a872f6051c04dffc5f3504205bef764df0692`.
No upstream visitor implementation is copied.
The existing `components/sceneutil/attach.cpp` was inspected: an empty part
filter allows its copy visitor to include the donor skeleton, which can hide
the actor's animated bones. The new original TES4 visitor copies only the
renderable's immediate subtree so rigs resolve the actor skeleton. Existing
OpenMW notices remain; this is not a claim of completed equipment/body masks.

Spline format semantics were checked against NifSkope at already-registered
`3a85ac55e65cc60abc3434cc4aaca2a5cc712eef`, `src/gl/glcontroller.cpp`, SHA256
`8f842e3bdf8317cbe29606443f99dea03fed02e1d54228a859690e8bee4b03b8`.
Its file-level notice is BSD-3-Clause, Copyright 2005-2015 NIF File Format
Library and Tools; project LICENSE.md SHA256 is
`565cf4270dfd82d48f63f37dfc904934eae2095f6ad271895b265ed2c1c4601f`.
The new evaluator is independently written, using the documented control-point
layout and clamped cubic basis; Qt code and bundled Havok/MOPP are not copied.
Preserve reference credit and this audit. Any later direct adaptation must
retain the full BSD notice. NIFXML/PyFFI are unchanged private inspection inputs,
not generated/vendored implementation. Owner clips and raw reports stay private.

This is a per-candidate reuse register, not permission to copy an entire repository. Exact revisions are immutable below and in [upstreams.lock.json](upstreams.lock.json). GitHub license hints were checked against actual license text where stated. Unclear or mixed rights remain explicit. No engine/game binary from Bethesda or Havok is included.

| Repository / exact revision studied | License evidence | Relevant systems | Compatibility decision | Reuse status | Attribution / distribution requirements |
|---|---|---|---|---|---|
| [OpenMW/openmw](https://github.com/OpenMW/openmw/tree/46bd4599203ee52ffc0f3e8edb3fc159a0303a49)<br>`46bd4599203ee52ffc0f3e8edb3fc159a0303a49` | GPLv3 at project level; zlib notices on cc9cii ESM4 reader files | ESM4, BSA, NIF, cell streaming and later-game runtime references | Compatible for the GPLv3 build; preserve per-file exceptions | Linked unchanged external reader slice; no vendored engine source | Keep LICENSE, authors and all file notices; ship matching corresponding source and build scripts with binary distributions. |
| [vsgopenmw-dev/vsgopenmw](https://github.com/vsgopenmw-dev/vsgopenmw/tree/2830e7e2b4f18ef08ee24eff45a13568ec917061)<br>`2830e7e2b4f18ef08ee24eff45a13568ec917061` | GPLv3 project; per-file licenses also apply | VulkanSceneGraph rendering and migration work | GPLv3 candidate; full dependency audit required | Research only; no code copied or linked | Retain GPL/source obligations and per-file notices if adopted; avoid treating dependencies as GPL by default. |
| [TES3MP/TES3MP](https://github.com/TES3MP/TES3MP/tree/49be5b6405d6ab427e06ed350cf76c715a1f3bdd)<br>`49be5b6405d6ab427e06ed350cf76c715a1f3bdd` | GPLv3 with additional Section 7 terms, appended to LICENSE | Multiplayer packets, synchronization and server scripting interfaces | Candidate; preserve appended terms and audit CrabNet before reuse | Research only; no code copied or linked | Preserve copyright/trademark/origin notices, mark changes, supply matching source; retain additional terms. |
| [TES3MP/CoreScripts](https://github.com/TES3MP/CoreScripts/tree/3e397a11eaf7d0d4ff08df4bb9925e67748b4db8)<br>`3e397a11eaf7d0d4ff08df4bb9925e67748b4db8` | MIT | Death/respawn, persistence and server mode examples | Compatible with notice retention | Research only | Retain TES3MP copyright and MIT permission/disclaimer text if adapted. |
| [xyzz/openmw-android](https://github.com/xyzz/openmw-android/tree/bfd613230ebe57170cbe4966aa8938d54afa6efa)<br>`bfd613230ebe57170cbe4966aa8938d54afa6efa` | GPLv3 (LICENSE.txt) | Historical Android build, input and launcher integration | GPLv3 candidate; archived, dependencies unaudited | Research only | Keep GPL and corresponding source/build scripts; audit bundled libraries separately. |
| [niftools/niflib](https://github.com/niftools/niflib/tree/e29166183e23c3477fb7e08d4523dd111440947e)<br>`e29166183e23c3477fb7e08d4523dd111440947e` | BSD-3-Clause (license.txt) | Native NIF decoding and schema-generated types | Compatible for original library files | Research only | Retain copyright, conditions and disclaimer in source and binary documentation; no endorsement. |
| [niftools/nifskope](https://github.com/niftools/nifskope/tree/3a85ac55e65cc60abc3434cc4aaca2a5cc712eef)<br>`3a85ac55e65cc60abc3434cc4aaca2a5cc712eef` | BSD-3-Clause for original sources (LICENSE.md); dependencies mixed | BSA v103/104 handling and NIF viewer diagnostics | Original source candidate; Havok/bundled libraries excluded | Research only | Retain BSD notices; do not copy proprietary Havok/MOPP binaries or assume included libraries share the license. |
| [niftools/nifxml](https://github.com/niftools/nifxml/tree/970a6238218a106daaeb89a61bcda0eeaf9d08c4)<br>`970a6238218a106daaeb89a61bcda0eeaf9d08c4` | GPLv3 (LICENSE) | NIF version/block schema reference | GPLv3 schema candidate; audit generation/output before use | Research only at locked current revision | Preserve schema license and provenance if distributed or used for generated source. |
| [niftools/pyffi](https://github.com/niftools/pyffi/tree/7f4404dbb8cf832dadd4b3150819340b8764f9b0)<br>`7f4404dbb8cf832dadd4b3150819340b8764f9b0` | BSD-3-Clause for original Python sources (LICENSE.rst); bundled tools mixed | Offline NIF decoding in existing Asset Lab | BSD source candidate only; schema dependency assessed separately | External six-test reproduction; not a runtime dependency | Retain BSD notices for copied Python; exclude Mopper/Havok and xdelta binaries; do not assign BSD to the whole bundle. |
| [llde/xOBSE](https://github.com/llde/xOBSE/tree/f64a8fa0481e24b3e159d276b29b721a548876bf)<br>`f64a8fa0481e24b3e159d276b29b721a548876bf` | No unambiguous repository-wide grant found in inspected files/README | Command opcodes, form layouts and observed classic behavior | Unresolved: do not copy or link | Research only; independently implement needed behavior | README contribution guidance is not a license grant. Resolve rights for exact files before adapting. |
| [TES5Edit/TES5Edit](https://github.com/TES5Edit/TES5Edit/tree/9fb016884bec138ea6c7b872cec831537d464c3e)<br>`9fb016884bec138ea6c7b872cec831537d464c3e` | MPL-2.0 (LICENSE.txt and Core/wbDefinitionsTES4.pas header) | TES4 record definitions, flags, conditions and script fields | Conditional candidate; check secondary-license exclusions for exact files | Research only; no definitions copied | Preserve MPL notices and source availability for covered files; review MPL 3.3 and Exhibit B before GPL combination. |
| [vsg-dev/VulkanSceneGraph](https://github.com/vsg-dev/VulkanSceneGraph/tree/2feabc69359c1f3fdc22825f4dcca7147903da67)<br>`2feabc69359c1f3fdc22825f4dcca7147903da67` | MIT (LICENSE.md) | Vulkan scene graph/resource management | Compatible with notice retention | Research only; not linked yet | Retain Robert Osfield copyright and MIT license in substantial copies/binary documentation. |
| [lsalzman/enet](https://github.com/lsalzman/enet/tree/5a9c537fd464b3c6d3c55e1d3bd47588faf71b42)<br>`5a9c537fd464b3c6d3c55e1d3bd47588faf71b42` | MIT (LICENSE) | Bounded reliable/unreliable UDP transport candidate | Compatible with notice retention | Research only; not linked | Retain Lee Salzman copyright and MIT permission/disclaimer text. |
| [BulletPhysics/bullet3](https://github.com/bulletphysics/bullet3/tree/63c4d67e337017f9d8b298c900e9aabdb69296e7)<br>`63c4d67e337017f9d8b298c900e9aabdb69296e7` | Zlib for core; Extras/examples/ThirdPartyLibs excluded (LICENSE.txt) | Collision and character-controller candidate; no Havok binary dependency | Compatible for audited core files | Research only; not linked | Preserve license, origin and changed-source marking; audit anything from excluded directories. |
| [libsdl-org/SDL](https://github.com/libsdl-org/SDL/tree/56a72f8c869fd5ebd69c1bd4ba7abcdf0b7b83b4)<br>`56a72f8c869fd5ebd69c1bd4ba7abcdf0b7b83b4` | Zlib (LICENSE.txt) | Desktop window/input and Android integration candidate | Compatible for audited SDL source | Research only; not linked | Preserve origin/license, mark altered source and separately audit bundled dependencies. |
| [ColeDeanShepherd/TESUnity](https://github.com/ColeDeanShepherd/TESUnity/tree/f4d5e19f68da380da9da745356c7904f3428b9d6)<br>`f4d5e19f68da380da9da745356c7904f3428b9d6` | MIT for original code (LICENSE.txt); vendor/schema rights separate | Alternative world-viewer/VR architecture | MIT original code candidate; Unity is an external engine dependency | Research only; README targets Morrowind | Retain Cole Shepherd notice; audit Vendors/nif.xml separately; not evidence of a native Oblivion runtime. |
| [madpai/open-asset-lab](https://github.com/madpai/open-asset-lab/tree/e5f9dcb29f67ed6346954e66ee6d0af575f832fc)<br>`e5f9dcb29f67ed6346954e66ee6d0af575f832fc` | GPLv3 (LICENSE); optional decoder has separate license | Classic BSA/static NIF import, provenance and compiler/native agreement | GPLv3 candidate; no runtime/content-package compatibility assumption | Six original-fixture tests; unchanged external BSA API used by the private scene packager, not included in the APK | Retain GPL/source and decoder notices if reused; keep owner assets and compiled packages private. |
| [madpai/megamod-showdown](https://github.com/madpai/megamod-showdown/tree/b6f54ea71c92953441751a28b0f93375e53bf1bc)<br>`b6f54ea71c92953441751a28b0f93375e53bf1bc` | GPLv3 (LICENSE) | Vulkan/Android experience, host-owned survival rules and evidence workflow | GPLv3 candidate; inherited dependencies require audit | Read-only architecture study; no code copied | Retain GPL/source and third-party notices if reused; no donor data or personal APK contents. |

## Standalone reproduction dependencies

These are external research checkouts, not assets/source vendored into this
repository or dependencies of the native reader executables.

| Repository / revision | License and notices | Actual use / compatibility |
|---|---|---|
| [OpenMW/example-suite](https://gitlab.com/OpenMW/example-suite/-/tree/a41b44d9403ff3f8a1505c1b4bc152c4dd623b64), `a41b44d9403ff3f8a1505c1b4bc152c4dd623b64` | LICENSE: CC0 1.0 assets; GPLv3 MyGUI configuration. AUTHORS.md credits creators. Documentation identifies a separate Pelagiad font exception; no such font is shipped here. | Unchanged external base game/template for the documented later-game viewer configuration. No assets copied into OpenOblivion. Preserve GPL notices for any configuration reuse; audit each font/dependency before distribution. |
| [MyGUI/mygui](https://github.com/MyGUI/mygui/tree/dae9ac4be5a09e672bec509b1a8552b107c40214), `dae9ac4be5a09e672bec509b1a8552b107c40214` (3.4.3) | MIT, COPYING.MIT; retain AUTHORS and permission/disclaimer. Media/plugins have exceptions documented in Docs/src/license.txt; not a whole-repository MIT assumption. | Core built unchanged by full upstream CMake, compatible with GPLv3 notice retention; not linked into the OpenOblivion probes. No MyGUI media/plugins redistributed. |
| [OpenMW/recastnavigation](https://github.com/OpenMW/recastnavigation/tree/03259f3287ff8330f0d66fcd98d022edddffaa97), `03259f3287ff8330f0d66fcd98d022edddffaa97` | Zlib, License.txt; preserve origin, license and changed-source marking. | Built unchanged by full upstream CMake; compatible for audited core. No navigation/runtime code copied here. |
| [OpenMW/openmw 0.49.0](https://github.com/OpenMW/openmw/tree/675146bd8bce6245d78889f543b5c02a1e3936fe), `675146bd8bce6245d78889f543b5c02a1e3936fe` | GPLv3 project with per-file notices, as above. | Release source studied to compare startup behavior; not built or linked in this checkpoint. |

## Audited linked slice

### TES4 interaction integration (2026-10-03)

Desktop OpenMW `46bd4599203ee52ffc0f3e8edb3fc159a0303a49` and Android engine
`f4bec41444214a7903bebd178389ca22ca13f646`: changes to
`apps/openmw/mwlua/types/{types.cpp,types.hpp}` and
`apps/openmw/mwlua/cellbindings.cpp` and
`apps/openmw/mwrender/esm4npcanimation.cpp` use the project's GPLv3 grant.
Existing notices remain in the external source trees. The new bindings header,
patch application tool and container scripts are independently authored
GPL-3.0-only integration code. The existing OpenMW record, scene instance and
skinning APIs are used rather than copying game executable code.
`components/esm4/{loadcont,loadnpc,loadcrea,inventory}.hpp` are read unchanged;
their cc9cii zlib notices stay with the external dependency. Intended use is
private Linux/Android builds; public distribution contains source patches and
original test fixtures only. Names and base inventory snapshots do not imply
loot transfer, leveled-item evaluation, TES4 saves or dialogue compatibility.

The same integration adds a lock-state reset at the start of
`components/esm4/loadrefr.cpp` (cc9cii zlib notice at the revisions above),
using an original helper. All existing notices stay intact; patches explicitly
mark the altered behavior. `loadrefr.cpp` is compiled unchanged for the public
synthetic regression fixture; only the external runtime applies the patch.
TES4 XLOC definitions in the pinned TES5Edit checkout are research references;
no xEdit source is copied or linked by this change.

CMake lists 14 upstream translation units: `components/esm4/{reader,loadtes4}.cpp`, `components/esm/{formid,refid,stringrefid,generatedrefid,indexrefid,esm3exteriorcellrefid}.cpp`, `components/files/{constrainedfilestreambuf,conversion}.cpp`, `components/platform/fileposix.cpp`, `components/toutf8/toutf8.cpp`, `components/debug/debuglog.cpp`, and `components/vfs/manager.cpp`. Their headers are read from the same verified commit. Reader/header files credit **cc9cii** under zlib notices; files without narrower grants are treated under the OpenMW project GPLv3. The checkout and notices remain unchanged. The build checker verifies every tracked blob before building, including edits hidden by Git index flags.

`src/inspect.cpp` and `src/vulkan_probe.cpp` are independently authored orchestration. There is no copied OpenMW traversal helper: the scanner uses the reader API directly to avoid the final-record omission documented in [REPRODUCTION.md](REPRODUCTION.md).

System/NDK **zlib** and **Vulkan loader/headers** are build dependencies, not vendored repositories. Record their installed/toolchain versions in reproduction evidence; a distributable dependency bundle needs its own source/notices inventory. No binary distribution is published by this founding work.

Asset Lab reproduction used PyFFI `7f4404dbb8cf832dadd4b3150819340b8764f9b0` with its NIF schema submodule `f265c56482c728c6877e45d5b5993d3bff83670a`, distinct from the newer nifxml revision above. The older schema has no separate LICENSE file in that local checkout; it is not copied or shipped here, and its redistribution remains unaudited.

## Future reuse procedure

Before importing code, record upstream path and blob hash, exact license/notice, original vs adapted status, changed lines, and the OpenOblivion destination. Preserve notices next to copied files and in a distribution notice inventory. Audit transitive dependencies and generated output, not just a top-level license badge. Researching behavior does not authorize copying code from an unclear-license repository.

Canonical license references: [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html), [MPL-2.0](https://www.mozilla.org/en-US/MPL/2.0/). MPL compatibility remains conditional on exact covered files and secondary-license eligibility.

## Private Android baseline (2026-10-01)

Before staging any donor files, inspected **Andiweli/OpenMW-Android**, tag
`0.51.0-11`, source `7c97200966c9cb35a76b74d16d5c76f1a8939612`. LICENSE is GPLv3;
individual source notices and dependency licenses still apply. The release APK
SHA256 is `c0ea41c9f862d95c10796909d3b0edef6f401d5ac92ce9dd3bf92f967f32ee07`.
Its `libopenmw.so` SHA256 is
`a99f89d2e8de0f652de219af9acd29db48db10f55f0026cc7a911c426a7efdc0`, matching
`source/buildscripts/openmw-051-patch39-libopenmw.sha256` at that source revision.
Native engine base is OpenMW 0.51.0,
`f4bec41444214a7903bebd178389ca22ca13f646`, with the donor's documented patches.
This is a separate reproduction host, not our 0.52 reader runtime or Vulkan renderer.

Intended use: copy the eight unchanged Java files in
`source/app/src/main/java/org/libsdl/app/` to an **external private build directory**,
plus the six released ARM64 libraries (OpenMW, SDL2, GL4ES, OpenAL, Collada DOM,
libc++), engine resources and base configuration. Preserve donor LICENSE and
`source/3rdparty-licenses.txt`, engine resource notices, and Template LICENSE /
AUTHORS. No donor launcher, Bugsnag libraries, icons, proprietary game binaries,
or runtime payloads are committed here. OpenOblivion's launcher, touch overlay,
packager and download service are independently authored GPL-3.0-only code.

SDL has zlib upstream licensing; this port's modified Java bridge is conservatively
treated as GPLv3 under the donor project. OpenAL is LGPL, GL4ES MIT, Collada DOM
MIT-style, libc++ Apache-2.0 with LLVM exceptions; statically linked engine
dependencies retain their individual licenses. The donor build scripts and full
third-party notices accompany the private test. Dependency recipes include
historical/floating inputs: a hash-verified released binary is **not** proof of a
fully reproducible transitive source build. Public binary release remains gated
on a complete dependency revision/source inventory and corresponding-source
bundle. This personal package is supplied back to the installation owner over
their private tailnet; it must never enter public releases or CI artifacts.

[Exact donor source and patches](https://github.com/Andiweli/OpenMW-Android/tree/7c97200966c9cb35a76b74d16d5c76f1a8939612).

The 0.2 scene dependency traversal and read-only phone QA Lua are independently
authored; no upstream parser or Lua implementation is copied. Field layouts
were checked against the pinned OpenMW reader, and camera/debug API contracts
against the Android engine's 0.51 base. The gallery/QA workflow was studied in
the already-listed MegaMod checkout; its server/page code is not reused.

The 0.3 preview camera fallback and desktop fault/motion harness are also
independently authored GPL-3.0-only code using documented APIs. Camera tracking
behavior and exterior-grid constants were checked against OpenMW engine base
`f4bec41444214a7903bebd178389ca22ca13f646` and the unchanged 0.52 desktop pin.
No camera implementation or donor script is copied/modified. Released native
libraries and their notice/source requirements remain unchanged.

The native-player trajectory driver, one-time test placement, analysis and
synthetic trajectory fixtures are independently authored GPL-3.0-only code.
No controller implementation is copied. Behavior research inspected
`components/nifbullet/bulletnifloader.cpp` at the 0.51 base above (SHA256
`6cafec42e7f0231331656d88fdb47b730b4bb4c0e707fbd9377d200884abf2be`) and the
locked 0.52 pin (Git blob `0194105efaeed61610edbee0d9400e6059d2b426`, file
SHA256 `d6eb13007b07c03e359c40f6bd29e596804b7f812167c904883779f7d342fbc2`).
The static-collision patches are original insertions against those exact files.
Their context remains OpenMW's. The strip expander is original. No Havok or
MOPP binary is redistributed. Private stair geometry inspection uses the
already-listed external PyFFI; no schema or game collision mesh is copied.

The 0.4 grounded-eye filter, bounded phone movement/view sampling and original
stair generator are independently authored GPL-3.0-only code. API semantics
were checked against `apps/openmw/mwlua/camerabindings.cpp`,
`apps/openmw/mwrender/camera.cpp` and `files/lua_api/openmw/{camera,types}.lua`
at the exact 0.51 base above and the unchanged locked 0.52 checkout. TES3 fixture
envelopes were checked against 0.52 `components/esm3/{loadtes3,loadstat,loadcell,cellref}.cpp`.
No engine algorithm, resource, donor script or format implementation was copied.
Fixtures are boxes/treads authored from numeric dimensions, generated outside
the checkout; no owner geometry is adapted. Native binary/source obligations
remain unchanged. The static strip loader is the audited insertion described
above, not a new physics library.

## Native movement integration (2026-10-01)

Before applying native changes, audited the GPLv3 project grant and exact files
`apps/openmw/mwrender/{camera.cpp,camera.hpp}` at desktop revision
`46bd4599203ee52ffc0f3e8edb3fc159a0303a49` (Git blobs
`8f0cf6f7d80a04576950826461a5d851c378cdfd` and
`2d0633b09d45ee48005cedc2cd1b3f7ac416075a`). These files have no narrower
file-level grant. The integration will modify only an external checkout;
published patch context retains OpenMW's GPL and attribution through NOTICE.md
and this ledger. The bounded C++ height filter is independently authored
OpenOblivion code, not a copy of an upstream controller or camera algorithm.

The Android build reproduction uses an external worktree of the already-audited
Andiweli revision `7c97200966c9cb35a76b74d16d5c76f1a8939612`.
`source/buildscripts/CMakeLists.txt` is Git blob
`39cfa5c6574b5d09d8ab9c03ce1e65d6a073ba1e`;
`source/3rdparty-licenses.txt` is `6fdf9d0139ce8d7df31c9ddf9e3e6c615bca14f0`.
Its GPLv3 build scripts and patches remain external with their notices.
Intended changes are locked download inputs and build-host compatibility;
the engine base remains `f4bec41444214a7903bebd178389ca22ca13f646`.
Every source archive must receive a recorded SHA256 and license inventory before
its resulting native runtime is packaged. This source build does not promise
bit-for-bit identity with the donor's Windows/WSL release.

Exact dependency archive SHA256s and inspected notice hashes are recorded in
[android-native.lock.json](android-native.lock.json). Nineteen archives are
external build inputs: JPEG 1.5.3 (IJG/BSD/Zlib), PNG 1.6.42 (libpng license),
FreeType 2.13.2 (FTL chosen, include its credit), OpenAL 1.23.1 (LGPL-2.0-or-later),
Boost 1.83 (BSL-1.0), FFmpeg 6.1 (LGPLv3 for this codec configuration), SDL 2.0.22
(Zlib, HIDAPI BSD alternative), Bullet 3.25 (Zlib core), MyGUI 3.4.3 (MIT core),
LZ4 1.9.3 (BSD library), LuaJIT (MIT/Lua notices), zlib 1.3.1 (Zlib), libxml
2.12.5 (MIT with per-file notices), Collada DOM 2.5 (SCEA MIT-style plus embedded
PCRE BSD/minizip Zlib), ICU 70.1 (Unicode/ICU notices) and exact GL4ES/OSG/engine
revisions. OSG uses OSGPL/LGPL with linking exceptions; disabled unrelated
plugins/media are excluded. Each archive keeps all original notices externally.
The donor's retired Duron27 bzip2 URL is replaced by canonical bzip2 1.0.8
(Julian Seward's permissive license), with an independently authored build
adapter. NDK r26b is hash-verified; its libc++ notices remain separate.

The same camera-only integration targets Android engine base
`f4bec41444214a7903bebd178389ca22ca13f646`: camera.cpp Git blob
`9a2240915854f7ce693a20bf2a01c26c79dabdec`, camera.hpp
`e09a26529335f95183ead56138f01bcc9aec03d8`, GPLv3 as above. The patch preserves
existing camera collision queries, actor motion, look and first-person behavior.
It is opt-in and is not a general OpenMW camera rewrite. Nested engine
FetchContent and bundled notices must also enter the corresponding-source
inventory before any binary is distributed publicly.
