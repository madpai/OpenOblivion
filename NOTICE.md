# Attribution and source provenance

Original OpenOblivion source: GPL-3.0-only; see LICENSE.

The native inspector compiles unchanged source from **OpenMW**, revision
`46bd4599203ee52ffc0f3e8edb3fc159a0303a49`. OpenMW is a separate project;
OpenOblivion is not an official OpenMW release. Source is fetched from
https://github.com/OpenMW/openmw and keeps its original LICENSE, authors and
per-file notices. The ESM4 reader/header files credit **cc9cii** and carry zlib
license notices. Other linked files retain the OpenMW project license or their
individual grants. The linked reader source remains unmodified and external.
The optional native movement integration distributes a small GPLv3 camera
patch against audited OpenMW revisions; it modifies only external builds.
A second optional patch loads fixed static `bhkNiTriStripsShape` triangles into
Bullet. Patch context belongs to OpenMW and its contributors. The C++ height
filter and the strip expander are independently authored OpenOblivion code.
See tools/native and the exact-file license ledger; this is not an official
OpenMW engine release.

The optional TES4 interaction patches modify external OpenMW type/cell
bindings and NPC scene assembly under its GPLv3 project grant, and reset
optional reference lock fields in the cc9cii zlib-licensed record loader.
Existing dependency notices remain intact. The bindings/reset helpers,
application tool, container UI and regression fixtures are original
OpenOblivion GPL-3.0-only code. Public tests compile the external reference
loader unchanged; OpenSceneGraph headers remain an external dependency.

The optional TES4 animation and door patches extend audited OpenMW NIF,
scene-animation, Lua-door and Bullet-shape interfaces under its GPLv3 project
grant. Existing notices remain in the external source. The transform KF and
embedded-clip adapters, skin selector, keyframed-box helper and their original
fixtures are OpenOblivion GPL-3.0-only code. Exact file revisions and changes
are recorded in docs/research/LICENSE_MATRIX.md. No proprietary game or Havok
runtime code is copied into these implementations.

The optional TES4 player-body patch changes external OpenMW actor shape
creation and two support checks in its movement solver/stepper under the same
GPLv3 project grant. The measured hull constants, helper header and fixtures
are original OpenOblivion GPL-3.0-only code; they record numbers measured from
the owner's licensed executable and contain no Bethesda or Havok code.

No source from TES3MP, vsgopenmw, NifTools, xEdit, xOBSE, SDL, ENet, Bullet,
MegaMod or Asset Lab is copied into this checkout. Those projects are studied
as documented in docs/research/LICENSE_MATRIX.md; Asset Lab original fixture
tests are executed only in its separate local checkout.

System/NDK zlib and Vulkan development libraries are external dependencies.
A future binary distribution must include matching source/build information
and an audited dependency notice inventory. This founding checkout publishes
no binary package or game data.

The standalone upstream research build uses externally fetched MyGUI (MIT
core), Recast (zlib) and installed system libraries. The private viewer uses
the external OpenMW Example Suite Template (CC0 assets; GPLv3 MyGUI
configuration), credited in its AUTHORS.md. The template, assets and upstream
scripts keep their own notices and are not vendored here. OpenOblivion's scene
automation and fetch/integrity tools are independently authored.

The Elder Scrolls IV: Oblivion belongs to its respective rights holders.
This independent interoperability project supplies code; users supply game data.

The optional personal Android scene preview uses an external unchanged
OpenMW Android release by Andiweli and preceding port contributors, source
`7c97200966c9cb35a76b74d16d5c76f1a8939612` (GPLv3 plus individual dependency
licenses). Its patched SDL Java bridge and native/runtime resources are staged
only outside this checkout. The independently authored OpenOblivion host is
not an official OpenMW app. See the license matrix for exact binary provenance
and restrictions on any future public binary release. Owner game content in
a personal APK is private and is not licensed by this project's GPL.
