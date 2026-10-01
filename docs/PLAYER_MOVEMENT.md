# Player movement priority

The owner requested that engine work prioritize actual in-game player movement.
The existing scene preview is a test harness for the player controller and
content collision. A camera-only stair treatment cannot fix forward movement
catching on the steps.

On 2026-10-01 the owner reported walking, stopping, ordinary collision, jumping
and look working in the tested phone scenes. Stairs have both bounce and forward
catching/slowing. These are owner observations, not a timed collision corpus or
an animation/performance pass. Keep 0.3 as the working phone baseline.

The original `--player-movement` desktop probe drives the existing native player
controls through five seconds of walking, stopping, jumping and landing. It
records player position, ground state and expected walk speed up to 20 times
per simulation second. It does not animate the camera or move the actor by
teleporting each frame. Optional initial placement selects a particular surface
before the test starts; the subsequent path is solved by upstream physics.

```sh
python3 tools/upstream/probe_scene.py \
  --build-work /outside/upstream-work --template /outside/example-suite \
  --data '/your/Oblivion/Data' --start Vilverin \
  --output /outside/evidence/player-stairs \
  --player-movement --movement-position X Y Z --movement-heading 180 \
  --missing-player-model --camera-repair
```

Coordinates are scene-specific test placement, not a public fixture or a new
spawn rule. `--movement-turn` applies an initial relative turn through player
controls. Placement, driver and raw trajectories stay out of the phone APK.

Probe completion means a complete trace and clean requested-cell run. Separate
metrics report horizontal distance, requested-distance ratio, time below 25%
of requested walking speed, vertical range, grounded fraction, stopping drift
and jump/landing. Movement requires horizontal travel; vertical-only motion or
camera motion cannot pass. A wall/door can correctly block a route; failed
walking/jumping there is not automatically a controller defect. A large
trajectory discontinuity invalidates movement acceptance, preventing respawn
or teleport from counting as traversal. The analyzer never declares general
collision fidelity from one trajectory.

Acceptance thresholds are authored diagnostics, not recovered engine constants:
walking response requires over 50 units, 50..125% of requested distance and
less than 20% severely slowed time; stopping allows under one horizontal unit
after a 0.2-second grace period; jump/landing requires over ten vertical units
and a final grounded state. Discontinuity detection allows 128 units plus four
times requested speed over an interval. Results depend on route clearance and
must be assessed with its geometry and trace.

The first stock exterior path covers about 729 units at 99% of requested
horizontal distance, with 0.33-unit stopping drift and a 113-unit jump followed
by landing. The default interior route is obstructed. Initial selected-stair
placements also give an invalid fall/reset or obstructed route; neither is a
successful ascent/descent reproduction. Preserve that evidence and correct
test placement before attributing the owner's catching to a particular solver
branch.

The pinned 0.51 and 0.52 collision loaders generate TES4 collision from visible
geometry and skip the authored Bethesda Havok collision shapes. See the
[0.51 loader](https://github.com/OpenMW/openmw/blob/f4bec41444214a7903bebd178389ca22ca13f646/components/nifbullet/bulletnifloader.cpp#L121)
and [0.52 loader](https://github.com/OpenMW/openmw/blob/46bd4599203ee52ffc0f3e8edb3fc159a0303a49/components/nifbullet/bulletnifloader.cpp#L134).
Private stair inspection finds separate `bhkMoppBvTreeShape` /
`bhkNiTriStripsShape` geometry with fewer vertices than its visible counterpart.
This is a concrete compatibility gap and a candidate contributor to catching;
it is not yet a proven explanation of the owner's stair issue.

The next controller work should proceed in this order:

1. Reproduce ascent/descent on identified stair placements; compare commanded
   travel with the solved player path, ground transitions and clearance.
2. Create original collision fixtures with deliberately different visible and
   authored surfaces. Audit a bounded static TES4 collision path: strip geometry,
   node/body transforms, units, layers and unsupported-shape fallback. Reuse
   existing NIF decoding and Bullet queries; no proprietary physics binary.
3. Compare that collision path against the stock fallback on the same route.
   Then change step-up/down or grounded velocity handling when the traces
   identify a controller defect. Include short/tall steps, ramp, ceiling, wall,
   descent, jump/landing and stopping regression cases.
4. Integrate a verified change into the Android native runtime and repeat phone
   stair traversal. Keep the working walk/stop/jump baseline and measured scope.

Rendering polish, viewer expansion and camera filtering are lower priority than
these controller/collision gates. Skeletal animation remains separate work.
The eventual server validates movement commands and owns accepted positions;
this desktop driver is not a multiplayer authority implementation.
