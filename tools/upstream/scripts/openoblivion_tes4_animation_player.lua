-- SPDX-License-Identifier: GPL-3.0-only
local core = require('openmw.core')
local self = require('openmw.self')
local debug = require('openmw.debug')
local camera = require('openmw.camera')
local nearby = require('openmw.nearby')
local util = require('openmw.util')
local elapsed, stage = 0, 0
local viewPosition, viewYaw
return {
eventHandlers = {OpenOblivionAnimationView = function(data)
    local center = data.position + util.vector3(0, 0, 80)
    for direction = 0, 15 do
        local yaw = direction * math.pi / 8
        local candidate = center + util.vector3(math.sin(yaw) * 150, -math.cos(yaw) * 150, 0)
        if not nearby.castRay(center, candidate).hit then
            viewPosition, viewYaw = candidate, yaw
            print('OPENOBLIVION_ANIMATION_VIEW direction=' .. direction)
            break
        end
    end
    assert(viewPosition ~= nil, 'no clear NPC observation direction')
end},
engineHandlers = {
onFrame = function()
    if viewPosition then
        camera.setMode(camera.MODE.Static)
        camera.setStaticPosition(viewPosition)
        camera.setYaw(viewYaw)
        camera.setPitch(0)
    end
end,
onUpdate = function(dt)
    elapsed = elapsed + dt
    if stage < 3 and elapsed >= 4 + stage * 3 then
        stage = stage + 1
        print('OPENOBLIVION_SCENE_PROBE cell=' .. tostring(self.cell.id)
            .. ' name=' .. tostring(self.cell.name) .. ' exterior=' .. tostring(self.cell.isExterior))
        debug.takeScreenshot()
    end
    if elapsed >= 15 then
        print('OPENOBLIVION_SCENE_PROBE_DONE')
        core.quit()
    end
end}}
