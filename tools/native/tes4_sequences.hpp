// SPDX-License-Identifier: GPL-3.0-only
// Original embedded TES4 transform-clip bridge. No game data or runtime code.
#pragma once
#include "openoblivion_tes4_kf.hpp"
#include <components/nif/node.hpp>
#include <osg/Node>
#include <osg/UserDataContainer>
#include <unordered_set>

namespace OpenOblivion::Animation
{
    inline bool hasManagedController(const Nif::NiAVObject& node)
    {
        std::unordered_set<const Nif::NiTimeController*> visited;
        for (auto controller = node.mController; !controller.empty(); controller = controller->mNext)
        {
            if (!visited.insert(controller.getPtr()).second) break;
            if (controller->isActive() && (controller->mRecordType == Nif::RC_NiControllerManager
                || controller->mRecordType == Nif::RC_NiMultiTargetTransformController)) return true;
        }
        return false;
    }

    // Cached with the scene template. Controllers are cloned when assigned to
    // an object, so separate references never share a playback clock.
    class EmbeddedClips : public osg::Object
    {
    public:
        EmbeddedClips() = default;
        EmbeddedClips(const EmbeddedClips& copy, const osg::CopyOp& op)
            : osg::Object(copy, op), clips(copy.clips) {}
        META_Object(OpenOblivion, EmbeddedClips)
        std::vector<osg::ref_ptr<const SceneUtil::KeyframeHolder>> clips;
    };

    inline void attachEmbeddedClips(Nif::FileView file, osg::Node& root)
    {
        // Later-game formats require a separate compatibility audit.
        if (file.getVersion() < 0x0a000102u || file.getVersion() > 0x14000005u) return;
        osg::ref_ptr<EmbeddedClips> result = new EmbeddedClips;
        std::unordered_set<const Nif::NiAVObject*> visited;
        std::unordered_set<const Nif::NiTimeController*> controllers;
        std::unordered_set<const Nif::NiControllerSequence*> sequences;
        std::unordered_set<std::string> names;
        std::vector<const Nif::NiAVObject*> pending;
        for (std::size_t i = 0; i < file.numRoots(); ++i)
            if (const auto* node = dynamic_cast<const Nif::NiAVObject*>(file.getRoot(i))) pending.push_back(node);
        while (!pending.empty())
        {
            const auto* node = pending.back(); pending.pop_back();
            if (!visited.insert(node).second) continue;
            for (auto controller = node->mController; !controller.empty(); controller = controller->mNext)
            {
                if (!controllers.insert(controller.getPtr()).second) break;
                const auto* manager = dynamic_cast<const Nif::NiControllerManager*>(controller.getPtr());
                if (!manager || !manager->isActive()) continue;
                for (const auto& entry : manager->mSequences)
                {
                    if (entry.empty() || !sequences.insert(entry.getPtr()).second) continue;
                    const std::string name = Misc::StringUtils::lowerCase(entry->mName);
                    if (!names.insert(name).second) throw std::runtime_error("Duplicate embedded sequence: " + name);
                    osg::ref_ptr<SceneUtil::KeyframeHolder> clip = new SceneUtil::KeyframeHolder;
                    loadControllerSequence(*entry.getPtr(), file.getVersion(), *clip);
                    if (!clip->mKeyframeControllers.empty()) result->clips.push_back(clip);
                }
            }
            if (const auto* parent = dynamic_cast<const Nif::NiNode*>(node))
                for (const auto& child : parent->mChildren)
                    if (!child.empty()) pending.push_back(child.getPtr());
        }
        if (!result->clips.empty()) root.getOrCreateUserDataContainer()->addUserObject(result);
    }

    inline const EmbeddedClips* embeddedClips(const osg::Node& root)
    {
        const auto* data = root.getUserDataContainer();
        if (data)
            for (unsigned i = 0; i < data->getNumUserObjects(); ++i)
                if (const auto* clips = dynamic_cast<const EmbeddedClips*>(data->getUserObject(i))) return clips;
        return nullptr;
    }
}
