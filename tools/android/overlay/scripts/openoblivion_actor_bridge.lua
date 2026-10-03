-- SPDX-License-Identifier: GPL-3.0-only
-- TES4 actor bridge. Classic NPCs load as animated objects without physics,
-- stats or AI. When one becomes active, replace it with a host actor proxy that
-- carries the TES4 NPC's record ID in its head field; the native TES4 renderer
-- draws that NPC's body, outfit and original animations, while the host actor
-- supplies collision, pathfinding, AI and death. The TES4 object is disabled.
local types = require('openmw.types')
local world = require('openmw.world')

local proxyRecords = {}

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

return {
    engineHandlers = {
        onObjectActive = function(object)
            if not types.ESM4Npc or not types.ESM4Npc.objectIsInstance(object) or not object.enabled then return end
            if #world.players == 0 then return end
            local record = types.ESM4Npc.record(object)
            local proxy = world.createObject(proxyRecord(object), 1)
            proxy:teleport(object.cell, object.position, { rotation = object.rotation })
            proxy:addScript('scripts/openoblivion_bridge_actor.lua', { formId = formId(record.id), name = record.name })
            object.enabled = false
            print('OPENOBLIVION_ACTOR_BRIDGE ' .. tostring(record.name) .. ' ' .. tostring(record.id))
        end,
    },
}
