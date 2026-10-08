// SPDX-License-Identifier: GPL-3.0-only
// OpenOblivion: classic TES4 player grounded motion (support range, hover, landing capture, sliding).
//
// Recovered on 2026-10-08 from the owner's own copy of the original game with the read-only sampler used for the
// airborne motor (docs/research/TES4_AIRBORNE.md, "Support range, landing capture and the sliding state"); no game
// data or code is reproduced. Each controller update, with the controller's own step `dt`:
//   * the controller is *supported* while the ground is less than 2.0 Havok units (13.998 game units) below its
//     resting height; capture needs a non-rising velocity;
//   * supported on level ground: the vertical velocity is reset to -g*dt every update (it does not accumulate), so
//     the hull sinks g*dt^2 per update until it rests (a hover); the update that captures a fall keeps the
//     velocity it already had;
//   * supported on a steep contact (stair nosings under the 40-unit-wide cone) the state stays "ground" while the
//     velocity accumulates by g*dt per update (inferred classification, see the research note);
//   * not supported: ordinary gravity, `vz = vz - g*dt`, then move.
// The solver integrates explicitly and stores the velocity for the next step, so these functions return the
// velocity to store for the next physics step and the height to take now (after the horizontal solve).
#ifndef OPENMW_OPENOBLIVION_TES4_GROUNDED_LAW_HPP
#define OPENMW_OPENOBLIVION_TES4_GROUNDED_LAW_HPP

#if __has_include("../mwmechanics/openoblivion_tes4_airborne.hpp")
#include "../mwmechanics/openoblivion_tes4_airborne.hpp"
#else
#include "tes4_airborne.hpp"
#endif

#include <algorithm>
#include <cstdlib>
#include <cstring>

namespace OpenOblivion
{
    // 2.0 Havok units: measured bracket 1.9717 (still grounded) to 2.0003 (airborne).
    inline constexpr float sTes4SupportRange = 2.f * sTes4HavokToUnits;
    // The host solver rests the hull this far above the surface it stands on (MWPhysics::sGroundOffset).
    inline constexpr float sTes4RestOffset = 1.f;

    // OPENOBLIVION_TES4_GROUNDED: 1 = hover and capture on walkable ground (steep contacts keep the host solver),
    // 2 = also the sliding state. Needs the airborne switch (the law uses its gravity).
    inline int tes4GroundedMode()
    {
        static const int mode = [] {
            if (!tes4AirborneEnabled())
                return 0;
            const char* value = std::getenv("OPENOBLIVION_TES4_GROUNDED");
            if (value == nullptr)
                return 0;
            if (std::strcmp(value, "1") == 0)
                return 1;
            if (std::strcmp(value, "2") == 0)
                return 2;
            return 0;
        }();
        return mode;
    }

    inline bool tes4GroundedEnabled()
    {
        return tes4GroundedMode() > 0;
    }

    enum class Tes4Contact
    {
        Walkable,
        Steep,
    };

    // What the downward hull sweep found below the hull.
    struct Tes4GroundQuery
    {
        bool found = false; // a surface (not an actor, not water) within reach
        float restZ = 0.f; // height of the hull reference at which it rests on that surface
        Tes4Contact contact = Tes4Contact::Walkable;
    };

    struct Tes4GroundResult
    {
        float z = 0.f; // height to take now
        float vz = 0.f; // vertical velocity stored for the next step
        bool supported = false; // the next step starts grounded
        bool resting = false; // the hull rests on the surface
    };

    // How far below the starting height the sweep has to look: the move of this update plus the support range.
    inline float tes4GroundReach(bool wasSupported, float vz, float dt)
    {
        const float move = wasSupported ? std::max(0.f, -vz * dt) : 0.f;
        return move + sTes4SupportRange + sTes4RestOffset + 0.5f;
    }

    // One update. `z0` is the height after the horizontal solve (a grounded hull has not moved vertically yet; an
    // airborne hull has already moved by its stored velocity), `vz` the velocity used by this update, `dt` its step.
    // The returned velocity is for the next update, whose step is `dtNext` (the host's physics step is fixed, so
    // callers pass the same value; a replay of recorded updates passes the recorded next step).
    inline Tes4GroundResult tes4GroundStep(bool wasSupported, float z0, float vz, float dt, float slowFall,
        const Tes4GroundQuery& surface, float dtNext)
    {
        const float g = sTes4GravityUnits;
        Tes4GroundResult out;
        float z = wasSupported ? z0 + vz * dt : z0;
        if (surface.found && z <= surface.restZ + 0.05f)
        {
            z = std::max(z, surface.restZ);
            out.resting = true;
        }
        const bool inRange = surface.found && z - surface.restZ < sTes4SupportRange;
        // A rising hull is never captured, whatever lies below it.
        out.supported = inRange && (wasSupported || vz <= 0.f);
        out.z = z;
        if (!out.supported)
        {
            float next = (wasSupported ? 0.f : vz) - g * dtNext;
            if (next < 0.f)
                next *= slowFall;
            out.vz = next;
        }
        else if (surface.contact == Tes4Contact::Steep)
            out.vz = out.resting ? 0.f : std::min(vz, 0.f) - g * dtNext;
        else
            out.vz = wasSupported ? -g * dtNext : vz;
        return out;
    }
}

#endif
