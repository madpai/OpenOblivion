// SPDX-License-Identifier: GPL-3.0-only
// Independently authored TES4 snapshots for the private preview.
// Included once by the audited OpenMW types.cpp translation unit.
#include <components/esm4/loadcont.hpp>
#include <components/esm4/loadcrea.hpp>
#include <components/esm4/loadnpc.hpp>
#include <apps/openmw/mwworld/class.hpp>
#include <apps/openmw/mwworld/esmstore.hpp>
#include <apps/openmw/mwworld/manualref.hpp>

namespace MWLua
{
    namespace
    {
        template <class Record>
        void addTes4NameSnapshot(sol::table type, const Context& context)
        {
            type["record"] = [lua = context.sol()](const Object& object) mutable -> sol::table {
                const MWWorld::Ptr& ptr = verifyType(Record::sRecordId, object.ptr());
                const Record& record = *ptr.get<Record>()->mBase;
                sol::table result = lua.create_table();
                result["id"] = ESM::RefId(record.mId).serializeText();
                result["name"] = std::string(ptr.getClass().getName(ptr));
                return result; // Copy; never a mutable game record.
            };
        }
    }

    void addESM4NpcBindings(sol::table npc, const Context& context)
    {
        addTes4NameSnapshot<ESM4::Npc>(npc, context);
    }

    void addESM4CreatureBindings(sol::table creature, const Context& context)
    {
        addTes4NameSnapshot<ESM4::Creature>(creature, context);
    }

    void addESM4ContainerBindings(sol::table container, const Context& context)
    {
        addTes4NameSnapshot<ESM4::Container>(container, context);
        container["contents"] = [lua = context.sol()](const Object& object) mutable -> sol::table {
            const MWWorld::Ptr& ptr = verifyType(ESM::REC_CONT4, object.ptr());
            const auto& inventory = ptr.get<ESM4::Container>()->mBase->mInventory;
            const MWWorld::ESMStore& store = *MWBase::Environment::get().getESMStore();
            sol::table result = lua.create_table();
            size_t index = 1;
            for (const ESM4::InventoryItem& entry : inventory)
            {
                const ESM::RefId id(ESM::FormId::fromUint32(entry.item));
                sol::table row = lua.create_table();
                row["recordId"] = id.serializeText();
                row["count"] = entry.count;
                // Base snapshots do not consume RNG or create live inventory.
                std::string name;
                try
                {
                    MWWorld::ManualRef item(store, id);
                    name = item.getPtr().getClass().getName(item.getPtr());
                }
                catch (const std::exception&)
                {
                    // Keep missing/leveled entries visible without exposing IDs.
                }
                row["name"] = name;
                result[index++] = row;
            }
            return result;
        };
    }
}
