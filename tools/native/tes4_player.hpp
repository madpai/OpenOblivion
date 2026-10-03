// SPDX-License-Identifier: GPL-3.0-only
// OpenOblivion: render the preview player as the classic TES4 Player record.
//
// The engine player stays the template actor for mechanics. With
// OPENOBLIVION_TES4_PLAYER=1 its third-person view uses the master's Player
// NPC (FormID 00000007): its skeleton, race body and head parts and hair, and
// the original male/female locomotion KF files. TES4 KF sequence names repeat
// across files (walkforward.kf and sneakforward.kf are both "Forward"), so the
// animation group is chosen from the file name and mapped to the group names
// the host character controller requests.
#ifndef OPENMW_OPENOBLIVION_TES4_PLAYER_HPP
#define OPENMW_OPENOBLIVION_TES4_PLAYER_HPP

#include <components/debug/debuglog.hpp>
#include <components/esm/formid.hpp>
#include <components/esm/refid.hpp>
#include <components/esm4/loadhair.hpp>
#include <components/esm4/loadnpc.hpp>
#include <components/esm4/loadrace.hpp>
#include <components/misc/strings/algorithm.hpp>
#include <components/misc/strings/lower.hpp>
#include <components/sceneutil/keyframe.hpp>

#include "../mwworld/cellref.hpp"
#include "../mwworld/esmstore.hpp"
#include "../mwworld/ptr.hpp"

#include <array>
#include <cstdlib>
#include <cstring>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace OpenOblivion
{
    inline constexpr ESM::FormId32 sTes4PlayerFormId = 0x00000007;

    // ESM4 model fields are std::string in the Android 0.51 tree and ESM::Path
    // in the desktop 0.52 tree.
    inline std::string tes4PathText(const std::string& path) { return path; }
    template <class Path>
    inline auto tes4PathText(const Path& path) -> decltype(std::string(path.getOriginal()))
    {
        return std::string(path.getOriginal());
    }

    inline bool tes4PlayerEnabled()
    {
        const char* value = std::getenv("OPENOBLIVION_TES4_PLAYER");
        return value != nullptr && std::strcmp(value, "1") == 0;
    }

    // The master's Player NPC when the switch is on and ptr is the engine player.
    inline const ESM4::Npc* tes4PlayerRecordFor(const MWWorld::Ptr& ptr, const MWWorld::ESMStore& store)
    {
        if (!tes4PlayerEnabled() || ptr.isEmpty() || ptr.getCellRef().getRefId() != ESM::RefId::stringRefId("Player"))
            return nullptr;
        // Load order renumbers the master's 00000007, so find it by editor ID once.
        static const ESM4::Npc* found = nullptr;
        static bool searched = false;
        if (!searched)
        {
            searched = true;
            for (const ESM4::Npc& candidate : store.get<ESM4::Npc>())
                if (candidate.mIsTES4 && (candidate.mId.toUint32() & 0xffffff) == sTes4PlayerFormId
                    && Misc::StringUtils::ciEqual(candidate.mEditorId, "Player"))
                {
                    found = &candidate;
                    break;
                }
        }
        const ESM4::Npc* npc = found;
        if (npc == nullptr || tes4PathText(npc->mModel).empty())
        {
            static bool reported = false;
            if (!reported)
                Log(Debug::Warning) << "OPENOBLIVION_TES4_PLAYER unavailable: no TES4 Player record";
            reported = true;
            return nullptr;
        }
        return npc;
    }

    inline bool tes4PlayerFemale(const ESM4::Npc& npc)
    {
        return (npc.mBaseConfig.tes4.flags & ESM4::Npc::TES4_Female) != 0;
    }

    // Body, head and hair meshes, in the order the TES4 NPC renderer attaches them.
    // First person uses the original _1stperson skeleton/clips and only body parts
    // (arms and hands); the head and hair would sit in front of the camera.
    inline std::vector<std::string> tes4PlayerPartModels(
        const ESM4::Npc& npc, const MWWorld::ESMStore& store, bool firstPerson)
    {
        std::vector<std::string> models;
        // TES4 race records carry body textures, not body meshes; the bare body
        // is the fixed set in Characters\_Male (female meshes share that folder).
        const std::string_view prefix = tes4PlayerFemale(npc) ? "female" : "";
        for (std::string_view piece : { "upperbody", "lowerbody", "hand", "foot" })
            if (!firstPerson || piece == "upperbody" || piece == "hand")
                models.push_back("Characters\\_Male\\" + std::string(prefix) + std::string(piece) + ".nif");
        const ESM4::Race* race = store.get<ESM4::Race>().search(npc.mRace);
        if (race != nullptr)
        {
            for (const ESM4::Race::BodyPart& part : tes4PlayerFemale(npc) ? race->mBodyPartsFemale : race->mBodyPartsMale)
                if (!part.mesh.empty())
                    models.push_back(part.mesh);
            if (!firstPerson)
                for (const ESM4::Race::BodyPart& part : race->mHeadParts)
                    if (!part.mesh.empty())
                        models.push_back(part.mesh);
        }
        if (!firstPerson && !npc.mHair.isZeroOrUnset())
            if (const ESM4::Hair* hair = store.get<ESM4::Hair>().search(npc.mHair))
                if (!tes4PathText(hair->mModel).empty())
                    models.push_back(tes4PathText(hair->mModel));
        return models;
    }

    inline std::string tes4PlayerSkeleton(std::string thirdPerson, bool firstPerson)
    {
        if (!firstPerson)
            return thirdPerson;
        const auto slash = thirdPerson.find_last_of('/');
        const auto parent = thirdPerson.find_last_of('/', slash == 0 ? 0 : slash - 1);
        return thirdPerson.substr(0, parent + 1) + "_1stperson/skeleton.nif";
    }

    // Original locomotion files (next to the skeleton) and the host group names.
    inline const std::array<std::pair<std::string_view, std::string_view>, 22>& tes4LocomotionGroups()
    {
        static const std::array<std::pair<std::string_view, std::string_view>, 22> groups{ {
            { "idle.kf", "idle" },
            { "walkforward.kf", "walkforward" },
            { "walkbackward.kf", "walkback" },
            { "walkleft.kf", "walkleft" },
            { "walkright.kf", "walkright" },
            { "walkfastforward.kf", "runforward" },
            { "walkfastbackward.kf", "runback" },
            { "walkfastleft.kf", "runleft" },
            { "walkfastright.kf", "runright" },
            { "walkturnleft.kf", "turnleft" },
            { "walkturnright.kf", "turnright" },
            { "sneakidle.kf", "idlesneak" },
            { "sneakforward.kf", "sneakforward" },
            { "sneakbackward.kf", "sneakback" },
            { "sneakleft.kf", "sneakleft" },
            { "sneakright.kf", "sneakright" },
            { "swimidle.kf", "idleswim" },
            { "swimforward.kf", "swimwalkforward" },
            { "swimbackward.kf", "swimwalkback" },
            { "swimleft.kf", "swimwalkleft" },
            { "swimright.kf", "swimwalkright" },
            { "swimfastforward.kf", "swimrunforward" },
        } };
        return groups;
    }

    // Copy a loaded clip with every text key moved to the chosen group.
    inline osg::ref_ptr<SceneUtil::KeyframeHolder> tes4RenamedKeyframes(
        const SceneUtil::KeyframeHolder& source, std::string_view group)
    {
        osg::ref_ptr<SceneUtil::KeyframeHolder> renamed = new SceneUtil::KeyframeHolder;
        renamed->mKeyframeControllers = source.mKeyframeControllers;
        for (const auto& [time, key] : source.mTextKeys)
        {
            const auto separator = key.find(':');
            std::string text = separator == std::string::npos ? Misc::StringUtils::lowerCase(key)
                                                              : key.substr(separator + 1);
            renamed->mTextKeys.emplace(time, std::string(group) + ":" + text);
        }
        return renamed;
    }
}

#endif
