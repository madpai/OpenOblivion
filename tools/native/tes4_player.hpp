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
#include <components/esm4/loadweap.hpp>
#include <components/misc/strings/algorithm.hpp>
#include <components/misc/strings/lower.hpp>
#include <components/misc/resourcehelpers.hpp>
#include <components/resource/imagemanager.hpp>
#include <components/resource/resourcesystem.hpp>
#include <components/resource/scenemanager.hpp>
#include <components/sceneutil/keyframe.hpp>
#include <components/sceneutil/texturetype.hpp>
#include <components/sceneutil/nodecallback.hpp>

#include <osg/Material>
#include <osg/MatrixTransform>
#include <osg/StateSet>
#include <osg/Texture2D>

#include "../mwclass/esm4base.hpp"
#include "openoblivion_tes4_crash.hpp"
#include "../mwworld/cellref.hpp"
#include "../mwworld/class.hpp"
#include "../mwworld/esmstore.hpp"
#include "../mwworld/inventorystore.hpp"
#include "../mwworld/ptr.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <map>
#include <cstdlib>
#include <cstring>
#include <string>
#include <string_view>
#include <tuple>
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
        tes4InstallCrashLog(); // first reached on the game thread
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
        std::vector<std::uint32_t> mSlots; // per model
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
            if (model.empty()) // many items have one biped model for both sexes
                model = tes4PathText(record.mModelMale);
            if (model.empty())
                model = tes4PathText(record.mModel);
            if (model.empty())
                return;
            worn.mModels.push_back(model);
            worn.mSlots.push_back(flags & 0xffff);
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

    // One attached mesh and how the original draws it: a texture replacing the
    // mesh's own (race head parts, the NPC's baked FaceGen face, hair and eye
    // icons) and the hair colour that tints it.
    struct Tes4PartLook
    {
        std::string mModel;
        std::string mTexture;
        std::string mFallbackTexture; // when mTexture is not in the data (no baked face)
        bool mOpaque = false; // skin: the original ignores texture alpha
        bool mRigidHead = false; // an unskinned mesh in head bind space (hair), carried by the head bone
        bool mTinted = false;
        float mTint[3] = { 1.f, 1.f, 1.f };
    };

    // The NPC's baked FaceGen head texture. The Construction Set writes one per
    // NPC next to the master; it is the original's face for that record. The
    // Player and runtime-generated characters have none.
    inline std::string tes4BakedFaceTexture(const ESM4::Npc& npc, const MWWorld::ESMStore& store)
    {
        // Baked faces are filed under the plugin name; only the master's are known.
        const ESM4::Npc* player = tes4PlayerRecord(store);
        if (player == nullptr || npc.mId.mContentFile != player->mId.mContentFile)
            return {};
        char name[80];
        std::snprintf(name, sizeof(name), "textures\\faces\\oblivion.esm\\%08x_0.dds", npc.mId.mIndex & 0xffffff);
        return name;
    }

    // Body, head and hair meshes, in the order the TES4 NPC renderer attaches them.
    // First person uses the original _1stperson skeleton/clips and only body parts
    // (arms and hands); the head and hair would sit in front of the camera.
    inline std::vector<Tes4PartLook> tes4PlayerParts(
        const ESM4::Npc& npc, const MWWorld::ESMStore& store, bool firstPerson, const MWWorld::Ptr& ptr = {})
    {
        std::vector<Tes4PartLook> parts;
        const Tes4Worn worn = tes4PlayerWorn(npc, store, ptr);
        const bool female = tes4PlayerFemale(npc);
        // TES4 race records carry body textures, not body meshes; the bare body
        // is the fixed set in Characters\_Male (female meshes share that folder).
        // A worn item replaces the body piece in its slot.
        const std::string_view prefix = female ? "female" : "";
        const ESM4::Race* race = store.get<ESM4::Race>().search(npc.mRace);
        // The race gives each body piece its own skin texture (list order: upper body,
        // legs, hands, feet); the meshes' own paths are the Imperial default.
        auto raceBodyTexture = [&](std::size_t index) -> std::string {
            if (race == nullptr)
                return {};
            if (female && index < race->mBodyPartsFemale.size() && !race->mBodyPartsFemale[index].texture.empty())
                return race->mBodyPartsFemale[index].texture;
            return index < race->mBodyPartsMale.size() ? race->mBodyPartsMale[index].texture : std::string();
        };
        const std::tuple<std::string_view, std::uint32_t, std::size_t> pieces[] = { { "upperbody", sTes4SlotUpper, 0 },
            { "lowerbody", sTes4SlotLower, 1 }, { "hand", sTes4SlotHand, 2 }, { "foot", sTes4SlotFoot, 3 } };
        for (const auto& [piece, slot, index] : pieces)
            if ((worn.mCovered & slot) == 0 && (!firstPerson || slot == sTes4SlotUpper || slot == sTes4SlotHand))
                parts.push_back({ "Characters\\_Male\\" + std::string(prefix) + std::string(piece) + ".nif",
                    raceBodyTexture(index) });
        // First person shows only upper-body and hand pieces: the original
        // first-person clips do not pose the legs.
        for (std::size_t i = 0; i < worn.mModels.size(); ++i)
            if (!firstPerson || (worn.mSlots[i] & (sTes4SlotUpper | sTes4SlotHand)) != 0)
                parts.push_back({ worn.mModels[i], {} });
        if (race != nullptr)
        {
            for (const ESM4::Race::BodyPart& part : female ? race->mBodyPartsFemale : race->mBodyPartsMale)
                if (!part.mesh.empty())
                    parts.push_back({ part.mesh, {} });
            if (!firstPerson)
            {
                // Head parts by index: 0 head, 1/2 male/female ears, 3 mouth, 4/5 teeth,
                // 6 tongue, 7/8 eyes. The race gives each its own texture; the engine does
                // not load EYES records, so eyes keep the race's eye texture.
                // A part the female list leaves empty (the race shares one head
                // mesh between the sexes) comes from the male list.
                const std::vector<ESM4::Race::BodyPart>& head = race->mHeadParts;
                for (std::size_t i = 0; i < head.size(); ++i)
                {
                    const ESM4::Race::BodyPart& own = female && i < race->mHeadPartsFemale.size()
                            && !race->mHeadPartsFemale[i].mesh.empty()
                        ? race->mHeadPartsFemale[i]
                        : head[i];
                    if (own.mesh.empty() || (i == 1 && female) || (i == 2 && !female))
                        continue;
                    Tes4PartLook look{ own.mesh, own.texture.empty() ? head[i].texture : own.texture };
                    if (i == 0)
                    {
                        look.mOpaque = true;
                        const std::string face = tes4BakedFaceTexture(npc, store);
                        if (!face.empty())
                        {
                            look.mFallbackTexture = look.mTexture;
                            look.mTexture = face;
                        }
                    }
                    parts.push_back(std::move(look));
                }
            }
        }
        if (!firstPerson && (worn.mCovered & (sTes4SlotHead | sTes4SlotHair)) == 0 && !npc.mHair.isZeroOrUnset())
            if (const ESM4::Hair* hair = store.get<ESM4::Hair>().search(npc.mHair))
                if (!tes4PathText(hair->mModel).empty())
                {
                    Tes4PartLook look{ tes4PathText(hair->mModel), hair->mIcon };
                    look.mRigidHead = true;
                    look.mTinted = true;
                    look.mTint[0] = npc.mHairColour.red / 255.f;
                    look.mTint[1] = npc.mHairColour.green / 255.f;
                    look.mTint[2] = npc.mHairColour.blue / 255.f;
                    parts.push_back(std::move(look));
                }
        // Debug: OPENOBLIVION_HIDE_PART=<text> drops parts whose model path contains the text.
        if (const char* hide = std::getenv("OPENOBLIVION_HIDE_PART"); hide != nullptr && *hide != '\0')
            parts.erase(std::remove_if(parts.begin(), parts.end(),
                            [hide](const Tes4PartLook& part) {
                                return Misc::StringUtils::lowerCase(part.mModel).find(Misc::StringUtils::lowerCase(hide))
                                    != std::string::npos;
                            }),
                parts.end());
        return parts;
    }

    inline std::vector<std::string> tes4PlayerPartModels(
        const ESM4::Npc& npc, const MWWorld::ESMStore& store, bool firstPerson, const MWWorld::Ptr& ptr = {})
    {
        std::vector<std::string> models;
        for (const Tes4PartLook& part : tes4PlayerParts(npc, store, firstPerson, ptr))
            models.push_back(part.mModel);
        return models;
    }

    // The Construction Set's baked face textures carry a constant alpha of 127
    // that the original ignores. The host would alpha-test the whole head away,
    // so skin textures are used opaque. Edits a private copy of the image.
    inline void tes4ForceOpaque(osg::Image& image)
    {
        unsigned char* data = image.data();
        if (data == nullptr)
            return;
        const std::size_t size = image.getTotalSizeInBytesIncludingMipmaps();
        switch (image.getPixelFormat())
        {
            case GL_COMPRESSED_RGBA_S3TC_DXT5_EXT: // 8-byte alpha block first: both endpoints 255, all indices 0
                for (std::size_t i = 0; i + 16 <= size; i += 16)
                {
                    data[i] = data[i + 1] = 255;
                    std::memset(data + i + 2, 0, 6);
                }
                break;
            case GL_COMPRESSED_RGBA_S3TC_DXT3_EXT:
                for (std::size_t i = 0; i + 16 <= size; i += 16)
                    std::memset(data + i, 0xff, 8);
                break;
            case GL_RGBA:
                if (!image.isCompressed() && image.getDataType() == GL_UNSIGNED_BYTE)
                    for (std::size_t i = 3; i < size; i += 4)
                        data[i] = 255;
                break;
            default:
                break;
        }
    }

    // Decoded 8-bit RGBA of an image, or false: S3TC (DXT1/3/5) blocks and plain
    // 8-bit RGB/RGBA/BGR/BGRA. Level 0 only.
    inline bool tes4DecodeRgba(const osg::Image& image, std::vector<unsigned char>& rgba, int& width, int& height)
    {
        width = image.s();
        height = image.t();
        const unsigned char* data = image.data();
        if (data == nullptr || width <= 0 || height <= 0)
            return false;
        rgba.assign(static_cast<std::size_t>(width) * height * 4, 255);
        const GLenum format = image.getPixelFormat();
        auto expand = [](unsigned c, unsigned char* out) {
            out[0] = static_cast<unsigned char>(((c >> 11) & 31) * 255 / 31);
            out[1] = static_cast<unsigned char>(((c >> 5) & 63) * 255 / 63);
            out[2] = static_cast<unsigned char>((c & 31) * 255 / 31);
        };
        if (format == GL_COMPRESSED_RGB_S3TC_DXT1_EXT || format == GL_COMPRESSED_RGBA_S3TC_DXT1_EXT
            || format == GL_COMPRESSED_RGBA_S3TC_DXT3_EXT || format == GL_COMPRESSED_RGBA_S3TC_DXT5_EXT)
        {
            const bool dxt1 = format == GL_COMPRESSED_RGB_S3TC_DXT1_EXT || format == GL_COMPRESSED_RGBA_S3TC_DXT1_EXT;
            const bool dxt3 = format == GL_COMPRESSED_RGBA_S3TC_DXT3_EXT;
            const std::size_t blockSize = dxt1 ? 8 : 16;
            for (int by = 0; by < (height + 3) / 4; ++by)
                for (int bx = 0; bx < (width + 3) / 4; ++bx)
                {
                    const unsigned char* block = data + (static_cast<std::size_t>(by) * ((width + 3) / 4) + bx) * blockSize;
                    const unsigned char* color = block + (dxt1 ? 0 : 8);
                    const unsigned c0 = color[0] | (color[1] << 8), c1 = color[2] | (color[3] << 8);
                    unsigned char palette[4][4];
                    expand(c0, palette[0]);
                    expand(c1, palette[1]);
                    palette[0][3] = palette[1][3] = palette[2][3] = palette[3][3] = 255;
                    for (int k = 0; k < 3; ++k)
                    {
                        if (c0 > c1 || !dxt1)
                        {
                            palette[2][k] = static_cast<unsigned char>((2 * palette[0][k] + palette[1][k]) / 3);
                            palette[3][k] = static_cast<unsigned char>((palette[0][k] + 2 * palette[1][k]) / 3);
                        }
                        else
                        {
                            palette[2][k] = static_cast<unsigned char>((palette[0][k] + palette[1][k]) / 2);
                            palette[3][k] = 0;
                        }
                    }
                    if (dxt1 && c0 <= c1)
                        palette[3][3] = 0;
                    // Alpha: DXT5 interpolated, DXT3 explicit 4-bit.
                    unsigned char alpha[16];
                    std::fill(alpha, alpha + 16, static_cast<unsigned char>(255));
                    if (dxt3)
                    {
                        for (int i = 0; i < 16; ++i)
                            alpha[i] = static_cast<unsigned char>(((block[i / 2] >> ((i & 1) * 4)) & 15) * 17);
                    }
                    else if (!dxt1)
                    {
                        unsigned char table[8];
                        table[0] = block[0];
                        table[1] = block[1];
                        if (table[0] > table[1])
                            for (int k = 1; k < 7; ++k)
                                table[k + 1] = static_cast<unsigned char>(((7 - k) * table[0] + k * table[1]) / 7);
                        else
                        {
                            for (int k = 1; k < 5; ++k)
                                table[k + 1] = static_cast<unsigned char>(((5 - k) * table[0] + k * table[1]) / 5);
                            table[6] = 0;
                            table[7] = 255;
                        }
                        std::uint64_t bits = 0;
                        for (int k = 0; k < 6; ++k)
                            bits |= static_cast<std::uint64_t>(block[2 + k]) << (8 * k);
                        for (int i = 0; i < 16; ++i)
                            alpha[i] = table[(bits >> (3 * i)) & 7];
                    }
                    const std::uint32_t indices = static_cast<std::uint32_t>(color[4]) | (static_cast<std::uint32_t>(color[5]) << 8)
                        | (static_cast<std::uint32_t>(color[6]) << 16) | (static_cast<std::uint32_t>(color[7]) << 24);
                    for (int i = 0; i < 16; ++i)
                    {
                        const int x = bx * 4 + (i & 3), y = by * 4 + (i >> 2);
                        if (x >= width || y >= height)
                            continue;
                        unsigned char* out = &rgba[(static_cast<std::size_t>(y) * width + x) * 4];
                        const unsigned char* texel = palette[(indices >> (2 * i)) & 3];
                        out[0] = texel[0];
                        out[1] = texel[1];
                        out[2] = texel[2];
                        out[3] = dxt1 ? texel[3] : alpha[i];
                    }
                }
            return true;
        }
        if (image.isCompressed() || image.getDataType() != GL_UNSIGNED_BYTE)
            return false;
        bool swap = false, hasAlpha = false;
        switch (format)
        {
            case GL_RGB:
                break;
            case GL_RGBA:
                hasAlpha = true;
                break;
            case GL_BGR:
                swap = true;
                break;
            case GL_BGRA:
                swap = hasAlpha = true;
                break;
            default:
                return false;
        }
        for (int y = 0; y < height; ++y)
            for (int x = 0; x < width; ++x)
            {
                const unsigned char* in = image.data(x, y);
                unsigned char* out = &rgba[(static_cast<std::size_t>(y) * width + x) * 4];
                out[0] = in[swap ? 2 : 0];
                out[1] = in[1];
                out[2] = in[swap ? 0 : 2];
                out[3] = hasAlpha ? in[3] : 255;
            }
        return true;
    }

    // The face as the original builds it: the race head texture multiplied by
    // the NPC's baked FaceGen map twice over (a map of mid-grey leaves the
    // skin unchanged), as a Gamebryo detail map does. Opaque.
    inline osg::ref_ptr<osg::Image> tes4ComposeFace(const osg::Image& base, const osg::Image& baked)
    {
        std::vector<unsigned char> head, map;
        int baseWidth = 0, baseHeight = 0, width = 0, height = 0;
        if (!tes4DecodeRgba(base, head, baseWidth, baseHeight) || !tes4DecodeRgba(baked, map, width, height))
            return nullptr;
        osg::ref_ptr<osg::Image> face = new osg::Image;
        face->allocateImage(width, height, 1, GL_RGBA, GL_UNSIGNED_BYTE);
        face->setInternalTextureFormat(GL_RGBA8);
        for (int y = 0; y < height; ++y)
            for (int x = 0; x < width; ++x)
            {
                // Bilinear sample of the base at the face map's pixel.
                const float u = (x + 0.5f) * baseWidth / width - 0.5f, v = (y + 0.5f) * baseHeight / height - 0.5f;
                const int x0 = std::clamp(static_cast<int>(std::floor(u)), 0, baseWidth - 1);
                const int y0 = std::clamp(static_cast<int>(std::floor(v)), 0, baseHeight - 1);
                const int x1 = std::min(x0 + 1, baseWidth - 1), y1 = std::min(y0 + 1, baseHeight - 1);
                const float fx = std::clamp(u - x0, 0.f, 1.f), fy = std::clamp(v - y0, 0.f, 1.f);
                unsigned char* out = face->data(x, y);
                for (int c = 0; c < 3; ++c)
                {
                    auto at = [&](int px, int py) {
                        return static_cast<float>(head[(static_cast<std::size_t>(py) * baseWidth + px) * 4 + c]);
                    };
                    const float baseValue = (at(x0, y0) * (1 - fx) + at(x1, y0) * fx) * (1 - fy)
                        + (at(x0, y1) * (1 - fx) + at(x1, y1) * fx) * fy;
                    const float tint = map[(static_cast<std::size_t>(y) * width + x) * 4 + c] / 255.f;
                    out[c] = static_cast<unsigned char>(std::clamp(baseValue * tint * 2.f, 0.f, 255.f));
                }
                out[3] = 255;
            }
        return face;
    }

    // As MWRender::overrideTexture, with the skin alpha removed.
    // With a base texture, the image is that base multiplied by the face map (tes4ComposeFace).
    inline void tes4OverrideOpaqueTexture(VFS::Path::NormalizedView texture, Resource::ResourceSystem* resourceSystem,
        osg::Node& node, VFS::Path::NormalizedView base = {})
    {
        static std::map<std::string, osg::ref_ptr<osg::Texture2D>> cache;
        osg::ref_ptr<osg::Texture2D>& tex = cache[std::string(texture.value()) + "|" + std::string(base.value())];
        if (!tex)
        {
            osg::ref_ptr<osg::Image> image;
            if (!base.value().empty())
                image = tes4ComposeFace(*resourceSystem->getImageManager()->getImage(base),
                    *resourceSystem->getImageManager()->getImage(texture));
            if (!image)
            {
                image = new osg::Image(*resourceSystem->getImageManager()->getImage(texture), osg::CopyOp::DEEP_COPY_ALL);
                tes4ForceOpaque(*image);
            }
            tex = new osg::Texture2D(image);
            tex->setWrap(osg::Texture::WRAP_S, osg::Texture::CLAMP_TO_EDGE);
            tex->setWrap(osg::Texture::WRAP_T, osg::Texture::CLAMP_TO_EDGE);
            resourceSystem->getSceneManager()->applyFilterSettings(tex);
        }
        osg::ref_ptr<osg::StateSet> stateset;
        if (const osg::StateSet* const source = node.getStateSet())
            stateset = new osg::StateSet(*source, osg::CopyOp::SHALLOW_COPY);
        else
            stateset = new osg::StateSet;
        stateset->setTextureAttribute(0, tex, osg::StateAttribute::OVERRIDE);
        stateset->setTextureAttribute(0, new SceneUtil::TextureType("diffuseMap"), osg::StateAttribute::OVERRIDE);
        node.setStateSet(stateset);
    }

    // As MWRender::overrideTexture, with the colour channels multiplied by the
    // hair colour (alpha kept, so strands stay cut out). The original tints hair
    // by modulating its neutral-grey texture; tinting a material instead gave
    // wrong hues on the host's shaders.
    inline void tes4OverrideTintedTexture(VFS::Path::NormalizedView texture, Resource::ResourceSystem* resourceSystem,
        osg::Node& node, const float* rgb)
    {
        static std::map<std::string, osg::ref_ptr<osg::Texture2D>> cache;
        char key[64];
        std::snprintf(key, sizeof(key), "|%.3f,%.3f,%.3f", rgb[0], rgb[1], rgb[2]);
        osg::ref_ptr<osg::Texture2D>& tex = cache[std::string(texture.value()) + key];
        if (!tex)
        {
            std::vector<unsigned char> pixels;
            int width = 0, height = 0;
            osg::ref_ptr<osg::Image> source = resourceSystem->getImageManager()->getImage(texture);
            if (!tes4DecodeRgba(*source, pixels, width, height))
                return;
            osg::ref_ptr<osg::Image> image = new osg::Image;
            image->allocateImage(width, height, 1, GL_RGBA, GL_UNSIGNED_BYTE);
            image->setInternalTextureFormat(GL_RGBA8);
            for (int y = 0; y < height; ++y)
                for (int x = 0; x < width; ++x)
                {
                    const unsigned char* in = &pixels[(static_cast<std::size_t>(y) * width + x) * 4];
                    unsigned char* out = image->data(x, y);
                    for (int c = 0; c < 3; ++c)
                        out[c] = static_cast<unsigned char>(std::clamp(in[c] * rgb[c], 0.f, 255.f));
                    out[3] = in[3];
                }
            tex = new osg::Texture2D(image);
            tex->setWrap(osg::Texture::WRAP_S, osg::Texture::CLAMP_TO_EDGE);
            tex->setWrap(osg::Texture::WRAP_T, osg::Texture::CLAMP_TO_EDGE);
            resourceSystem->getSceneManager()->applyFilterSettings(tex);
        }
        osg::ref_ptr<osg::StateSet> stateset;
        if (const osg::StateSet* const source = node.getStateSet())
            stateset = new osg::StateSet(*source, osg::CopyOp::SHALLOW_COPY);
        else
            stateset = new osg::StateSet;
        stateset->setTextureAttribute(0, tex, osg::StateAttribute::OVERRIDE);
        stateset->setTextureAttribute(0, new SceneUtil::TextureType("diffuseMap"), osg::StateAttribute::OVERRIDE);
        node.setStateSet(stateset);
    }

    // The weapon an actor carries in its right hand slot: the TES4 mesh, the
    // host animation short group it selects, and the skeleton node that holds
    // it holstered. TES4 weapon types 0..5 are generated as host types
    // LongBladeOneHand, LongBladeTwoHand, BluntOneHand, BluntTwoClose,
    // BluntTwoWide (staff) and MarksmanBow (tools/android/tes4_items.py).
    struct Tes4WeaponLook
    {
        std::string mModel;
        std::string mShort; // host weapon short group: 1h 2c 1b 2b 2w bow
        const char* mSheath = "sideweapon";
    };

    inline Tes4WeaponLook tes4EquippedWeapon(const MWWorld::Ptr& ptr, const MWWorld::ESMStore& store)
    {
        Tes4WeaponLook look;
        if (ptr.isEmpty() || !tes4HostItemsLoaded(store) || !ptr.getClass().hasInventoryStore(ptr))
            return look;
        const MWWorld::InventoryStore& inventory = ptr.getClass().getInventoryStore(ptr);
        const auto equipped = inventory.getSlot(MWWorld::InventoryStore::Slot_CarriedRight);
        if (equipped == inventory.cend())
            return look;
        const ESM4::Weapon* weapon
            = store.get<ESM4::Weapon>().search(tes4ItemRecordId(equipped->getCellRef().getRefId(), store));
        if (weapon == nullptr || tes4PathText(weapon->mModel).empty())
            return look;
        static constexpr const char* shorts[] = { "1h", "2c", "1b", "2b", "2w", "bow" };
        if (weapon->mData.type > 5)
            return look;
        look.mModel = tes4PathText(weapon->mModel);
        look.mShort = shorts[weapon->mData.type];
        // One-handed weapons hang at the hip; two-handed weapons, staves and bows on the back.
        look.mSheath = (weapon->mData.type == 0 || weapon->mData.type == 2) ? "sideweapon" : "backweapon";
        return look;
    }

    // Original clips of a weapon family as (file, host group) pairs. The host
    // groups are the weapon short group suffixed variants of the plain names.
    inline std::vector<std::pair<std::string, std::string>> tes4WeaponClips(std::string_view shortGroup)
    {
        std::vector<std::pair<std::string, std::string>> clips;
        std::string_view family;
        if (shortGroup == "1h" || shortGroup == "1b")
            family = "onehand";
        else if (shortGroup == "2c" || shortGroup == "2b")
            family = "twohand";
        else if (shortGroup == "2w")
            family = "staff";
        else if (shortGroup == "bow")
            family = "bow";
        else
            return clips;
        static constexpr std::pair<std::string_view, std::string_view> names[] = { { "idle", "idle" },
            { "forward", "walkforward" }, { "backward", "walkback" }, { "left", "walkleft" },
            { "right", "walkright" }, { "fastforward", "runforward" }, { "fastbackward", "runback" },
            { "fastleft", "runleft" }, { "fastright", "runright" }, { "turnleft", "turnleft" },
            { "turnright", "turnright" }, { "equip", "tes4equip" }, { "unequip", "tes4unequip" },
            { "attackright", "tes4attackright" }, { "attackleft", "tes4attackleft" },
            { "attackpower", "tes4attackpower" }, { "attack", "tes4attackright" }, { "blockidle", "tes4blockidle" },
            { "stagger", "tes4stagger" }, { "recoil_01", "tes4recoil" } };
        for (const auto& [suffix, group] : names)
            clips.emplace_back(std::string(family) + std::string(suffix) + ".kf", std::string(group) + std::string(shortGroup));
        return clips;
    }

    // Identifies the attached part set and weapon family, so an equipment
    // change can rebuild it.
    inline std::string tes4PartSignature(const std::vector<std::string>& models, std::string_view weaponShort = {})
    {
        std::string signature;
        for (const std::string& model : models)
            signature += Misc::StringUtils::lowerCase(model) + '|';
        return signature + '#' + std::string(weaponShort);
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

    // First-person view pitch for the TES4 rig. The host pitches only the neck
    // so the arms follow the view; on a TES4 first-person skeleton that bends
    // the arms away from a still torso and stretches worn upper-body meshes.
    // Instead pitch the whole rig ("Bip01") rigidly about Camera01, which every
    // original first-person clip animates, so the view point does not move.
    class Tes4FirstPersonPitch : public SceneUtil::NodeCallback<Tes4FirstPersonPitch, osg::MatrixTransform*>
    {
    public:
        Tes4FirstPersonPitch(osg::Node* relativeTo, osg::Node* camera)
            : mRelativeTo(relativeTo)
            , mCamera(camera)
        {
        }

        void setPitch(float pitch) { mRotate = osg::Quat(pitch, osg::Vec3f(-1, 0, 0)); }
        void setOffset(const osg::Vec3f& offset) { mOffset = offset; }

        void operator()(osg::MatrixTransform* node, osg::NodeVisitor* nv)
        {
            // Without a keyframe update this frame, start again from the animated pose.
            osg::Matrix matrix = node->getMatrix();
            if (matrix == mWritten)
                matrix = mBase;
            else
                mBase = matrix;
            osg::Quat worldOrient;
            const osg::NodePathList paths = node->getParentalNodePaths(mRelativeTo);
            if (!paths.empty())
                worldOrient = osg::computeLocalToWorld(paths[0]).getRotate();
            const osg::Quat worldOrientInverse = worldOrient.inverse();
            osg::Vec3f before = matrix.getTrans();
            const osg::NodePathList cameraPaths = mCamera->getParentalNodePaths(node);
            if (!cameraPaths.empty())
            {
                osg::NodePath path = cameraPaths[0];
                if (!path.empty() && path.front() == node)
                    path.erase(path.begin());
                before = osg::computeLocalToWorld(path).getTrans() * matrix;
            }
            const osg::Vec3f local = before * osg::Matrix::inverse(matrix);
            osg::Matrix rotated = matrix;
            rotated.setRotate(worldOrient * mRotate * worldOrientInverse * matrix.getRotate());
            rotated.setTrans(rotated.getTrans() + (before - local * rotated) + worldOrientInverse * mOffset);
            node->setMatrix(rotated);
            mWritten = rotated;
            traverse(node, nv);
        }

    private:
        osg::Quat mRotate;
        osg::Vec3f mOffset;
        osg::Node* mRelativeTo;
        osg::ref_ptr<osg::Node> mCamera;
        osg::Matrix mBase;
        osg::Matrix mWritten;
    };

    inline Tes4FirstPersonPitch* tes4FirstPersonPitch(osg::Node* root)
    {
        osg::UserDataContainer* data = root != nullptr ? root->getUserDataContainer() : nullptr;
        return data != nullptr ? dynamic_cast<Tes4FirstPersonPitch*>(data->getUserObject("openoblivionPitch")) : nullptr;
    }

    // The original first-person readied movement clips leave the torso bones
    // unanimated, which stretches worn upper-body meshes; first person moves
    // with the plain clips and keeps the readied idle on the arms instead.
    inline bool tes4UseClip(std::string_view group, bool firstPerson)
    {
        return !firstPerson || group == "idlehh" || group.size() < 2 || group.substr(group.size() - 2) != "hh";
    }

    // Copy a loaded clip with every text key moved to the chosen group.
    // First-person clips each pose the whole rig and are not made to be mixed
    // by body half (lower-body idle with upper-body readied idle twisted the
    // torso and stretched the shirt). Naming every controller after the host's
    // torso blend root puts the whole rig in one blend group.
    inline osg::ref_ptr<SceneUtil::KeyframeHolder> tes4RenamedKeyframes(
        const SceneUtil::KeyframeHolder& source, std::string_view group, bool wholeRig = false)
    {
        osg::ref_ptr<SceneUtil::KeyframeHolder> renamed = new SceneUtil::KeyframeHolder;
        renamed->mKeyframeControllers = source.mKeyframeControllers;
        if (wholeRig)
            for (auto& [bone, controller] : renamed->mKeyframeControllers)
            {
                osg::ref_ptr<SceneUtil::KeyframeController> copy
                    = osg::clone(controller.get(), osg::CopyOp::SHALLOW_COPY);
                copy->setName("Bip01 Spine1");
                controller = copy;
            }
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
