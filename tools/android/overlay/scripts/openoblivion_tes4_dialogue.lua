-- SPDX-License-Identifier: GPL-3.0-only
-- TES4 dialogue: which topics an NPC offers, which response a topic gives, and what saying it does.
-- Pure Lua over the generated dialogue data (tools/android/tes4_gamedata.py); the script runtime
-- (openoblivion_tes4_script.lua) evaluates conditions and runs result scripts.
--
-- Rules implemented, from the Construction Set's documented behaviour (not yet compared with the
-- original executable):
--   * responses of a topic are tried in file order; the first whose conditions pass is used;
--   * a response with the "random" flag is chosen at random among the passing random ones;
--   * "say once" responses are skipped after they have been said;
--   * a response bound to NPCs by GetIsID is only considered for those NPCs;
--   * topics the game hands out with AddTopic (or a response's add-topic list) are listed once
--     learned, every other topic of type "topic" is listed when a response passes;
--   * a response's add-topic list and result script run when it is said.
local D = {}

local FLAG_GOODBYE, FLAG_RANDOM, FLAG_SAY_ONCE = 1, 2, 4
local function flag(value, mask) return math.floor((value or 0) / mask) % 2 == 1 end
local TOPIC_TYPE = 0

function D.new(rt, data)
    local d = { rt = rt }
    local topicCache = {}

    -- All responses of a topic in file order, from its slices.
    local function infosOf(dial)
        local infos = topicCache[dial]
        if infos then return infos end
        infos = {}
        local entry = data.index.topics[dial]
        if entry then
            local slices = {}
            for _, number in ipairs(entry.chunks) do
                for _, slice in ipairs(data.load('dial', number)(rt)) do
                    if slice.dial == dial then table.insert(slices, slice) end
                end
            end
            table.sort(slices, function(a, b) return a.from < b.from end)
            for _, slice in ipairs(slices) do
                for _, info in ipairs(slice.infos) do table.insert(infos, info) end
            end
        end
        topicCache[dial] = infos
        return infos
    end
    d.infosOf = infosOf

    local function boundTo(info, npc)
        if not info.speakers then return true end
        for _, id in ipairs(info.speakers) do
            if id == npc then return true end
        end
        return false
    end

    -- The response a topic gives `npc` now, or nil.
    function d.pick(dial, npc)
        local ctx = { subject = npc, target = 0x14 }
        local passing = {}
        for _, info in ipairs(infosOf(dial)) do
            if boundTo(info, npc) and not (flag(info.flags, FLAG_SAY_ONCE) and rt.state.said[info.id])
                and rt.check(info.cond, ctx) then
                if not flag(info.flags, FLAG_RANDOM) then
                    if #passing == 0 then return info end
                else
                    table.insert(passing, info)
                end
            end
        end
        if #passing == 0 then return nil end
        return passing[math.floor(rt.host.random() * #passing) % #passing + 1]
    end

    local function isListed(dial, entry)
        if entry.type ~= TOPIC_TYPE or entry.name == '' or entry.id == 'GREETING' or entry.choice then return false end
        if entry.learned and not rt.state.topics[dial] then return false end
        return true
    end

    -- Topics `npc` offers, in listing order: {{id = formId, name = text}}.
    function d.topics(npc)
        local out, seen = {}, {}
        local function consider(dial)
            if seen[dial] then return end
            seen[dial] = true
            local entry = data.index.topics[dial]
            if entry and isListed(dial, entry) and d.pick(dial, npc) then
                table.insert(out, { id = dial, name = entry.name })
            end
        end
        for _, dial in ipairs(data.index.speakerTopics[npc] or {}) do consider(dial) end
        for _, dial in ipairs(data.index.genericTopics) do consider(dial) end
        table.sort(out, function(a, b) return a.name:lower() < b.name:lower() end)
        return out
    end

    -- Say `info`: mark it, learn its topics, run its result script. Returns the spoken lines.
    function d.say(info, npc)
        if flag(info.flags, FLAG_SAY_ONCE) then rt.state.said[info.id] = true end
        for _, dial in ipairs(info.add or {}) do rt.C.addtopic(dial) end
        rt.state.talked = rt.state.talked or {}
        rt.state.talked[npc] = true
        local lines = {}
        for _, response in ipairs(info.r or {}) do
            table.insert(lines, { text = response.text or '', emotion = response.emotion, number = response.n })
        end
        if info.result then
            local fn = rt.fragment(info.result)
            if fn then
                local ok, err = pcall(fn, { ref = npc }, {})
                if not ok then rt.host.log('TES4 dialogue result error: ' .. tostring(err)) end
            end
        end
        return lines
    end

    local function choicesOf(info)
        local out = {}
        for _, dial in ipairs(info.choices or {}) do
            local entry = data.index.topics[dial]
            if entry then table.insert(out, { id = dial, name = entry.name }) end
        end
        return out
    end

    -- Start talking to an NPC (by base record). Returns the first lines and the topic list.
    function d.begin(npc)
        local session = { npc = npc, lines = {}, topics = {}, choices = {}, ended = false }
        local greeting = data.index.greeting and d.pick(data.index.greeting, npc)
        if greeting then
            session.lines = d.say(greeting, npc)
            session.choices = choicesOf(greeting)
            session.ended = flag(greeting.flags, FLAG_GOODBYE)
        end
        session.topics = d.topics(npc)
        return session
    end

    -- Choose a topic or a choice. Returns the updated session.
    function d.choose(session, dial)
        local info = d.pick(dial, session.npc)
        session.lines, session.choices = {}, {}
        if info then
            session.lines = d.say(info, session.npc)
            session.choices = choicesOf(info)
            session.ended = flag(info.flags, FLAG_GOODBYE)
        end
        session.topics = d.topics(session.npc)
        return session
    end

    return d
end

return D
