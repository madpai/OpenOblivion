-- SPDX-License-Identifier: GPL-3.0-only
-- Container list formatting, without an OpenMW runtime.
local root = assert(arg[1], 'repository root required')
package.path = root .. '/tools/android/?.lua;' .. package.path
local missingWorld, worldError = pcall(require, 'openmw.world')
assert(not missingWorld, 'openmw.world must be absent in this fixture')
assert(type(worldError) == 'string' and worldError:find("module 'openmw.world' not found", 1, true),
    tostring(worldError))
local container = require('scripts.openoblivion_container_items')
local checks = 0
local function check(value, message)
    checks = checks + 1
    assert(value, message)
end

check(container.engineHandlers == nil, 'unit load must not register activation')
check(container.canOpen(nil) == false, 'a missing type does not open')
check(container.canOpen({}) == false, 'a type without contents does not open')
check(container.canOpen({ contents = function() end }) == false, 'contents alone is not enough')
check(container.canOpen({ contents = function() end, record = function() end }) == true,
    'contents and record can open')

check(container.itemLabel({ name = 'Iron Longsword', count = 1 }) == 'Iron Longsword', 'one item has no count')
check(container.itemLabel({ name = ' Lockpick ', count = 4 }) == 'Lockpick x4', 'a stack shows a count')
check(container.itemLabel({ name = '', count = 2 }) == 'Unresolved item x2', 'empty names remain unresolved')
check(container.itemLabel({ count = 1 }) == 'Unresolved item', 'missing names remain unresolved')
check(container.itemLabel('nope') == nil, 'a non-table is skipped')

local rows, extra = container.rows({
    { name = 'Gold', count = 12 },
    { name = 'Key', count = 1 },
}, 8)
check(#rows == 2 and rows[1] == 'Gold x12' and rows[2] == 'Key' and extra == 0, 'short lists are complete')

local many = {}
for i = 1, 10 do many[i] = { name = 'Item' .. i, count = 1 } end
rows, extra = container.rows(many, 8)
check(#rows == 8 and rows[8] == 'Item8' and extra == 2, 'the window keeps eight rows')
check(select(2, container.rows(nil, 8)) == 0, 'a missing list is empty')
check(container.itemLabel({ name = 'Empty', count = 0 }) == nil, 'zero stacks are skipped')
check(container.itemLabel({ name = 'Empty', count = -1 }) == nil, 'negative stacks are skipped')
check(container.itemLabel({ name = 'Empty', count = 0/0 }) == nil, 'NaN counts are skipped')
rows, extra = container.rows({false, {name = 'Key', count = 1}}, 1)
check(#rows == 1 and rows[1] == 'Key' and extra == 0, 'invalid rows do not use the display limit')

print('container checks passed: ' .. checks)

-- Exercise the activation boundary: locked/trapped/non-player objects must
-- never dispatch a player UI event, even when a native snapshot is available.
local callback, sent, reads = nil, 0, 0
local Player, Container = {}, {}
Container.record = function() return { name = 'Original fixture chest' } end
Container.contents = function() reads = reads + 1; return {{name = 'Original key', count = 1}} end
package.loaded['openmw.types'] = {
    Player = Player, ESM4Container = Container,
    Lockable = { isLocked = function(o) return o.locked end,
        getTrapSpell = function(o)
            if o.brokenTrap then error('missing spell record') end
            return o.trap
        end },
}
package.loaded['openmw.interfaces'] = {
    Activation = { addHandlerForType = function(t, fn)
        assert(t == Container); callback = fn
    end },
}
local global = require('scripts.openoblivion_container')
global.engineHandlers.onInit()
check(type(callback) == 'function', 'activation handler is installed')
local actor = {type = Player, sendEvent = function(_, event, data)
    assert(event == 'OpenOblivionContainer' and data.name == 'Original fixture chest')
    sent = sent + 1
end}
callback({locked = true}, actor)
callback({trap = {}}, actor)
callback({brokenTrap = true}, actor)
callback({}, {type = {}})
check(sent == 0 and reads == 0, 'locks, traps, bad traps and NPCs do not read or open')
check(callback({}, actor) == false and sent == 1 and reads == 1, 'player activation opens exactly one snapshot')
print('container activation checks passed: ' .. checks)
