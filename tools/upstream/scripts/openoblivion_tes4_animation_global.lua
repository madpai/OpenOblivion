-- SPDX-License-Identifier: GPL-3.0-only
-- Private-scene automation; original owner records are never distributed.
local world = require('openmw.world')
local types = require('openmw.types')
local elapsed, started = 0, false
return {engineHandlers = {onUpdate = function(dt)
    elapsed = elapsed + dt
    if started or elapsed < 1 then return end
    started = true
    local player = world.players[1]
    local actors = player.cell:getAll(types.ESM4Npc)
    assert(#actors > 0, 'animation scene requires TES4 NPCs')
    for _, actor in ipairs(actors) do
        actor:addScript('scripts/openoblivion_tes4_animation_actor.lua')
    end
    local actor = actors[1]
    player:sendEvent('OpenOblivionAnimationView', {position = actor.position})
    print('OPENOBLIVION_ANIMATION_TARGET actors=' .. #actors
        .. ' name=' .. types.ESM4Npc.record(actor).name)
end}}
