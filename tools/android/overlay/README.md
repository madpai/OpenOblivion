# Phone launcher overlay

Files here ship inside the APK (`assets/overlay`) rather than the owner data
payload. The launcher copies them to `files/overlay` on every start and adds
that directory last in `openmw.cfg`, so a file here overrides the payload copy
with the same path. Changing them never changes the payload ID, so phones keep
their downloaded game data.

- `start_position.omwscripts`, `scripts/openoblivion_start_position.lua`:
  start at the original prologue sewer exit.
- `scripts/openoblivion_run_gate.lua`: overrides the payload's run gate; run
  by default (as in Oblivion), WALK holds Shift.
- `scripts/openoblivion_tes4_stats.lua`: applies the Player record's starting
  attributes and measured health/magicka/fatigue formulas; its values file is
  generated from the owner's master by `tools/android/tes4_stats.py` at package time.
- `meshes/sky_atmosphere.osgt`: the CC0 example-suite `sky_atmosphere.dae`
  (Matjaž Lamut) converted with `convert_template_model.cpp` (OSG 3.6.5 COLLADA
  reader, animation callbacks and COLLADA user data stripped). Android's
  COLLADA loader fails on every `.dae`, so the sky lost its atmosphere layer;
  the launcher points `skyatmosphere` at this file.
