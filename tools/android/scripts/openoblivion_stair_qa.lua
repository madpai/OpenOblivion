-- SPDX-License-Identifier: GPL-3.0-only
-- Original read-only diagnostics for the separately pinned preview runtime.
local camera = require('openmw.camera')
local self = require('openmw.self')
local types = require('openmw.types')
local elapsed = 0
local nextMovementSample = 0
local movementSamples = 0
local movingUntil = 0
local previousZ

return {
    engineHandlers = {
        onUpdate = function(dt)
            elapsed = elapsed + dt
            -- Bound log growth so movement evidence fits the report form.
            if self.cell and movementSamples < 400 then
                local p = self.position
                local grounded = types.Actor.isOnGround(self)
                local movement = self.controls.movement
                if math.abs(movement) > 0.01 or math.abs(self.controls.sideMovement) > 0.01
                    or not grounded or (previousZ and math.abs(p.z - previousZ) > 0.01) then
                    movingUntil = elapsed + 0.5
                end
                previousZ = p.z
                if elapsed >= nextMovementSample then
                    nextMovementSample = elapsed + (elapsed < movingUntil and 0.05 or 1)
                    movementSamples = movementSamples + 1
                    print(string.format('OPENOBLIVION_STAIR_QA t=%.3f x=%.2f y=%.2f z=%.2f cz=%.2f tz=%.2f g=%d m=%.2f j=%d',
                        elapsed, p.x, p.y, p.z, camera.getPosition().z, camera.getTrackedPosition().z,
                        grounded and 1 or 0, movement, self.controls.jump and 1 or 0))
                end
            end

        end,
    },
}
