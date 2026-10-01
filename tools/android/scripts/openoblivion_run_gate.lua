-- SPDX-License-Identifier: GPL-3.0-only
-- Make the phone run button a held Shift. The borrowed control script treats
-- Shift as the opposite of the saved always-run setting, and its smooth-stick
-- path can ignore Shift. This preview has no stick, so those two settings are
-- pinned and the overlay owns the gait.
local storage = require('openmw.storage')
local settings = storage.playerSection('SettingsOMWControls')
local applied = false
local reported = false

local function apply()
    if applied then return end
    local ok, err = pcall(function()
        settings:set('alwaysRun', false)
        settings:set('smoothControllerMovement', false)
    end)
    if ok then
        applied = true
        print('OPENOBLIVION_RUN_GATE shift-run')
    elseif not reported then
        reported = true
        print('OPENOBLIVION_RUN_GATE failed ' .. tostring(err))
    end
end

return { engineHandlers = { onActive = apply, onUpdate = function() apply() end } }
