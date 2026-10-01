-- SPDX-License-Identifier: GPL-3.0-only
-- Display-name and activation-distance decisions, without an OpenMW runtime.
local root = assert(arg[1], 'repository root required')
package.path = root .. '/tools/android/?.lua;' .. package.path
local missingCamera, cameraError = pcall(require, 'openmw.camera')
assert(not missingCamera, 'openmw.camera must be absent in this fixture')
assert(type(cameraError) == 'string' and cameraError:find("module 'openmw.camera' not found", 1, true),
    tostring(cameraError))
local look = require('scripts.openoblivion_look_name')
local checks = 0
local function check(value, message)
    checks = checks + 1
    assert(value, message)
end

check(look.engineHandlers == nil, 'unit load must not return engine handlers')
check(look.fallbackActivationDistance == 192, 'measured activation fallback drifted')
check(look.unitsPerFoot == 22, 'feet-to-units conversion drifted')

check(look.displayName('Iron Longsword', 'weapirondagger') == 'Iron Longsword', 'name should win')
check(look.displayName('  Iron Longsword  ', 'id') == 'Iron Longsword', 'surrounding space is trimmed')
check(look.displayName('', 'statuelamp') == nil, 'empty name does not show the record id')
check(look.displayName(nil, 'doorvilverin') == nil, 'missing name does not show the record id')
check(look.displayName(' ', 'id') == nil, 'whitespace is not a name')
check(look.displayName('', '') == nil, 'empty name and id hide')
check(look.displayName(nil, nil) == nil, 'missing name and id hide')

local function plate(hit, activation, cameraDistance, telekinesis, allows)
    return look.plateText('Crate', 'crate01', hit, activation, cameraDistance, telekinesis, allows)
end

check(plate(nil, 192, 0, 0, false) == nil, 'a miss hides the plate')
check(plate(100, 192, 0, 0, false) == 'Crate', 'a hit inside range shows the name')
check(plate(192, 192, 0, 0, false) == 'Crate', 'the activation limit is inclusive')
check(plate(193, 192, 0, 0, false) == nil, 'one unit past the limit hides')
check(plate(240, 192, 50, 0, false) == 'Crate', 'camera pullback is not part of focus distance')
check(plate(243, 192, 50, 0, false) == nil, 'focus distance past the limit hides')
check(plate(250, 192, 0, 80, true) == 'Crate', 'telekinesis extends an allowed target')
check(plate(273, 192, 0, 80, true) == nil, 'telekinesis still has a limit')
check(plate(250, 192, 0, 80, false) == nil, 'actors and plain doors reject the extra reach')
check(plate(100, 192, 0, 0, false) ~= nil and look.plateText('', 'crate01', 100, 192, 0, 0, false) == nil,
    'in-range empty name hides instead of showing the record id')
check(look.plateText('', '', 10, 192, 0, 0, true) == nil, 'in-range target with no label hides')
check(look.plateText('Crate', 'crate01', 10, nil, 0, 0, true) == nil, 'unknown activation distance hides')

print('Look name checks passed: ' .. checks)
