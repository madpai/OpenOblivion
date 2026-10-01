-- SPDX-License-Identifier: GPL-3.0-only
-- Original read-only diagnostics for the separately pinned preview runtime.
local camera = require('openmw.camera')
local self = require('openmw.self')
local debug = require('openmw.debug')
local elapsed = 0
local sample = 1
local times = {1, 3, 8, 15, 25}

return {
    engineHandlers = {
        onUpdate = function(dt)
            elapsed = elapsed + dt
            if sample > #times or elapsed < times[sample] or not self.cell then return end
            print('OPENOBLIVION_PHONE_QA sample=' .. sample
                .. ' seconds=' .. string.format('%.2f', elapsed)
                .. ' cell=' .. tostring(self.cell.name)
                .. ' player=' .. tostring(self.position)
                .. ' camera=' .. tostring(camera.getPosition())
                .. ' tracked=' .. tostring(camera.getTrackedPosition())
                .. ' pitch=' .. tostring(camera.getPitch())
                .. ' yaw=' .. tostring(camera.getYaw())
                .. ' collision=' .. tostring(debug.isCollisionEnabled()))
            sample = sample + 1
        end,
    },
}
