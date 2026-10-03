-- SPDX-License-Identifier: GPL-3.0-only
-- Read-only actor clock observations; does not start an animation itself.
local self = require('openmw.self')
local animation = require('openmw.animation')
local elapsed, nextSample = 0, 1
return {engineHandlers = {onUpdate = function(dt)
    elapsed = elapsed + dt
    if elapsed < nextSample then return end
    nextSample = nextSample + 1
    assert(animation.isPlaying(self, 'idle'), 'default idle is not playing')
    local time = animation.getCurrentTime(self, 'idle')
    assert(time ~= nil and time >= 0, 'default idle time is missing')
    print(string.format('OPENOBLIVION_ANIMATION_SAMPLE id=%s elapsed=%.6f time=%.6f loops=%d',
        self.id, elapsed, time, animation.getLoopCount(self, 'idle')))
end}}
