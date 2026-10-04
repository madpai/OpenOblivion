-- SPDX-License-Identifier: GPL-3.0-only
-- Apply the classic Player record's starting stats to the preview player.
-- The values file is generated at package time from the owner's master
-- (tools/android/tes4_stats.py) and is never committed. The host actor has
-- the same eight attributes; TES4 skills (21, unlike the host's 27) are kept
-- here for the TES4 rules layer and exposed as interface TES4Stats.
local self = require('openmw.self')
local types = require('openmw.types')

local ok, values = pcall(require, 'scripts.openoblivion_tes4_stats_values')
local applied = false

local function apply()
    if applied then return end
    applied = true
    if not ok then
        print('OPENOBLIVION_TES4_STATS unavailable: ' .. tostring(values))
        return
    end
    local attributes = types.Actor.stats.attributes
    for name, value in pairs(values.attributes) do
        if attributes[name] then attributes[name](self).base = value end
    end
    for _, name in ipairs({ 'health', 'magicka', 'fatigue' }) do
        local stat = types.Actor.stats.dynamic[name](self)
        stat.base = values[name]
        stat.current = values[name]
    end
    print(string.format('OPENOBLIVION_TES4_STATS level=%d health=%d magicka=%d fatigue=%d strength=%d speed=%d',
        values.level, values.health, values.magicka, values.fatigue, values.attributes.strength,
        values.attributes.speed))
end

return {
    interfaceName = 'TES4Stats',
    interface = {
        version = 1,
        skill = function(name) return ok and values.skills[name] or nil end,
        attribute = function(name) return ok and values.attributes[name] or nil end,
        level = function() return ok and values.level or nil end,
    },
    engineHandlers = {
        onUpdate = function() apply() end,
        -- Stats are starting values: apply once per character, not on every load.
        onSave = function() return { applied = applied } end,
        onLoad = function(saved) applied = saved and saved.applied or false end,
    },
}
