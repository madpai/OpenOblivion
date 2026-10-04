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
#include <components/esm3/loadmisc.hpp>
#include <components/esm4/loadarmo.hpp>
#include <components/esm4/loadclot.hpp>
#include <components/esm4/loadlvli.hpp>
#include <components/esm4/loadhair.hpp>
#include <components/esm4/loadnpc.hpp>
#include <components/esm4/loadrace.hpp>
#include <components/misc/strings/algorithm.hpp>
#include <components/misc/strings/lower.hpp>
#include <components/sceneutil/keyframe.hpp>

#include "../mwclass/esm4base.hpp"
#include "../mwworld/cellref.hpp"
#include "../mwworld/class.hpp"
#include "../mwworld/esmstore.hpp"
#include "../mwworld/inventorystore.hpp"
#include "../mwworld/ptr.hpp"

#include <algorithm>
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

    inline const ESM4::Npc* tes4PlayerRecord(const MWWorld::ESMStore& store);

    // The TES4 NPC this host actor stands for: the master's Player record for the
    // engine player, or, for an actor-bridge proxy, the ESM4 NPC whose record ID
    // the proxy carries in its (otherwise unused) head field.
    inline const ESM4::Npc* tes4ActorRecordFor(
        const MWWorld::Ptr& ptr, const ESM::RefId& head, const MWWorld::ESMStore& store)
    {
        if (!tes4PlayerEnabled() || ptr.isEmpty())
            return nullptr;
        if (ptr.getCellRef().getRefId() == ESM::RefId::stringRefId("Player"))
            return tes4PlayerRecord(store);
        if (!head.is<ESM::FormId>())
            return nullptr;
        const ESM4::Npc* npc = store.get<ESM4::Npc>().search(head);
        return npc != nullptr && npc->mIsTES4 && !tes4PathText(npc->mModel).empty() ? npc : nullptr;
    }

    inline const ESM4::Npc* tes4PlayerRecord(const MWWorld::ESMStore& store)
    {
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

    // TES4 biped slot bits (BMDT) that hide the bare body piece they cover.
    inline constexpr std::uint32_t sTes4SlotHead = 0x01, sTes4SlotHair = 0x02, sTes4SlotUpper = 0x04,
                                   sTes4SlotLower = 0x08, sTes4SlotHand = 0x10, sTes4SlotFoot = 0x20;

    struct Tes4Worn
    {
        std::vector<std::string> mModels;
        std::vector<ESM::RefId> mIds;
        std::uint32_t mCovered = 0;
    };

    // Host item records generated from TES4 items (openoblivion_rules.omwaddon)
    // are named "oo4_" + the master FormID's low 24 bits in hex.
    inline constexpr std::string_view sTes4ItemPrefix = "oo4_";

    inline bool tes4HostItemsLoaded(const MWWorld::ESMStore& store)
    {
        return store.get<ESM::Miscellaneous>().search(ESM::RefId::stringRefId("oo4_items")) != nullptr;
    }

    // The master record a generated host item stands for.
    inline ESM::RefId tes4ItemRecordId(const ESM::RefId& hostId, const MWWorld::ESMStore& store)
    {
        const ESM4::Npc* player = tes4PlayerRecord(store);
        if (player == nullptr || !hostId.startsWith(sTes4ItemPrefix))
            return {};
        const std::string text = hostId.getRefIdString();
        std::uint32_t index = 0;
        for (const char c : std::string_view(text).substr(sTes4ItemPrefix.size()))
        {
            const int digit = c >= '0' && c <= '9' ? c - '0' : (c | 0x20) >= 'a' && (c | 0x20) <= 'f' ? (c | 0x20) - 'a' + 10 : -1;
            if (digit < 0)
                return {};
            index = index * 16 + static_cast<std::uint32_t>(digit);
        }
        return ESM::RefId::formIdRefId(ESM::FormId{ index & 0xffffff, player->mId.mContentFile });
    }

    // What the actor wears: with the generated host items loaded, the host
    // inventory's equipped items (so equipping, looting and stripping show);
    // otherwise everything wearable in the TES4 record's base inventory.
    inline Tes4Worn tes4PlayerWorn(const ESM4::Npc& npc, const MWWorld::ESMStore& store, const MWWorld::Ptr& ptr = {})
    {
        Tes4Worn worn;
        const bool female = tes4PlayerFemale(npc);
        auto add = [&](const auto& record, std::uint32_t flags) {
            std::string model = tes4PathText(female ? record.mModelFemale : record.mModelMale);
            if (model.empty())
                model = tes4PathText(record.mModel);
            if (model.empty())
                return;
            worn.mModels.push_back(model);
            worn.mCovered |= flags & 0xffff;
        };
        if (!ptr.isEmpty() && tes4HostItemsLoaded(store) && ptr.getClass().hasInventoryStore(ptr))
        {
            const MWWorld::InventoryStore& inventory = ptr.getClass().getInventoryStore(ptr);
            for (int slot = 0; slot < MWWorld::InventoryStore::Slots; ++slot)
            {
                const auto equipped = inventory.getSlot(slot);
                if (equipped == inventory.cend())
                    continue;
                const ESM::RefId id = tes4ItemRecordId(equipped->getCellRef().getRefId(), store);
                if (id.empty() || std::find(worn.mIds.begin(), worn.mIds.end(), id) != worn.mIds.end())
                    continue;
                worn.mIds.push_back(id);
                if (const auto* armor = store.get<ESM4::Armor>().search(id))
                    add(*armor, armor->mArmorFlags);
                else if (const auto* clothing = store.get<ESM4::Clothing>().search(id))
                    add(*clothing, clothing->mClothingFlags);
            }
            return worn;
        }
        for (const ESM4::InventoryItem& item : npc.mInventory)
        {
            const ESM::FormId id = ESM::FormId::fromUint32(item.item);
            if (const auto* armor = MWClass::ESM4Impl::resolveLevelled<ESM4::LevelledItem, ESM4::Armor>(id))
                add(*armor, armor->mArmorFlags);
            else if (const auto* clothing
                = MWClass::ESM4Impl::resolveLevelled<ESM4::LevelledItem, ESM4::Clothing>(id))
                add(*clothing, clothing->mClothingFlags);
        }
        return worn;
    }

    // Body, head and hair meshes, in the order the TES4 NPC renderer attaches them.
    // First person uses the original _1stperson skeleton/clips and only body parts
    // (arms and hands); the head and hair would sit in front of the camera.
    inline std::vector<std::string> tes4PlayerPartModels(
        const ESM4::Npc& npc, const MWWorld::ESMStore& store, bool firstPerson, const MWWorld::Ptr& ptr = {})
    {
        std::vector<std::string> models;
        const Tes4Worn worn = tes4PlayerWorn(npc, store, ptr);
        // TES4 race records carry body textures, not body meshes; the bare body
        // is the fixed set in Characters\_Male (female meshes share that folder).
        // A worn item replaces the body piece in its slot.
        const std::string_view prefix = tes4PlayerFemale(npc) ? "female" : "";
        const std::pair<std::string_view, std::uint32_t> pieces[] = { { "upperbody", sTes4SlotUpper },
            { "lowerbody", sTes4SlotLower }, { "hand", sTes4SlotHand }, { "foot", sTes4SlotFoot } };
        for (const auto& [piece, slot] : pieces)
            if ((worn.mCovered & slot) == 0 && (!firstPerson || slot == sTes4SlotUpper || slot == sTes4SlotHand))
                models.push_back("Characters\\_Male\\" + std::string(prefix) + std::string(piece) + ".nif");
        models.insert(models.end(), worn.mModels.begin(), worn.mModels.end());
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
        if (!firstPerson && (worn.mCovered & (sTes4SlotHead | sTes4SlotHair)) == 0 && !npc.mHair.isZeroOrUnset())
            if (const ESM4::Hair* hair = store.get<ESM4::Hair>().search(npc.mHair))
                if (!tes4PathText(hair->mModel).empty())
                    models.push_back(tes4PathText(hair->mModel));
        return models;
    }

    // Identifies the attached part set, so an equipment change can rebuild it.
    inline std::string tes4PartSignature(const std::vector<std::string>& models)
    {
        std::string signature;
        for (const std::string& model : models)
            signature += Misc::StringUtils::lowerCase(model) + '|';
        return signature;
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
    inline const std::array<std::pair<std::string_view, std::string_view>, 45>& tes4LocomotionGroups()
    {
        static const std::array<std::pair<std::string_view, std::string_view>, 45> groups{ {
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
            // Combat clips play through the TES4 rules layer (Lua), by these names.
            { "handtohandattackright.kf", "tes4attackright" },
            { "handtohandattackleft.kf", "tes4attackleft" },
            { "handtohandattackpower.kf", "tes4attackpower" },
            { "handtohandblockidle.kf", "tes4blockidle" },
            { "handtohandrecoil.kf", "tes4recoil" },
            { "handtohandstagger.kf", "tes4stagger" },
            // Readied fists: the host hand-to-hand stance ("hh") idle and movement.
            { "handtohandidle.kf", "idlehh" },
            { "handtohandforward.kf", "walkforwardhh" },
            { "handtohandbackward.kf", "walkbackhh" },
            { "handtohandleft.kf", "walklefthh" },
            { "handtohandright.kf", "walkrighthh" },
            { "handtohandfastforward.kf", "runforwardhh" },
            { "handtohandfastbackward.kf", "runbackhh" },
            { "handtohandfastleft.kf", "runlefthh" },
            { "handtohandfastright.kf", "runrighthh" },
            { "handtohandturnleft.kf", "turnlefthh" },
            { "handtohandturnright.kf", "turnrighthh" },
            { "handtohandequip.kf", "tes4equip" },
            { "handtohandunequip.kf", "tes4unequip" },
            { "jumpstart.kf", "tes4jumpstart" },
            { "jumploop.kf", "tes4jumploop" },
            { "jumpland.kf", "tes4jumpland" },
            // TES4 ragdolls on death; its posed-dead idle stands in as the host death clip.
            { "idleanims/deathidle.kf", "death1" },
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
