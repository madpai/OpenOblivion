// SPDX-License-Identifier: GPL-3.0-only
// Original numeric fixtures, no game keyframes or copied decoder algorithms.
#include "tes4_animation.hpp"
#include <cassert>
#include <iostream>
#include <vector>
using namespace OpenOblivion::Animation;
static void close(float a, float b) { assert(std::abs(a - b) < 0.00002f); }
int main()
{
    std::uint32_t checks = 0;
    // Four-point clamped cubic is a Bezier curve. These analytic coefficients
    // independently specify the expected result, including both endpoints.
    const std::vector<float> controls{2.f, -1.f, 4.f, 8.f};
    for (int i = 0; i <= 100; ++i)
    {
        const float t = i / 100.f, r = 1.f - t;
        auto sample = splineChannel<1, float>(controls, 0, 4, t);
        assert(sample); close((*sample)[0], 2*r*r*r - 3*t*r*r + 12*t*t*r + 8*t*t*t);
        ++checks;
    }
    // Linear Greville control positions for five points reproduce t exactly.
    const std::vector<float> linear{0.f, 1.f/6.f, .5f, 5.f/6.f, 1.f};
    for (int i = 0; i <= 100; ++i)
    {
        float t = i / 100.f;
        auto sample = splineChannel<1, float>(linear, 0, 5, t);
        assert(sample); close((*sample)[0], t); ++checks;
    }
    // Shared packed array, interleaved XYZ components and a nonzero handle.
    const std::vector<std::int16_t> compact{123, 32767,0,-32767, 32767,0,-32767,
        32767,0,-32767, 32767,0,-32767, 456};
    auto xyz = splineChannel<3, std::int16_t>(compact, 1, 4, .42f, 2.f, 5.f);
    assert(xyz); close((*xyz)[0], 7.f); close((*xyz)[1], 5.f); close((*xyz)[2], 3.f);
    assert((!splineChannel<3, std::int16_t>(compact, 3, 4, .5f)));
    assert((!splineChannel<1, float>(controls, 0xffffffffu, 4, .5f)));
    assert(!cubicBasis(3, .5f)); assert(!cubicBasis(1'000'001, .5f));
    assert(!cubicBasis(4, std::numeric_limits<float>::quiet_NaN()));
    auto lo = splineChannel<1, float>(controls, 0, 4, -10.f);
    auto hi = splineChannel<1, float>(controls, 0, 4, 10.f);
    assert(lo && hi); close((*lo)[0], 2.f); close((*hi)[0], 8.f);
    assert(!validValue(-std::numeric_limits<float>::max()));
    assert(!validValue(std::numeric_limits<float>::infinity()));
    const std::string_view palette("bone\0NiTransformController\0", 27);
    assert(paletteName(palette, 0) == "bone");
    assert(paletteName(palette, 5) == "NiTransformController");
    assert(paletteName(palette, 0xffffffffu) == "");
    assert(!paletteName(palette, 27)); assert(!paletteName("unterminated", 0));
    std::cout << checks << " analytic curve samples plus packed/bounds/palette checks passed\n";
}
