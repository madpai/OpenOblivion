// SPDX-License-Identifier: GPL-3.0-only
// OpenOblivion: classic TES4 player ground speed.
//
// Formula read from the original executable's character speed routine
// (Oblivion.exe 0x547c00 and its run wrapper 0x547d00), on 2026-10-03:
//   walk = (fMoveCharWalkMin + (fMoveCharWalkMax - fMoveCharWalkMin) * Speed * 0.01)
//          * (1 - encumbranceEffect * normalizedWeight)
//   walk *= fMoveNoWeaponMult when no weapon is drawn
//   walk *= fMoveSneakMult while sneaking
//   run  = walk * (fMoveRunMult + fMoveRunAthleticsMult * Athletics * 0.01)
// Setting values are the owner's Oblivion.esm overrides; fMoveRunAthleticsMult
// is absent from the master and uses the executable default (1.0). Speed 40 and
// Athletics 5 are the master's Player record until TES4 actor stats exist.
// Carried weight is not modelled yet (treated as unencumbered).
// See docs/research/TES4_MOVEMENT.md.
#ifndef OPENMW_OPENOBLIVION_TES4_MOVEMENT_HPP
#define OPENMW_OPENOBLIVION_TES4_MOVEMENT_HPP

#include <algorithm>
#include <cstdlib>
#include <cstring>

namespace OpenOblivion
{
    inline constexpr float sTes4MoveCharWalkMin = 90.f;
    inline constexpr float sTes4MoveCharWalkMax = 130.f;
    inline constexpr float sTes4MoveRunMult = 3.f;
    inline constexpr float sTes4MoveRunAthleticsMult = 1.f;
    inline constexpr float sTes4MoveNoWeaponMult = 1.1f;
    inline constexpr float sTes4MoveSneakMult = 0.6f;
    inline constexpr float sTes4PlayerSpeed = 40.f;
    inline constexpr float sTes4PlayerAthletics = 5.f;

    inline bool tes4MovementEnabled()
    {
        const char* value = std::getenv("OPENOBLIVION_TES4_MOVEMENT");
        return value != nullptr && std::strcmp(value, "1") == 0;
    }

    inline float tes4GroundSpeed(float speedAttribute, float athletics, bool running, bool sneaking, bool weaponDrawn)
    {
        float speed = sTes4MoveCharWalkMin + (sTes4MoveCharWalkMax - sTes4MoveCharWalkMin) * speedAttribute * 0.01f;
        if (!weaponDrawn)
            speed *= sTes4MoveNoWeaponMult;
        if (sneaking)
            speed *= sTes4MoveSneakMult;
        speed = std::max(0.f, speed);
        if (running)
            speed *= sTes4MoveRunMult + sTes4MoveRunAthleticsMult * athletics * 0.01f;
        return speed;
    }

    inline float tes4PlayerGroundSpeed(bool running, bool sneaking, bool weaponDrawn)
    {
        return tes4GroundSpeed(sTes4PlayerSpeed, sTes4PlayerAthletics, running, sneaking, weaponDrawn);
    }
}

#endif
