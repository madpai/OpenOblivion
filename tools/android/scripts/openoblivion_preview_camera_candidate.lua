-- SPDX-License-Identifier: GPL-3.0-only
-- EXPERIMENTAL: pre-physics Lua timing regresses measured Vilverin ascent.
-- Explicit desktop probe opt-in only; excluded from the personal packager.
-- Original preview workaround: missing Camera/Head bones strand first-person
-- tracking at the origin. Native third-person tracking uses the actor root.
local camera = require('openmw.camera')
local core = require('openmw.core')
local interfaces = require('openmw.interfaces')
local self = require('openmw.self')
local types = require('openmw.types')
local util = require('openmw.util')
local eye = require('scripts.openoblivion_grounded_eye').new()
local active = false
local brokenTime = 0
local tag = 'OpenOblivionPreviewCamera'

local function activate()
    local controls = interfaces.Camera
    controls.disableModeControl(tag)
    controls.disableStandingPreview(tag)
    controls.disableHeadBobbing(tag)
    controls.disableZoom(tag)
    controls.disableThirdPersonOffsetControl(tag)
    controls.setBaseThirdPersonDistance(0)
    camera.setMode(camera.MODE.ThirdPerson, true)
    camera.setFocalPreferredOffset(util.vector2(0, 0))
    -- Apply our bounded grounded-height response directly. Keep native camera
    -- collision casts; instantTransition each frame would also alter turning.
    camera.setFocalTransitionSpeed(1000000)
    camera.setPreferredThirdPersonDistance(0)
    camera.instantTransition()
    active = true
    print('OPENOBLIVION_CAMERA_REPAIR activated: missing head tracking; using actor root at eye height')
end

return {
    engineHandlers = {
        onFrame = function(dt)
            if not self.cell or core.isWorldPaused() then eye.reset(); return end
            if not active then
                -- A normal head is roughly 124 units above the actor. Allow
                -- startup/teleport transients; do not alter healthy tracking.
                local trackingLost = camera.getMode() == camera.MODE.FirstPerson
                    and (camera.getTrackedPosition() - self.position):length() > 512
                brokenTime = trackingLost and (brokenTime + dt) or 0
                if brokenTime >= 0.25 then activate() end
            end
            if active then
                camera.setPreferredThirdPersonDistance(0)
                local offset = eye.update(self.position, self.cell.id,
                    types.Actor.isOnGround(self), self.controls.jump,
                    types.Actor.isSwimming(self), dt)
                camera.setFocalPreferredOffset(util.vector2(0, offset))
                camera.showCrosshair(true)
            end
        end,
    },
}
