-- SPDX-License-Identifier: GPL-3.0-only
-- Original bounded desktop fault test; never packaged into the personal APK.
local camera = require('openmw.camera')
local interfaces = require('openmw.interfaces')
local self = require('openmw.self')
local elapsed = 0
local started = false
local stopped = false
local initial

return {
    engineHandlers = {
        onFrame = function(dt)
            if not self.cell then return end
            elapsed = elapsed + dt
            if elapsed >= 1 and not started then
                interfaces.Controls.overrideMovementControls(true)
                initial = self.position
                started = true
            end
            if started and not stopped then
                self.controls.movement = 1
                self.controls.run = false
                self.controls.yawChange = dt * 0.2
                if elapsed >= 3 then
                    self.controls.movement = 0
                    self.controls.yawChange = 0
                    interfaces.Controls.overrideMovementControls(false)
                    stopped = true
                    print('OPENOBLIVION_CAMERA_MOTION distance=' .. tostring((self.position - initial):length())
                        .. ' camera_player_distance=' .. tostring((camera.getPosition() - self.position):length())
                        .. ' yaw=' .. tostring(camera.getYaw()))
                end
            end
        end,
    },
}
