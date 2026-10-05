-- SPDX-License-Identifier: GPL-3.0-only
-- TES4 actor bridge. Classic NPCs load as animated objects without physics,
-- stats or AI. When one becomes active, replace it with a host actor proxy that
-- carries the TES4 NPC's record ID in its head field; the native TES4 renderer
-- draws that NPC's body, outfit and original animations, while the host actor
-- supplies collision, pathfinding, AI and death. The TES4 object is disabled.
--
-- Items: the proxy gets the NPC record's inventory, rolled through the TES4
-- leveled lists. Apparel and melee weapons go on now (drawn from the host
-- equipment; the TES4 combat layer fights with the wielded weapon); bows,
-- staves and everything else are held back until death, then placed on the
-- body for looting. The player receives the Player record's starting items.
local items = require('scripts.openoblivion_tes4_items')
local I = require('openmw.interfaces')
local types = require('openmw.types')
local world = require('openmw.world')

local proxyRecords = {}
local playersEquipped = {}

local function give(actor, rows)
    local inventory = types.Actor.inventory(actor)
    for _, row in ipairs(rows) do
        local made, object = pcall(world.createObject, row.id, row.count)
        if made then object:moveInto(inventory) else print('OPENOBLIVION_ITEMS missing ' .. row.id) end
    end
end

local function playerLevel()
    local player = world.players[1]
    return player and types.Actor.stats.level(player).current or 1
end

local function proxyRecord(npc)
    local record = types.ESM4Npc.record(npc)
    if proxyRecords[record.id] then return proxyRecords[record.id] end
    local template = types.NPC.record(world.players[1].recordId)
    local draft = types.NPC.createRecordDraft({ template = template, name = record.name, head = record.id })
    local created = world.createRecord(draft)
    proxyRecords[record.id] = created.id
    return created.id
end

local function formId(recordId)
    local hex = recordId:match('0x(%x+)')
    return hex and (tonumber(hex, 16) % 0x1000000) or nil
end

-- Activating a living bridged NPC opens the TES4 conversation window instead of the host's
-- dialogue window. The NPC's base record is the `head` of its proxy record.
local function conversationBase(object)
    local ok, record = pcall(types.NPC.record, object)
    if not ok or not record or type(record.head) ~= 'string' then return nil end
    return formId(record.head)
end

if I.Activation and I.Activation.addHandlerForType then
    I.Activation.addHandlerForType(types.NPC, function(object, actor)
        local base = conversationBase(object)
        local game = I.OpenOblivionTES4
        if not base or not game or not types.Player.objectIsInstance(actor) then return end
        if types.Actor.isDead(object) then return end
        if game.talk(object, actor, base) then return false end
    end)
end

return {
    eventHandlers = {
        -- Desktop probes and scripts: put a generated item in an actor's inventory.
        TES4Give = function(event)
            if event.actor and event.id then give(event.actor, { { id = event.id, count = event.count or 1 } }) end
        end,
        -- A proxy died: its held-back items go on the body.
        TES4Loot = function(event)
            if event.actor and event.items then give(event.actor, event.items) end
        end,
    },
    engineHandlers = {
        onPlayerAdded = function(player)
            if playersEquipped[player.id] or not items.available then return end
            playersEquipped[player.id] = true
            local rows = items.inventory(7, 1)
            give(player, rows)
            player:sendEvent('TES4EquipApparel')
            print('OPENOBLIVION_ITEMS player starts with ' .. #rows .. ' items')
        end,
        onSave = function() return { playersEquipped = playersEquipped } end,
        onLoad = function(saved) playersEquipped = saved and saved.playersEquipped or {} end,
        onObjectActive = function(object)
            if not types.ESM4Npc or not types.ESM4Npc.objectIsInstance(object) or not object.enabled then return end
            if #world.players == 0 then return end
            local record = types.ESM4Npc.record(object)
            local proxy = world.createObject(proxyRecord(object), 1)
            proxy:teleport(object.cell, object.position, { rotation = object.rotation })
            local apparel, held = {}, {}
            for _, row in ipairs(items.inventory(formId(record.id), playerLevel())) do
                table.insert((items.isApparel(row.id) or items.isMeleeWeapon(row.id)) and apparel or held, row)
            end
            give(proxy, apparel)
            proxy:addScript('scripts/openoblivion_bridge_actor.lua',
                { formId = formId(record.id), name = record.name, held = held })
            print(string.format('OPENOBLIVION_ITEMS %s wears %d held %d', tostring(record.name), #apparel, #held))
            object.enabled = false
            print('OPENOBLIVION_ACTOR_BRIDGE ' .. tostring(record.name) .. ' ' .. tostring(record.id))
        end,
    },
}
