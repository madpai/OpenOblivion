-- SPDX-License-Identifier: GPL-3.0-only
-- Player-side UI for the TES4 quests and dialogue: HUD messages, the conversation window and
-- the journal. State lives in openoblivion_tes4_game.lua; this script only shows it and sends
-- the player's choices back as events.
local uiOk, ui = pcall(require, 'openmw.ui')
if not uiOk then return {} end

local async = require('openmw.async')
local core = require('openmw.core')
local util = require('openmw.util')
local self = require('openmw.self')
local I = require('openmw.interfaces')

local LAYER = 'OpenOblivionTES4'
local PAGE = 8
local GOLD = util.color.rgb(0.93, 0.82, 0.55)
local TEXT = util.color.rgb(0.92, 0.9, 0.84)
local DIM = util.color.rgb(0.62, 0.6, 0.55)
local LINK = util.color.rgb(0.75, 0.9, 1)

local window, kind

-- Panel and column sizes follow the screen (the phone runs 960x540, desktop probes 800x600).
local function sizes()
    local screen = ui.screenSize()
    local width, height = screen.x - 48, screen.y - 48
    local left = 300
    return { width = width, height = height, left = left, right = width - left - 48 }
end
local dialogue = { page = 1 }
local journal = { quests = {}, selected = 1 }

local function ensureLayer()
    if ui.layers.indexOf(LAYER) == nil then
        ui.layers.insertAfter('HUD', LAYER, { interactive = true })
    end
end

local function close()
    local was = kind
    if window then window:destroy(); window = nil end
    kind = nil
    if was == 'dialogue' then
        core.sendGlobalEvent('TES4DialogueClose', { player = self.object })
        I.UI.removeMode('Interface')
    elseif was == 'journal' then
        I.UI.removeMode('Journal')
    end
end

-- The window was removed from outside (a mode change): drop ours without touching modes.
local function vanish()
    if window then window:destroy(); window = nil end
    if kind == 'dialogue' then core.sendGlobalEvent('TES4DialogueClose', { player = self.object }) end
    kind = nil
end

local function text(content, props)
    props = props or {}
    return {
        type = ui.TYPE.Text,
        props = { text = content, textSize = props.size or 20, textColor = props.color or TEXT, autoSize = props.autoSize ~= false,
            multiline = props.multiline, wordWrap = props.wordWrap, size = props.box },
        events = props.onClick and { mouseClick = async:callback(props.onClick) } or nil,
    }
end

local function row(content, props)
    -- a tappable row: larger text and a gap below so a finger can pick it
    props = props or {}
    props.size = props.size or 23
    return {
        type = ui.TYPE.Flex, props = { horizontal = false, autoSize = true },
        content = ui.content { text(content, props), text(' ', { size = 9 }) },
    }
end

local function panel(size, content)
    return ui.create {
        layer = LAYER,
        type = ui.TYPE.Widget,
        props = { position = util.vector2(24, 24), size = size },
        content = ui.content {
            { type = ui.TYPE.Image, props = { resource = ui.texture { path = 'white' },
                color = util.color.rgb(0.05, 0.045, 0.04), alpha = 0.92, relativeSize = util.vector2(1, 1) } },
            { type = ui.TYPE.Flex, props = { position = util.vector2(14, 10), horizontal = true }, content = content },
        },
    }
end

local function column(width, height, rows)
    local content = ui.content {}
    for _, row in ipairs(rows) do content:add(row) end
    return { type = ui.TYPE.Flex, props = { horizontal = false, size = util.vector2(width, height - 20) }, content = content }
end

-- -- conversation ---------------------------------------------------------------
local function chooseTopic(id)
    core.sendGlobalEvent('TES4DialogueChoose', { player = self.object, topic = id })
end

local function showDialogue()
    local state = dialogue
    if window then window:destroy(); window = nil end
    ensureLayer()
    if kind ~= 'dialogue' then
        kind = 'dialogue'
        I.UI.addMode('Interface', { windows = {} })
    end
    local left = { text(state.name or '', { size = 24, color = GOLD }), text(' ', { size = 8 }) }
    local source = (#state.choices > 0) and state.choices or state.topics
    local pages = math.max(1, math.ceil(#source / PAGE))
    if state.page > pages then state.page = pages end
    if #state.choices > 0 then table.insert(left, text('Choose:', { size = 18, color = DIM })) end
    for i = (state.page - 1) * PAGE + 1, math.min(#source, state.page * PAGE) do
        local entry = source[i]
        table.insert(left, row(entry.name, { color = LINK, onClick = function() chooseTopic(entry.id) end }))
    end
    if pages > 1 then
        table.insert(left, {
            type = ui.TYPE.Flex, props = { horizontal = true, autoSize = true },
            content = ui.content {
                text('< prev   ', { size = 19, color = LINK, onClick = function()
                    state.page = math.max(1, state.page - 1); showDialogue() end }),
                text(string.format('%d/%d   ', state.page, pages), { size = 18, color = DIM }),
                text('next >', { size = 19, color = LINK, onClick = function()
                    state.page = math.min(pages, state.page + 1); showDialogue() end }),
            },
        })
    end
    table.insert(left, text(' ', { size = 8 }))
    table.insert(left, row('Goodbye', { color = GOLD, onClick = close }))
    local right = { text(' ', { size = 8 }) }
    local size = sizes()
    for _, line in ipairs(state.lines) do
        table.insert(right, text(line.text, { size = 21, multiline = true, wordWrap = true, autoSize = false,
            box = util.vector2(size.right - 20, 28 * math.ceil(#line.text / math.max(20, (size.right - 20) / 11)) + 8) }))
    end
    if #state.lines == 0 then table.insert(right, text('...', { size = 21, color = DIM })) end
    window = panel(util.vector2(size.width, size.height),
        ui.content { column(size.left + 20, size.height, left), column(size.right, size.height, right) })
end

local function openDialogue(data)
    dialogue = { name = data.name, lines = data.lines or {}, topics = data.topics or {}, choices = data.choices or {},
        page = 1, ended = data.ended }
    showDialogue()
end

local function updateDialogue(data)
    dialogue.lines, dialogue.topics, dialogue.choices = data.lines or {}, data.topics or {}, data.choices or {}
    dialogue.ended = data.ended
    dialogue.page = 1
    showDialogue()
    if dialogue.ended and #dialogue.choices == 0 then
        -- the conversation ends after its last line: leave the text up until the player taps Goodbye
        dialogue.topics = {}
        showDialogue()
    end
end

-- -- journal ---------------------------------------------------------------------
local function showJournal()
    if window then window:destroy(); window = nil end
    ensureLayer()
    kind = 'journal'  -- the Journal mode is already active: it is what called us
    local left = { text('Journal', { size = 24, color = GOLD }), text(' ', { size = 8 }) }
    local quests = journal.quests
    for i, quest in ipairs(quests) do
        local color = i == journal.selected and GOLD or (quest.completed and DIM or LINK)
        table.insert(left, row(quest.name .. (quest.completed and ' (done)' or ''), { size = 21, color = color,
            onClick = function() journal.selected = i; showJournal() end }))
    end
    if #quests == 0 then table.insert(left, text('No entries yet.', { size = 19, color = DIM })) end
    table.insert(left, text(' ', { size = 8 }))
    table.insert(left, row('Close', { color = GOLD, onClick = close }))
    local right = { text(' ', { size = 8 }) }
    local quest = quests[journal.selected]
    local size = sizes()
    if quest then
        for _, line in ipairs(quest.lines) do
            table.insert(right, text(line, { size = 18, multiline = true, wordWrap = true, autoSize = false,
                box = util.vector2(size.right - 20, 24 * math.ceil(#line / math.max(20, (size.right - 20) / 10)) + 8) }))
        end
    end
    window = panel(util.vector2(size.width, size.height),
        ui.content { column(size.left + 20, size.height, left), column(size.right, size.height, right) })
end

local function registerJournal()
    if I.UI and I.UI.registerWindow then
        I.UI.registerWindow('Journal', function()
            core.sendGlobalEvent('TES4JournalRequest', { player = self.object })
        end, function()
            if kind == 'journal' then vanish() end
        end)
    end
end

return {
    engineHandlers = {
        onInit = registerJournal,
        onLoad = registerJournal,
    },
    eventHandlers = {
        TES4Notify = function(data) if data and data.text and data.text ~= '' then ui.showMessage(data.text) end end,
        TES4Journal = function() ui.showMessage('Journal updated') end,
        TES4Topic = function() end,
        TES4DialogueOpen = openDialogue,
        TES4DialogueUpdate = updateDialogue,
        TES4JournalData = function(data)
            journal.quests = data.quests or {}
            if journal.selected > #journal.quests then journal.selected = 1 end
            showJournal()
        end,
        UiModeChanged = function(data)
            if kind == 'dialogue' and data.newMode ~= 'Interface' then vanish() end
        end,
    },
}
