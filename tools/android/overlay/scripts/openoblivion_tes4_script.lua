-- SPDX-License-Identifier: GPL-3.0-only
-- TES4 script runtime. Runs the Lua that tools/android/tes4_script.py compiles
-- from the owner's Oblivion.esm: quest stages, dialogue results, quest and
-- object scripts, and the conditions of dialogue and journal entries.
--
-- The core is plain Lua so it can be tested without the game. Everything that
-- touches the world goes through `host` (see openoblivion_tes4_game.lua):
--   host.player()              -> the player object
--   host.object(formId)        -> a placed reference, or nil when it is not loaded
--   host.notify(text)          -- HUD message
--   host.log(text)
--   host.itemCount(refId, baseId) / host.addItem(refId, baseId, n) / host.removeItem(...)
--   host.cell(refId)           -> {exterior = bool, x = n, y = n, interior = formId|nil}
--   host.hour()                -> game hour 0..24
--   host.random()              -> 0..1
--   host.fire(name, payload)   -- events for the UI (journal, topics, ...)
-- and the static game data (`data`): quests, index, actors, and a loader for chunks.
--
-- Commands the runtime does not implement are logged once and ignored; they
-- return 0 in expressions. Nothing here claims TES4 parity beyond what a test shows.
local M = {}

local PLAYER = 0x14
local AV_NAMES = {
    [0] = 'strength', 'intelligence', 'willpower', 'agility', 'speed', 'endurance', 'personality', 'luck',
    'health', 'magicka', 'fatigue', 'encumbrance', 'armorer', 'athletics', 'blade', 'block', 'blunt', 'handtohand',
    'heavyarmor', 'alchemy', 'alteration', 'conjuration', 'destruction', 'illusion', 'mysticism', 'restoration',
    'acrobatics', 'lightarmor', 'marksman', 'mercantile', 'security', 'sneak', 'speechcraft', 'aggression',
    'confidence', 'energy', 'responsibility', 'bounty', 'fame', 'infamy',
}
local FLAG_OR, FLAG_RUN_ON_TARGET, FLAG_GLOBAL = 1, 2, 4

-- LuaJIT is Lua 5.1: no bit operators.
local function flag(value, mask) return math.floor(value / mask) % 2 == 1 end
M.flag = flag

local function num(x)
    if x == nil or x == false then return 0 end
    if x == true then return 1 end
    return x
end

local function trunc(x)
    x = num(x)
    return x >= 0 and math.floor(x) or -math.floor(-x)
end

function M.new(host, data)
    local rt = { host = host, data = data, N = num, trunc = trunc }
    local state = {
        quests = {},     -- [formId] = {running, stage, done = {[n]=true}, vars = {}, journal = {{stage, text}}, completed}
        globals = {},    -- [formId] = value
        topics = {},     -- [topic formId] = true, topics the player has been given
        said = {},       -- [info formId] = true
        ranks = {},      -- [actor formId] = {[faction formId] = rank}
        refvars = {},    -- [ref formId] = {name = value}
        disposition = {},-- [actor formId] = modifier
        talked = {},     -- [actor base formId] = true once the player has spoken to them
        began = false,   -- the new-game state has been set up
    }
    rt.state = state
    local missing = {}
    local scriptCache, fragmentCache = {}, {}
    local C = {}
    rt.C = C
    setmetatable(C, { __index = function(_, name)
        return function()
            if not missing[name] then
                missing[name] = true
                host.log('TES4 command not implemented: ' .. name)
            end
            return 0
        end
    end })

    -- -- data -------------------------------------------------------------
    local function quest(formId) return data.quests[formId] end
    local function qstate(formId)
        local q = state.quests[formId]
        if not q then
            q = { running = false, stage = 0, done = {}, vars = {}, journal = {}, completed = false }
            state.quests[formId] = q
        end
        return q
    end
    rt.qstate = qstate

    local function fragment(id)
        local fn = fragmentCache[id]
        if fn == nil then
            local per = data.index.fragmentsPerChunk
            local chunk = data.load('frag', math.floor((id - 1) / per) + 1)
            for key, value in pairs(chunk(rt)) do fragmentCache[key] = value end
            fn = fragmentCache[id] or false
        end
        return fn
    end
    rt.fragment = fragment

    -- A script instance: variables plus the compiled blocks.
    function rt.instance(scriptId, ref)
        local compiled = scriptCache[scriptId]
        if compiled == nil then
            local number = data.index.scriptChunk[scriptId]
            if not number then
                scriptCache[scriptId] = false
                return nil
            end
            for key, value in pairs(data.load('script', number)(rt)) do scriptCache[key] = value end
            compiled = scriptCache[scriptId] or false
        end
        if not compiled then return nil end
        local v = {}
        for _, declaration in ipairs(compiled.vars) do v[declaration[1]] = 0 end
        return { compiled = compiled, v = v, S = { ref = ref, script = scriptId }, id = scriptId }
    end

    function rt.runBlock(instance, block)
        local fn = instance.compiled.blocks[block]
        if not fn then return false end
        local ok, err = pcall(fn, instance.S, instance.v)
        if not ok then host.log('TES4 script error in block ' .. block .. ': ' .. tostring(err)) end
        return ok
    end

    -- A quest's variables live in its script instance, created on first use.
    local questInstances = {}
    local function questInstance(formId)
        local instance = questInstances[formId]
        if instance == nil then
            local def = quest(formId)
            instance = def and def.script and rt.instance(def.script, nil) or false
            questInstances[formId] = instance
        end
        return instance
    end
    rt.questInstance = questInstance

    function rt.qget(formId, name)
        local instance = questInstance(formId)
        if instance then return num(instance.v[name]) end
        return num(qstate(formId).vars[name])
    end
    function rt.qset(formId, name, value)
        local instance = questInstance(formId)
        if instance then instance.v[name] = value else qstate(formId).vars[name] = value end
    end
    function rt.rget(refId, name)
        local vars = state.refvars[refId]
        return vars and num(vars[name]) or 0
    end
    function rt.rset(refId, name, value)
        local vars = state.refvars[refId]
        if not vars then vars = {}; state.refvars[refId] = vars end
        vars[name] = value
    end
    function rt.gget(formId)
        local value = state.globals[formId]
        if value == nil then value = data.index.globals[formId] end
        return num(value)
    end
    function rt.gset(formId, value) state.globals[formId] = value end

    -- -- conditions ---------------------------------------------------------
    local function conditionValue(c)
        if flag(c[2], FLAG_GLOBAL) then return rt.gget(c[3]) end
        return c[3]
    end
    local function compare(op, a, b)
        if op == 0x00 then return a == b
        elseif op == 0x20 then return a ~= b
        elseif op == 0x40 then return a > b
        elseif op == 0x60 then return a >= b
        elseif op == 0x80 then return a < b
        else return a <= b end
    end

    -- Evaluate a condition list: groups separated where a condition lacks the OR flag,
    -- members of a group are OR'd, groups are AND'd. `ctx.subject` is the speaker or the
    -- reference the condition runs on; `ctx.target` is the player.
    function rt.check(conds, ctx)
        if not conds or #conds == 0 then return true end
        local groupResult, open = false, false
        for _, c in ipairs(conds) do
            open = true
            local entry = data.index.functions and data.index.functions[c[1]]
            local value = 0
            if entry then
                local subject = flag(c[2], FLAG_RUN_ON_TARGET) and (ctx.target or PLAYER) or (ctx.subject or PLAYER)
                local name, parent = entry[1], entry[2]
                local p1, p2 = rt.convert(entry[3], c[4]), rt.convert(entry[4], c[5])
                local override = rt.condition[name]
                if override then
                    value = num(override(subject, p1, p2, ctx))
                elseif parent then
                    value = num(C[name](subject, p1, p2))
                else
                    value = num(C[name](p1, p2))
                end
            else
                rt.unknownCondition = rt.unknownCondition or {}
                rt.unknownCondition[c[1]] = true
            end
            -- operator bits: 0x00 ==, 0x20 ~=, 0x40 >, 0x60 >=, 0x80 <, 0xA0 <=
            if compare(c[2] - c[2] % 32, value, conditionValue(c)) then groupResult = true end
            if not flag(c[2], FLAG_OR) then
                if not groupResult then return false end
                groupResult, open = false, false
            end
        end
        -- A last condition that still carries the OR flag leaves its group open: it decides alone.
        return (not open) or groupResult
    end
    rt.condition = {}  -- condition-specific overrides: function(subject, p1, p2, ctx)

    -- Condition parameters arrive as numbers; some commands expect words.
    local AXES, SEXES = { [0] = 'x', 'y', 'z' }, { [0] = 'male', 'female' }
    function rt.convert(kind, value)
        if kind == 'ActorValue' then return AV_NAMES[value] or tostring(value) end
        if kind == 'Axis' then return AXES[value] or 'x' end
        if kind == 'Sex' then return SEXES[value] or 'male' end
        return value
    end

    -- -- quests -------------------------------------------------------------
    function rt.setStage(formId, stage)
        local def = quest(formId)
        if not def then host.log(string.format('SetStage on unknown quest %x', formId)); return end
        local q = qstate(formId)
        -- Setting a stage starts a quest that is not running (MQ02 is never started any other way).
        if not q.running and not q.completed then q.running = true end
        q.stage = stage
        q.done[stage] = true
        local entries = def.stages and def.stages[stage] or {}
        for _, entry in ipairs(entries) do
            if rt.check(entry.cond, { subject = PLAYER }) then
                if entry.log and entry.log ~= '' then
                    table.insert(q.journal, { stage = stage, text = entry.log })
                    host.fire('journal', { quest = formId, stage = stage, text = entry.log })
                end
                if flag(entry.flags, 1) then
                    q.completed = true
                    q.running = false
                    host.fire('questCompleted', { quest = formId })
                end
                if entry.result then
                    local fn = fragment(entry.result)
                    if fn then
                        local ok, err = pcall(fn, { ref = nil, quest = formId }, {})
                        if not ok then host.log('TES4 stage result error: ' .. tostring(err)) end
                    end
                end
            end
        end
    end

    function rt.startQuest(formId)
        local q = qstate(formId)
        if not q.running then
            q.running = true
            q.completed = false
        end
    end

    -- Quests flagged "start game enabled" run from the first moment.
    function rt.newGame()
        for formId, def in pairs(data.quests) do
            if flag(def.flags, 1) then rt.startQuest(formId) end
        end
    end

    -- Run the GameMode block of every running quest's script (the original does it every few seconds).
    function rt.updateQuests()
        for formId, q in pairs(state.quests) do
            if q.running then
                local instance = questInstance(formId)
                if instance then rt.runBlock(instance, 'gamemode') end
            end
        end
    end

    -- -- persistence --------------------------------------------------------
    function rt.save()
        local saved = {}
        for key, value in pairs(state) do saved[key] = value end
        local vars = {}
        for formId, instance in pairs(questInstances) do
            if instance then vars[formId] = instance.v end
        end
        saved.questVars = vars
        return saved
    end
    function rt.load(saved)
        if not saved then return end
        for key in pairs(state) do state[key] = saved[key] or state[key] end
        for formId, v in pairs(saved.questVars or {}) do
            local instance = questInstance(formId)
            if instance then
                for name, value in pairs(v) do instance.v[name] = value end
            end
        end
    end

    require('scripts.openoblivion_tes4_commands')(rt, host, data, state, PLAYER, AV_NAMES)
    return rt
end

return M
