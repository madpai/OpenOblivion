-- SPDX-License-Identifier: GPL-3.0-only
-- Fixtures for the transcribed TES4 hand-to-hand formula.
local root = arg[1]
local combat = dofile(root .. '/tools/android/overlay/scripts/openoblivion_tes4_combat.lua')
local checks = 0
local function near(a, b, message)
    checks = checks + 1
    if math.abs(a - b) > 1e-3 then error(message .. ': ' .. a .. ' ~= ' .. b) end
end
local h, f = combat.handToHand(5, 50, 50, 150, 150)
near(h, 1.2625, 'starting player health damage'); near(f, 1.63125, 'starting player fatigue damage')
h = combat.handToHand(40, 35, 50, 160, 160)
near(h, 2.47, 'bandit hand-to-hand 40, strength 35')
near(combat.effectiveSkill(5, 50), 5, 'luck 50 is neutral')
near(combat.effectiveSkill(100, 100), 100, 'effective skill clamps to 100')
near(combat.effectiveSkill(0, 0), 0, 'effective skill clamps to 0')
near(combat.fatigueFactor(0, 150), 0.5, 'exhausted fatigue factor')
h = combat.handToHand(100, 100, 50, 150, 150)
near(h, 1 + 14 * 0.75, 'master health cap scale')
near(combat.handReach(), 128 * 0.6 + 21 + 13.3, 'reach edge to edge')
print('TES4 combat fixtures passed: ' .. checks .. ' checks')
