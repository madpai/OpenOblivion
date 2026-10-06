#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Build the six native libraries for an x86_64 Android emulator from the audited engine source.
#
# Why: the emulator on an x86_64 host runs the arm64 libraries through a translation layer whose GLES
# proxy crashes inside GL4ES (docs/ANDROID.md). A native x86_64 build of the same source avoids it.
#
# Needs a finished arm64 build in <work> first (tools/native/prepare_android.py --build --grounded-eye
# plus every tes4_*.py receipt applied), because its engine tree is the audited source we overlay.
# Everything stays outside the checkout. Output: <work>/runtime-x86_64/*.so (stripped engine).
#
# Usage: build_emulator_x86_64.sh <work> [jobs]     then tools/android/make_emulator_apk.py
set -euo pipefail
WORK=$(realpath "${1:?usage: build_emulator_x86_64.sh <work> [jobs]}")
JOBS=${2:-6}
SCRIPTS=$WORK/source/source/buildscripts
ARM=$SCRIPTS/build/arm64/openmw-prefix/src/openmw
X86=$SCRIPTS/build/x86_64/openmw-prefix/src/openmw
OUT=$WORK/runtime-x86_64
[ -d "$ARM" ] || { echo "no arm64 engine tree at $ARM: build and patch arm64 first" >&2; exit 1; }
ls "$ARM"/.openoblivion-*.json >/dev/null 2>&1 || { echo "arm64 engine tree has no receipts applied" >&2; exit 1; }

# 1. Two donor-script fixes for x86_64 (idempotent; originals kept as *.pre-x86_64).
python3 - "$SCRIPTS" <<'EOF'
import sys, pathlib
root = pathlib.Path(sys.argv[1])
def patch(path, old, new):
    p = root / path
    text = p.read_text()
    if new in text:
        return
    if old not in text:
        sys.exit('expected text not found in %s' % path)
    backup = p.with_name(p.name + '.pre-x86_64')
    if not backup.exists():
        backup.write_text(text)
    p.write_text(text.replace(old, new, 1))
# no nasm is needed: libjpeg-turbo SIMD stays off for x86_64 as the donor already does for x86
patch('CMakeLists.txt', 'set(libjpeg_turbo_flags "")\nif (${ARCH} STREQUAL "x86")',
      'set(libjpeg_turbo_flags "")\nif ((${ARCH} STREQUAL "x86") OR (${ARCH} STREQUAL "x86_64"))')
# FFmpeg's configure rejects the donor's -march=intel; x86-64 is the generic baseline
patch('include/version.sh', 'NDK_TRIPLET="x86_64-linux-android"\n\tFFMPEG_CPU="intel"',
      'NDK_TRIPLET="x86_64-linux-android"\n\tFFMPEG_CPU="x86-64"')
EOF

# 2. Dependencies and the baseline engine for x86_64 (--no-resources: shared resource dirs stay untouched).
( cd "$WORK/source/source" && bash buildscripts/build.sh --arch x86_64 --jobs "$JOBS" --release --no-resources )

# 3. Overlay the audited, receipt-patched engine source (checksums decide what changes; times are not kept
#    so make rebuilds exactly the changed files), then rebuild the engine target.
rsync -rlc --no-times --exclude=.git "$ARM"/ "$X86"/
cmake --build "$SCRIPTS/build/x86_64/openmw-prefix/src/openmw-build" --target openmw --parallel "$JOBS"

# 4. Collect the six libraries; strip debug info from the engine as the arm64 flow does.
mkdir -p "$OUT"
JNI=$WORK/source/source/app/src/main/jniLibs/x86_64
for lib in libc++_shared libSDL2 libGL libopenal libcollada-dom2.5-dp; do cp "$JNI/$lib.so" "$OUT/"; done
cp "$SCRIPTS/build/x86_64/openmw-prefix/src/openmw-build/libopenmw.so" "$OUT/libopenmw.so"
"$SCRIPTS/toolchain/ndk/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip" --strip-debug "$OUT/libopenmw.so"
( cd "$OUT" && sha256sum ./*.so )
echo "x86_64 runtime: $OUT (next: tools/android/make_emulator_apk.py)"
