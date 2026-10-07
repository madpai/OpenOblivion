// SPDX-License-Identifier: GPL-3.0-only
// OpenOblivion: classic TES4 player airborne motion (jump, gravity, air control).
//
// Everything below was recovered from the owner's own copy of the original game on 2026-10-06
// (docs/research/TES4_AIRBORNE.md); no game data or code is reproduced:
//   * world gravity read from the running game: 73.575 Havok units/s^2 (9.81 * 7.5); Havok units are
//     game units * 0.1428767293691635, so 514.9 game units/s^2;
//   * jump height  h = fJumpHeightMin + (fJumpHeightMax - fJumpHeightMin) * Acrobatics / 100
//     (static read of the executable; the controller field held 9.8585 Havok = 69 units for Acrobatics 5);
//   * takeoff speed sqrt(2 g h) with the horizontal velocity kept (static read, replayed on three
//     recorded jumps: the first airborne velocity agrees to four decimals);
//   * every update subtracts g*dt from the vertical velocity and then moves by the new velocity
//     (replayed exactly on 100+ recorded airborne updates, including a 166 ms frame);
//   * while airborne the horizontal velocity relaxes toward the desired ground velocity by
//     f = fJumpMoveBase + fJumpMoveMult * Acrobatics / 100 per update (replayed exactly on a recorded
//     jump from a walk; the gain was also seen at run speed).
// Setting values: fJumpHeightMin 64 and fJumpMoveBase 0 and fJumpMoveMult 0.3 are executable defaults
// (absent from the master); fJumpHeightMax 164 is the master's override. Acrobatics 5 is the master's
// Player record until TES4 actor stats exist. Fatigue cost, fall damage and swimming are not modelled.
#ifndef OPENMW_OPENOBLIVION_TES4_AIRBORNE_HPP
#define OPENMW_OPENOBLIVION_TES4_AIRBORNE_HPP

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <cstring>

namespace OpenOblivion
{
    inline constexpr float sTes4HavokToUnits = 1.f / 0.1428767293691635f;
    inline constexpr float sTes4GravityHavok = 73.575f;
    inline constexpr float sTes4GravityUnits = sTes4GravityHavok * sTes4HavokToUnits;
    inline constexpr float sTes4JumpHeightMin = 64.f;
    inline constexpr float sTes4JumpHeightMax = 164.f;
    inline constexpr float sTes4JumpMoveBase = 0.f;
    inline constexpr float sTes4JumpMoveMult = 0.3f;
    inline constexpr float sTes4PlayerAcrobatics = 5.f;
    // OpenMW's fixed physics step. The first physics step after takeoff already integrates once.
    inline constexpr float sTes4PhysicsStep = 1.f / 60.f;

    inline bool tes4AirborneEnabled()
    {
        static const bool enabled = [] {
            const char* value = std::getenv("OPENOBLIVION_TES4_AIRBORNE");
            return value != nullptr && std::strcmp(value, "1") == 0;
        }();
        return enabled;
    }

    inline float tes4JumpHeight(float acrobatics)
    {
        return sTes4JumpHeightMin + (sTes4JumpHeightMax - sTes4JumpHeightMin) * acrobatics * 0.01f;
    }

    // sqrt(2 g h): the speed at which the original launches the player.
    inline float tes4JumpSpeed(float acrobatics)
    {
        return std::sqrt(2.f * sTes4GravityUnits * tes4JumpHeight(acrobatics));
    }

    // The solver integrates explicitly (move, then subtract gravity). The original subtracts first, so the
    // launch step carries one step of gravity already; this reproduces its sequence exactly.
    inline float tes4TakeoffVerticalSpeed(float acrobatics)
    {
        return tes4JumpSpeed(acrobatics) - sTes4GravityUnits * sTes4PhysicsStep;
    }

    // Per-update gain of the horizontal velocity toward the desired one while airborne.
    inline float tes4AirControl(float acrobatics)
    {
        return std::clamp(sTes4JumpMoveBase + sTes4JumpMoveMult * acrobatics * 0.01f, 0.f, 1.f);
    }

    struct Tes4Vec2
    {
        float x = 0.f;
        float y = 0.f;
    };

    // The physics solver adds the actor's inertia to the movement vector in the air. A jump stores the
    // takeoff velocity in the inertia (base); walking off an edge stores nothing. The controller therefore
    // passes the difference between the wanted airborne velocity and that base as the movement vector.
    struct Tes4AirState
    {
        bool active = false;
        Tes4Vec2 base;
        Tes4Vec2 velocity;
        Tes4Vec2 lastGround;
    };

    inline void tes4AirTakeoff(Tes4AirState& state, Tes4Vec2 velocity)
    {
        state.active = true;
        state.base = velocity;
        state.velocity = velocity;
    }

    inline void tes4AirFall(Tes4AirState& state)
    {
        state.active = true;
        state.base = Tes4Vec2();
        state.velocity = state.lastGround;
    }

    inline void tes4AirGround(Tes4AirState& state, Tes4Vec2 desired)
    {
        state.active = false;
        state.base = Tes4Vec2();
        state.velocity = Tes4Vec2();
        state.lastGround = desired;
    }

    // One controller update in the air: relax toward `desired`, return the movement vector for the solver.
    inline Tes4Vec2 tes4AirStep(Tes4AirState& state, Tes4Vec2 desired, float gain)
    {
        state.velocity.x += gain * (desired.x - state.velocity.x);
        state.velocity.y += gain * (desired.y - state.velocity.y);
        return { state.velocity.x - state.base.x, state.velocity.y - state.base.y };
    }
}

#endif
