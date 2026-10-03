// SPDX-License-Identifier: GPL-3.0-only
// Converts a template COLLADA model to OSG ASCII without animation or COLLADA extras.
#include <osg/NodeVisitor>
#include <osgDB/ReadFile>
#include <osgDB/WriteFile>
#include <iostream>
struct Strip : osg::NodeVisitor {
    Strip() : osg::NodeVisitor(TRAVERSE_ALL_CHILDREN) {}
    void apply(osg::Node& n) override { n.setUpdateCallback(nullptr); n.setUserDataContainer(nullptr); traverse(n); }
};
int main(int argc, char** argv) {
    osg::ref_ptr<osg::Node> node = osgDB::readNodeFile(argv[1]);
    if (!node) { std::cerr << "read failed\n"; return 1; }
    Strip s; node->accept(s);
    if (!osgDB::writeNodeFile(*node, argv[2])) { std::cerr << "write failed\n"; return 2; }
    std::cout << "converted\n"; return 0;
}
