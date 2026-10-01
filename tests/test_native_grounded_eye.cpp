// SPDX-License-Identifier: GPL-3.0-only
#include "grounded_eye.hpp"

#include <array>
#include <cstdlib>
#include <iostream>
#include <limits>

using Eye = OpenOblivion::GroundedEye;
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

int main()
{
    int cellA = 0, cellB = 0;
    Eye filter;
    Eye::Sample p{ 10000, 0, 124, &cellA, true, false, false };
    require(filter.update(p, 1.0 / 60) == 0, "initial frame must retain native height");
    for (int direction : { -1, 1 })
    {
        for (int fps : { 30, 60, 120 })
        {
            filter.reset();
            p = { 10000, 0, 124, &cellA, true, false, false };
            filter.update(p, 1.0 / fps);
            double last = p.z, maximumDelta = 0;
            for (int i = 1; i <= fps * 3; ++i)
            {
                p.y = 60.0 * i / fps;
                p.z = 124 + direction * 16 * static_cast<int>(i * 5.0 / fps);
                double offset = filter.update(p, 1.0 / fps);
                double view = p.z + offset;
                require(std::abs(offset) <= 48, "view must remain near body");
                require(direction * (view - last) >= -1e-9, "constant stair travel must not recoil");
                require(direction * offset <= 1e-9, "filter must not overshoot solved height");
                maximumDelta = std::max(maximumDelta, std::abs(view - last));
                last = view;
            }
            require(maximumDelta < 16 * 0.6, "per-tread jump must be substantially reduced");
            for (int i = 0; i < fps; ++i)
                filter.update(p, 1.0 / fps);
            require(std::abs(filter.update(p, 1.0 / fps)) < 0.002, "stationary view must settle");
        }
    }
    // Constant ramp motion must converge to the same height lag at any cadence.
    std::array<double, 3> lag{};
    int index = 0;
    for (int fps : { 30, 60, 120 })
    {
        filter.reset();
        p = { 10000, 0, 124, &cellA, true, false, false };
        filter.update(p, 1.0 / fps);
        for (int i = 1; i <= fps * 2; ++i)
        {
            p.y = 120.0 * i / fps;
            p.z = 124 + 80.0 * i / fps;
            lag[index] = filter.update(p, 1.0 / fps);
        }
        require(std::abs(lag[index]) <= 8.01, "ramp lag must remain bounded");
        ++index;
    }
    require(std::abs(lag[0] - lag[2]) < 1.1, "ramp response must agree across frame cadences");
    // Every case first creates a real lag, then requires an immediate native reset.
    for (int reason = 0; reason < 10; ++reason)
    {
        filter.reset();
        p = { 10000, 0, 124, &cellA, true, false, false };
        filter.update(p, 0.016);
        p.z += 16;
        require(filter.update(p, 0.016) < -10, "reset tests need a nonzero correction");
        double dt = 0.016;
        switch (reason)
        {
            case 0: p.jumping = true; break;
            case 1: p.grounded = false; break;
            case 2: p.swimming = true; break;
            case 3: p.cell = &cellB; break;
            case 4: p.x += 129; break;
            case 5: p.z += 63; break;
            case 6: dt = 0; break;
            case 7: dt = 0.251; break;
            case 8: filter.reset(); break;
            case 9: dt = std::numeric_limits<double>::quiet_NaN(); break;
        }
        require(filter.update(p, dt) == 0, "jump/fall/transition must retain native height immediately");
    }
    std::cout << "Native grounded eye: " << checks << " trajectory checks passed\n";
}
