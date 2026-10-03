// SPDX-License-Identifier: GPL-3.0-only
#pragma once

namespace OpenOblivion
{
    // A Reference reader can reuse one record object. Optional XLOC fields
    // must never carry a preceding reference's lock or key into a new record.
    template <class Reference>
    void resetReferenceLocks(Reference& reference)
    {
        reference.mIsLocked = false;
        reference.mLockLevel = 0;
        reference.mKey = {};
    }
}
