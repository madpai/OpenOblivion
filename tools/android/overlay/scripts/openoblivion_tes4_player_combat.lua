-- SPDX-License-Identifier: GPL-3.0-only
-- Player side of the TES4 rules layer: hand-to-hand attacks with the original
-- clips and damage formula, and damage received from TES4 actors.
--
-- Fists are readied like a weapon, as in the original: the host weapon stance
-- (WEAPON button) is the readied state, raising and lowering play the original
-- equip/unequip clips, and attacking while holstered readies instead of
-- punching. Readied idle/movement are the host "hh" groups (TES4 renderer).
-- A carried melee weapon works the same way with its own clip family (group
-- names carry the host weapon short group: 1h, 1b, 2c, 2b), its damage from
-- the weapon formula and its reach from the weapon record.
local anim = require('openmw.animation')
local input = require('openmw.input')
local interfaces = require('openmw.interfaces')
local nearby = require('openmw.nearby')
local self = require('openmw.self')
local types = require('openmw.types')
local util = require('openmw.util')
local combat = require('scripts.openoblivion_tes4_combat')
local items = require('scripts.openoblivion_tes4_items')

local attacking = false
local wasPressed = false
local leftNext = false
local attackClock = 0
-- The clip's stop key can be lost when another animation interrupts it.
local ATTACK_TIMEOUT = 1.2
local CLIPS = { 'tes4attackright', 'tes4attackleft' }
local SHORTS = { '', '1h', '1b', '2c', '2b', '2w', 'bow' }

-- A clip group name for the carried weapon's family ('' for fists).
local function group(name, weapon) return name .. (weapon and weapon.short or '') end
local stance = nil
local equipPending = 0
local readying = 0
local READY_TIME = 0.6

local function forward()
    return util.transform.rotateZ(self.rotation:getYaw()) * util.vector3(0, 1, 0)
end

local function strike()
    local stats = interfaces.TES4Stats
    if not stats then return end
    local fatigue = types.Actor.stats.dynamic.fatigue(self)
    local weapon = items.equippedWeapon(self)
    if weapon and not weapon.melee then weapon = nil end
    local health, fatigueDamage
    local reach = combat.handReach()
    if weapon then
        health = combat.weapon(weapon.damage, stats.skill(weapon.skill) or 5, stats.attribute('strength') or 50,
            stats.attribute('luck') or 50, fatigue.current, fatigue.base, weapon.condition)
        fatigueDamage = 0
        reach = combat.weaponReach(weapon.reach)
    else
        health, fatigueDamage = combat.handToHand(stats.skill('handToHand') or 5, stats.attribute('strength') or 50,
            stats.attribute('luck') or 50, fatigue.current, fatigue.base)
    end
    local best, bestDistance = nil, reach
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
    for _, short in ipairs(SHORTS) do
        interfaces.AnimationController.addTextKeyHandler(clip .. short, function(_, key)
            if key == 'hit' then strike()
            elseif key == 'stop' then attacking = false end
        end)
    end
end

local function play(clip, speed)
    interfaces.AnimationController.playBlendedAnimation(clip, {
        startKey = 'start', stopKey = 'stop', priority = anim.PRIORITY.Scripted,
        blendMask = anim.BLEND_MASK.UpperBody, autoDisable = true, speed = speed or 1 })
end

local function attack()
    if attacking or types.Actor.isDead(self) then return end
    local weapon = items.equippedWeapon(self)
    if types.Actor.getStance(self) ~= types.Actor.STANCE.Weapon then
        types.Actor.setStance(self, types.Actor.STANCE.Weapon)
        print('OPENOBLIVION_TES4_COMBAT player readies ' .. (weapon and weapon.short or 'fists'))
        return
    end
    -- Bows and staves have no combat rules yet; a weapon whose clips are not loaded punches.
    if weapon and not (weapon.melee and anim.hasGroup(self, group(CLIPS[1], weapon))) then weapon = nil end
    if not anim.hasGroup(self, group(CLIPS[1], weapon)) or readying > 0 then return end
    attacking = true
    attackClock = 0
    local clip = group(leftNext and anim.hasGroup(self, group(CLIPS[2], weapon)) and CLIPS[2] or CLIPS[1], weapon)
    leftNext = not leftNext
    print('OPENOBLIVION_TES4_COMBAT player swings ' .. clip)
    play(clip, weapon and weapon.speed or 1)
end

return {
    engineHandlers = {
        onFrame = function(dt)
            if attacking then
                attackClock = attackClock + dt
                if attackClock > ATTACK_TIMEOUT then attacking = false end
            end
            readying = math.max(0, readying - dt)
            -- Starting items arrive from the global script; equip once they are in.
            if equipPending > 0 then
                equipPending = equipPending - 1
                local count = items.equipApparel(self)
                if count > 0 or equipPending == 0 then
                    equipPending = 0
                    print('OPENOBLIVION_ITEMS player equips ' .. count)
                end
            end
            local now = types.Actor.getStance(self)
            if stance ~= nil and now ~= stance then
                local weapon = items.equippedWeapon(self)
                local equip, unequip = group('tes4equip', weapon), group('tes4unequip', weapon)
                if now == types.Actor.STANCE.Weapon and anim.hasGroup(self, equip) then
                    play(equip); readying = READY_TIME
                elseif stance == types.Actor.STANCE.Weapon and anim.hasGroup(self, unequip) then
                    play(unequip); attacking = false
                end
            end
            stance = now
            -- Menu taps are clicks too; only attack in gameplay.
            local pressed = input.isActionPressed(input.ACTION.Use)
            if interfaces.UI and interfaces.UI.getMode() ~= nil then
                wasPressed = pressed
                return
            end
            if pressed and not wasPressed then attack() end
            wasPressed = pressed
        end,
    },
    eventHandlers = {
        -- Desktop probes cannot press buttons; they request an attack instead.
        TES4PlayerAttack = function() attack() end,
        TES4EquipApparel = function() equipPending = 5 end,
        -- Desktop probes: carry and wield a generated weapon.
        TES4WieldWeapon = function(event)
            local weapon = items.equipWeapon(self)
            print('OPENOBLIVION_ITEMS player wields ' .. tostring(weapon and weapon.item.recordId))
        end,
        TES4Hit = function(hit)
            local health = types.Actor.stats.dynamic.health(self)
            local fatigue = types.Actor.stats.dynamic.fatigue(self)
            local stats = interfaces.TES4Stats
            local rating = 0
            if stats then
                rating = items.armorRating(self, stats.skill, stats.attribute('luck') or 50)
                hit = { health = hit.health * combat.armorFactor(rating), fatigue = hit.fatigue, attacker = hit.attacker }
            end
            health.current = math.max(0, health.current - hit.health)
            fatigue.current = fatigue.current - hit.fatigue
            print(string.format('OPENOBLIVION_TES4_COMBAT player takes health=%.2f fatigue=%.2f armor=%.1f now=%.1f',
                hit.health, hit.fatigue, rating, health.current))
        end,
    },
}
