-- SPDX-License-Identifier: GPL-3.0-only
-- Classic TES4 melee damage, transcribed from the original executable
-- (hand-to-hand Oblivion.exe 0x547280, weapons 0x547070, effective skill
-- 0x547b90, fatigue factor 0x547f00) with the owner's master overrides; see
-- docs/research/TES4_COMBAT.md.
local M = {}

-- Executable defaults, replaced where Oblivion.esm overrides them.
M.settings = {
    iActorLuckSkillBase = -20, fActorLuckSkillMult = 0.4,
    fHandDamageSkillBase = 0, fHandDamageSkillMult = 1.0,
    fHandDamageStrengthBase = 0, fHandDamageStrengthMult = 0.75,
    fFatigueBase = 1.0, fFatigueMult = 0.5,              -- master overrides
    fHandHealthMin = 1.0, fHandHealthMax = 15.0,          -- master overrides max
    fHandFatigueDamageMult = 0.5, fHandFatigueDamageBase = 1.0, -- master overrides
    fCombatDistance = 128.0, fHandReachMult = 0.6,        -- master overrides reach
    -- Weapons: exe defaults (skill base) and master overrides (the rest).
    fDamageWeaponMult = 0.5,
    fDamageWeaponConditionBase = 0.5, fDamageWeaponConditionMult = 0.5,
    fDamageSkillBase = 0.2, fDamageSkillMult = 1.5,
    fDamageStrengthBase = 0.75, fDamageStrengthMult = 0.5,
}

local function clamp(value, low, high) return math.max(low, math.min(high, value)) end

function M.effectiveSkill(skill, luck)
    local s = M.settings
    return clamp(skill + luck * s.fActorLuckSkillMult + s.iActorLuckSkillBase, 0, 100)
end

function M.fatigueFactor(current, base)
    local s = M.settings
    local ratio = base > 0 and clamp(current / base, 0, 1) or 1
    return s.fFatigueBase - (1 - ratio) * s.fFatigueMult
end

-- Returns health damage and fatigue damage for one hand-to-hand hit.
function M.handToHand(skill, strength, luck, fatigueCurrent, fatigueBase)
    local s = M.settings
    local skillTerm = M.effectiveSkill(skill, luck) * 0.01 * s.fHandDamageSkillMult + s.fHandDamageSkillBase
    local strengthTerm = math.min(strength, 100) * 0.01 * s.fHandDamageStrengthMult + s.fHandDamageStrengthBase
    local raw = skillTerm * strengthTerm * M.fatigueFactor(fatigueCurrent, fatigueBase)
    local health = s.fHandHealthMin + (s.fHandHealthMax - s.fHandHealthMin) * math.min(raw, 1)
    return health, health * s.fHandFatigueDamageMult + s.fHandFatigueDamageBase
end

-- Health damage of one weapon hit (0x547070): weapon damage x weapon mult x
-- condition term x skill term x strength term x fatigue factor. The skill is
-- the weapon's (blade, blunt, marksman); condition is the item's health
-- fraction. Fatigue cost per swing and power attack bonuses are not applied.
function M.weapon(damage, skill, strength, luck, fatigueCurrent, fatigueBase, condition)
    local s = M.settings
    local weaponTerm = damage * s.fDamageWeaponMult
    local conditionTerm = s.fDamageWeaponConditionBase + s.fDamageWeaponConditionMult * clamp(condition, 0, 1)
    local skillTerm = s.fDamageSkillBase + s.fDamageSkillMult * M.effectiveSkill(skill, luck) * 0.01
    local strengthTerm = s.fDamageStrengthBase + s.fDamageStrengthMult * math.min(strength, 100) * 0.01
    return weaponTerm * conditionTerm * skillTerm * strengthTerm * M.fatigueFactor(fatigueCurrent, fatigueBase)
end

-- Weapon reach: fCombatDistance x the weapon's reach, with the same body
-- allowance as hand reach (an inference).
function M.weaponReach(reach)
    return M.settings.fCombatDistance * reach + M.PLAYER_HALF_WIDTH + M.ACTOR_HALF_WIDTH
end

-- Hand reach, edge to edge as the host AI measures it: fCombatDistance x
-- fHandReachMult plus both bodies' half widths (player hull ~21, host actor
-- box ~13.3). Treating the TES4 reach as edge distance is an inference.
M.PLAYER_HALF_WIDTH = 21
M.ACTOR_HALF_WIDTH = 13.3
function M.handReach()
    return M.settings.fCombatDistance * M.settings.fHandReachMult + M.PLAYER_HALF_WIDTH + M.ACTOR_HALF_WIDTH
end

return M
