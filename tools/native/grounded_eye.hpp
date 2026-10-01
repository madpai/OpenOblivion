// SPDX-License-Identifier: GPL-3.0-only
// Independently authored OpenOblivion presentation filter. No actor mutation.
#pragma once

#include <algorithm>
#include <cmath>

namespace OpenOblivion
{
    class GroundedEye
    {
    public:
        struct Sample
        {
            double x, y, z;
            const void* cell;
            bool grounded, jumping, swimming;
        };

        void reset() { mValid = false; }

        double update(const Sample& p, double dt)
        {
            if (!std::isfinite(p.x) || !std::isfinite(p.y) || !std::isfinite(p.z) || !std::isfinite(dt))
            {
                reset();
                return 0;
            }
            const double dx = p.x - mPrevious.x, dy = p.y - mPrevious.y;
            const bool discontinuity = !mValid || p.cell != mPrevious.cell || !p.grounded
                || !mPrevious.grounded || p.jumping || p.swimming || dt <= 0 || dt > 0.25
                || std::abs(p.z - mPrevious.z) > 62 || dx * dx + dy * dy > 128 * 128;
            if (discontinuity)
                mHeight = p.z;
            else
                mHeight = std::clamp(p.z + (mHeight - p.z) * std::exp(-dt / 0.1), p.z - 48, p.z + 48);
            mPrevious = p;
            mValid = true;
            return mHeight - p.z;
        }

    private:
        bool mValid = false;
        double mHeight = 0;
        Sample mPrevious{ 0, 0, 0, nullptr, false, false, false };
    };
}
