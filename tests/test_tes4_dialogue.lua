-- SPDX-License-Identifier: GPL-3.0-only
-- Fixtures for TES4 dialogue selection (synthetic topics, no game data).
local root = arg[1]
package.preload['scripts.openoblivion_tes4_commands'] = function()
    return dofile(root .. '/tools/android/overlay/scripts/openoblivion_tes4_commands.lua')
end
local Script = dofile(root .. '/tools/android/overlay/scripts/openoblivion_tes4_script.lua')
local Dialogue = dofile(root .. '/tools/android/overlay/scripts/openoblivion_tes4_dialogue.lua')
local checks = 0
local function check(ok, message) checks = checks + 1; if not ok then error(message, 2) end end

local random = 0
local host = {
    log = function() end, notify = function() end, messageBox = function() end, fire = function() end,
    random = function() return random end, hour = function() return 12 end,
    itemCount = function() return 0 end, addItem = function() end, removeItem = function() end,
}
local GREETING, RUMORS, JAUFFRE, SECRET, CHOICE = 10, 11, 12, 13, 14
local NPC_A, NPC_B, QUEST = 100, 101, 500
local ran = {}
local chunks = {
    frag = { [1] = function(rt) return { [1] = function(S, v) table.insert(ran, S.ref); rt.C.setstage(QUEST, 20) end } end },
    dial = {
        [1] = function()
            return {
                { dial = GREETING, from = 0, infos = {
                    { id = 1, flags = 0, speakers = { NPC_A }, r = { { text = 'Hello, traveller.', emotion = 0, n = 1 } } },
                    { id = 2, flags = 4, r = { { text = 'Hello, stranger. (first time)', emotion = 0, n = 1 } },
                      cond = { { 58, 0, 0.0, QUEST, 0 } } },
                    { id = 3, flags = 0, r = { { text = 'Hello.', emotion = 0, n = 1 } } },
                } },
                { dial = RUMORS, from = 0, infos = {
                    { id = 4, flags = 2, r = { { text = 'Rumor one.', n = 1 } } },
                    { id = 5, flags = 2, r = { { text = 'Rumor two.', n = 1 } } },
                    { id = 6, flags = 1, r = { { text = 'Never reached.', n = 1 } } },
                } },
                { dial = JAUFFRE, from = 0, infos = {
                    { id = 7, flags = 1, speakers = { NPC_B }, r = { { text = 'I am Jauffre.', n = 1 } },
                      add = { SECRET }, result = 1, choices = { CHOICE } },
                    { id = 8, flags = 0, r = { { text = 'Never heard of him.', n = 1 } } },
                } },
                { dial = SECRET, from = 0, infos = { { id = 9, flags = 0, r = { { text = 'A secret.', n = 1 } } } } },
                { dial = CHOICE, from = 0, infos = { { id = 10, flags = 0, r = { { text = 'You chose.', n = 1 } } } } },
            }
        end,
    },
}
local data = {
    quests = { [QUEST] = { id = 'Q', name = 'Q', flags = 0, priority = 1, stages = { [20] = { { flags = 0, log = 'Twenty.' } } } } },
    index = {
        fragmentsPerChunk = 128, scriptChunk = {}, globals = {}, cells = {}, greeting = GREETING,
        functions = { [58] = { 'getstage', false, 'Quest' } },
        topics = {
            [GREETING] = { id = 'GREETING', name = 'GREETING', type = 0, chunks = { 1 } },
            [RUMORS] = { id = 'Rumors', name = 'Rumors', type = 0, chunks = { 1 } },
            [JAUFFRE] = { id = 'JauffreTopic', name = 'Jauffre', type = 0, chunks = { 1 } },
            [SECRET] = { id = 'SecretTopic', name = 'A secret', type = 0, chunks = { 1 }, learned = true },
            [CHOICE] = { id = 'Choice1', name = 'Say yes', type = 0, chunks = { 1 }, choice = true },
        },
        speakerTopics = { [NPC_B] = { JAUFFRE } },
        genericTopics = { GREETING, RUMORS, JAUFFRE, SECRET, CHOICE },
    },
    load = function(kind, number) return chunks[kind][number] end,
}
local rt = Script.new(host, data)
local d = Dialogue.new(rt, data)

-- greeting: speaker-bound response first; say-once generic response with a condition; plain fallback
local s = d.begin(NPC_A)
check(s.lines[1].text == 'Hello, traveller.', 'bound greeting wins for its NPC')
s = d.begin(NPC_B)
check(s.lines[1].text == 'Hello, stranger. (first time)', 'conditional say-once greeting: ' .. s.lines[1].text)
check(rt.state.said[2], 'say-once remembered')
s = d.begin(NPC_B)
check(s.lines[1].text == 'Hello.', 'say-once response is skipped afterwards')

-- topics: Rumors is generic, Jauffre is listed for everyone (generic response), the learned topic is hidden
local names = {}
for _, t in ipairs(s.topics) do names[t.name] = true end
check(names.Rumors and names.Jauffre and not names['A secret'] and not names.GREETING and not names['Say yes'],
    'topic list: generic topics listed, learned/choice/greeting hidden')
check(s.topics[1].name == 'Jauffre' and s.topics[2].name == 'Rumors', 'topics sorted by name')

-- random responses: chosen among the passing random ones
random = 0
s = d.choose(d.begin(NPC_A), RUMORS)
check(s.lines[1].text == 'Rumor one.', 'random pick 0')
random = 0.99
s = d.choose(d.begin(NPC_A), RUMORS)
check(s.lines[1].text == 'Rumor two.', 'random pick 1')

-- a speaker-bound response, its goodbye flag, add-topic, result script and choices
s = d.begin(NPC_B)
s = d.choose(s, JAUFFRE)
check(s.lines[1].text == 'I am Jauffre.' and s.ended, 'bound topic response and goodbye flag')
check(rt.state.topics[SECRET], 'response added a topic')
check(#ran == 1 and ran[1] == NPC_B and rt.C.getstage(QUEST) == 20, 'result script ran with the speaker as its reference')
check(#s.choices == 1 and s.choices[1].name == 'Say yes', 'choices from the response')
local after = {}
for _, t in ipairs(s.topics) do after[t.name] = true end
check(after['A secret'], 'learned topic is listed once learned')
s = d.choose(s, CHOICE)
check(s.lines[1].text == 'You chose.', 'choice answered')

-- the other NPC gets the generic answer for the same topic
s = d.choose(d.begin(NPC_A), JAUFFRE)
check(s.lines[1].text == 'Never heard of him.' and not s.ended, 'generic response for an NPC the topic is not bound to')
print(string.format('TES4 dialogue fixtures passed: %d checks', checks))
