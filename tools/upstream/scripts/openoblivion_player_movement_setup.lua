-- SPDX-License-Identifier: GPL-3.0-only
-- Original optional test placement; never used by the personal APK.
local world = require('openmw.world')
local util = require('openmw.util')
local config = require('scripts.openoblivion_movement_config')
local placed = false
return {
    engineHandlers = {
        onUpdate = function()
            if placed or not config.position then return end
            local player = world.players[1]
            if not player or not player.cell then return end
            player:teleport(player.cell, util.vector3(unpack(config.position)),
                {rotation=util.transform.rotateZ(config.heading)})
            player:sendEvent('OOPlayerMovementReady', {})
            placed = true
        end,
    },
}
