// SPDX-License-Identifier: GPL-3.0-only
// Triangle-strip expansion for authored static collision. No Havok bytecode.
#pragma once

#include <cstddef>
#include <cstdint>

namespace OpenOblivion
{

    // nif.xml OblivionLayer::OL_STATIC. This is the collision layer, not a material id.
    inline constexpr std::uint8_t kOblivionStaticLayer = 1;

    // Gamebryo strip rule: step 0 keeps (a, b, c) and each later step swaps the winding.
    // Degenerate triples are omitted. Indices stay in the strip's own vertex list.
    template <class Index, class Emit>
    void expandTriangleStrip(const Index* indices, std::size_t count, Emit&& emit)
    {
        if (count < 3 || indices == nullptr)
            return;

        Index b = indices[0];
        Index c = indices[1];
        for (std::size_t i = 2; i < count; ++i)
        {
            const Index a = b;
            b = c;
            c = indices[i];
            if (a == b || b == c || a == c)
                continue;
            if ((i % 2) == 0)
                emit(a, b, c);
            else
                emit(a, c, b);
        }
    }

}
