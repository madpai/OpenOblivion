// SPDX-License-Identifier: GPL-3.0-only
#include "tes4_movement.hpp"

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

static bool near(float a, float b)
{
    return std::abs(a - b) < 0.01f;
}

int main()
{
    using namespace OpenOblivion;
    // Starting player (Speed 40, Athletics 5) with the owner's master settings.
    require(near(tes4PlayerGroundSpeed(false, false, false), 116.6f), "walk, weapon sheathed");
    require(near(tes4PlayerGroundSpeed(false, false, true), 106.f), "walk, weapon drawn");
    require(near(tes4PlayerGroundSpeed(true, false, false), 355.63f), "run, weapon sheathed");
    require(near(tes4PlayerGroundSpeed(true, false, true), 323.3f), "run, weapon drawn");
    require(near(tes4PlayerGroundSpeed(false, true, false), 69.96f), "sneak walk");
    require(near(tes4PlayerGroundSpeed(true, true, false), 213.378f), "sneak run");
    // Formula endpoints.
    require(near(tes4GroundSpeed(0, 0, false, false, true), 90.f), "minimum walk");
    require(near(tes4GroundSpeed(100, 100, true, false, true), 130.f * 4.f), "maximum run");
    unsetenv("OPENOBLIVION_TES4_MOVEMENT");
    require(!tes4MovementEnabled(), "disabled by default");
    setenv("OPENOBLIVION_TES4_MOVEMENT", "1", 1);
    require(tes4MovementEnabled(), "1 enables");
    std::cout << "TES4 movement fixtures passed: " << checks << " checks\n";
}
