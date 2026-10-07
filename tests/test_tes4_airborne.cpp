// SPDX-License-Identifier: GPL-3.0-only
#include "tes4_airborne.hpp"

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

// The original's per-update law: subtract g*dt, then move by the new velocity (semi-implicit Euler).
static float originalApex(float speed, float dt)
{
    float velocity = speed, height = 0.f, apex = 0.f;
    for (int i = 0; i < 4000 && velocity > -speed; ++i)
    {
        velocity -= OpenOblivion::sTes4GravityUnits * dt;
        height += velocity * dt;
        apex = std::max(apex, height);
    }
    return apex;
}

// The donor solver: move by the stored velocity, then subtract gravity (explicit Euler), as movementsolver.cpp does.
static float solverApex(float speed, float dt)
{
    float velocity = speed, height = 0.f, apex = 0.f;
    for (int i = 0; i < 4000 && velocity > -speed; ++i)
    {
        height += velocity * dt;
        velocity -= OpenOblivion::sTes4GravityUnits * dt;
        apex = std::max(apex, height);
    }
    return apex;
}

int main()
{
    using namespace OpenOblivion;
    require(near(sTes4GravityUnits, 514.95f, 0.05f), "gravity in game units (73.575 Havok)");
    require(near(tes4JumpHeight(5.f), 69.f, 0.001f), "jump height, Acrobatics 5");
    require(near(tes4JumpHeight(0.f), 64.f, 0.001f), "jump height, Acrobatics 0");
    require(near(tes4JumpHeight(100.f), 164.f, 0.001f), "jump height, Acrobatics 100");
    require(near(tes4JumpSpeed(5.f), 266.58f, 0.05f), "takeoff speed sqrt(2 g h)");
    require(near(tes4AirControl(5.f), 0.015f, 1e-6f), "air control gain, Acrobatics 5");
    require(near(tes4AirControl(100.f), 0.3f, 1e-6f), "air control gain, Acrobatics 100");

    // The recorded original ran at about 35 ms per update; the apex of the same law is 64.4 units (the
    // recorded jumps reached 64.35 and 64.39), against 69 in the continuous limit.
    require(near(originalApex(tes4JumpSpeed(5.f), 0.035f), 64.39f, 0.05f), "apex at 35 ms updates");
    require(near(originalApex(tes4JumpSpeed(5.f), 1.f / 60.f), 66.78f, 0.05f), "apex at 60 Hz");
    require(originalApex(tes4JumpSpeed(5.f), 0.0005f) > 68.9f, "apex approaches the formula height");
    // The donor integrates the other way round. Carrying one step of gravity in the launch speed makes the
    // solver's sequence identical to the original's at its fixed step.
    require(near(solverApex(tes4TakeoffVerticalSpeed(5.f), sTes4PhysicsStep), 66.78f, 0.05f), "solver apex at 60 Hz");
    require(solverApex(tes4JumpSpeed(5.f), sTes4PhysicsStep) > 70.5f, "without the correction the solver overshoots");

    // Air control: a jump from a 89.7 u/s walk toward 117.3 u/s gains 0.4 per update at first (recorded).
    Tes4AirState state;
    tes4AirGround(state, { 0.f, 117.3f });
    tes4AirTakeoff(state, { 0.f, 89.7f });
    const Tes4Vec2 first = tes4AirStep(state, { 0.f, 117.3f }, tes4AirControl(5.f));
    require(near(first.y, 0.4f, 0.02f), "first airborne gain");
    require(near(state.velocity.y, 90.1f, 0.02f), "velocity after one update");
    for (int i = 0; i < 28; ++i)
        tes4AirStep(state, { 0.f, 117.3f }, tes4AirControl(5.f));
    // Closed form: V = T - (T - V0)(1 - f)^n, after 29 updates 99.5 as recorded.
    require(near(state.velocity.y, 117.3f - (117.3f - 89.7f) * std::pow(1.f - 0.015f, 29.f), 0.01f), "closed form");
    require(near(state.velocity.y, 99.5f, 0.1f), "recorded value after 29 updates");

    // Walking off an edge keeps the last ground velocity and leaves nothing in the solver's inertia.
    Tes4AirState walkOff;
    tes4AirGround(walkOff, { 100.f, 0.f });
    tes4AirFall(walkOff);
    const Tes4Vec2 movement = tes4AirStep(walkOff, { 100.f, 0.f }, tes4AirControl(5.f));
    require(near(movement.x, 100.f, 1e-3f) && near(movement.y, 0.f, 1e-3f), "walk-off movement");
    // No input in the air still keeps the takeoff momentum (movement delta decays but velocity does not vanish).
    Tes4AirState coast;
    tes4AirTakeoff(coast, { 50.f, 0.f });
    Tes4Vec2 delta = tes4AirStep(coast, { 0.f, 0.f }, tes4AirControl(5.f));
    require(near(coast.velocity.x, 50.f * (1.f - 0.015f), 1e-3f) && near(delta.x, -0.75f, 1e-3f), "coasting");

    // Rise bookkeeping for the device log line.
    Tes4AirState tracked;
    tes4AirTakeoff(tracked, { 0.f, 0.f }, 100.f);
    require(tes4AirTakeoffPending(tracked), "takeoff pending until the physics lifts the player");
    tes4AirTrack(tracked, 130.f, 0.1f);
    require(!tes4AirTakeoffPending(tracked) && tracked.sawAir, "air seen");
    tes4AirTrack(tracked, 166.f, 0.1f);
    tes4AirTrack(tracked, 150.f, 0.1f);
    require(near(tes4AirRise(tracked), 66.f, 1e-3f) && near(tracked.seconds, 0.3f, 1e-3f) && tracked.jumped, "rise tracking");
    Tes4AirState lost;
    tes4AirTakeoff(lost, { 10.f, 0.f }, 0.f);
    lost.seconds = 0.2f;
    require(!tes4AirTakeoffPending(lost), "a takeoff the physics never acted on expires");
    tes4AirGround(tracked, {});
    require(!tracked.jumped, "landing clears the jump");

    unsetenv("OPENOBLIVION_TES4_AIRBORNE");
    require(!tes4AirborneEnabled(), "disabled by default");
    std::cout << "TES4 airborne fixtures passed: " << checks << " checks\n";
}
