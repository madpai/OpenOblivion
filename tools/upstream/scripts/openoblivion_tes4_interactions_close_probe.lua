-- SPDX-License-Identifier: GPL-3.0-only
-- Test-only close/capture driver; never included in the phone APK.
local I = require('openmw.interfaces')
local self = require('openmw.self')
local debug = require('openmw.debug')
local frames, captured = 0, false
return {
    engineHandlers = {
        onFrame = function()
            if captured or I.UI.getMode() ~= 'Interface' then return end
            -- onFrame receives zero dt while the interface pauses simulation.
            frames = frames + 1
            if frames < 10 then return end
            debug.takeScreenshot()
            print('OPENOBLIVION_CONTAINER_UI_CAPTURED')
            self:sendEvent('OpenOblivionContainerClose', {})
            captured = true
        end,
    },
}
