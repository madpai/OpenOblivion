-- SPDX-License-Identifier: GPL-3.0-only
-- Original desktop test of native player movement, not a camera animation.
local core = require('openmw.core')
local camera = require('openmw.camera')
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
local nextAttack = nil
local nearby = require('openmw.nearby')
local uiOpened = nil
local util = require('openmw.util')
local faced = false
local gave, wielded = false, false

-- Puts a static camera in front of the nearest actor's face (look inspection).
local function faceNearestActor()
    local best, bestDistance = nil, math.huge
    for _, actor in ipairs(nearby.actors) do
        if actor ~= self.object then
            local distance = (actor.position - self.position):length()
            if distance < bestDistance then best, bestDistance = actor, distance end
        end
    end
    if not best then return end
    -- The side the actor faces, so the camera sees its face whatever the player does.
    local yaw = best.rotation:getYaw() + math.rad(config.faceAngle or 0)
    local flat = util.vector2(math.sin(yaw), math.cos(yaw))
    local target = best.position + util.vector3(0, 0, config.faceHeight or 148)
    local distance = config.faceDistance or 70
    local sign = distance >= 0 and 1 or -1
    local position = target + util.vector3(flat.x, flat.y, 0) * distance
    camera.setMode(camera.MODE.Static, true)
    camera.setStaticPosition(position)
    camera.setYaw(math.atan2(-flat.x * sign, -flat.y * sign))
    camera.setPitch(0)
    print(string.format('OPENOBLIVION_SCENE_PROBE face actor=%s pos=%.0f,%.0f,%.0f yaw=%.2f player=%.0f,%.0f,%.0f', tostring(best.recordId),
        best.position.x, best.position.y, best.position.z, best.rotation:getYaw(), self.position.x, self.position.y, self.position.z))
    for _, actor in ipairs(nearby.actors) do
        print('OPENOBLIVION_SCENE_PROBE actor ' .. tostring(actor.recordId) .. ' ' .. tostring(actor.type == types.Player) .. string.format(' %.0f,%.0f,%.0f', actor.position.x, actor.position.y, actor.position.z))
    end
end

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
            -- Menus pause the world (and onUpdate); time the menu shot in real time.
            if uiOpened and not finished then
                if not captured and core.getRealTime() - uiOpened > 0.6 then
                    captured = true
                    print('OPENOBLIVION_SCENE_PROBE ui=' .. tostring(config.ui))
                    debug.takeScreenshot()
                elseif core.getRealTime() - uiOpened > 1.5 then
                    finished = true
                    print('OPENOBLIVION_SCENE_PROBE_DONE')
                    core.quit()
                end
                return
            end
            if not ready or not self.cell or core.isWorldPaused() or finished then return end
            interfaces.Controls.overrideMovementControls(true)
            if config.camera == 'third' and not faced and camera.getMode() ~= camera.MODE.ThirdPerson then
                camera.setMode(camera.MODE.ThirdPerson, true)
                camera.setPreferredThirdPersonDistance(260)
                camera.instantTransition()
            end
            self.controls.movement = (phase() == 'walk' and config.gait ~= 'none') and 1 or 0
            self.controls.sideMovement = 0
            self.controls.run = config.gait == 'run'
            self.controls.sneak = config.gait == 'sneak'
            self.controls.jump = phase() == 'jump'
            self.controls.yawChange = turned and 0 or config.turn
            self.controls.pitchChange = turned and 0 or (config.pitch or 0)
            turned = true
            -- Hand the player a generated weapon and wield it (desktop probes cannot use menus).
            if config.weapon and not gave and elapsed >= 0.4 then
                gave = true
                core.sendGlobalEvent('TES4Give', { actor = self.object, id = config.weapon })
            end
            if config.weapon and gave and not wielded and elapsed >= 0.9 then
                wielded = true
                self.object:sendEvent('TES4WieldWeapon', {})
            end
            if config.face and not faced and elapsed >= (config.shot or 6.5) - 0.5 then
                faced = true
                faceNearestActor()
            end
            if config.attack and elapsed >= (nextAttack or 1) then
                nextAttack = elapsed + 1.5
                self.object:sendEvent('TES4PlayerAttack', {})
            end
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
                print(string.format('OPENOBLIVION_PLAYER_GAIT t=%.6f gait=%s walk_speed=%.6f run_speed=%.6f current_speed=%.6f running=%s sneaking=%s',
                    elapsed, tostring(config.gait), types.Actor.getWalkSpeed(self), types.Actor.getRunSpeed(self),
                    types.Actor.getCurrentSpeed(self), tostring(types.Actor.isRunning and types.Actor.isRunning(self)),
                    tostring(self.controls.sneak)))
                print(string.format('OPENOBLIVION_PLAYER_VIEW t=%.6f camera_z=%.6f tracked_z=%.6f pitch=%.6f yaw=%.6f',
                    elapsed, camera.getPosition().z, camera.getTrackedPosition().z, camera.getPitch(), camera.getYaw()))
            end
            if config.ui and not uiOpened and elapsed >= (config.shot or 6.5) then
                uiOpened = core.getRealTime()
                if config.ui == 'loot' then
                    local corpse
                    for _, actor in ipairs(nearby.actors) do
                        if actor ~= self.object and types.Actor.isDead(actor) then corpse = actor end
                    end
                    print('OPENOBLIVION_SCENE_PROBE loot=' .. tostring(corpse and corpse.recordId))
                    if corpse then interfaces.UI.setMode('Container', { target = corpse }) end
                else
                    interfaces.UI.setMode('Interface', { windows = { 'Inventory' } })
                end
                return
            end
            if not captured and elapsed >= (config.shot or 6.5) then
                captured = true
                print('OPENOBLIVION_SCENE_PROBE cell=' .. tostring(self.cell.id)
                    .. ' name=' .. tostring(self.cell.name)
                    .. ' exterior=' .. tostring(self.cell.isExterior))
                debug.takeScreenshot()
            end
            if elapsed >= (config.duration or 12) then
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
