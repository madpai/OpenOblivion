-- SPDX-License-Identifier: GPL-3.0-only
-- Left-side list for a TES4 container. Closes on the Close row.
local uiOk, ui = pcall(require, 'openmw.ui')
if not uiOk then
    if type(ui) ~= 'string' or not ui:find("module 'openmw.ui' not found", 1, true) then
        error(ui)
    end
    return {}
end

local async = require('openmw.async')
local util = require('openmw.util')
local container = require('scripts.openoblivion_container_items')
local I = require('openmw.interfaces')

local LAYER = 'OpenOblivionContainer'
local window

local function closeWindow()
    if window ~= nil then
        window:destroy()
        window = nil
        I.UI.removeMode('Interface')
    end
end

local function showWindow(data)
    closeWindow()
    if ui.layers.indexOf(LAYER) == nil then
        ui.layers.insertAfter('HUD', LAYER, { interactive = true })
    end
    local title = type(data.name) == 'string' and data.name:match('^%s*(.-)%s*$') or ''
    if title == '' then title = 'Container' end
    local lines, extra = container.rows(data.items, 8)
    I.UI.addMode('Interface', { windows = {} })
    local content = ui.content {}
    content:add { type = ui.TYPE.Text, props = {
        text = title .. ' (base contents)',
        textSize = 22,
        textColor = util.color.rgb(1, 0.92, 0.7),
        autoSize = true,
    } }
    for i = 1, #lines do
        content:add { type = ui.TYPE.Text, props = {
            text = lines[i],
            textSize = 18,
            textColor = util.color.rgb(1, 1, 1),
            autoSize = true,
        } }
    end
    if extra > 0 then
        content:add { type = ui.TYPE.Text, props = {
            text = '+' .. tostring(extra) .. ' more',
            textSize = 16,
            textColor = util.color.rgb(0.8, 0.8, 0.8),
            autoSize = true,
        } }
    end
    content:add {
        type = ui.TYPE.Text,
        props = {
            text = 'Close',
            textSize = 18,
            textColor = util.color.rgb(0.75, 0.9, 1),
            autoSize = true,
        },
        events = { mouseClick = async:callback(function() closeWindow() end) },
    }
    window = ui.create {
        layer = LAYER,
        type = ui.TYPE.Widget,
        props = {
            position = util.vector2(16, 48),
            size = util.vector2(280, 36 + 22 * (#lines + (extra > 0 and 1 or 0) + 2)),
        },
        content = ui.content {
            {
                type = ui.TYPE.Image,
                props = {
                    resource = ui.texture { path = 'white' },
                    color = util.color.rgb(0.05, 0.07, 0.08),
                    alpha = 0.88,
                    relativeSize = util.vector2(1, 1),
                },
            },
            {
                type = ui.TYPE.Flex,
                props = {
                    position = util.vector2(12, 10),
                    horizontal = false,
                    arrange = ui.ALIGNMENT.Start,
                },
                content = content,
            },
        },
    }
end

return {
    eventHandlers = {
        OpenOblivionContainerClose = closeWindow,
        UiModeChanged = function(data)
            if data.newMode ~= 'Interface' then closeWindow() end
        end,
        OpenOblivionContainer = function(data)
            if type(data) ~= 'table' then return end
            showWindow(data)
        end,
    },
}
