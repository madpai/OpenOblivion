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

## Port: `tes4_grounded` receipt (opt-in, 2026-10-08)

`OPENOBLIVION_TES4_GROUNDED=1` (probe `--tes4-grounded 1`; needs `OPENOBLIVION_TES4_AIRBORNE=1` for the gravity). Receipt
`tools/native/tes4_grounded.py` after the airborne one, hash-locked for both engine vintages. It owns only
`apps/openmw/mwphysics/mtphysics.cpp` (an include and the call that runs the movement solver for an actor) and two new headers:
`tes4_grounded_law.hpp` (pure functions, unit-tested) and `tes4_grounded.hpp` (the wrapper). The solver still does all horizontal
work (walls, stepping up, sliding); the wrapper runs after it for the **player only** and replaces the vertical outcome: the host's
snap down to the ground (up to 64 units) is undone, the hull sweeps down 14 + 1.5 units to find the surface, and the law above
decides supported, hover, capture or fall. A takeoff, the host's own steep-slope state, swimming, flying and actors/water as the
surface keep the host's result. The launcher turns it on only when `files/preview-user/config/openoblivion-grounded.txt` contains
`1` (the feel is not confirmed on a device); `2`, the experimental sliding mode below, is reachable from probes only.

| Check | Result |
|---|---|
| The law against the recorded original | 4 recorded drops (15.1, 20.1, 25.1, 45.1 units above rest, 10 to 14 updates each, 44 to 52 ms steps) replay through `tes4GroundStep` with a residual below 0.05 units (rounding of the recording) and the identical ground/air state sequence, `tests/test_tes4_grounded.cpp` (277 checks) |
| Desktop jump, switch on (nominally 60 Hz physics) | rise unchanged at 66.7; captured about 9 to 14 units above the floor, then sinks 0.44 units per 50 ms sample (8.6 units/s = g*dt^2 per 1/60 s step) and rests after about 1.1 s; before: it snapped to the floor in the frame it entered the 2 unit range |
| Stair, ramp, wall, ceiling fixtures (mode 1, two runs each with the switch off) | walk ratio 0.777, grounded fraction 1.0, stop drift 0, jump heights 66.6 to 66.7 (ceiling 5.0), vertical-velocity variation 1075 to 1389 (the same few percent spread as before): **stairs are unchanged** because their contacts are steep and keep the host's handling |
| The original's Vilverin stairs, walked from the same start (heights at the flights' landings) | original 297.7 at y 340 and 258.3 at y 384; the port without the receipt 300 at y 341 and 257 at y 384 (z against y agrees within about 7 units); mode 1 the same within a few units |

**Mode 2 (sliding) does not reproduce the stairs and must not ship.** It keeps the state "ground" while accumulating `vz` on steep
hull contacts, as inferred above. On the Vilverin flight it left the hull 22 units above the treads and in the air for stretches (state
`a` in the probe), where the original stayed grounded the whole flight within a few units of the treads. The downward hull sweep does
not reliably report the steep normal at the top edge of a flight (the hull is still half over the landing), so the first steps after the
edge are classified as level and hover. The stair law needs the proxy's real classification (read its contact code) before it can be
ported.

Android (x86_64 emulator, same receipt-patched source as the arm64 library, marker file `1`): the engine logs `OpenOblivion TES4 grounded motion:
mode 1`; three jumps via `input keyevent KEYCODE_E` rise 61.24, 62.06 and 62.65 units with the receipt and 61.24, 62.05 and 62.66 without (the
spawn is on a slope), air time 0.934 to 0.936 s against 0.979 to 0.984 s (0.045 s shorter, as predicted); the spawn drop settles over about
a second at 8.7 units/s (z 305.98 to 297.74) instead of at once. The emulator gate passes with and without the marker.

What changes for the player with mode 1, so nobody reads it as a regression of the phone-confirmed 0.46:

- **Landings:** the jump log's `air time` ends at capture, 9 to 14 units above the floor while still falling at 230 to 260 units/s, so it
  is only about 0.05 s shorter than before (probe: first grounded sample at 8.01 s against 8.05 s without the receipt); the roughly one
  second of hover that follows is counted as grounded (jumping again during it is possible, as in the original) and the air-control
  phase ends at capture.
- **Hover:** after any jump or ledge drop shorter than 14 units the camera settles over about a second instead of at once. This is the
  original's law and matches its recorded 21 and 30 Hz behaviour, but the 60 Hz duration is an extrapolation; **it is the first thing
  to check on the owner's phone** (see PARITY.md).
- **Walking downhill on walkable ground changes the most, and is unmeasured on the original.** The host used to snap the hull to the
  ground every step; with the receipt the hull keeps its height, sinks 0.14 units per 1/60 s step and only falls once the ground is
  more than 14 units below, so on a slope that drops faster than 8.6 units/s it rides about 14 units above the surface and leaves
  the ground for stretches. Measured on the generated 28 degree ramp walked downhill from the top (`fx-rampdown-*`, desktop, 117 units/s,
  drop rate 62 units/s): without the receipt the hull follows the surface to within 0.5 units and is grounded 100% of the time; with mode 1 it
  is 0.8 to 20.2 units above the surface (mean 14.8) and grounded 35% of the time (state alternates ground, short fall, capture).
  The law predicts the same for the original at 60 fps (the glide per update is `g*dt^2`: 0.14 at 60 Hz, 1.2 at 21 Hz, so at the
  recorded 21 to 30 Hz a slope this gentle is followed almost exactly and nothing could be seen), but **no recording of the original on a
  walkable slope exists** (the exterior ran at 10 to 13 frames per second under software GL, too slow to say anything about 60 Hz).
  Decides whether mode 1 can become the default: measure the original walking down a walkable interior ramp at 30 Hz or more, or run
  it on hardware GL.
- **Not changed:** walking on the level, walls, stairs (steep contact), slopes judged steep by the host, swimming, NPCs.
- The host's physics step is nominally 1/60 s and grows under load (steps of 0.2, 0.07 and 0.02 s were logged while a cell
  loaded); the wrapper prepares the next velocity with the current step, which is exact at a fixed step and off by `g*dt*d(dt)` per
  step when it changes (hence the replay test passes the recorded next step).

## On the phone (0.46-jumplog, 2026-10-06)

The receipt writes one line per jump to the engine log (`OpenOblivion TES4 jump: rise ... units, air time ... s`); the phone keeps it
in the app's `preview-user/config/openmw.log` (`run-as`, the build is debuggable). This gave the first on-device check without a probe,
and it found a bug the desktop could not show:

- **Bug (fixed in 0.46):** at 120 fps the controller runs about twice per 60 Hz physics step. The frame after a takeoff still reported "on
  ground", so the bookkeeping treated it as a landing and reset the air state (log: `rise 0 units, air time 0 s` for every jump). A running
  jump would then have carried its takeoff velocity twice. A takeoff is now pending until the physics reports the air (at most 0.1 s), and the
  landing is only logged after the air was seen. Desktop probes cannot show this (they run below 60 fps); the phone is the test.
- **Check:** the phone's own 20 Hz position samples for a standing jump fit the original's law at 60 Hz physics within 2.7 units
  (model apex 66.8, air time about 1.0 s); the desktop probe logs `rise 66.77 units, air time 0.999 s`.
- **Confirmed on the phone with the fixed 0.46 (owner's three running jumps, on flat ground):** logged rise 66.8, 66.4 and 67.7 units
  (model at 60 Hz: 66.8), air time 1.07, 1.13 and 1.00 s; horizontal speed in the air 320 to 355 units/s, i.e. the run speed (355.6) kept, not
  doubled. A running leap therefore covers about 350 to 390 units (roughly 5 m), which is what the original's law gives (run speed kept for
  about a second, steering gain 0.015 per update). The owner's "too far" on the buggy build matches the doubled speed; standing jumps from a
  ledge read 61 to 63 units (a slope at the spawn point, not measured further).
- Lesson recorded in the compendium: per-frame bookkeeping in a controller that runs faster than the physics step sees stale ground state.

## Support range, landing capture and the sliding state (measured 2026-10-08)

Closes unknown 1 below for flat ground. Method as above (read-only 200 Hz sampler on the isolated original, per-update replay with the
logged `dt`); the trial placed the player 5 to 125 units above the base of the Vilverin stairs with `player.setpos z` and let it fall
(raw captures `evidence/tes4-motor-20261006/motor-drops{1,2,3}.json`, private). The game was run at 800x600 (about 21 Hz updates, `dt` 0.045
to 0.05) and at 320x240 (about 30 Hz, `dt` 0.033): the law below replays at both, so it is a function of `dt`, not of a fixed step.

| Law | Value | Evidence |
|---|---|---|
| Support range | the controller counts as **supported** while the ground is less than **2.0 Havok units (13.998 game units)** below its resting height. Placed 13.8 units above rest it stays grounded; at 14.0, 14.2, 14.5, 15.1 it leaves the ground (state 2) at the first update; 5.1 and 10.1 stay grounded | **verified** (bracket 1.9717 to 2.0003 Havok, 8 offsets, 2 trials each frame rate) |
| Grounded vertical velocity | while supported on level ground, every update sets `vz = -g*dt` (it does **not** accumulate); the hull therefore sinks `g*dt^2` per update (1.19 units at 48 ms, 0.56 at 33 ms, 0.14 at 16.7 ms, 0.036 at 8.3 ms) until it rests | **verified**, exact replay (position and velocity) on about 120 grounded updates |
| Capture | an airborne update whose pre-move height is inside the support range switches the state to ground **and keeps the velocity of that update** (no gravity added, no reset); the next update resets to `-g*dt`. Captured at 11.8, 13.7, 13.4 units (slow falls) and 9.1 to 11.1 units (fast falls, which cross the zone in one step) | **verified**, exact replay (e.g. the captured update moves by exactly the previous `vz*dt`) |
| Capture needs descent | rising updates after a takeoff are inside the range for several updates and stay airborne (state 2, `vz > 0`); capture only happens with `vz <= 0` | **verified** on the recorded jumps (runjump trace, takeoff updates) |
| Fast falls | the hull is not stopped at the surface: 25 units/update falls pass through the floor by about 1.5 units, then the controller pushes it back up by 0.07 units per update (penetration recovery) | observed, not modelled |

Consequence at the port's 60 Hz physics (computed from the law, not measured): after a jump the player is captured about 14 units above
the floor and then sinks 0.14 units per step (8.6 units/s, about 1.6 s to rest); stepping off a ledge lower than 14 units hovers and sinks
the same way; gentle downhill ground (drop rate above 8.6 units/s at walking speed) alternates hover, a short fall and capture. The original
at 60 fps should do the same; **no measurement of the original above 30 Hz exists**, so the hover duration at 60 Hz is an extrapolation. It is
the first item on the owner's feel list in [PARITY.md](../PARITY.md).

**The stairs are a second ground behaviour, not covered by the reset rule.** In the recorded stair descents (`motor-runjump-a`, `motor-run-a`)
the state stays 0 while `vz` accumulates by `g*dt` per update (ratio -1.96, -2.91, -3.99 ... -10.5 over ten updates, position steps 1.3 to
6 units), then resets to `-g*dt` on the level landing; the horizontal speed on those contacts is 12.8 Havok units/s against 16.76 on level
ground. Flat-floor hover and level walking read `-1.00` every update. The controller flags (`fl` 0x708/0x70c on the stairs, 0x700 and 0x708 on
the level) and the proxy's own velocity field do not separate the two cases. **Inferred (not verified):** the support check classifies the
surface it finds like Havok's character proxy does, as supported, sliding or unsupported; the measured hull is a cone 40 units wide, so on
stair nosings the contact normal is steeper than the walkable limit (inclination about 58 degrees) and the state is "sliding" (the velocity keeps
accumulating); on level ground the apex contact is flat and the velocity resets. The port's body receipt judges walkability from the centre of
the hull instead (see TES4_PLAYER_BODY.md), which is why stair descent is a ramp there. The compendium finding
`oblivion-grounded-state-falls-under-gravity` holds for stairs and is **contradicted for level ground** by the hover data above.

## Unknowns and next measurements

1. ~~The support check range~~ measured above (2.0 Havok units). Still open: the **sliding** classification (slope limit and contact
   normal rule, only inferred), the support range on slopes and stair nosings, and the original above 30 Hz. A 125-unit drop kills the
   level-1 player: restore health (`player.restoreav health 1000`) between drops, or the game returns to the main menu.
2. Step height and slope limit (not found as numbers; likely emergent from the hull and the support check).
3. Air-control gain at other Acrobatics values on flat floor (Acrobatics 100 was consistent with 0.3 but measured on stairs).
4. Fall damage thresholds (`fJumpFall*` settings exist), fatigue per jump, encumbrance, swimming, NPC and creature values.
5. Frame-rate dependence: the original at 60 fps (needs hardware GL) to confirm the 66.8 apex directly.

Do not repeat: judging the jump from a single apex number, from wall-clock curves, or from a trial under a ceiling; setting
the jump from the Morrowind formula; porting only the speed formula and calling the motor done.
