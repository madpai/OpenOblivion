-- SPDX-License-Identifier: GPL-3.0-only
-- Player side of the TES4 rules layer: hand-to-hand attacks with the original
-- clips and damage formula, and damage received from TES4 actors.
local anim = require('openmw.animation')
local input = require('openmw.input')
local interfaces = require('openmw.interfaces')
local nearby = require('openmw.nearby')
local self = require('openmw.self')
local types = require('openmw.types')
local util = require('openmw.util')
local combat = require('scripts.openoblivion_tes4_combat')

local attacking = false
local wasPressed = false
local leftNext = false
local attackClock = 0
-- The clip's stop key can be lost when another animation interrupts it.
local ATTACK_TIMEOUT = 1.2
local CLIPS = { 'tes4attackright', 'tes4attackleft' }

local function forward()
    return util.transform.rotateZ(self.rotation:getYaw()) * util.vector3(0, 1, 0)
end

local function strike()
    local stats = interfaces.TES4Stats
    if not stats then return end
    local fatigue = types.Actor.stats.dynamic.fatigue(self)
    local health, fatigueDamage = combat.handToHand(stats.skill('handToHand') or 5, stats.attribute('strength') or 50,
        stats.attribute('luck') or 50, fatigue.current, fatigue.base)
    local best, bestDistance = nil, combat.handReach()
    for _, actor in ipairs(nearby.actors) do
        if actor ~= self.object and not types.Actor.isDead(actor) then
            local offset = actor.position - self.position
            local distance = offset:length()
            if distance <= bestDistance and distance > 0 and (offset / distance):dot(forward()) > 0.5 then
                best, bestDistance = actor, distance
            end
        end
    end
    if not best then
        local closest, cd, cdot = nil, math.huge, 0
        for _, actor in ipairs(nearby.actors) do
            if actor ~= self.object and not types.Actor.isDead(actor) then
                local offset = actor.position - self.position
                if offset:length() < cd then closest, cd, cdot = actor, offset:length(), (offset / offset:length()):dot(forward()) end
            end
        end
        print(string.format('OPENOBLIVION_TES4_COMBAT player swings at nothing (closest %.0f units, facing %.2f)', cd, cdot))
    end
    if best then
        best:sendEvent('TES4Hit', { health = health, fatigue = fatigueDamage, attacker = self.object })
        print(string.format('OPENOBLIVION_TES4_COMBAT player hits %s health=%.2f fatigue=%.2f', best.recordId, health,
            fatigueDamage))
    end
end

for _, clip in ipairs(CLIPS) do
    interfaces.AnimationController.addTextKeyHandler(clip, function(_, key)
        if key == 'hit' then strike()
        elseif key == 'stop' then attacking = false end
    end)
end

local function attack()
    if attacking or types.Actor.isDead(self) or not anim.hasGroup(self, CLIPS[1]) then return end
    attacking = true
    attackClock = 0
    local clip = leftNext and CLIPS[2] or CLIPS[1]
    leftNext = not leftNext
    print('OPENOBLIVION_TES4_COMBAT player swings ' .. clip)
    interfaces.AnimationController.playBlendedAnimation(clip, {
        startKey = 'start', stopKey = 'stop', priority = anim.PRIORITY.Weapon,
        blendMask = anim.BLEND_MASK.UpperBody, autoDisable = true })
end

return {
    engineHandlers = {
        onFrame = function(dt)
            if attacking then
                attackClock = attackClock + dt
                if attackClock > ATTACK_TIMEOUT then attacking = false end
            end
            local pressed = input.isActionPressed(input.ACTION.Use)
            if pressed and not wasPressed then attack() end
            wasPressed = pressed
        end,
    },
    eventHandlers = {
        -- Desktop probes cannot press buttons; they request an attack instead.
        TES4PlayerAttack = function() attack() end,
        TES4Hit = function(hit)
            local health = types.Actor.stats.dynamic.health(self)
            local fatigue = types.Actor.stats.dynamic.fatigue(self)
            health.current = math.max(0, health.current - hit.health)
            fatigue.current = fatigue.current - hit.fatigue
            print(string.format('OPENOBLIVION_TES4_COMBAT player takes health=%.2f fatigue=%.2f now=%.1f', hit.health,
                hit.fatigue, health.current))
        end,
    },
}
