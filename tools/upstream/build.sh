#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
set -euo pipefail
oo_require_revision() {
    if [[ "$(git -C "$1" rev-parse HEAD)" != "$2" ]]; then
        printf 'Unaudited upstream revision in %s\n' "$1" >&2
        exit 1
    fi
}
# Keep these revisions aligned with docs/research/upstreams.lock.json.
oo_require_revision /source 46bd4599203ee52ffc0f3e8edb3fc159a0303a49
cmake -S /source -B /work/build -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_LAUNCHER=OFF -DBUILD_WIZARD=OFF -DBUILD_OPENCS=OFF \
    -DBUILD_COMPONENTS_TESTS=OFF -DBUILD_OPENMW_TESTS=OFF \
    -DBUILD_NAVMESHTOOL=OFF -DBUILD_BULLETOBJECTTOOL=OFF -DBUILD_DOCS=OFF \
    -DOPENMW_USE_SYSTEM_MYGUI=OFF -DOPENMW_USE_SYSTEM_RECASTNAVIGATION=OFF
# MyGUI/Recast are extracted archives, not Git checkouts. The unchanged
# upstream FetchContent declarations verify their locked SHA-512 downloads.
cmake --build /work/build --target openmw esmtool bsatool niftest --parallel "${OO_BUILD_JOBS:-8}"
