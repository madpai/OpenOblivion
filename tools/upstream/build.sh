#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
set -euo pipefail
cmake -S /source -B /work/build -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_LAUNCHER=OFF -DBUILD_WIZARD=OFF -DBUILD_OPENCS=OFF \
    -DBUILD_COMPONENTS_TESTS=OFF -DBUILD_OPENMW_TESTS=OFF \
    -DBUILD_NAVMESHTOOL=OFF -DBUILD_BULLETOBJECTTOOL=OFF -DBUILD_DOCS=OFF \
    -DOPENMW_USE_SYSTEM_MYGUI=OFF -DOPENMW_USE_SYSTEM_RECASTNAVIGATION=OFF
cmake --build /work/build --target openmw esmtool bsatool niftest --parallel "${OO_BUILD_JOBS:-8}"
