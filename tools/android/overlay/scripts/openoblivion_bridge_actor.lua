-- SPDX-License-Identifier: GPL-3.0-only
-- Per-proxy TES4 data: base health (the original console shows level-1 NPCs
-- keep their record health) and AI aggression. The host AI attacks on sight
-- from a fight rating near 100, which is used as the stand-in for TES4
-- aggression until disposition and factions are implemented.
local anim = require('openmw.animation')
local core = require('openmw.core')
local items = require('scripts.openoblivion_tes4_items')
local interfaces = require('openmw.interfaces')
local nearby = require('openmw.nearby')
local util = require('openmw.util')
local combat = require('scripts.openoblivion_tes4_combat')
local self = require('openmw.self')
local types = require('openmw.types')

local ok, npcs = pcall(require, 'scripts.openoblivion_tes4_npc_values')
local data
local nextReport = 0
local nextSense = 0
local attacking = false
local attackStarted = 0
local nextAttack = 0
local leftNext = false
local reportedDeath = false
local equipped = false
local stance = nil
local CLIPS = { 'tes4attackright', 'tes4attackleft' }
local SHORTS = { '', '1h', '1b', '2c', '2b', '2w', 'bow' }
local function group(name, weapon) return name .. (weapon and weapon.short or '') end
-- Stand-in for TES4 detection until sneak/detection is implemented: an
-- aggressive actor (aggression >= 80) engages a visible player within range.
local HOSTILE_AGGRESSION = 80
local DETECT_RANGE = 1500
local clock = 0

local function apply()
    if not data or not ok then return end
    local row = npcs[data.formId]
    if not row then return end
    local aggression, confidence, health, fatigue = row[1], row[2], row[3], row[4]
    if fatigue and fatigue > 0 then
        local stat = types.Actor.stats.dynamic.fatigue(self)
        stat.base = fatigue
        stat.current = fatigue
    end
    if health and health > 0 then
        local stat = types.Actor.stats.dynamic.health(self)
        stat.base = health
        stat.current = health
    end
    types.Actor.stats.ai.fight(self).base = aggression
    types.Actor.stats.ai.flee(self).base = math.floor(math.max(0, 100 - confidence) / 2)
    print(string.format('OPENOBLIVION_BRIDGE_ACTOR %s health=%d aggression=%d confidence=%d',
        tostring(data.name), health, aggression, confidence))
end

-- The wielded melee weapon, or nil for fists.
local function wielded()
    local weapon = items.equippedWeapon(self)
    return weapon and weapon.melee and weapon or nil
end

local function strike()
    local row = ok and data and npcs[data.formId]
    local player = nearby.players[1]
    if not row or not player or types.Actor.isDead(self) then return end
    local weapon = wielded()
    local offset = player.position - self.position
    if offset:length() > (weapon and combat.weaponReach(weapon.reach) or combat.handReach()) then return end
    local fatigue = types.Actor.stats.dynamic.fatigue(self)
    local health, fatigueDamage
    if weapon then
        local skill = (weapon.skill == 'blade' and row[8]) or (weapon.skill == 'blunt' and row[9]) or row[10] or 5
        health, fatigueDamage = combat.weapon(weapon.damage, skill, row[6], row[7], fatigue.current, fatigue.base,
            weapon.condition), 0
    else
        health, fatigueDamage = combat.handToHand(row[5], row[6], row[7], fatigue.current, fatigue.base)
    end
    player:sendEvent('TES4Hit', { health = health, fatigue = fatigueDamage, attacker = self.object })
end

for _, clip in ipairs(CLIPS) do
    for _, short in ipairs(SHORTS) do
        interfaces.AnimationController.addTextKeyHandler(clip .. short, function(_, key)
            if key == 'hit' then strike()
            elseif key == 'stop' then attacking = false end
        end)
    end
end

local function fight(player)
    if attacking and clock - attackStarted > 1.2 then attacking = false end
    local weapon = wielded()
    if weapon and not anim.hasGroup(self, group(CLIPS[1], weapon)) then weapon = nil end
    if attacking or clock < nextAttack or not anim.hasGroup(self, group(CLIPS[1], weapon)) then return end
    if (player.position - self.position):length() > (weapon and combat.weaponReach(weapon.reach) or combat.handReach()) then
        return
    end
    attacking = true
    attackStarted = clock
    local speed = weapon and weapon.speed or 1
    nextAttack = clock + 1.5 / speed
    local clip = group(leftNext and anim.hasGroup(self, group(CLIPS[2], weapon)) and CLIPS[2] or CLIPS[1], weapon)
    leftNext = not leftNext
    interfaces.AnimationController.playBlendedAnimation(clip, {
        startKey = 'start', stopKey = 'stop', priority = anim.PRIORITY.Scripted,
        blendMask = anim.BLEND_MASK.UpperBody, autoDisable = true, speed = speed })
end

return {
    eventHandlers = {
        TES4Hit = function(hit)
            if types.Actor.isDead(self) then return end
            local health = types.Actor.stats.dynamic.health(self)
            local fatigue = types.Actor.stats.dynamic.fatigue(self)
            local row = ok and data and npcs[data.formId]
            local rating = 0
            if row then
                rating = items.armorRating(self, function(name)
                    return name == 'heavyArmor' and row[11] or row[12]
                end, row[7])
                hit = { health = hit.health * combat.armorFactor(rating), fatigue = hit.fatigue, attacker = hit.attacker }
            end
            health.current = math.max(0, health.current - hit.health)
            fatigue.current = fatigue.current - hit.fatigue
            print(string.format('OPENOBLIVION_TES4_COMBAT %s takes health=%.2f armor=%.1f now=%.1f',
                tostring(data and data.name), hit.health, rating, health.current))
            if health.current > 0 and anim.hasGroup(self, 'tes4recoil') then
                interfaces.AnimationController.playBlendedAnimation('tes4recoil', {
                    startKey = 'start', stopKey = 'stop', priority = anim.PRIORITY.Hit, autoDisable = true })
            end
            if hit.attacker then interfaces.AI.startPackage({ type = 'Combat', target = hit.attacker }) end
        end,
    },
    engineHandlers = {
        onInit = function(initData) data = initData; apply() end,
        onUpdate = function(dt)
            clock = clock + dt
            local row = ok and data and npcs[data.formId]
            if types.Actor.isDead(self) then
                if not reportedDeath then
                    reportedDeath = true
                    print('OPENOBLIVION_TES4_COMBAT ' .. tostring(data and data.name) .. ' dies')
                    if data and data.held and #data.held > 0 then
                        core.sendGlobalEvent('TES4Loot', { actor = self.object, items = data.held })
                        data.held = nil
                    end
                end
                return
            end
            -- Apparel arrives from the global script a frame later.
            local carried = false
            if not equipped then
                for _, item in ipairs(types.Actor.inventory(self):getAll()) do
                    if item.recordId:sub(1, 4) == 'oo4_' then carried = true end
                end
            end
            if not equipped and (carried or clock > 3) then
                equipped = true
                local worn = items.equipApparel(self)
                local weapon = items.equipWeapon(self)
                print(string.format('OPENOBLIVION_ITEMS %s equips %d wields %s', tostring(data and data.name), worn,
                    tostring(weapon and weapon.item.recordId)))
            end
            -- The host AI readies hand-to-hand for combat; play the original raise/lower clips.
            local now = types.Actor.getStance(self)
            if stance ~= nil and now ~= stance then
                local weapon = wielded()
                local clip = now == types.Actor.STANCE.Weapon and group('tes4equip', weapon)
                    or stance == types.Actor.STANCE.Weapon and group('tes4unequip', weapon) or nil
                if clip and anim.hasGroup(self, clip) then
                    interfaces.AnimationController.playBlendedAnimation(clip, { startKey = 'start', stopKey = 'stop',
                        priority = anim.PRIORITY.Scripted, blendMask = anim.BLEND_MASK.UpperBody, autoDisable = true })
                end
            end
            stance = now
            local package = interfaces.AI.getActivePackage()
            if package and package.type == 'Combat' and nearby.players[1] then fight(nearby.players[1]) end
            if row and row[1] >= HOSTILE_AGGRESSION and clock >= nextSense then
                nextSense = clock + 0.5
                local player = nearby.players[1]
                if player and not (package and package.type == 'Combat')
                    and (player.position - self.position):length() <= DETECT_RANGE then
                    local eye = util.vector3(0, 0, 100)
                    local hit = nearby.castRay(self.position + eye, player.position + eye,
                        { collisionType = nearby.COLLISION_TYPE.World + nearby.COLLISION_TYPE.Door, ignore = self })
                    if not hit.hit then
                        interfaces.AI.startPackage({ type = 'Combat', target = player })
                        print('OPENOBLIVION_BRIDGE_COMBAT ' .. tostring(data.name) .. ' engages the player')
                    end
                end
            end
            -- Sparse QA trace of what the host AI is doing with this proxy.
            if clock < nextReport or not data then return end
            nextReport = clock + 2
            local package = interfaces.AI and interfaces.AI.getActivePackage and interfaces.AI.getActivePackage()
            local p = self.position
            print(string.format('OPENOBLIVION_BRIDGE_STATE %s ai=%s health=%.0f pos=%.0f,%.0f,%.0f', tostring(data.name),
                package and package.type or 'none', types.Actor.stats.dynamic.health(self).current, p.x, p.y, p.z))
        end,
        onSave = function() return { data = data, equipped = equipped } end,
        onLoad = function(saved)
            if saved and saved.data then data, equipped = saved.data, saved.equipped else data, equipped = saved, true end
        end,
    },
}
