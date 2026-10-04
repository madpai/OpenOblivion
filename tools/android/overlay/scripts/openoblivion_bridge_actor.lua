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

local function strike()
    local row = ok and data and npcs[data.formId]
    local player = nearby.players[1]
    if not row or not player or types.Actor.isDead(self) then return end
    local offset = player.position - self.position
    if offset:length() > combat.handReach() then return end
    local fatigue = types.Actor.stats.dynamic.fatigue(self)
    local health, fatigueDamage = combat.handToHand(row[5], row[6], row[7], fatigue.current, fatigue.base)
    player:sendEvent('TES4Hit', { health = health, fatigue = fatigueDamage, attacker = self.object })
end

for _, clip in ipairs(CLIPS) do
    interfaces.AnimationController.addTextKeyHandler(clip, function(_, key)
        if key == 'hit' then strike()
        elseif key == 'stop' then attacking = false end
    end)
end

local function fight(player)
    if attacking and clock - attackStarted > 1.2 then attacking = false end
    if attacking or clock < nextAttack or not anim.hasGroup(self, CLIPS[1]) then return end
    if (player.position - self.position):length() > combat.handReach() then return end
    attacking = true
    attackStarted = clock
    nextAttack = clock + 1.5
    local clip = leftNext and CLIPS[2] or CLIPS[1]
    leftNext = not leftNext
    interfaces.AnimationController.playBlendedAnimation(clip, {
        startKey = 'start', stopKey = 'stop', priority = anim.PRIORITY.Scripted,
        blendMask = anim.BLEND_MASK.UpperBody, autoDisable = true })
end

return {
    eventHandlers = {
        TES4Hit = function(hit)
            if types.Actor.isDead(self) then return end
            local health = types.Actor.stats.dynamic.health(self)
            local fatigue = types.Actor.stats.dynamic.fatigue(self)
            health.current = math.max(0, health.current - hit.health)
            fatigue.current = fatigue.current - hit.fatigue
            print(string.format('OPENOBLIVION_TES4_COMBAT %s takes health=%.2f now=%.1f', tostring(data and data.name),
                hit.health, health.current))
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
                print(string.format('OPENOBLIVION_ITEMS %s equips %d', tostring(data and data.name),
                    items.equipApparel(self)))
            end
            -- The host AI readies hand-to-hand for combat; play the original raise/lower clips.
            local now = types.Actor.getStance(self)
            if stance ~= nil and now ~= stance then
                local clip = now == types.Actor.STANCE.Weapon and 'tes4equip'
                    or stance == types.Actor.STANCE.Weapon and 'tes4unequip' or nil
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
