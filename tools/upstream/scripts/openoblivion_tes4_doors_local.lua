-- SPDX-License-Identifier: GPL-3.0-only
-- Observe the ordinary object clock without starting playback from this script.
local self = require('openmw.self')
local animation = require('openmw.animation')
local elapsed, nextSample = 0, 0.25
return {engineHandlers = {onUpdate = function(dt)
    elapsed = elapsed + dt
    if elapsed < nextSample then return end
    nextSample = nextSample + 0.25
    for _, group in ipairs({'open', 'close'}) do
        local time = animation.getCurrentTime(self, group)
        if time then
            print(string.format('OPENOBLIVION_DOOR_CLOCK group=%s elapsed=%.6f time=%.6f playing=%s',
                group, elapsed, time, tostring(animation.isPlaying(self, group))))
        end
    end
end}}
