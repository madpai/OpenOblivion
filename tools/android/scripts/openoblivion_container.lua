-- SPDX-License-Identifier: GPL-3.0-only
-- Read-only TES4 base-record inventory; no loot transfer or leveled rolls.
local items = require('scripts.openoblivion_container_items')
local types = require('openmw.types')
local I = require('openmw.interfaces')

local function onContainer(object, actor)
    if actor == nil or actor.type ~= types.Player then return end
    if not items.canOpen(types.ESM4Container) then return end
    local trapOk, trap = pcall(types.Lockable.getTrapSpell, object)
    if types.Lockable.isLocked(object) or not trapOk or trap ~= nil then return end
    local ok, contents = pcall(types.ESM4Container.contents, object)
    if not ok or type(contents) ~= 'table' then return end
    local name = ''
    local recordOk, record = pcall(types.ESM4Container.record, object)
    if recordOk and record ~= nil and type(record.name) == 'string' then name = record.name end
    print('OPENOBLIVION_CONTAINER name=' .. tostring(name):gsub('[%c]', ' ')
        .. ' base_rows=' .. tostring(#contents))
    actor:sendEvent('OpenOblivionContainer', { name = name, items = contents })
    return false
end

return {
    engineHandlers = {
        onInit = function()
            print('OPENOBLIVION_CONTAINER registered=' .. tostring(items.canOpen(types.ESM4Container)))
            if items.canOpen(types.ESM4Container) and I.Activation ~= nil then
                I.Activation.addHandlerForType(types.ESM4Container, onContainer)
            end
        end,
    },
}
