-- SPDX-License-Identifier: GPL-3.0-only
-- Exercise the packaged USE handler through ordinary activation events.
local world = require('openmw.world')
local types = require('openmw.types')
local util = require('openmw.util')
local config = require('scripts.openoblivion_door_config')
local openTime, closeTime, finishTime = 3, 7, 10
if config.traversal then openTime, closeTime, finishTime = 7, 12, 15 end
local elapsed, target, stage = 0, nil, 0
return {engineHandlers = {onUpdate = function(dt)
    elapsed = elapsed + dt
    local player = world.players[1]
    if elapsed >= 1 and stage == 0 then
        for _, door in ipairs(player.cell:getAll(types.ESM4Door)) do
            if (door.position - util.vector3(-4928, 64, -384)):length() < 1
                and not types.ESM4Door.isTeleport(door) and types.ESM4Door.hasSequence(door, 'Open')
                and types.ESM4Door.hasSequence(door, 'Close') then target = door; break end
        end
        assert(target, 'scene requires an embedded Open/Close door')
        assert(not types.ESM4Door.hasSequence(target, 'NoSuchOriginalFixture'), 'unknown clip was advertised')
        assert(not types.ESM4Door.playSequence(target, 'NoSuchOriginalFixture'), 'unknown clip was accepted')
        target:addScript('scripts/openoblivion_tes4_doors_local.lua')
        if config.traversal then
            player:teleport(player.cell, target.position + target.rotation:apply(util.vector3(0, -150, 256)), target.rotation)
        end
        player:sendEvent('OpenOblivionDoorView', {position = target.position, rotation = target.rotation, id = target.id})
        print('OPENOBLIVION_DOOR_TARGET id=' .. target.id .. ' name=' .. types.ESM4Door.record(target).name)
        stage = 1
    elseif elapsed >= openTime and stage == 1 then
        target:activateBy(player); stage = 2
        print('OPENOBLIVION_DOOR_ACTIVATE open')
    elseif elapsed >= openTime + 0.4 and stage == 2 then
        target:activateBy(player); stage = 3
        print('OPENOBLIVION_DOOR_ACTIVATE busy')
    elseif elapsed >= closeTime and stage == 3 then
        assert(target.enabled, 'opening hid the door')
        assert(not types.ESM4Door.isSequencePlaying(target, 'Open'), 'open sequence did not finish')
        target:activateBy(player); stage = 4
        print('OPENOBLIVION_DOOR_ACTIVATE close')
    elseif elapsed >= finishTime and stage == 4 then
        assert(target.enabled, 'closing hid the door')
        assert(not types.ESM4Door.isSequencePlaying(target, 'Close'), 'close sequence did not finish')
        print('OPENOBLIVION_DOOR_CYCLE_DONE'); stage = 5
    end
end}}
