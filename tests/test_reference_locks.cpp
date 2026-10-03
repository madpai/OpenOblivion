// SPDX-License-Identifier: GPL-3.0-only
#include <components/esm4/loadrefr.hpp>
#include <components/esm4/reader.hpp>
#include <components/toutf8/toutf8.hpp>
#include "reference_locks.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>

int main(int argc, char** argv)
{
    if (argc != 2) return 2;
    try
    {
        const std::filesystem::path path(argv[1]);
        const ToUTF8::StatelessUtf8Encoder encoder(ToUTF8::calculateEncoding("win1252"));
        ESM4::Reader reader(std::make_unique<std::ifstream>(path, std::ios::binary), path, nullptr, &encoder, true);
        ESM4::Reference reference{};
        // Poison the optional fields so the first absent-XLOC record is checked too.
        reference.mIsLocked = true;
        reference.mLockLevel = 99;
        reference.mKey = ESM::FormId::fromUint32(0x1234);
        unsigned index = 0;
        while (reader.hasMoreRecs())
        {
            reader.exitGroupCheck();
            if (!reader.getRecordHeader()) throw std::runtime_error("missing fixture header");
            if (reader.hdr().record.typeId == ESM4::REC_GRUP)
            {
                reader.enterGroup();
                continue;
            }
            reader.getRecordData(false);
            OpenOblivion::resetReferenceLocks(reference);
            reference.load(reader); // Audited upstream implementation, unchanged.
            const bool locked = index == 1;
            if (reference.mIsLocked != locked || reference.mLockLevel != (locked ? 15 : 0)
                || reference.mKey.isZeroOrUnset() == locked)
                throw std::runtime_error("optional lock/key fields leaked across reference loads");
            ++index;
        }
        if (index != 3) throw std::runtime_error("incomplete regression fixture");
        std::cout << "reference lock reset: unlocked/locked/unlocked passed\n";
        return 0;
    }
    catch (const std::exception& error)
    {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
