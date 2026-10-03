-- SPDX-License-Identifier: GPL-3.0-only
-- Place a new preview game where the classic prologue ends: outside the
-- Imperial Sewers exit. The position and heading are the destination of the
-- original exit door (ImperialSewers03 door 0004BED7) in Oblivion.esm.
-- The engine's --start option only selects the cell (it places the player at
-- the cell centre, in the lake), so this moves the player once on arrival.
local world = require('openmw.world')
local util = require('openmw.util')

local START_CELL = 'icprisonsewerexit01'
local EXIT_POSITION = util.vector3(47073.2, 82958.1, 301.8)
local EXIT_HEADING = 0.785398
local done = false

return {
    engineHandlers = {
        onUpdate = function()
            if done then return end
            local player = world.players[1]
            if not player or not player.cell then return end
            done = true
            if (player.cell.name or ''):lower() ~= START_CELL then return end
            player:teleport(player.cell, EXIT_POSITION, {rotation = util.transform.rotateZ(EXIT_HEADING)})
            print('OPENOBLIVION_START sewer-exit')
        end,
    },
}
