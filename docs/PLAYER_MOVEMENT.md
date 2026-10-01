# Player movement priority

The owner requested that engine work prioritize actual in-game player movement.
The existing scene preview is a test harness for the player controller and
content collision. Smooth travel up and down stairs is the target; the owner's
latest feedback accepts subtle stepping when it feels comfortable.
Keep solved player motion and eye-height presentation measurable separately.

On 2026-10-01 the owner reported walking, stopping, ordinary collision, jumping
and look working in the tested phone scenes. The earlier answer described some
catching/slowing; the owner then clarified that ascent/descent works and the
main problem is a vertical camera jolt on each tread in both directions. This
clarification supersedes treating failed traversal as the established defect.
These are owner observations, not a timed collision corpus or animation pass.
Build 0.3 remains the archived working phone baseline.

## Latest phone feedback and next steps (2026-10-01)

On **0.5-native-stairs**, the owner now describes stairs as very smooth, with
almost realistic stepping they like. Preserve that feel as the current
reference. They also report swimming working and a breath indicator appearing.
These are qualitative observations; swim transitions, breath depletion/recovery
and drowning behavior have not been systematically tested.

The latest `OO-ANDROID-005` upload matches the served 0.5 APK hash and logs
native grounded-eye enablement, actor-root fallback activation, changing player
positions and touch look. Its selector says interior, but the log starts in
VilverinExterior and records exterior travel. Its 400 bounded samples are not
a controlled stair comparison. Device/model and Android fields are blank;
there are no attached screenshots. Stair comfort comes from the owner's chat
feedback, independently of the desktop variation measurements.

One-to-one Oblivion movement, including stair contact, is not the current
target. The pinned runtime still builds static collision from visible geometry
and skips authored Havok shapes. A read of the owner master found Player
`00000007` (Imperial `00000907`, height 1, Speed 40, Athletics 5, Acrobatics 5)
and the present settings `fMoveCharWalkMin/Max` 90/130, `fMoveRunMult` 3,
`fMoveNoWeaponMult` 1.1, `fMoveEncumEffect` 0.4, `fMoveWeightMax` 150,
`fMoveSneakMult` 0.6 and `fJumpHeightMax` 164. `fJumpHeightMin`,
`fMoveRunAthleticsMult`, the unworn encumbrance setting, and the swim and
air-control settings are absent from that master and from `Oblivion_default.ini`.
Applying the published defaults on top of the current motor would change speed
and jump without making stair collision match. The 0.5 stair filter stays as
the owner left it.

Preview **0.7-controls** does not change walk speed, jump height, gravity,
collision, or the stair filter. On this engine Space activates and E jumps, so
the lower-right button is USE and the button above it is JUMP. The 0.7 log
stays near 151 units per second, so the Caps Lock pulse did not change gait.
Preview 0.8 holds Shift for run and pins always-run off. Its phone log still
has no second gait: median 149.9 and maximum 165.1 across 357 grounded moving
samples. 0.6, 0.7, and further binding experiments are withdrawn. Water entry,
breath, and drowning remain untested. Further speed and binding changes are
blocked until authored collision is measured. See
[Havok collision](research/HAVOK_COLLISION.md).

Animation and broader viewer work follow the dependable player baseline.
The 0.8 phone control change is the host overlay and a small settings pin. The movement probe and
stair filter are unchanged.

The original `--player-movement` desktop probe drives the existing native player
controls through five seconds of walking, stopping, jumping and landing. It
records player position, ground state, expected walk speed and camera/tracked
height up to 20 times per simulation second. It does not move the actor by
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
test placement before attributing the owner's issue to a particular solver
branch.

The pinned 0.51 and 0.52 collision loaders generate TES4 collision from visible
geometry and skip the authored Bethesda Havok collision shapes. See the
[0.51 loader](https://github.com/OpenMW/openmw/blob/f4bec41444214a7903bebd178389ca22ca13f646/components/nifbullet/bulletnifloader.cpp#L121)
and [0.52 loader](https://github.com/OpenMW/openmw/blob/46bd4599203ee52ffc0f3e8edb3fc159a0303a49/components/nifbullet/bulletnifloader.cpp#L134).
Private stair inspection finds separate `bhkMoppBvTreeShape` /
`bhkNiTriStripsShape` geometry with fewer vertices than its visible counterpart.
This is a concrete compatibility gap and a candidate contributor to uneven physical movement;
it is not yet a proven explanation of the owner's stair issue.

Remaining physical collision/controller work, when a separate defect is reproduced:

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

Rendering polish and viewer expansion remain lower priority than player travel.
Skeletal animation remains separate work.
The eventual server validates movement commands and owns accepted positions;
this desktop driver is not a multiplayer authority implementation.

## Grounded stair eye-height experiment (unshipped)

The preview's missing-head fallback follows native actor-root height directly;
head bobbing is already disabled. The original stair generator creates a clear
route with twenty 16-unit rises and 24-unit treads. Native controls and Bullet
solve the path; neither the fixture nor the driver supplies per-frame positions.
Use `--movement-fixture --start OpenOblivionStairs` without owner `--data`, with
initial position `10000 -120 2` for ascent, or `10000 650 322` and heading 180
for descent. `--grounded-eye` explicitly enables the experiment; `--raw-eye` supplies the comparison's zero-offset filter. Generated
plugin/mesh files remain in the external evidence directory.

The independently authored Lua filter applies a bounded vertical focal offset
only while the missing-head fallback is active and the player is grounded. Its
100 ms exponential response targets per-tread jolts; lag is capped
at 48 engine units. Jump intent, airborne motion, swimming, cell changes, large
position changes, pauses and long frame gaps reset it immediately. Healthy
first-person tracking is untouched. Native camera collision tests stay active,
and the filter does not modify player position, movement commands or look.

The player body still traverses physical treads. This is a treatment of the
reported eye-height bounce, not ramp collision generation or a new stair motor.
Forward slowing, if reproduced separately, still requires a physical fix. The real
Vilverin ascent comparison regresses, so this version is withheld from phone
QA. The engine invokes Lua `onFrame` before physics and the camera update; a
height correction calculated there can arrive out of phase with the solved
step. This inference fits the increased ascent variation. A post-physics
presentation path is required before it can become the default.
`OPENOBLIVION_STAIR_QA` adds bounded movement/view samples in the opt-in probe; the
desktop probe compares vertical velocity variation as a diagnostic of tread
jolts, independently of walking/stopping/jumping acceptance.

## Native post-physics comparison

The independent filter now has a C++ implementation applied by a small audited
camera patch in an external integration checkout. It samples the tracked root
inside the camera position update, after physics/world transforms, and adds
its vertical correction before the original native focal/camera sphere casts.
An environment switch enables it only for zero-distance actor-root views.
The unchanged reader and stock desktop baselines remain separate.

Native desktop comparisons use the same integrated binary with smoothing
enabled/disabled, the existing controls driver and the same initial placement.
Measured 2026-10-01:

| Route | Raw view velocity variation | Native smoothed variation | Reduction |
| --- | ---: | ---: | ---: |
| Original 20-step ascent | 2347.48 | 528.79 | 77.5% |
| Actual Vilverin entrance ascent | 1321.40 | 535.69 | 59.5% |
| Actual Vilverin entrance descent | 2266.39 | 546.82 | 75.9% |

The three paired routes pass walking response, stopping and jump/landing.
Real Vilverin walking ratios are 1.009/1.016 uphill and 0.995/0.994 downhill
(raw/native). Runtime cadence varies; these diagnostics are not perceptual
comfort scores or Android performance measurements. The native correction
does not show the earlier real-ascent Lua regression in these comparisons.

Separate original descent/ramp routes pass movement gates. An original wall
stops the body 10.26 units before its front face, while stopping and jumping
remain valid; blocked walking correctly fails its walking-response gate.
On low-ceiling stairs, 58 walking samples retain at least 10 units of vertical
view clearance. This verifies those fixtures, not all TES4 collision shapes.
Native fallback look motion covers about 301 units with changing yaw; healthy
first-person tracking does not activate the fallback. The C++ trajectory suite
checks 3,817 assertions across stair directions, frame cadences, ramp response
and transition resets.

Private evidence names are `native-stair-ascent-{raw,smoothed}-05`,
`native-vilverin-{ascent,descent}-{raw,smoothed}-05`,
`native-surface-{stairs,ramp,wall,ceiling}-05`, `native-look-control-05` and
`native-healthy-tracking-control-05`. Native source/build instructions are in
[tools/native](../tools/native/README.md). The latest owner phone feedback now
supports stair comfort on 0.5, separately from these desktop metrics. Further
motor tuning is blocked on [HAVOK_COLLISION.md](research/HAVOK_COLLISION.md).
The 0.5 stair filter stays until an authored-collision trace exists.
