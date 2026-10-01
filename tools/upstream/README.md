# Standalone upstream reproduction

This builds **unchanged OpenMW**, separately from OpenOblivion's native tools.
Docker is required. Keep dependency sources, build output, owner files and
evidence outside this repository. No image or binary is published here.

The Ubuntu base image is pinned by digest. Apt packages remain repository
resolved, so record the resulting image ID/package inventory for each build;
this recipe is reproducible from source, not a bit-identical dependency lock.

From the OpenOblivion root:

```sh
python3 tools/fetch_upstream.py --cache ../openoblivion-deps
python3 tools/check_upstream.py ../openoblivion-deps/openmw
docker build -t openoblivion-research-build:founding tools/upstream
mkdir -p ../openoblivion-private/upstream-work
docker run --rm --init --cpus 8 --memory 24g \
  --cap-drop ALL --security-opt no-new-privileges \
  --user "$(id -u):$(id -g)" \
  --volume "$PWD/../openoblivion-deps/openmw:/source:ro" \
  --volume "$PWD/../openoblivion-private/upstream-work:/work" \
  openoblivion-research-build:founding
```

The full build uses the upstream-selected MyGUI/Recast sources, recorded in
the [license matrix](../../docs/research/LICENSE_MATRIX.md). It builds
`openmw`, `esmtool`, `bsatool` and `niftest`. System packages are isolated from
the host; the source mount is read-only. The build script rejects a different
engine revision; unchanged upstream CMake verifies the MyGUI/Recast archive
downloads against SHA-512 pins. An edited extracted dependency cache requires
separate investigation; do not treat an old CMake download stamp as an audit.
Record Docker image identity with
`docker image inspect` and installed package versions with `dpkg-query` in
that image. Raw output stays in the private workspace.

## Owner scene probe

The [official later-game setup](https://openmw.org/2025/openmw-0-49-0-released/)
loads Oblivion alongside a base game. We use the public OpenMW Template;
Oblivion alone lacks the TES3 globals/player/skills that this baseline expects.
This is a viewer bootstrap, not an OpenOblivion gameplay implementation.

```sh
python3 tools/fetch_upstream.py --cache ../openoblivion-deps --project example-suite
python3 tools/upstream/hydrate_template.py --source ../openoblivion-deps/example-suite
python3 tools/upstream/probe_scene.py \
  --build-work ../openoblivion-private/upstream-work \
  --template ../openoblivion-deps/example-suite \
  --data "/your/Oblivion/Data" --start Vilverin \
  --output ../openoblivion-private/evidence/interior-01
```

The template fetcher downloads only `game_template/data` LFS objects from
revision-specific GitLab URLs. It verifies pointer size/SHA-256 before writing.
The integrity checker accepts either locked pointers or their exact materialized
bytes for this template, while rejecting source changes, index changes and
untracked files. All other upstreams require their exact Git blob contents.
Git may display hydrated files as modified if Git LFS is not installed; the
checker verifies them against committed pointers rather than trusting status.

The probe uses Xvfb and software OpenGL, an 800x600 window, a read-only owner
installation and a fresh private evidence directory. Networking is disabled
inside the scene container. Independently authored Lua requests a screenshot
after five simulation seconds and quits after seven. A 120-second wall limit
stops the uniquely named container on timeout. Success requires the completion
marker, a screenshot and engine exit zero; inspect the image and logs before
claiming scene compatibility. It also verifies the engine revision and observed
cell name and records the image/binary/master identities. Raw logs, hashes and
screenshots are private.

To check a generated Android scene slice without accidentally supplying missing
files from the full archives, add `--scene-data /outside/android-preview-build/scene-data`.
This mounts only the master from the owner's Data directory and registers no
BSA archives. `--phone-qa` also runs the original Android diagnostic Lua script.
These options test visual dependency coverage and diagnostics on the desktop
0.52 reference runtime; they do not exercise the Android 0.51 binary or its GPU.

`--missing-player-model` deliberately points the template's player model settings
at a nonexistent path, reproducing the missing-head camera condition without
editing upstream assets. Compare a control run with one adding `--camera-repair`.
Use `--phone-qa` to record camera positions and mode. `--camera-motion` applies
bounded movement and turning for two seconds through the engine's control API.
That flag requires measured movement, turning and a camera within 256 units of
the player for probe success. These fault/motion scripts are desktop test tools;
the motion script is never included in the APK.

`--player-movement` replaces the short screenshot script with a native-player
walk/stop/jump/landing driver and a dense trajectory. It cannot be combined with
`--camera-motion`. `--movement-turn DEGREES` sets the initial relative heading;
`--movement-position X Y Z --movement-heading DEGREES` optionally places the
player once before testing a specific surface. These controls never enter the
APK. Trace completion and movement acceptance are reported separately;
horizontal response, stopping drift and jump/landing metrics exclude camera
motion and reject large respawn/teleport discontinuities. See
[player movement priority](../../docs/PLAYER_MOVEMENT.md) for current evidence,
blocked-route limitations and collision work.

This does not test Vulkan, a phone, quests, original animation, multiplayer,
performance or collision accuracy. Engine/asset support warnings remain part
of the evidence even when a screenshot is produced.


The original native stair fixture needs the public Template but no owner data:

```sh
python3 tools/upstream/probe_scene.py \
  --build-work /outside/upstream-work --template /outside/example-suite \
  --start OpenOblivionStairs --movement-fixture --player-movement \
  --movement-position 10000 -120 2 --missing-player-model --camera-repair --grounded-eye \
  --output /outside/evidence/stair-ascent
```

For descent use position `10000 650 322` and `--movement-heading 180`. Compare
with `--raw-eye` in a separate output directory to disable only the eye-height
filter. The generated plugin/COLLADA mesh stays in the external evidence
folder. Both runs still use native controls/physics, measure physical response
and report camera-height velocity variation separately. Healthy tracking must
remain untouched. These desktop comparisons do not replace phone comfort QA.
