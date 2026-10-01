-- SPDX-License-Identifier: GPL-3.0-only
-- Original desktop test of native player movement, not a camera animation.
local core = require('openmw.core')
local debug = require('openmw.debug')
local interfaces = require('openmw.interfaces')
local self = require('openmw.self')
local types = require('openmw.types')
local config = require('scripts.openoblivion_movement_config')
local elapsed = 0
local nextSample = 0
local captured = false
local finished = false
local turned = false
local ready = not config.position

local function phase()
    if elapsed < 1 then return 'settle' end
    if elapsed < 6 then return 'walk' end
    if elapsed < 7 then return 'stop' end
    if elapsed < 7.15 then return 'jump' end
    return 'land'
end

return {
    eventHandlers = {
        OOPlayerMovementReady = function() elapsed = 0; ready = true end,
    },
    engineHandlers = {
        onFrame = function()
            if not ready or not self.cell or core.isWorldPaused() or finished then return end
            interfaces.Controls.overrideMovementControls(true)
            self.controls.movement = phase() == 'walk' and 1 or 0
            self.controls.sideMovement = 0
            self.controls.run = false
            self.controls.jump = phase() == 'jump'
            self.controls.yawChange = turned and 0 or config.turn
            turned = true
        end,
        onUpdate = function(dt)
            if not ready or not self.cell or finished or dt <= 0 then return end
            elapsed = elapsed + dt
            if elapsed >= nextSample then
                nextSample = elapsed + 0.05
                local p = self.position
                print(string.format('OPENOBLIVION_PLAYER_MOVEMENT t=%.6f phase=%s x=%.6f y=%.6f z=%.6f grounded=%s expected_speed=%.6f',
                    elapsed, phase(), p.x, p.y, p.z,
                    tostring(types.Actor.isOnGround(self)), types.Actor.getWalkSpeed(self)))
            end
            if not captured and elapsed >= 6.5 then
                captured = true
                print('OPENOBLIVION_SCENE_PROBE cell=' .. tostring(self.cell.id)
                    .. ' name=' .. tostring(self.cell.name)
                    .. ' exterior=' .. tostring(self.cell.isExterior))
                debug.takeScreenshot()
            end
            if elapsed >= 12 then
                self.controls.movement = 0
                self.controls.jump = false
                interfaces.Controls.overrideMovementControls(false)
                finished = true
                print('OPENOBLIVION_SCENE_PROBE_DONE')
                core.quit()
            end
        end,
    },
}
