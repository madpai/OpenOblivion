# Original door audio in the private preview

Checkpoint: 2026-10-03. The Android host now permits native audio initialization.
The smaller Vilverin bundle includes the scene's referenced opening/closing
sound files, and the packaged same-cell handler emits them at the door. The
complete installation already contains the original sound/music archives.
This is an audio connection checkpoint toward the active 1:1 goal.

## Implementation and measured output

The previous launcher passed `--no-sound` unconditionally. Removing that
argument enables the existing audited OpenAL/decoder path; no native library
changes are made. The original packaging traversal follows classic DOOR
`SNAM`/`ANAM` references into SOUN `FNAM` paths, preserving both references.
The bounded slice adds **22 unchanged sound files / 6,266,200 bytes**. Its
directory-valued `fire_torchmounted_lp/` request remains unresolved; variants,
loop selection and general audio dependency closure are separate work.

The existing engine already resolves TES4 sound records. Its distance/volume
initialization is explicitly a placeholder (`volume=1, min=1, max=255` in
`mwsound/soundbuffer.cpp`). The owner's gate records encode min/max bytes
60/12, frequency adjustment 0, flags 0 and static attenuation 352 centibels.
This checkpoint does **not** apply those fields or establish original spatial
attenuation. A closing sound can be active yet inaudible beyond the current
255-unit limit. That limit remains unchanged until its original conversion
and runtime behavior are recovered.

The original opening and closing samples last **1.123265** and **1.808265
seconds** at 44,100 Hz. Private full-installation and actual bounded-package
desktop probes activate the packaged handler, observe both sound IDs playing
on the door, and capture the engine's OpenAL mix at 48,000 Hz. A nearby listener
holds still during each sample; music is muted only in these evidence runs.
Ordinary player controls still block at the closed gate and cross after opening.
No original movement or physics constants change.

Independent FFmpeg decoding and normalized waveform correlation identify both
original samples in each engine mix. Full-data correlation is **0.999548
opening / 0.997605 closing**; bounded-slice correlation is **0.999547 /
0.997605**. These establish sample playback, not original-executable timing,
mix balance, attenuation or audible phone acceptance. Earlier probes with music
or a listener beyond the placeholder range are retained privately and do not
establish both output samples.

`probe_scene.py --tes4-doors --door-traversal --audio-capture` writes its wave
configuration and output only into a fresh private evidence directory. The
capture uses the documented [OpenAL Soft wave backend](https://github.com/kcat/openal-soft/blob/1.23.1/alsoftrc.sample).
It does not replace the shipped audio device or volume settings. Source layout
and API provenance are recorded in [the license matrix](LICENSE_MATRIX.md).

## Packages and acceptance

Single APK **0.18-audio**, versionCode 18: **667,757,183 bytes**, SHA256
`eb7ed317ddd2c6823e4305ee1870b60757f66bc6b89b1babdce292c070999783`.
It contains **4,192 payload files / 869,963,115 unpacked bytes**.
Complete installed-data set **0.19-installed-audio**, versionCode 19:
**5,569,251,880 bytes**, SHA256
`d331b4beb93532b90c3c04ed2fb12c2c3c913373088f97cd5207cdfb6805acab`.
Its **824 payload files / 5,955,597,123 unpacked bytes** retain all 73 original
Data files unchanged, with the same six-APK installation structure.
See [installed assets](INSTALLED_ASSETS.md). The source-built native libraries
are identical to [the door checkpoint](TES4_DOORS.md).

The original fixtures cover both sound references, path normalization,
malformed links, and the door emitter; all 14 CTest groups pass. Both packages
compile with the unchanged native runtime. The single APK's signature and
alignment pass, and the isolated Android 14 emulator verifies all 4,192
extracted files, the installed APK hash and ready launcher. Android scene
rendering and audible physical-phone playback remain pending; the historical
emulator GLES translation failure still applies.

The subsequent full-set upgrade installs all six matching APKs and verifies
all **824 extracted file hashes** plus the ready launcher; preparation takes
**90.79 seconds** in this emulator. Full download CRCs and all six nested APK
hashes also pass. A transient file read error interrupted the first full-set
assembly; a complete rebuild and these independent checks pass, and the failed
log is retained privately.

Remaining: original attenuation/conversion, random/looping/directory sounds,
actor footsteps, effects, voice/dialogue synchronization, music selection,
mixing, and mobile audio focus/pause/resume. Full-set music files are present
and the desktop baseline can play an original explore MP3; the borrowed music
selector does not establish TES4 selection behavior. Native traces still
report attempted empty `sound/` resources during movement. This checkpoint
does not implement the unresolved audio/gameplay systems in [PARITY.md](../PARITY.md).

All original WAVs, mixes, raw logs and captures remain private under
`openoblivion-private/evidence/tes4-audio-*`.
