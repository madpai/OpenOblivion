-- SPDX-License-Identifier: GPL-3.0-only
-- Fixtures for the TES4 script runtime: quests, stages, conditions and commands (synthetic data).
local root = arg[1]
package.preload['scripts.openoblivion_tes4_commands'] = function()
    return dofile(root .. '/tools/android/overlay/scripts/openoblivion_tes4_commands.lua')
end
local M = dofile(root .. '/tools/android/overlay/scripts/openoblivion_tes4_script.lua')
local checks = 0
local function check(ok, message) checks = checks + 1; if not ok then error(message, 2) end end

local log, notes, events = {}, {}, {}
local items = {}
local host = {
    log = function(text) table.insert(log, text) end,
    notify = function(text) table.insert(notes, text) end,
    messageBox = function(text) table.insert(notes, text) end,
    fire = function(name, payload) table.insert(events, { name, payload }) end,
    random = function() return 0.5 end,
    hour = function() return 13.5 end,
    itemCount = function(ref, base) return items[base] or 0 end,
    addItem = function(ref, base, n) items[base] = (items[base] or 0) + n end,
    removeItem = function(ref, base, n) items[base] = (items[base] or 0) - n end,
    cell = function(ref) return { world = 9, x = 3, y = -4 } end,
}

local Q1, Q2, GOLD, TOPIC = 1000, 2000, 15, 5000
-- Compiled forms exactly as tools/android/tes4_script.py writes them.
local chunks = {
    frag = {
        [1] = function(rt)
            local C = rt.C
            return {
                [1] = function(S, v) C.setstage(Q2, 10) end,
                [2] = function(S, v) C.addtopic(TOPIC); C.additem(20, GOLD, 100) end,
            }
        end,
    },
    script = {
        [1] = function(rt)
            local C, N = rt.C, rt.N
            return {
                [77] = {
                    vars = { { 'count', 'short' } },
                    blocks = {
                        gamemode = function(S, v)
                            v.count = rt.trunc(v.count + 1.9)
                            if N(C.getincell(20, 7777)) == 1 then C.setstage(Q1, 30) end
                        end,
                    },
                },
            }
        end,
    },
}
local data = {
    quests = {
        [Q1] = { id = 'QOne', name = 'One', flags = 1, priority = 50, script = 77, stages = {
            [10] = { { flags = 0, log = 'Ten.', result = 1 } },
            [20] = { { flags = 0, log = 'Never shown.', cond = { { 58, 0, 99.0, Q1, 0 } } },
                     { flags = 1, log = 'Twenty, done.', result = 2 } },
        } },
        [Q2] = { id = 'QTwo', name = 'Two', flags = 0, priority = 40, stages = { [10] = { { flags = 0, log = 'Two ten.' } } } },
    },
    index = {
        fragmentsPerChunk = 128, scriptChunk = { [77] = 1 }, globals = { [900] = 5.0 }, cells = { [9] = { ['3,-4'] = 7777 } }, areas = { [8888] = { world = 9 }, [8889] = { world = 10 }, [8890] = { world = 9, cells = { ['3,-4'] = true } },
            [8891] = { world = 9, cells = { ['0,0'] = true } } },
        functions = {
            [58] = { 'getstage', false, 'Quest' }, [14] = { 'getactorvalue', true, 'ActorValue' },
            [72] = { 'getisid', true, 'ObjectID' }, [77] = { 'getrandompercent', false },
            [47] = { 'getitemcount', true, 'ObjectID' }, [71] = { 'getinfaction', true, 'Faction' },
        },
    },
    actors = { [50] = { race = 3, female = true, level = 4, factions = { { 600, 2 } } }, [7] = { race = 1, level = 1 } },
    load = function(kind, number) return chunks[kind][number] end,
}

local rt = M.new(host, data)

-- quests flagged "start game enabled" run from a new game; others do not
rt.newGame()
check(rt.qstate(Q1).running and not rt.qstate(Q2).running, 'new game starts flagged quests')

-- SetStage records journal text, runs the stage result and chains into other quests
rt.C.setstage(Q1, 10)
check(rt.C.getstage(Q1) == 10 and rt.C.getstagedone(Q1, 10) == 1 and rt.C.getstagedone(Q1, 20) == 0, 'stage bookkeeping')
check(rt.C.getstage(Q2) == 10, 'a stage result may set another quest stage')
check(#rt.qstate(Q1).journal == 1 and rt.qstate(Q1).journal[1].text == 'Ten.', 'journal entry added')
check(rt.qstate(Q2).journal[1].text == 'Two ten.', 'chained journal entry added')

-- entries with conditions: the failing one is skipped; the flag-1 entry completes the quest
rt.C.setstage(Q1, 20)
check(#rt.qstate(Q1).journal == 2 and rt.qstate(Q1).journal[2].text == 'Twenty, done.', 'conditional entry skipped')
check(rt.qstate(Q1).completed and not rt.qstate(Q1).running, 'completion flag')
check(rt.C.getquestcompleted(Q1) == 1 and rt.C.getquestrunning(Q1) == 0, 'completion commands')
check(host.items == nil and items[GOLD] == 100 and rt.state.topics[TOPIC], 'result: AddItem and AddTopic')

-- quest scripts: GameMode block, short truncation, quest variables, GetInCell via the cell grid
rt.startQuest(Q1)
rt.updateQuests()
check(rt.qget(Q1, 'count') == 1, 'quest variable truncated to short and readable')
check(rt.C.getstage(Q1) == 30, 'GetInCell compares the exterior grid with the CELL')
check(rt.C.getincell(20, 8888) == 1 and rt.C.getincell(20, 8889) == 0, 'a placeholder CELL means being in its worldspace')
check(rt.C.getincell(20, 8890) == 1 and rt.C.getincell(20, 8891) == 0, 'a placeholder CELL may cover only some exterior cells')
rt.qset(Q1, 'count', 5)
check(rt.qget(Q1, 'count') == 5 and rt.C.getquestvariable(Q1, 'count') == 5, 'qset/qget')

-- conditions: AND of groups, OR within a group, operators, global values, converted parameters
local ctx = { subject = 50 }
check(rt.check(nil, ctx) and rt.check({}, ctx), 'no conditions pass')
check(rt.check({ { 72, 0, 1.0, 50, 0 } }, ctx), 'GetIsID == 1')
check(not rt.check({ { 72, 0, 1.0, 51, 0 } }, ctx), 'GetIsID for someone else')
check(rt.check({ { 72, 1, 1.0, 51, 0 }, { 72, 0, 1.0, 50, 0 } }, ctx), 'OR group: first fails, second passes')
check(not rt.check({ { 72, 1, 1.0, 51, 0 }, { 72, 0, 1.0, 52, 0 }, { 72, 0, 1.0, 50, 0 } }, ctx), 'OR group fails, AND stops')
check(not rt.check({ { 72, 1, 1.0, 51, 0 }, { 72, 1, 1.0, 52, 0 } }, ctx), 'a group left open by a trailing OR flag decides alone')
check(rt.check({ { 72, 1, 1.0, 51, 0 }, { 72, 1, 1.0, 50, 0 } }, ctx), 'open trailing group passes when a member passes')
check(rt.check({ { 71, 0, 1.0, 600, 0 } }, ctx), 'GetInFaction from the record')
check(not rt.check({ { 71, 0, 1.0, 601, 0 } }, ctx), 'GetInFaction not a member')
check(rt.check({ { 77, 0x60, 50.0, 0, 0 } }, ctx), 'GetRandomPercent >= 50 with the host random')
check(rt.check({ { 58, 0x40, 5.0, Q1, 0 } }, ctx), 'GetStage > 5')
check(not rt.check({ { 58, 0x80, 5.0, Q1, 0 } }, ctx), 'GetStage < 5 fails')
check(rt.check({ { 58, 0x20, 0.0, Q1, 0 } }, ctx), 'GetStage != 0')
check(rt.check({ { 58, 0x04 + 0x60, 900, Q1, 0 } }, ctx), 'comparison against a global (5.0) with GetStage 30')
items[GOLD] = 42
check(rt.check({ { 47, 0x60, 40.0, GOLD, 0 } }, ctx), 'GetItemCount')
rt.C.setfactionrank(50, 700, 3)
check(rt.C.getinfaction(50, 700) == 1 and rt.C.getfactionrank(50, 700) == 3 and rt.C.getfactionrank(50, 701) == -1, 'faction ranks')
rt.C.moddisposition(50, 20, 15)
check(rt.C.getdisposition(50, 20) == 65, 'disposition modifier')

-- messages
rt.C.messagebox('Gold: %g of %.1f %s &sUActnForward;', 7, 2.5, 'x')
check(notes[#notes] == 'Gold: 7 of 2.5 x ?', 'message formatting: ' .. tostring(notes[#notes]))

-- persistence round trip
local saved = rt.save()
local again = M.new(host, data)
again.load(saved)
check(again.C.getstage(Q1) == 30 and again.state.topics[TOPIC] and again.qget(Q1, 'count') == 5, 'save/load')

-- unknown commands are logged once and return 0
check(rt.C.frobnicate() == 0 and rt.C.frobnicate() == 0, 'unknown command returns 0')
local count = 0
for _, line in ipairs(log) do if line:find('frobnicate') then count = count + 1 end end
check(count == 1, 'unknown command logged once')
rt.C.evaluatepackage(20)
check(rt.stubbed.evaluatepackage == 1, 'stubs are counted')
print(string.format('TES4 script runtime fixtures passed: %d checks', checks))
