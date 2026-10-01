-- SPDX-License-Identifier: GPL-3.0-only
-- Original automation using the pinned upstream API, not OpenOblivion server rules.
local core = require('openmw.core')
local self = require('openmw.self')
local debug = require('openmw.debug')
local elapsed = 0
local captured = false

return {
    engineHandlers = {
        onUpdate = function(dt)
            elapsed = elapsed + dt
            if not captured and elapsed >= 5 then
                captured = true
                print('OPENOBLIVION_SCENE_PROBE cell=' .. tostring(self.cell.id)
                    .. ' name=' .. tostring(self.cell.name)
                    .. ' exterior=' .. tostring(self.cell.isExterior))
                debug.takeScreenshot()
            end
            if elapsed >= 7 then
                print('OPENOBLIVION_SCENE_PROBE_DONE')
                core.quit()
            end
        end,
    },
}
