-- SPDX-License-Identifier: GPL-3.0-only
-- Bounded native record/activation probe using only the supplied local scene.
local world = require('openmw.world')
local types = require('openmw.types')
local core = require('openmw.core')
local elapsed, completed = 0, false

return {
    engineHandlers = {
        onUpdate = function(dt)
            elapsed = elapsed + dt
            if completed or elapsed < 2 then return end
            completed = true
            local player = world.players[1]
            assert(player ~= nil and player.cell ~= nil, 'player cell required')
            local actors, containers, rows = 0, 0, 0
            for _, npc in ipairs(player.cell:getAll(types.ESM4Npc)) do
                local record = types.ESM4Npc.record(npc)
                assert(type(record.name) == 'string' and record.name ~= '', 'NPC name missing')
                actors = actors + 1
                print('OPENOBLIVION_TES4_NAME name=' .. record.name)
            end
            local target
            for _, object in ipairs(player.cell:getAll(types.ESM4Container)) do
                local record = types.ESM4Container.record(object)
                local contents = types.ESM4Container.contents(object)
                assert(type(record.name) == 'string', 'container name missing')
                assert(type(contents) == 'table', 'container contents missing')
                for _, item in ipairs(contents) do
                    assert(type(item.name) == 'string' and type(item.count) == 'number', 'invalid snapshot row')
                    rows = rows + 1
                end
                containers = containers + 1
                print('OPENOBLIVION_CONTAINER_PROBE name=' .. record.name
                    .. ' locked=' .. tostring(types.Lockable.isLocked(object))
                    .. ' enabled=' .. tostring(object.enabled))
                if target == nil and not types.Lockable.isLocked(object) then target = object end
            end
            assert(actors > 0 and containers > 0, 'scene must exercise NPCs and containers')
            if target ~= nil then
                print('OPENOBLIVION_CONTAINER_PROBE activate=' .. target.id)
                -- The activation event exercises the installed global handler and UI.
                target:activateBy(player)
            end
            print('OPENOBLIVION_TES4_INTERACTIONS actors=' .. actors .. ' containers=' .. containers .. ' rows=' .. rows)
        end,
    },
}
