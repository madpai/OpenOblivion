// SPDX-License-Identifier: GPL-3.0-only
#include "authored_strips.hpp"

#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <vector>

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

static std::vector<std::array<std::uint16_t, 3>> expand(const std::vector<std::uint16_t>& strip)
{
    std::vector<std::array<std::uint16_t, 3>> triangles;
    OpenOblivion::expandTriangleStrip(strip.data(), strip.size(), [&](std::uint16_t a, std::uint16_t b, std::uint16_t c) {
        triangles.push_back({ a, b, c });
    });
    return triangles;
}

int main()
{
    require(OpenOblivion::kOblivionStaticLayer == 1, "static layer must stay OL_STATIC");
    require(expand({}).empty(), "empty strip");
    require(expand({ 0, 1 }).empty(), "short strip");
    const auto one = expand({ 0, 1, 2 });
    require(one.size() == 1 && one[0][0] == 0 && one[0][1] == 1 && one[0][2] == 2, "first triangle keeps order");
    const auto two = expand({ 0, 1, 2, 3 });
    require(two.size() == 2, "two triangles");
    require(two[1][0] == 1 && two[1][1] == 3 && two[1][2] == 2, "odd step swaps winding");
    const auto three = expand({ 0, 1, 2, 3, 4 });
    require(three.size() == 3 && three[2][0] == 2 && three[2][1] == 3 && three[2][2] == 4, "even step keeps order");
    require(expand({ 0, 0, 1 }).empty(), "degenerate first edge");
    require(expand({ 0, 1, 1 }).empty(), "degenerate second edge");
    require(expand({ 0, 1, 0 }).empty(), "degenerate closing edge");
    require(expand({ 4, 5, 4, 6 }).size() == 1, "one degenerate step is skipped");
    std::cout << "authored strip fixtures passed: " << checks << '\n';
    return 0;
}
