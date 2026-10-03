# Classic TES4 player body: measurement and native integration

Date: 2026-10-03. This closes the "character body is unknown" gap recorded in
[HAVOK_COLLISION.md](HAVOK_COLLISION.md) and [PLAYER_MOVEMENT.md](../PLAYER_MOVEMENT.md).
It does not establish original motor, gait, run speed or step parity.

## How it was measured

The owner's classic installation was copied to a private reference directory
and run unchanged under Proton on an isolated virtual display. Its user folders
were redirected away from the owner's documents. Input went through XTEST
using the unchanged original key bindings. A read-only sampler read the
running process memory (`/proc/<pid>/mem`) at 20 Hz: the player reference, its
character controller, the controller's Havok phantom and its shape. No game
file was modified and nothing from the executable is published. The raw
captures, scripts and disassembly notes are private under
`evidence/tes4-controller-executable-20261003`.

States sampled: standing, walking down the Vilverin entrance stairs, jumping,
sneaking on and off, turning, and resting at three separate points on the floor.

## Measured facts

Units: Havok values are converted with the executable's own scale constant
`0.1428767293691635` (stored next to the constant `18.28822135925293`, which
is 128 game units). Game units are given in brackets.

| Quantity | Havok | Game units |
|---|---:|---:|
| Shape | 18-vertex convex hull (vtable `0xa99f28`) | |
| Ring radius (8 vertices per ring) | 2.893253803 | 20.25 |
| Lower ring height from centre | −4.614932060 | −32.30 |
| Upper ring height from centre | +7.697484016 | +53.875 |
| Apexes | ±9.144110680 | ±64.0 |
| Total height (controller field) | 18.28822136 | 128.0 |
| Convex radius | 0.1 | 0.70 |
| Hull centre above the reference position | | 71.0 (constant in every sample) |

- The hull is an eight-sided prism with a pointed cone at each end. Its
  diagonal vertices sit 1.96e-5 Havok units inside the exact ring, consistent
  with the executable's own cos 45° rounding.
- Shape, radius and height are **identical** while standing, walking, jumping
  (controller states 0/1/2) and sneaking. Sneak does not shrink the body.
- The hull **rotates with the player's heading**: at heading 0.4 rad the
  phantom rotation rows are (0.921, −0.389) / (0.389, 0.921).
- The controller's contact manifold (proxy `+0x74`, 48-byte points) reports
  a horizontal support plane directly beneath the hull apex. On flat floor, at
  three separate resting points, that contact lies 2.88–2.98 units above the
  reference position with a reported distance of 0.474–0.489 Havok units
  (3.3–3.4 units). On the stair edge a second, steep contact (normal
  0, 0.861, 0.509) touches the cone face while the flat support stays under
  the apex.

## Inferences (not measurements)

- Taking the contact point as the floor's outer surface (including the
  floor's own 0.70 convex radius), the reference position sits about
  2.25 units below the floor triangles, and the hull's lowest point floats
  about 4 units above them. The port rests its shape one unit above the floor
  and its reference on the shape's lowest point, so its reference is about
  3.25 units higher than the original's on flat floor. The Vilverin starting
  landing agrees: the port settles at Z 513.0 where the original rests at 509.7.
- The cone resting on tread edges, with support judged under the apex, is what
  makes the original's stair motion a ramp rather than discrete steps.

## Unknowns

The original controller's stepping, maximum step height, slope limit, gait,
run speed, acceleration, jump impulse, swimming and how race height scale
alters the hull are not measured here. The float between hull and floor is
measured but not reproduced.

## Implementation

`tools/native/tes4_body.hpp` builds the hull from the measured Havok values and
scale, with the convex radius as the Bullet margin. `tes4_body.py` applies a
hash-locked patch, chained after the door receipt, to `actor.cpp`,
`movementsolver.cpp` and `stepper.cpp` in both the desktop and Android engine
trees. With `OPENOBLIVION_ORIGINAL_BODY=1` only the player gets the hull, as a
rotating shape with half extents 20.95 × 20.95 × 64.70. Other actors are
unchanged.

The hull alone exposed a defect in the host solver. The cone's contact with a
tread edge is steeper than the walkable limit, so the normal step-down fails
and the inherited Morrowind "extra stair hack" moves 10 units per frame. On
the original stair fixture that made the player climb at 440–480 units/s
(distance ratio 1.42). The patch therefore judges walkability for the hull
only from the surface directly beneath its centre, matching the measured
support under the apex. This applies in the stepper's step-down test and the
solver's ground test. Missing support, or support beyond the apex plus the 34-unit
step reach, falls back to the contact normal. The 34/62 step constants,
gravity, speeds and the 0.5 camera filter are unchanged. The Android shell
sets the switch alongside authored collision and the camera filter.

## Desktop evidence

Same recorded binary for every row, software GL, one async physics worker,
the Android player model and settings rewrite. "Variation" is the existing
`walk_player_vertical_velocity_variation` metric (lower is smoother).

| Route | Box (template) | Measured hull |
|---|---:|---:|
| Original stair fixture, ascent | 2,127.6 | **1,469.4** (−31%) |
| Original stair fixture, descent | 2,338.5 | **1,547.8** (−34%) |
| Vilverin entrance stairs, authored collision | 2,533.9 | **1,448.1** (−43%) |
| Vilverin height vs original's own Z(Y) samples: mean / median / RMS | +6.58 / +10.0 / 8.44 | **−0.30 / +0.72 / 5.23** |
| Low-ceiling stair fixture (150 units above treads) | blocked (distance ratio 0.24) | passes (0.97) |
| Ramp fixture variation | 82.6 (earlier run) | 91.1 |
| Wall fixture | blocked as designed | blocked as designed |
| Vilverin gate, closed / open / closed ray hits | 21 / 0 / 21 | 21 / 0 / 21 |
| Gate: body stops at local Y while closed | −18.28 | −25.92 |
| Gate: crosses after Open to local Y | +374.6 | +372.3 |

All walk, stop and jump/landing gates pass on every route except the wall,
which blocks by design. Peak horizontal speeds stay within 163–177 for both
bodies. The hull stops 7.64 units earlier at the closed gate, the radius
difference (20.95 − 13.31). Box-body variation differs between repeated runs
(2,379 vs 2,128 on ascent), so compare rows rather than single digits.
The original's own stair walk moved at 82 units/s while the probe moves at 150,
so the height comparison is approximate. The default NPC idle (5 NPCs, two
loops) and container window/Close regressions also pass with the switch on.

Evidence: `evidence/tes4-body-final-*` (final binary), `tes4-body-*-01/-02`
(development runs, including the rejected hull-only build) and
`tes4-body-20261003` (receipts, public build/test logs, APK build logs).

Reproduce with the recorded build and `tools/upstream/probe_scene.py`, adding
`--original-body` (requires `--native-manifest` and `--player-collision-model`).
`--authored-collision` enables the fixed-strip loader for a movement run
without the door driver.

## Private packages and acceptance

The phone packages enable the hull. `0.20-fit`/`0.21-installed-fit` remain
the recovery builds with the template box.

| Package | Bytes | SHA256 |
|---|---:|---|
| 0.22-body single APK, versionCode 22 | 667,765,887 | `05e64000ad986f62a8c90b9dd9f754d89dc7635a9922365c655bae73ffc8616c` |
| 0.23-installed-body complete ZIP, versionCode 23 | 5,569,260,819 | `1809edf31133846fa91db012d3997e0567dff77e313100996a6eec44b67907fc` |

Native `libopenmw.so` (debug-stripped, symbols kept) is
`45f4928ca31b76b366aca00f74a89cc43407492f7819ffb1905babb27e0a401a`; the desktop
engine is `18808a649243ec35762b0e9f28c43cd8e0e2e87fc26c44ad384ab69baf74fc05`.
Payload IDs are unchanged from 0.20/0.21 (`3739014d…` single, `75eee511…`
complete). Signer `4e74a9af…`, alignment, CRCs, the six nested APK hashes and
split versionCodes pass. The emulator install check was not repeated: only the
engine library, one launcher environment line and the version changed. One
complete-set build failed its own CRC check on this host's known faulty RAM
and was rebuilt; the delivered set passes. Phone acceptance is pending. Compare stairs both ways with
0.20 for comfort, check the gate in both directions, corridors, low ceilings,
jumping and sneaking. This is a measured-body checkpoint, not a 1:1 motor.
