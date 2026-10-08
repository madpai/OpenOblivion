// SPDX-License-Identifier: GPL-3.0-only
#include "tes4_grounded_law.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>

static int checks = 0;

static void require(bool value, const char* message)
{
    ++checks;
    if (!value)
    {
        std::cerr << message << '\n';
        std::exit(1);
    }
}

static bool near(float a, float b, float tolerance)
{
    return std::abs(a - b) < tolerance;
}

using namespace OpenOblivion;

namespace
{
    Tes4GroundQuery flatFloor()
    {
        Tes4GroundQuery surface;
        surface.found = true;
        surface.restZ = 0.f;
        surface.contact = Tes4Contact::Walkable;
        return surface;
    }

    struct Update
    {
        float dt;
        float above; // height above rest after the update, game units (recorded)
        int state; // controller state during the update, 0 ground, 2 air (recorded)
    };

    // Replays recorded updates through the port's functions the way the solver wrapper uses them: a grounded hull
    // is moved by the stored velocity, an airborne hull has already been moved by the host solver.
    float replay(float start, const Update* updates, int count, const char* what)
    {
        const Tes4GroundQuery surface = flatFloor();
        float z = start;
        bool supported = z - surface.restZ < sTes4SupportRange;
        // Prepared at the placement: the first update's velocity is -g*dt either way (nothing to carry).
        float vz = -sTes4GravityUnits * updates[0].dt;
        float worst = 0.f;
        for (int i = 0; i < count; ++i)
        {
            // The recorded state is the support state during the update; the wrapper's flag at the start of the step.
            require((updates[i].state == 0) == supported, what);
            if (!supported)
                z += vz * updates[i].dt;
            const float next = i + 1 < count ? updates[i + 1].dt : updates[i].dt;
            const Tes4GroundResult result = tes4GroundStep(supported, z, vz, updates[i].dt, 1.f, surface, next);
            z = result.z;
            vz = result.vz;
            supported = result.supported;
            worst = std::max(worst, std::abs(z - updates[i].above));
        }
        return worst;
    }
}

int main()
{
    require(near(sTes4SupportRange, 13.998f, 0.001f), "support range is 2.0 Havok units");

    // Level hover at the port's physics step: g*dt^2 per step (0.143 units), no accumulation, then rest.
    {
        const float dt = sTes4PhysicsStep;
        const Tes4GroundQuery surface = flatFloor();
        float z = 10.f, vz = -sTes4GravityUnits * dt;
        bool supported = true;
        float previous = z;
        int steps = 0;
        while (z > 0.f && steps < 2000)
        {
            const Tes4GroundResult result = tes4GroundStep(supported, z, vz, dt, 1.f, surface, dt);
            require(result.supported, "stays supported while hovering");
            require(near(result.vz, -sTes4GravityUnits * dt, 1e-4f), "the velocity resets each update");
            require(near(previous - result.z, sTes4GravityUnits * dt * dt, 1e-4f) || result.z == 0.f,
                "sinks g*dt^2 per update");
            previous = z = result.z;
            vz = result.vz;
            supported = result.supported;
            ++steps;
        }
        require(steps > 60 && steps < 80, "a 10 unit hover takes about 70 steps (1.2 s) at 60 Hz");
    }

    // Beyond the support range the hull leaves the ground and then falls with ordinary gravity.
    {
        const float dt = sTes4PhysicsStep;
        Tes4GroundResult result = tes4GroundStep(true, 14.2f, -sTes4GravityUnits * dt, dt, 1.f, flatFloor(), dt);
        require(!result.supported, "14.2 units above rest is unsupported");
        require(near(result.vz, -sTes4GravityUnits * dt, 1e-4f), "first airborne velocity is -g*dt");
        const Tes4GroundResult next = tes4GroundStep(false, 14.f, result.vz, dt, 1.f, flatFloor(), dt);
        require(!next.supported && near(next.vz, -2.f * sTes4GravityUnits * dt, 1e-4f), "then it accumulates");
        result = tes4GroundStep(true, 13.9f, -sTes4GravityUnits * dt, dt, 1.f, flatFloor(), dt);
        require(result.supported, "13.9 units above rest is supported");
    }

    // Capture needs descent: a rising hull inside the range stays airborne, a falling one is captured and keeps its velocity.
    {
        const float dt = sTes4PhysicsStep;
        Tes4GroundResult rising = tes4GroundStep(false, 5.f, 100.f, dt, 1.f, flatFloor(), dt);
        require(!rising.supported, "no capture while rising");
        const Tes4GroundResult falling = tes4GroundStep(false, 11.f, -30.f, dt, 1.f, flatFloor(), dt);
        require(falling.supported && near(falling.vz, -30.f, 1e-4f), "capture keeps the velocity of that update");
        const Tes4GroundResult after = tes4GroundStep(true, 11.f, falling.vz, dt, 1.f, flatFloor(), dt);
        require(near(after.z, 11.f - 30.f * dt, 1e-4f) && near(after.vz, -sTes4GravityUnits * dt, 1e-4f),
            "the captured update moves by that velocity, the next resets");
    }

    // A fast fall is stopped by the surface and rests.
    {
        const Tes4GroundResult result = tes4GroundStep(true, 2.f, -90.f, 0.05f, 1.f, flatFloor(), 0.05f);
        require(result.resting && near(result.z, 0.f, 1e-6f) && result.supported, "clamped to the resting height");
    }

    // No surface within reach: the ground state ends and gravity takes over; slow fall scales a falling velocity.
    {
        Tes4GroundQuery none;
        const Tes4GroundResult result = tes4GroundStep(true, 30.f, -8.6f, 1.f / 60.f, 0.5f, none, 1.f / 60.f);
        require(!result.supported && result.vz < 0.f && near(result.vz, -sTes4GravityUnits / 60.f * 0.5f, 1e-4f),
            "airborne with slow fall");
    }

    // Steep contact (stair nosings): sliding accumulates while off the surface and stops on it.
    {
        const float dt = sTes4PhysicsStep;
        Tes4GroundQuery steep = flatFloor();
        steep.contact = Tes4Contact::Steep;
        Tes4GroundResult a = tes4GroundStep(true, 6.f, -sTes4GravityUnits * dt, dt, 1.f, steep, dt);
        require(a.supported && near(a.vz, -2.f * sTes4GravityUnits * dt, 1e-4f), "sliding accumulates");
        a = tes4GroundStep(true, 0.f, -sTes4GravityUnits * dt, dt, 1.f, steep, dt);
        require(a.resting && a.vz == 0.f, "resting on a steep contact stops the velocity");
    }

    // The recorded original (Vilverin stair base, 2026-10-08, updates of 44 to 52 ms; heights above the resting
    // height). Each row is one controller update: step, height after it, state during it. The recorded steps jitter
    // by a few milliseconds, so the replay hands each update's recorded step to the velocity prepared for it; the
    // residual is then only the three-decimal rounding of the recording.
    {
        static const Update drop15[] = { { 0.046f, 14.010f, 2 }, { 0.046f, 11.831f, 2 }, { 0.047f, 9.604f, 0 },
            { 0.048f, 8.418f, 0 }, { 0.047f, 7.280f, 0 }, { 0.047f, 6.143f, 0 }, { 0.052f, 4.750f, 0 },
            { 0.049f, 3.514f, 0 }, { 0.049f, 2.278f, 0 }, { 0.049f, 1.041f, 0 }, { 0.049f, 0.f, 0 }, { 0.051f, 0.f, 0 } };
        static const Update drop20[] = { { 0.044f, 19.103f, 2 }, { 0.046f, 16.971f, 2 }, { 0.047f, 13.655f, 2 },
            { 0.048f, 10.269f, 0 }, { 0.051f, 8.930f, 0 }, { 0.051f, 7.590f, 0 }, { 0.048f, 6.404f, 0 },
            { 0.049f, 5.167f, 0 }, { 0.049f, 3.931f, 0 }, { 0.049f, 2.694f, 0 }, { 0.047f, 1.557f, 0 },
            { 0.046f, 0.467f, 0 }, { 0.047f, 0.f, 0 } };
        static const Update drop25[] = { { 0.047f, 23.962f, 2 }, { 0.048f, 21.614f, 2 }, { 0.049f, 17.981f, 2 },
            { 0.047f, 13.358f, 2 }, { 0.044f, 9.030f, 0 }, { 0.049f, 7.794f, 0 }, { 0.049f, 6.557f, 0 },
            { 0.046f, 5.468f, 0 }, { 0.046f, 4.378f, 0 }, { 0.047f, 3.241f, 0 }, { 0.046f, 2.151f, 0 },
            { 0.046f, 1.061f, 0 }, { 0.045f, 0.019f, 0 }, { 0.047f, 0.f, 0 } };
        static const Update drop45[] = { { 0.046f, 44.010f, 2 }, { 0.049f, 41.613f, 2 }, { 0.045f, 38.369f, 2 },
            { 0.052f, 33.228f, 2 }, { 0.051f, 26.846f, 2 }, { 0.047f, 19.827f, 2 }, { 0.050f, 11.073f, 2 },
            { 0.051f, 2.144f, 0 }, { 0.049f, 0.907f, 0 }, { 0.048f, 0.f, 0 } };
        const float tolerance = 0.05f;
        require(replay(15.1f, drop15, 12, "state sequence, 15.1 units") < tolerance, "heights, 15.1 units");
        require(replay(20.1f, drop20, 13, "state sequence, 20.1 units") < tolerance, "heights, 20.1 units");
        require(replay(25.1f, drop25, 14, "state sequence, 25.1 units") < tolerance, "heights, 25.1 units");
        require(replay(45.1f, drop45, 10, "state sequence, 45.1 units") < tolerance, "heights, 45.1 units");
    }

    unsetenv("OPENOBLIVION_TES4_AIRBORNE");
    unsetenv("OPENOBLIVION_TES4_GROUNDED");
    require(!tes4GroundedEnabled(), "disabled by default");
    std::cout << "TES4 grounded fixtures passed: " << checks << " checks\n";
}
