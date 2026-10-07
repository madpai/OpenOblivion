# Classic TES4 airborne motion: jump, gravity, air control (and what the original does on the ground)

Date: 2026-10-06. Closes the "jump, gravity and fall are borrowed Morrowind numbers" gap listed in
[TES4_PLAYER_BODY.md](TES4_PLAYER_BODY.md) and [TES4_MOVEMENT.md](TES4_MOVEMENT.md), and verifies the run branch of the
ground-speed formula that was only static until now. Evidence levels: **static** (read from the executable),
**verified** (measured on the running original), **inferred**, **guessed**. Offsets and addresses stay private.

## How it was measured

The owner's retail Steam copy ran unchanged under Proton on an isolated display (containerised Xvfb and a window
manager), offline, with its own user folders. A separate read-only process sampled the player's character controller at
200 Hz: position, state, requested state, velocity, the controller's own last step time `dt`, the Havok world's
gravity vector and the phantom centre. Nothing was written to the process. Input was real keyboard events with
timestamps from the same clock, plus console commands for placement. Samples were collapsed into the game's own updates
(a new update is any change of state, position or velocity) and each candidate law was **replayed over every update with
the `dt` the game logged**. If the law is right the residual is zero. The method is written up for reuse in the
[compendium](https://github.com/madpai/game-decomp-compendium) (technique note "replaying a character controller from its
own timesteps"). Raw captures stay private (`evidence/tes4-motor-20261006`).

## What the original does

| Law | Value | Evidence |
|---|---|---|
| World gravity | (0, 0, -73.575) Havok units/s^2 = 9.81 x 7.5; 514.95 game units/s^2 (Havok unit = 1 / 0.1428767293691635 game units, the executable's own constant) | **verified** (read from the live Havok world) |
| Integration | every controller update: `vz -= g*dt`, then `z += vz*dt` with the update's own `dt` (semi-implicit Euler, no fixed sub-step) | **verified**: exact replay (0.000 residual in position and velocity) on 75 + 28 + 18 airborne updates of three traces, including one 166 ms frame |
| Jump height | `h = fJumpHeightMin + (fJumpHeightMax - fJumpHeightMin) * Acrobatics / 100` (64 and 164, so 69 for the player's Acrobatics 5); the controller field held 9.8585 Havok = 69.0 units | **static** formula, **verified** at Acrobatics 5, 50 and 100 (controller field 9.8585, 16.2879, 23.4318 Havok = 69, 114, 164 units; first airborne velocity minus one `g*dt` agrees to four decimals each time, replay residual about 4e-6) |
| Takeoff | vertical speed `sqrt(2 g h)` = 266.58 units/s; the horizontal velocity at the moment of the jump is kept (no reduction when moving) | **static**, **verified**: first airborne velocity minus one `g*dt` agrees to four decimals on three jumps |
| Air control | each update the horizontal velocity relaxes toward the wanted ground velocity: `v += f * (wanted - v)`, `f = fJumpMoveBase + fJumpMoveMult * Acrobatics / 100` = 0 + 0.3 * 0.05 = 0.015 | **verified** at Acrobatics 5: exact replay on a jump from a walk (28 updates, wanted 117.3); the same +1.2 per update was seen at run speed (wanted 355.6). At Acrobatics 100 the first mid-air step from rest gained 0.289 and later steps 0.28 to 0.29 (predicted 0.3; the stair contact lowers the wanted velocity), so consistent but not an exact replay |
| Controller states | 0 on ground, 1 jumping (one update, no motion), 2 in air; a separate request field uses 11 for "none" | **verified** for 0, 1, 2 |
| Run speed | 355.6 units/s with Speed 40 and Athletics 5, weapon sheathed: the controller's first velocity after Shift+W | **verified** (the formula's run branch was only static before) |

Consequences that explain earlier confusion: because the step is the frame time, **the realised apex depends on frame rate**
(69.0 in the continuous limit, 66.8 at 60 Hz, 64.4 at 35 ms updates, 62.5 at 50 ms). Every standing jump recorded under
software GL reached 64.0 to 64.4 units, which looked like "jump height 64" (the minimum setting) but is the formula's 69 at 35 ms steps. A jump
under a ceiling reads lower still (a first trial capped at 32.7 units in the start corridor and was discarded).
Air control is weak by design (0.015 per update) but not negligible: from the law, at 60 Hz a jump from rest with the
key held reaches about half the walking speed by landing (computed, not measured).

### Observed on the ground (not ported)

- **Gravity is applied on the ground too.** In the grounded state the controller adds `g*dt` to the vertical velocity every
  update and the contact solve resets it; descending a stair flight is therefore a free fall per tread (about 38-unit drops
  taking about 11 updates at 35 ms, vertical speed climbing 2.6 Havok units/s per update) **without the state ever leaving
  the ground state**. Drops of about 38 units never became "in air".
- **Landing capture.** After a jump the state switched to ground about 15 to 17 units above the final rest height (two
  update-steps of travel at that frame rate), vertical velocity was replaced by `-g*dt` and the hull then glided down at
  about 18 units/s for about a second. The hull is a fixed 71 units above the reference position throughout, so this is the
  body, not a lagging reference point. Cause not recovered: it follows the proxy's support check (a flag set after each
  integration from the proxy's supported state), whose range was not read.
- Horizontal speed on stair contacts is reduced by the contact (89.7 against 117.3 on the steep part, 110.2 on treads).

These are the facts behind the stair "ramp versus steps" question in [TES4_PLAYER_BODY.md](TES4_PLAYER_BODY.md); they are
recorded as oracle data, and **the port does not yet follow them** (see the next section).

## Port: `tes4_airborne` receipt (opt-in)

`OPENOBLIVION_TES4_AIRBORNE=1` (probe flag `--tes4-airborne`, set by the Android launcher beside the other switches).
Receipt `tools/native/tes4_airborne.py` after the trees receipt, hash-locked for both engine vintages; header
`tools/native/tes4_airborne.hpp`; fixtures `tests/test_tes4_airborne.cpp` (19 checks) and the receipt checks in
`tests/test_native_build.py`.

- `components/misc/constants.hpp`: `Constants::GravityConst` becomes a value that converts to float and picks the
  original's gravity when the switch is on (the physics solver and every other use keep working unchanged).
- `apps/openmw/mwmechanics/character.cpp` (player only): takeoff keeps the horizontal velocity and launches at
  `sqrt(2 g h) - g/60` (the solver integrates explicitly, so one step of gravity is carried to reproduce the original's
  order); in the air the controller feeds the solver `V - takeoff` where V relaxes toward the wanted velocity by the gain
  above, per controller update. Walking off an edge starts from the last ground velocity.
- The body receipt's solver is untouched. Stand-ins: Acrobatics 5 (the master's Player record) until TES4 stats exist;
  NPCs keep the donor's jump numbers but fall under the same gravity; no fatigue cost, fall damage or swimming.

### Port results (desktop, same binary, switch off then on; evidence `air-base-*`, `air-fix-*`)

| Probe | Switch off | Switch on | Original |
|---|---|---|---|
| Standing jump rise (flat floor, 60 Hz physics) | 78.0 | **66.7** | 66.8 modelled at 60 Hz (64.4 recorded at 35 ms) |
| Gravity fitted from the jump trajectory (units/s^2) | 620.3 | **513.6** | 514.95 |
| Trajectory against the original law with a free takeoff time (17 samples) | not run | max 1.8, apex 0.08 | |
| Jump height on the generated stair, ramp, wall fixtures | 77.9 to 78.0 | 66.6 to 66.8 | |
| Walk distance ratio, stair ascent / descent | 0.777 / 0.777 | 0.777 / 0.778 | |
| Stair vertical-velocity variation, ascent (two runs each) | 1377.9, 1419.3 | 1398.9, 1402.4 | |
| Stair vertical-velocity variation, descent (two runs each) | 1134.0, 1140.5 | 1178.7, 1157.2 | |
| Wall blocks; low ceiling blocks the jump; walk, stop and jump gates | pass | identical | |

The only drift in the regression rows is the descent variation (+1.5 to +3.4%), which starts with a settle fall under the
new gravity; run-to-run spread of this diagnostic is a few percent. 25 of 25 CTest suites and the content guard pass.
The 20 Hz probe samples are not aligned with the 60 Hz physics, so a 1 to 2 unit residual in the trajectory comparison is
sampling phase. Android: the same receipt is applied to the donor tree; see HANDOFF for the build state.

## Unknowns and next measurements

1. The **support check** (range and rule that make the ground state persist through a 38-unit drop and capture a landing 15
   units early). It decides stair descent feel, ledge walk-off and fall damage. Read the proxy's support code, then sample
   drops of 10, 20, 40, 80 and 120 units to find where ground becomes air.
2. Step height and slope limit (not found as numbers; likely emergent from the hull and the support check).
3. Air-control gain at other Acrobatics values on flat floor (Acrobatics 100 was consistent with 0.3 but measured on stairs).
4. Fall damage thresholds (`fJumpFall*` settings exist), fatigue per jump, encumbrance, swimming, NPC and creature values.
5. Frame-rate dependence: the original at 60 fps (needs hardware GL) to confirm the 66.8 apex directly.

Do not repeat: judging the jump from a single apex number, from wall-clock curves, or from a trial under a ceiling; setting
the jump from the Morrowind formula; porting only the speed formula and calling the motor done.
