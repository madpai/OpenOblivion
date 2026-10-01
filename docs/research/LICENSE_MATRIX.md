# License matrix

Research snapshot: 2026-09-30. Original OpenOblivion code is **GPL-3.0-only**.

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
