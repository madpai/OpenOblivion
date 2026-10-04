-- SPDX-License-Identifier: GPL-3.0-only
-- TES4 items for the phone overlay: leveled rolls over the master's lists and
-- equipping by TES4 body slot. Host item records are generated at package
-- time (tools/android/tes4_items.py) as "oo4_" + the FormID's low 24 bits.
--
-- Leveled rolls follow the Construction Set's documented LVLI rules (not yet
-- checked against the executable): roll chance none; candidates are entries at
-- or below the player's level, or only those at the highest such level unless
-- "calculate from all levels" (flag 1) is set; pick one at random; with
-- "calculate for each item in count" (flag 2) each counted item rolls again.
local types = require('openmw.types')

local ok, values = pcall(require, 'scripts.openoblivion_tes4_items_values')
local M = { available = ok }

function M.id(formId) return string.format('oo4_%06x', formId) end

local function flag(flags, bit) return math.floor(flags / bit) % 2 == 1 end

local function pick(list, level)
    if math.random(0, 99) < list[1] then return nil end
    local top = -math.huge
    for i = 3, #list do
        if list[i][1] <= level and list[i][1] > top then top = list[i][1] end
    end
    local candidates = {}
    for i = 3, #list do
        local entry = list[i]
        if entry[1] <= level and (flag(list[2], 1) or entry[1] == top) then candidates[#candidates + 1] = entry end
    end
    if #candidates == 0 then return nil end
    return candidates[math.random(1, #candidates)]
end

local function roll(formId, count, level, out, depth)
    local list = ok and values.lists[formId]
    if not list then
        out[M.id(formId)] = (out[M.id(formId)] or 0) + count
        return
    end
    if depth > 8 then return end
    local each = flag(list[2], 2)
    for _ = 1, each and count or 1 do
        local entry = pick(list, level)
        if entry then roll(entry[2], entry[3] * (each and 1 or count), level, out, depth + 1) end
    end
end

-- {{id, count}, ...} rolled from a TES4 NPC record's inventory.
function M.inventory(npcFormId, level)
    local out, rows = {}, {}
    for _, row in ipairs(ok and values.inventories[npcFormId] or {}) do roll(row[1], row[2], level, out, 0) end
    for id, count in pairs(out) do rows[#rows + 1] = { id = id, count = count } end
    table.sort(rows, function(a, b) return a.id < b.id end)
    return rows
end

function M.record(id)
    for _, kind in ipairs({ types.Armor, types.Clothing, types.Weapon, types.Miscellaneous, types.Book,
        types.Potion, types.Ingredient }) do
        local found, record = pcall(kind.record, id)
        if found and record then return record, kind end
    end
end

function M.isApparel(id)
    local _, kind = M.record(id)
    return kind == types.Armor or kind == types.Clothing
end

-- TES4 body regions each host type covers. TES4 equips one item per region; a
-- robe covers upper and lower body.
local function slotsFor(item)
    local S = types.Actor.EQUIPMENT_SLOT
    if types.Armor.objectIsInstance(item) then
        local T, kind = types.Armor.TYPE, types.Armor.record(item).type
        if kind == T.Helmet then return S.Helmet, { 'head' } end
        if kind == T.Cuirass then return S.Cuirass, { 'upper' } end
        if kind == T.Greaves then return S.Greaves, { 'lower' } end
        if kind == T.Boots then return S.Boots, { 'foot' } end
        if kind == T.LGauntlet then return S.LeftGauntlet, { 'hand' } end
        if kind == T.Shield then return S.CarriedLeft, { 'shield' } end
    elseif types.Clothing.objectIsInstance(item) then
        local T, kind = types.Clothing.TYPE, types.Clothing.record(item).type
        if kind == T.Robe then return S.Robe, { 'upper', 'lower' } end
        if kind == T.Shirt then return S.Shirt, { 'upper' } end
        if kind == T.Pants then return S.Pants, { 'lower' } end
        if kind == T.Skirt then return S.Skirt, { 'lower' } end
        if kind == T.Shoes then return S.Boots, { 'foot' } end
        if kind == T.LGlove then return S.LeftGauntlet, { 'hand' } end
        if kind == T.Amulet then return S.Amulet, { 'amulet' } end
        if kind == T.Ring then return S.LeftRing, { 'ring' } end
    end
end

-- Equip every generated apparel item the actor carries, one per TES4 region,
-- robes first, then armor, then clothing. Local scripts only (equips self).
function M.equipApparel(actor)
    local candidates = {}
    for _, item in ipairs(types.Actor.inventory(actor):getAll()) do
        if item.recordId:sub(1, 4) == 'oo4_' then
            local slot, regions = slotsFor(item)
            if slot then
                local rank = #regions == 2 and 0 or types.Armor.objectIsInstance(item) and 1 or 2
                candidates[#candidates + 1] = { item = item, slot = slot, regions = regions, rank = rank }
            end
        end
    end
    table.sort(candidates, function(a, b)
        if a.rank ~= b.rank then return a.rank < b.rank end
        return a.item.recordId < b.item.recordId
    end)
    local equipment, used, S = types.Actor.getEquipment(actor), {}, types.Actor.EQUIPMENT_SLOT
    local count = 0
    for _, c in ipairs(candidates) do
        local slot, regions = c.slot, c.regions
        if regions[1] == 'ring' and used.ring then slot, regions = S.RightRing, { 'ring2' } end
        local free = true
        for _, region in ipairs(regions) do
            if used[region] then free = false end
        end
        if free then
            for _, region in ipairs(regions) do used[region] = true end
            equipment[slot] = c.item
            count = count + 1
        end
    end
    types.Actor.setEquipment(actor, equipment)
    return count
end

return M
