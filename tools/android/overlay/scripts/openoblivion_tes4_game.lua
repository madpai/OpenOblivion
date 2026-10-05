-- SPDX-License-Identifier: GPL-3.0-only
-- TES4 quests, scripts and dialogue running inside OpenMW (global script).
-- Connects the script runtime (openoblivion_tes4_script.lua) and the dialogue engine
-- (openoblivion_tes4_dialogue.lua) to the world through `host`, runs the quest scripts
-- every few seconds, and talks to the player's UI (openoblivion_tes4_ui.lua) by events.
-- Without the generated data (scripts/tes4data) this script does nothing.
local ok, quests = pcall(require, 'scripts.tes4data.quests')
if not ok then return {} end

local core = require('openmw.core')
local world = require('openmw.world')
local types = require('openmw.types')
local vfsOk, vfs = pcall(require, 'openmw.vfs')
local Script = require('scripts.openoblivion_tes4_script')
local Dialogue = require('scripts.openoblivion_tes4_dialogue')
local items = require('scripts.openoblivion_tes4_items')

local PLAYER, MQ02, AMULET_OF_KINGS = 0x14, 0x1E724, 0x250A0
local UPDATE_SECONDS = 5

local data = {
    quests = quests,
    index = require('scripts.tes4data.index'),
    actors = require('scripts.tes4data.actors'),
    load = function(kind, number) return require(string.format('scripts.tes4data.%s_%03d', kind, number)) end,
}

local function player() return world.players[1] end
-- The FormID of a record id string such as "FormId:0x20223ad" without the load-order byte
-- (the master is index 2 in this setup, but the data is keyed by the record's own 24 bits).
local function hexId(refId)
    local hex = tostring(refId):match('0x(%x+)')
    return hex and tonumber(hex, 16) % 0x1000000 or nil
end
local function formString(formId) return core.getFormId('Oblivion.esm', formId % 0x1000000) end

-- A reference by FormID, or nil when it is not loaded (the engine throws on unloaded objects).
local function object(formId)
    if formId == PLAYER then return player() end
    local found, result = pcall(world.getObjectByFormId, formString(formId))
    if not found or not result then return nil end
    local usable = pcall(function() return result.position end)
    return usable and result or nil
end

local host = {}
function host.log(text) print('OPENOBLIVION_TES4 ' .. tostring(text)) end
function host.random() return math.random() end
function host.hour() return (core.getGameTime() / 3600) % 24 end
local function send(name, payload)
    local p = player()
    if p then p:sendEvent(name, payload) end
end
function host.notify(text) send('TES4Notify', { text = text }) end
host.messageBox = host.notify
local quiet = false  -- no notifications while the new-game state is being set up
function host.fire(name, payload)
    if not quiet then send('TES4' .. name:sub(1, 1):upper() .. name:sub(2), payload) end
end

function host.cell(ref)
    local target = ref == PLAYER and player() or object(ref)
    local found, cell = pcall(function() return target and target.cell end)
    if not found or not cell then return nil end
    if cell.isExterior then
        return { world = hexId(cell.worldSpaceId), x = cell.gridX, y = cell.gridY }
    end
    return { interior = hexId(cell.id) }
end

function host.distance(ref, other)
    local a, b = object(ref), object(other)
    if not a or not b then return 1e9 end  -- unloaded references are far away, not at distance 0
    local ok2, distance = pcall(function() return (a.position - b.position):length() end)
    return ok2 and distance or 1e9
end

local function inventoryOf(ref)
    local target = object(ref)
    if not target then return nil end
    local ok2, inventory = pcall(types.Actor.inventory, target)
    return ok2 and inventory or nil
end
function host.itemCount(ref, base)
    local inventory = inventoryOf(ref)
    return inventory and inventory:countOf(items.id(base)) or 0
end
function host.addItem(ref, base, count)
    local inventory = inventoryOf(ref)
    if not inventory or count <= 0 then return end
    local made, created = pcall(world.createObject, items.id(base), count)
    if made then created:moveInto(inventory) else host.log('missing item ' .. items.id(base)) end
end
function host.removeItem(ref, base, count)
    local inventory = inventoryOf(ref)
    local item = inventory and inventory:find(items.id(base))
    if item then item:remove(math.min(count, item.count)) end
end
function host.setEnabled(ref, enabled)
    local target = object(ref)
    if target then pcall(function() target.enabled = enabled end) end
end
function host.isDisabled(ref)
    local target = object(ref)
    if not target then return false end
    local found, enabled = pcall(function() return target.enabled end)
    return found and not enabled
end

local rt = Script.new(host, data)
local dialogue = Dialogue.new(rt, data)
local started = false
local sinceUpdate = 0
local sessions = {}      -- [player id] = {session, npc}
local game = {}          -- the interface other global scripts use

local function nameOf(npc)
    local ok2, record = pcall(types.NPC.record, npc)
    return ok2 and record and record.name or ''
end

-- The recorded voice of a conversation: lines play one after another from the NPC.
local function stopVoice(held)
    if held and held.queue then
        held.queue = nil
        pcall(core.sound.stopSay, held.npc)
    end
end

local function playNext(held)
    while held.queue and held.queue[held.index] do
        local line = held.queue[held.index]
        held.index = held.index + 1
        if line.voice and not (vfsOk and vfs.fileExists(line.voice)) then host.log('no recorded voice ' .. line.voice) end
        if line.voice and vfsOk and vfs.fileExists(line.voice) then
            local ok2, err = pcall(core.sound.say, line.voice, held.npc, line.text)
            if ok2 then return end
            host.log('voice failed ' .. tostring(err))
        end
    end
    held.queue = nil
end

local function startVoice(held)
    stopVoice(held)
    held.queue, held.index = held.session.lines, 1
    playNext(held)
end

local function pack(session, npc)
    return { name = nameOf(npc), lines = session.lines, topics = session.topics, choices = session.choices,
        ended = session.ended }
end

-- Called by the actor bridge when the player activates a bridged TES4 NPC. Returns true when
-- the conversation window took over (so the host's own dialogue window must not open).
function game.talk(npc, actor, base)
    if not started then return false end
    local session = dialogue.begin(base)
    local held = { session = session, npc = npc }
    sessions[actor.id] = held
    actor:sendEvent('TES4DialogueOpen', pack(session, npc))
    startVoice(held)
    return true
end

local function journalData()
    local out = {}
    for formId, q in pairs(rt.state.quests) do
        local def = data.quests[formId]
        if def and #q.journal > 0 then
            local lines = {}
            for _, entry in ipairs(q.journal) do table.insert(lines, entry.text) end
            table.insert(out, { name = def.name ~= '' and def.name or def.id, running = q.running,
                completed = q.completed, lines = lines })
        end
    end
    table.sort(out, function(a, b)
        if a.completed ~= b.completed then return not a.completed end
        return a.name < b.name
    end)
    return out
end

local function start()
    if started then return end
    started = true
    if not rt.state.began then
        rt.state.began = true
        quiet = true
        rt.newGame()
        -- The prologue is skipped: the game starts where it ends, at the sewer exit, with the
        -- main quest handed over exactly as MQ02's stage 0 does, and the Emperor's Amulet of Kings
        -- (which the prologue puts in the player's hands) in the inventory.
        rt.C.setstage(MQ02, 0)
        rt.C.additem(PLAYER, AMULET_OF_KINGS, 1)
        quiet = false
    end
end

return {
    interfaceName = 'OpenOblivionTES4',
    interface = game,
    engineHandlers = {
        onPlayerAdded = function() start() end,
        onSave = function() return { rt = rt.save() } end,
        onLoad = function(saved)
            if saved and saved.rt then rt.load(saved.rt) end
            if world.players[1] then start() end
        end,
        onUpdate = function(dt)
            if not started then return end
            for _, held in pairs(sessions) do
                if held.queue then
                    local ok2, active = pcall(core.sound.isSayActive, held.npc)
                    if not (ok2 and active) then playNext(held) end
                end
            end
            sinceUpdate = sinceUpdate + dt
            if sinceUpdate >= UPDATE_SECONDS then
                sinceUpdate = 0
                rt.updateQuests()
            end
        end,
    },
    eventHandlers = {
        -- Probe hook: talk to a bridged NPC without going through activation.
        TES4Talk = function(event)
            local ok2, record = pcall(types.NPC.record, event.npc)
            local base = ok2 and record and type(record.head) == 'string' and hexId(record.head)
            if base then game.talk(event.npc, event.player, base) end
        end,
        TES4DialogueChoose = function(event)
            local held = event.player and sessions[event.player.id]
            if not held then return end
            held.session = dialogue.choose(held.session, event.topic)
            event.player:sendEvent('TES4DialogueUpdate', pack(held.session, held.npc))
            startVoice(held)
        end,
        TES4DialogueClose = function(event)
            if event.player then
                stopVoice(sessions[event.player.id])
                sessions[event.player.id] = nil
            end
        end,
        TES4JournalRequest = function(event)
            if event.player then event.player:sendEvent('TES4JournalData', { quests = journalData() }) end
        end,
    },
}
