// SPDX-License-Identifier: GPL-3.0-only
// Original TES4 part selection through audited OpenMW public scene interfaces.
#pragma once
#include <components/resource/scenemanager.hpp>
#include <components/sceneutil/attach.hpp>
#include <components/sceneutil/riggeometry.hpp>
#include <components/sceneutil/riggeometryosgaextension.hpp>
#include <components/sceneutil/skeleton.hpp>
#include <set>

namespace OpenOblivion::Skin
{
    class Parts : public osg::NodeVisitor
    {
    public:
        Parts() : osg::NodeVisitor(TRAVERSE_ALL_CHILDREN) {}
        void apply(osg::Drawable& node) override
        {
            if (!dynamic_cast<SceneUtil::RigGeometry*>(&node)
                && !dynamic_cast<SceneUtil::RigGeometryHolder*>(&node)) return;
            const auto& path = getNodePath();
            // Retain this renderable's local state/transform, while excluding
            // its private skeleton and the unrelated bind-pose bone hierarchy.
            const osg::Node* selected = &node;
            if (path.size() >= 2 && !dynamic_cast<SceneUtil::Skeleton*>(path[path.size() - 2]))
                selected = path[path.size() - 2];
            renderables.insert(selected);
        }
        std::set<const osg::Node*> renderables;
    };

    inline void attach(osg::ref_ptr<const osg::Node> part, osg::Group* actor, Resource::SceneManager* manager)
    {
        if (!dynamic_cast<const SceneUtil::Skeleton*>(part.get()))
        {
            SceneUtil::attach(part, actor, "", actor, manager);
            return;
        }
        Parts parts;
        const_cast<osg::Node*>(part.get())->accept(parts);
        for (const auto* renderable : parts.renderables)
            actor->addChild(manager->getInstance(renderable));
    }
}
