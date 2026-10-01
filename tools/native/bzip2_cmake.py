#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Original minimal CMake adapter for the unchanged bzip2 1.0.8 library."""
from pathlib import Path
import sys

source = Path(sys.argv[1])
if (source / 'CMakeLists.txt').exists():
    raise SystemExit('Refusing to overwrite an existing bzip2 build definition')
(source / 'CMakeLists.txt').write_text('''# Original OpenOblivion adapter; SPDX-License-Identifier: GPL-3.0-only
cmake_minimum_required(VERSION 3.16)
project(oo_bzip2 LANGUAGES C)
add_library(bz2 STATIC blocksort.c huffman.c crctable.c randtable.c compress.c decompress.c bzlib.c)
set_target_properties(bz2 PROPERTIES POSITION_INDEPENDENT_CODE ON)
install(TARGETS bz2 ARCHIVE DESTINATION lib)
install(FILES bzlib.h DESTINATION include)
''')
