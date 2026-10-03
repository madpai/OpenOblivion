// SPDX-License-Identifier: GPL-3.0-only
// Exercise the real OSG decoder; reading numbers from the text misses load failures.
#include <osg/ComputeBoundsVisitor>
#include <osg/Geode>
#include <osg/Geometry>
#include <osg/TriangleFunctor>
#include <osgDB/ReadFile>

#include <cmath>
#include <iostream>

namespace
{
    struct Triangles
    {
        unsigned int count = 0;
        void operator()(const osg::Vec3&, const osg::Vec3&, const osg::Vec3&) { ++count; }
    };

    bool near(float a, float b) { return std::abs(a - b) < 0.0001f; }
}

int main(int argc, char** argv)
{
    if (argc != 2) return 2;
    const auto root = osgDB::readRefNodeFile(argv[1]);
    if (!root || !root->asGroup() || root->asGroup()->getNumChildren() != 1)
    {
        std::cerr << "Player collision model did not load as one group\n";
        return 1;
    }
    const auto* collision = root->asGroup()->getChild(0)->asGeode();
    if (!collision || collision->getName() != "Collision" || collision->getNumDrawables() != 1)
        return 1;
    const auto* geometry = collision->getDrawable(0)->asGeometry();
    if (!geometry || !geometry->getVertexArray() || geometry->getVertexArray()->getNumElements() != 8)
        return 1;
    osg::TriangleFunctor<Triangles> triangles;
    geometry->accept(triangles);
    if (triangles.count != 12) return 1;
    osg::ComputeBoundsVisitor visitor;
    root->accept(visitor);
    const auto box = visitor.getBoundingBox();
    if (!near(box.xMin(), -13.3072f) || !near(box.xMax(), 13.3072f)
        || !near(box.yMin(), -13.3072f) || !near(box.yMax(), 13.3072f)
        || !near(box.zMin(), 1.7012f) || !near(box.zMax(), 140.f))
        return 1;
    std::cout << "Loaded Collision: 8 vertices, 12 triangles, original template bounds\n";
    return 0;
}
