-- SPDX-License-Identifier: GPL-3.0-only
-- Run the shipped Lua filter itself against original movement trajectories.
local root = assert(arg[1], 'repository root required')
package.path = root .. '/tools/android/?.lua;' .. package.path
local eye = require('scripts.openoblivion_grounded_eye')
local checks = 0
local function check(value, message)
    checks = checks + 1
    assert(value, message)
end
local function near(a, b, eps)
    check(math.abs(a-b) < (eps or 1e-7), tostring(a) .. ' differs from ' .. tostring(b))
end
local function position(z, x, y) return {x=x or 0, y=y or 0, z=z} end

-- Each tread changes physical height abruptly, in both directions. The eye
-- moves monotonically, without overshoot, and settles on the new landing.
for _, direction in ipairs({1, -1}) do
    local filter = eye.new()
    local view = 0
    filter.update(position(0), 'stairs', true, false, false, 1/60)
    for step=1,20 do
        local z = direction*step*16
        for frame=1,8 do
            local nextView = z + filter.update(position(z), 'stairs', true, false, false, 1/60)
            check(direction*(nextView-view) >= -1e-7, 'stair view reverses direction')
            check(math.abs(nextView-view) < 6, 'step jolt not reduced')
            check(math.abs(nextView-z) <= 48, 'eye lag is unbounded')
            view = nextView
        end
    end
    for frame=1,90 do
        view = direction*320 + filter.update(position(direction*320), 'stairs', true, false, false, 1/60)
    end
    near(view, direction*320, 0.001)
end

-- Continuous ramps and flat ground are stable at different frame cadences.
local results = {}
for _, fps in ipairs({30,60,120}) do
    local filter = eye.new()
    filter.update(position(0), 'ramp', true, false, false, 1/fps)
    local view
    for i=1,fps*3 do
        local z = 60*i/fps
        view = z + filter.update(position(z), 'ramp', true, false, false, 1/fps)
        check(view <= z and z-view < 7, 'ramp response overshoots or trails too far')
    end
    results[#results+1] = view
    for i=1,fps do view = 180+filter.update(position(180), 'ramp', true, false, false, 1/fps) end
    near(view, 180, 0.001)
end
check(math.abs(results[1]-results[3]) < 1, 'response depends excessively on frame cadence')

-- Jump intent, airborne motion, swimming, large drops, teleport/cell changes,
-- long frames and pause resets must immediately return to physical height.
local transitions = {
    {p=position(32), grounded=true, jumping=true},
    {p=position(32), grounded=false},
    {p=position(32), grounded=true, swimming=true},
    {p=position(-80), grounded=true},
    {p=position(32,200), grounded=true},
    {p=position(32), grounded=true, cell='other'},
    {p=position(32), grounded=true, dt=0.5},
}
for _, case in ipairs(transitions) do
    local filter = eye.new()
    filter.update(position(0), 'stairs', true, false, false, 1/60)
    check(filter.update(position(16), 'stairs', true, false, false, 1/60) < -10, 'test must begin with eye lag')
    near(filter.update(case.p, case.cell or 'stairs', case.grounded, case.jumping or false,
        case.swimming or false, case.dt or 1/60), 0)
end
local filter = eye.new()
filter.update(position(0), 'stairs', true, false, false, 1/60)
filter.update(position(16), 'stairs', true, false, false, 1/60)
filter.reset()
near(filter.update(position(16), 'stairs', true, false, false, 1/60), 0)
near(filter.update(position(32), 'stairs', false, false, false, 1/60), 0)
near(filter.update(position(16), 'stairs', true, false, false, 1/60), 0)
print('Grounded eye trajectory checks passed: ' .. checks)
