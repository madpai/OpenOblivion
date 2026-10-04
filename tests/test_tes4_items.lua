-- SPDX-License-Identifier: GPL-3.0-only
-- Fixtures for the TES4 leveled-list rolls (synthetic lists, no game data).
local root = arg[1]
package.preload['openmw.types'] = function() return {} end
package.preload['scripts.openoblivion_tes4_combat'] = function()
    return dofile(arg[1] .. '/tools/android/overlay/scripts/openoblivion_tes4_combat.lua')
end
package.preload['scripts.openoblivion_tes4_items_values'] = function()
    return {
        lists = {
            [100] = { 0, 0, { 1, 1, 1 }, { 5, 2, 1 }, { 5, 3, 1 }, { 10, 4, 1 } }, -- highest level only
            [101] = { 0, 1, { 1, 1, 1 }, { 5, 2, 1 }, { 10, 4, 1 } },             -- all levels
            [102] = { 100, 0, { 1, 1, 1 } },                                        -- always none
            [103] = { 0, 2, { 1, 50, 1 } },                                         -- each item in count
            [104] = { 0, 0, { 1, 5, 3 } },                                          -- entry count
        },
        inventories = { [7] = { { 100, 1 } }, [8] = { { 102, 1 } }, [9] = { { 103, 4 } }, [10] = { { 104, 2 } },
            [11] = { { 101, 1 } } },
    }
end
local items = dofile(root .. '/tools/android/overlay/scripts/openoblivion_tes4_items.lua')
local checks = 0
local function check(ok, message) checks = checks + 1; if not ok then error(message) end end
local function seen(npc, level)
    local out = {}
    for _ = 1, 400 do
        for _, row in ipairs(items.inventory(npc, level)) do out[row.id] = (out[row.id] or 0) + row.count end
    end
    return out
end
check(items.id(0x6c35e) == 'oo4_06c35e', 'host id format')
local s = seen(7, 7)
check(s.oo4_000002 and s.oo4_000003 and not s.oo4_000001 and not s.oo4_000004, 'only the highest level at or below the player')
s = seen(7, 1)
check(s.oo4_000001 == 400, 'level 1 has one candidate')
s = seen(11, 7)
check(s.oo4_000001 and s.oo4_000002 and not s.oo4_000004, 'all levels at or below the player')
check(next(seen(8, 20)) == nil, 'chance none 100 yields nothing')
s = seen(9, 1)
check(s.oo4_000032 == 1600, 'each item in count rolls the list per item')
s = seen(10, 1)
check(s.oo4_000005 == 2400, 'list count multiplies entry count')
print('TES4 item fixtures passed: ' .. checks .. ' checks')
