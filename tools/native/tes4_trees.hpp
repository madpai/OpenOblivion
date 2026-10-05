// SPDX-License-Identifier: GPL-3.0-only
// OpenOblivion: TES4 trees drawn from the original billboard textures.
//
// Oblivion's tree records point at SpeedTree `.spt` files, which only hold
// parameters for a procedural generator (1.3-2.3 KB each), and the engine
// ignores them. Every TREE record in Oblivion.esm and DLCShiveringIsles.esp
// has a pre-rendered image of the finished tree at
// textures/trees/billboards/<spt basename>.dds, and a BNAM subrecord holding
// the billboard's world size (width, height). With OPENOBLIVION_TES4_TREES=1
// an `.spt` model becomes two crossed, alpha-tested quads of that size with the
// original image, rooted at the reference origin. This is a stand-in for the
// 3D SpeedTree geometry, not an equivalent: no trunk collision, no wind and
// no near-range branches yet. See docs/research/TES4_TREES.md.
#ifndef OPENMW_OPENOBLIVION_TES4_TREES_HPP
#define OPENMW_OPENOBLIVION_TES4_TREES_HPP

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <string>
#include <string_view>
#include <unordered_map>

namespace OpenOblivion
{
    inline bool tes4TreesEnabled()
    {
        const char* value = std::getenv("OPENOBLIVION_TES4_TREES");
        return value != nullptr && std::strcmp(value, "1") == 0;
    }

    struct TreeBillboardSize
    {
        float mWidth = 0.f;
        float mHeight = 0.f;
    };

    // Lower-case file name without directory or extension, so a record's
    // `Trees\TreeYew.spt` and the VFS's `meshes/trees/treeyew.spt` meet.
    inline std::string treeKey(std::string_view path)
    {
        const std::size_t slash = path.find_last_of("/\\");
        if (slash != std::string_view::npos)
            path.remove_prefix(slash + 1);
        const std::size_t dot = path.rfind('.');
        if (dot != std::string_view::npos)
            path = path.substr(0, dot);
        std::string key(path);
        for (char& c : key)
            c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        return key;
    }

    struct TreeSizes
    {
        std::mutex mMutex;
        std::unordered_map<std::string, TreeBillboardSize> mSizes;
    };

    inline TreeSizes& treeSizes()
    {
        static TreeSizes sizes;
        return sizes;
    }

    inline void registerTreeSize(std::string_view modelPath, float width, float height)
    {
        if (!(width > 0.f) || !(height > 0.f))
            return;
        TreeSizes& sizes = treeSizes();
        std::lock_guard<std::mutex> lock(sizes.mMutex);
        sizes.mSizes[treeKey(modelPath)] = TreeBillboardSize{ width, height };
    }

    inline bool findTreeSize(std::string_view modelPath, TreeBillboardSize& size)
    {
        TreeSizes& sizes = treeSizes();
        std::lock_guard<std::mutex> lock(sizes.mMutex);
        const auto it = sizes.mSizes.find(treeKey(modelPath));
        if (it == sizes.mSizes.end())
            return false;
        size = it->second;
        return true;
    }

    // The TREE loader keeps its model path as std::string in one OpenMW
    // vintage and as ESM::Path in another.
    inline std::string_view treeModelText(const std::string& path)
    {
        return path;
    }

    template <class Path>
    auto treeModelText(const Path& path) -> decltype(std::string_view(path.getOriginal()))
    {
        return path.getOriginal();
    }
}

#endif
