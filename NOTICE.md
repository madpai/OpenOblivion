# Attribution and source provenance

Original OpenOblivion source: GPL-3.0-only; see LICENSE.

The native inspector compiles unchanged source from **OpenMW**, revision
`46bd4599203ee52ffc0f3e8edb3fc159a0303a49`. OpenMW is a separate project;
OpenOblivion is not an official OpenMW release. Source is fetched from
https://github.com/OpenMW/openmw and keeps its original LICENSE, authors and
per-file notices. The ESM4 reader/header files credit **cc9cii** and carry zlib
license notices. Other linked files retain the OpenMW project license or their
individual grants. No upstream source is vendored or modified here.

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
