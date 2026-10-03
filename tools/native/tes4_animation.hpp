// SPDX-License-Identifier: GPL-3.0-only
// Original bounded TES4 animation primitives. Spline layout was checked against
// NifSkope 3a85ac55e65cc60abc3434cc4aaca2a5cc712eef (BSD-3-Clause).
// The evaluator uses a four-value iterative clamped cubic basis, with no Qt or
// proprietary code. See docs/research/LICENSE_MATRIX.md for the source audit.
#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <optional>
#include <span>
#include <string_view>
#include <type_traits>

namespace OpenOblivion::Animation
{
    inline bool validValue(float value)
    {
        return std::isfinite(value) && value != -std::numeric_limits<float>::max();
    }

    inline bool missingHandle(std::uint32_t handle) { return handle == 0xffffu || handle == 0xffffffffu; }

    inline std::optional<std::string_view> paletteName(std::string_view palette, std::uint32_t offset)
    {
        if (offset == 0xffffffffu) return std::string_view{};
        if (offset >= palette.size()) return std::nullopt;
        const auto end = palette.find('\0', offset);
        if (end == std::string_view::npos) return std::nullopt;
        return palette.substr(offset, end - offset);
    }

    struct Basis
    {
        std::uint32_t first;
        std::array<float, 4> weights;
    };

    inline std::optional<Basis> cubicBasis(std::uint32_t count, float fraction)
    {
        // The format's implicit open, uniform cubic knot vector requires four
        // control points. Bound counts before arithmetic or data indexing.
        if (count < 4 || count > 1'000'000 || !std::isfinite(fraction)) return std::nullopt;
        const float u = std::clamp(fraction, 0.f, 1.f) * static_cast<float>(count - 3);
        const auto span = std::min(count - 1, 3u + static_cast<std::uint32_t>(u));
        auto knot = [count](std::uint32_t index) {
            return index <= 3 ? 0.f : static_cast<float>(std::min(index, count) - 3);
        };
        Basis out{span - 3, {1.f, 0.f, 0.f, 0.f}};
        std::array<float, 4> left{}, right{};
        for (std::uint32_t degree = 1; degree <= 3; ++degree)
        {
            left[degree] = u - knot(span + 1 - degree);
            right[degree] = knot(span + degree) - u;
            float carried = 0.f;
            for (std::uint32_t index = 0; index < degree; ++index)
            {
                const float divisor = right[index + 1] + left[degree - index];
                const float term = divisor == 0.f ? 0.f : out.weights[index] / divisor;
                out.weights[index] = carried + right[index + 1] * term;
                carried = left[degree - index] * term;
            }
            out.weights[degree] = carried;
        }
        return out;
    }

    template<std::size_t Dimensions, class Scalar>
    std::optional<std::array<float, Dimensions>> splineChannel(std::span<const Scalar> values,
        std::uint32_t handle, std::uint32_t count, float fraction, float halfRange = 1.f, float offset = 0.f)
    {
        static_assert(Dimensions >= 1 && Dimensions <= 4);
        static_assert(std::is_same_v<Scalar, float> || std::is_same_v<Scalar, std::int16_t>);
        if (missingHandle(handle)) return std::nullopt;
        const auto basis = cubicBasis(count, fraction);
        if (!basis || !validValue(halfRange) || !validValue(offset)
            || handle > values.size() || count > (values.size() - handle) / Dimensions) return std::nullopt;
        std::array<float, Dimensions> out{};
        for (std::size_t point = 0; point < 4; ++point)
            for (std::size_t component = 0; component < Dimensions; ++component)
            {
                float value = static_cast<float>(values[handle + (basis->first + point) * Dimensions + component]);
                if constexpr (std::is_same_v<Scalar, std::int16_t>) value /= 32767.f;
                if (!validValue(value)) return std::nullopt;
                out[component] += value * basis->weights[point];
            }
        for (auto& value : out)
        {
            value = value * halfRange + offset;
            if (!validValue(value)) return std::nullopt;
        }
        return out;
    }
}
