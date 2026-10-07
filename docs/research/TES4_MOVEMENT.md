# Classic TES4 player ground speed

Date: 2026-10-03. Owner report: sneak did nothing and run felt the same as walk.

## Cause

The borrowed engine picks run or sneak speed only when the character animation
state machine is in a run or sneak state. The preview player has no TES4
locomotion animations (the template `basicplayer.dae` body fails to load on
Android and desktop), so the state never changes and the player always moved
at the borrowed Morrowind walk speed, 150 units/s. A desktop probe reproduces
it: requested walk, run and sneak all measure `current_speed=150` while the
engine reports a run speed of 337.5.

## Original formula (measured)

The original executable's character speed routine (`0x547c00`, run wrapper
`0x547d00`) computes, with the settings it registers at startup:

```text
walk  = (fMoveCharWalkMin + (fMoveCharWalkMax - fMoveCharWalkMin) * Speed * 0.01)
        * (1 - encumbranceEffect * normalizedWeight)
walk *= fMoveNoWeaponMult      when no weapon is drawn
walk *= fMoveSneakMult         while sneaking
run   = walk * (fMoveRunMult + fMoveRunAthleticsMult * Athletics * 0.01)
```

Values: the owner's master overrides fMoveCharWalkMin/Max 90/130, fMoveRunMult
3, fMoveNoWeaponMult 1.1 and fMoveSneakMult 0.6. fMoveRunAthleticsMult is
absent from the master; the executable registers 1.0 (`fld1`). Its own
defaults for the overridden settings differ (no-weapon 1.2, sneak 0.75) and
are not used. The master's Player record has Speed 40 and Athletics 5.

| Starting player | Walk | Run | Sneak walk | Sneak run |
|---|---:|---:|---:|---:|
| Weapon sheathed | 116.6 | 355.6 | 70.0 | 213.4 |
| Weapon drawn | 106.0 | 323.3 | 63.6 | 194.0 |

An earlier private sample of the original walking down the Vilverin stairs
peaked at 117.3 units/s, consistent with the sheathed walk.

## Implementation

`tools/native/tes4_movement.hpp` and the hash-locked `tes4_movement.py`
receipt (after the body receipt) patch `Npc::getMaxSpeed` so that, with
`OPENOBLIVION_TES4_MOVEMENT=1`, the player's ground speed uses this formula and
the run/sneak stances directly. Swimming and levitation keep the existing
paths. The phone shell sets the switch. Desktop probe, same binary: walk
116.6, run 355.6, sneak 70.0 units/s (`evidence/tes4-gait-*-02`).

Update 2026-10-06: the run branch is now **verified** on the running original: the controller's first
velocity after Shift+W reads 355.6 units/s (Speed 40, Athletics 5, weapon sheathed), exactly the formula's value. Jump,
gravity and air control are recovered and ported separately ([TES4_AIRBORNE.md](TES4_AIRBORNE.md)).

Not yet modelled: carried weight (treated as unencumbered), changing
attributes/skills, the athletics/acrobatics skill use, swim speed and the sneak camera height. Other actors keep the
borrowed speeds.

## Start location

Phone builds from 0.27 add "Sewer exit (game start)", the default first
button. It starts in `ICPrisonSewerExit01` and a launcher overlay script moves
the player to the original prologue exit door destination
(47073.2, 82958.1, 301.8, heading 45°), because the engine's `--start`
option places the player at the cell centre, in the lake. Vilverin is the
neighbouring cell across the water. Overlay scripts ship inside the APK, not
the data payload, so changing them never forces a data re-download.
