-- SPDX-License-Identifier: GPL-3.0-only
-- Overlay version (overrides the payload copy). Oblivion runs by default, so
-- always-run is pinned on and the phone WALK toggle holds Shift to walk. A run
-- state no longer depends on a key press arriving after the game has loaded.
-- Smooth controller movement stays off because the preview has no stick.
local storage = require('openmw.storage')
local settings = storage.playerSection('SettingsOMWControls')
local applied = false
local reported = false

local function apply()
    if applied then return end
    local ok, err = pcall(function()
        settings:set('alwaysRun', true)
        settings:set('smoothControllerMovement', false)
    end)
    if ok then
        applied = true
        print('OPENOBLIVION_RUN_GATE always-run')
    elseif not reported then
        reported = true
        print('OPENOBLIVION_RUN_GATE failed ' .. tostring(err))
    end
end

return { engineHandlers = { onActive = apply, onUpdate = function() apply() end } }
