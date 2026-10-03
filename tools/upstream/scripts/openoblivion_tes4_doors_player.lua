-- SPDX-License-Identifier: GPL-3.0-only
-- Vilverin gate collision observations and fixed-camera captures.
local core = require('openmw.core')
local self = require('openmw.self')
local camera = require('openmw.camera')
local debug = require('openmw.debug')
local nearby = require('openmw.nearby')
local util = require('openmw.util')
local interfaces = require('openmw.interfaces')
local types = require('openmw.types')
local config = require('scripts.openoblivion_door_config')
local elapsed, nextSample, captures = 0, 0.25, 0
local position, rotation, targetId
return {
eventHandlers = {OpenOblivionDoorView = function(data)
    position, rotation, targetId = data.position, data.rotation, data.id
end},
engineHandlers = {
onFrame = function()
    if config.traversal and position then
        interfaces.Controls.overrideMovementControls(true)
        self.controls.movement = elapsed >= 3 and elapsed < 10 and 1 or 0
        self.controls.sideMovement = 0
        self.controls.yawChange = 0
        self.controls.run = false
        self.controls.jump = false
        return
    end
    if position then
        camera.setMode(camera.MODE.Static)
        camera.setStaticPosition(position + rotation:apply(util.vector3(0, -190, 85)))
        camera.setYaw(rotation:getYaw())
        camera.setPitch(0)
    end
end,
onUpdate = function(dt)
    elapsed = elapsed + dt
    if position and elapsed >= nextSample then
        nextSample = elapsed + 0.25
        local hits = 0
        for offset = -105, 105, 7 do
            local ray = nearby.castRay(position + rotation:apply(util.vector3(offset, -100, 80)),
                position + rotation:apply(util.vector3(offset, 100, 80)),
                {ignore = self})
            if ray.hitObject and ray.hitObject.id == targetId then hits = hits + 1 end
        end
        print(string.format('OPENOBLIVION_DOOR_COLLISION elapsed=%.6f hits=%d', elapsed, hits))
        if config.traversal then
            local localPosition = rotation:inverse():apply(self.position - position)
            print(string.format('OPENOBLIVION_DOOR_BODY elapsed=%.6f x=%.6f y=%.6f z=%.6f grounded=%s',
                elapsed, localPosition.x, localPosition.y, localPosition.z, tostring(types.Actor.isOnGround(self))))
        end
    end
    local times = {2, 6, 10}
    if config.traversal then times = {2, 10, 15} end
    if position and captures < #times and elapsed >= times[captures + 1] then
        captures = captures + 1
        print('OPENOBLIVION_SCENE_PROBE cell=' .. tostring(self.cell.id)
            .. ' name=' .. tostring(self.cell.name) .. ' exterior=' .. tostring(self.cell.isExterior))
        debug.takeScreenshot()
    end
    if elapsed >= (config.traversal and 16 or 11) then
        if config.traversal then
            self.controls.movement = 0
            interfaces.Controls.overrideMovementControls(false)
        end
        print('OPENOBLIVION_SCENE_PROBE_DONE'); core.quit()
    end
end}}
