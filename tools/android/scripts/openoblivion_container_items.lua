-- SPDX-License-Identifier: GPL-3.0-only
-- Pure presentation helpers shared by global/player scripts and fixtures.
local M = {}

function M.canOpen(containerType)
    return containerType ~= nil
        and type(containerType.contents) == 'function'
        and type(containerType.record) == 'function'
end

function M.itemLabel(item)
    if type(item) ~= 'table' then return nil end
    local name = type(item.name) == 'string' and item.name:match('^%s*(.-)%s*$') or ''
    if name == '' then name = 'Unresolved item' end
    local count = type(item.count) == 'number' and item.count or 1
    if count ~= count or count < 1 or count == math.huge then return nil end
    if count > 1 then return name .. ' x' .. tostring(math.floor(count)) end
    return name
end

function M.rows(items, limit)
    limit = math.max(0, math.floor(limit or 8))
    local valid, lines = {}, {}
    if type(items) ~= 'table' then return lines, 0 end
    for _, item in ipairs(items) do
        local label = M.itemLabel(item)
        if label ~= nil then valid[#valid + 1] = label end
    end
    for i = 1, math.min(#valid, limit) do lines[i] = valid[i] end
    return lines, math.max(0, #valid - limit)
end

return M
