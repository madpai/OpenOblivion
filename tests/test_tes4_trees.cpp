// SPDX-License-Identifier: GPL-3.0-only
#include "tes4_trees.hpp"

#include <cstdlib>
#include <iostream>
#include <string>

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

// Stand-in for ESM::Path, which wraps the original spelling.
struct FakePath
{
    std::string mOriginal;
    const std::string& getOriginal() const { return mOriginal; }
};

int main()
{
    using namespace OpenOblivion;
    // A record's model, the VFS path and a mixed-case spelling meet on one key.
    require(treeKey("Trees\\TreeYewForest.spt") == "treeyewforest", "backslash path");
    require(treeKey("meshes/trees/treeyewforest.spt") == "treeyewforest", "vfs path");
    require(treeKey("DBush16.SPT") == "dbush16", "bare upper-case name");
    require(treeKey("noextension") == "noextension", "no extension");

    TreeBillboardSize size;
    require(!findTreeSize("meshes/treeyewforest.spt", size), "unknown tree");
    registerTreeSize("TreeYewForest.spt", 1300.f, 1250.f);
    require(findTreeSize("meshes/trees/TREEYEWFOREST.SPT", size), "found by any spelling");
    require(size.mWidth == 1300.f && size.mHeight == 1250.f, "stored size");
    registerTreeSize("TreeYewForest.spt", 0.f, 500.f);
    require(findTreeSize("treeyewforest.spt", size) && size.mWidth == 1300.f, "zero size ignored");
    registerTreeSize("TreeYewForest.spt", 900.f, 900.f);
    require(findTreeSize("treeyewforest.spt", size) && size.mWidth == 900.f, "later record replaces");

    // Both record layouts of the model path.
    const std::string plain = "Trees\\ShrubBoxwood.spt";
    require(treeModelText(plain) == plain, "std::string model");
    const FakePath wrapped{ "Trees\\ShrubBoxwood.spt" };
    require(treeModelText(wrapped) == plain, "wrapped model");

    unsetenv("OPENOBLIVION_TES4_TREES");
    require(!tes4TreesEnabled(), "disabled by default");
    setenv("OPENOBLIVION_TES4_TREES", "1", 1);
    require(tes4TreesEnabled(), "1 enables");
    std::cout << "TES4 tree fixtures passed: " << checks << " checks\n";
}
