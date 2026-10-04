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
-- Weapons (Oblivion.exe 0x547070): damage x 0.5 x condition x skill x strength x fatigue.
-- Iron Longsword (damage 10) in the starting player's hands: blade 5, strength 50, luck 50.
near(combat.weapon(10, 5, 50, 50, 150, 150, 1), 1.375, 'starting player with an iron longsword')
near(combat.weapon(10, 100, 100, 50, 150, 150, 1), 5 * 1.0 * 1.7 * 1.25, 'master skill and strength')
near(combat.weapon(10, 5, 50, 50, 150, 150, 0), 1.375 * 0.5 / 1.0, 'broken weapon halves damage')
near(combat.weapon(10, 5, 50, 50, 0, 150, 1), 1.375 * 0.5, 'exhausted fatigue factor')
near(combat.weapon(10, 5, 150, 50, 150, 150, 1), combat.weapon(10, 5, 100, 50, 150, 150, 1), 'strength clamps to 100')
near(combat.weaponReach(1.3), 128 * 1.3 + 21 + 13.3, 'weapon reach')
-- Armor (Oblivion.exe 0x547370 piece rating, 0x60e540 total capped at fMaxArmorRating).
near(combat.armorPiece(10, 5, 50, 1), 10 * (0.35 + 0.65 * 0.05), 'iron cuirass at skill 5')
near(combat.armorPiece(10, 100, 100, 1), 10 * 1.0, 'master armor skill gives the full rating')
near(combat.armorPiece(10, 100, 100, 0.5), 5, 'condition scales the rating')
near(combat.armorFactor(0), 1, 'no armor lets everything through')
near(combat.armorFactor(20), 0.8, 'armor rating blocks that percentage')
near(combat.armorFactor(500), 0.15, 'rating caps at 85')
print('TES4 combat fixtures passed: ' .. checks .. ' checks')
