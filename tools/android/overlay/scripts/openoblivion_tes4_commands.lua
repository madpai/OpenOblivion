-- SPDX-License-Identifier: GPL-3.0-only
-- Script commands for the TES4 script runtime. Each `C.name(target, args...)` mirrors one
-- command of the original (the compiler passes the reference first for commands that need
-- one). Behaviour that needs the world goes through `host`; see openoblivion_tes4_script.lua.
-- Only commands with an effect we can state are here; the rest are logged once by the runtime.
return function(rt, host, data, state, PLAYER, AV_NAMES)
    local C, num, trunc = rt.C, rt.N, rt.trunc
    local PLAYER_BASE = 0x7
    local GOLD = 0xF

    local function actor(base) return (data.actors and data.actors[base]) or {} end
    local function baseOf(ref)
        if ref == PLAYER then return PLAYER_BASE end
        return host.baseOf and host.baseOf(ref) or ref
    end
    local function rankTable(ref)
        local ranks = state.ranks[ref]
        if not ranks then ranks = {}; state.ranks[ref] = ranks end
        return ranks
    end

    -- -- messages -------------------------------------------------------------
    -- "%g", "%.0f", "%d", "%s" take the extra arguments in order. "&sUActn...;" names a control.
    local function format(text, ...)
        local arguments, index = { ... }, 0
        text = text:gsub('&[%w_]+;', '?')
        text = text:gsub('%%(%.?%d*)([gfds])', function(precision, kind)
            index = index + 1
            local value = arguments[index]
            if value == nil then return '' end
            if kind == 's' then return tostring(value) end
            if kind == 'd' then return string.format('%d', trunc(value)) end
            if kind == 'f' then return string.format('%' .. precision .. 'f', value) end
            return string.format('%g', value)
        end)
        return text
    end
    rt.format = format
    function C.message(text, ...) host.notify(format(text, ...)); return 0 end
    function C.messagebox(text, ...) host.messageBox(format(text, ...)); return 0 end
    C.messageex, C.messageboxex = C.message, C.messagebox

    -- -- quests ---------------------------------------------------------------
    function C.setstage(quest, stage) rt.setStage(quest, trunc(stage)); return 0 end
    function C.getstage(quest) return rt.qstate(quest).stage end
    function C.getstagedone(quest, stage) return rt.qstate(quest).done[trunc(stage)] and 1 or 0 end
    function C.startquest(quest) rt.startQuest(quest); return 0 end
    function C.stopquest(quest) rt.qstate(quest).running = false; return 0 end
    function C.getquestrunning(quest) return rt.qstate(quest).running and 1 or 0 end
    function C.getquestcompleted(quest) return rt.qstate(quest).completed and 1 or 0 end
    function C.getquestvariable(quest, name) return rt.qget(quest, name) end
    function C.getscriptvariable(ref, name) return rt.rget(ref, name) end
    function C.setquestobject() return 0 end
    function C.showmap() return 0 end
    function C.addtopic(topic)
        if not state.topics[topic] then
            state.topics[topic] = true
            host.fire('topic', { topic = topic })
        end
        return 0
    end
    function C.getglobalvalue(global) return rt.gget(global) end

    -- -- time and chance ------------------------------------------------------
    function C.getrandompercent() return math.floor(host.random() * 100) end
    function C.getcurrenttime() return host.hour() end
    function C.getsecondspassed() return host.dt and host.dt() or 0 end

    -- -- actors -----------------------------------------------------------------
    function C.getisid(ref, base) return baseOf(ref) == base and 1 or 0 end
    function C.getlevel(ref)
        if host.level then return host.level(ref) end
        return actor(baseOf(ref)).level or 1
    end
    function C.getisrace(ref, race) return actor(baseOf(ref)).race == race and 1 or 0 end
    function C.getpcisrace(race) return actor(PLAYER_BASE).race == race and 1 or 0 end
    function C.getisclass(ref, class) return actor(baseOf(ref)).class == class and 1 or 0 end
    function C.getissex(ref, sex)
        local female = actor(baseOf(ref)).female and 1 or 0
        return ((sex == 'female' or sex == 1) and 1 or 0) == female and 1 or 0
    end
    function C.getpcissex(sex) return C.getissex(PLAYER, sex) end
    function C.getinfaction(ref, faction)
        if rankTable(ref)[faction] then return 1 end
        for _, membership in ipairs(actor(baseOf(ref)).factions or {}) do
            if membership[1] == faction then return 1 end
        end
        return 0
    end
    function C.getfactionrank(ref, faction)
        local rank = rankTable(ref)[faction]
        if rank then return rank end
        for _, membership in ipairs(actor(baseOf(ref)).factions or {}) do
            if membership[1] == faction then return membership[2] end
        end
        return -1
    end
    function C.setfactionrank(ref, faction, rank) rankTable(ref)[faction] = trunc(rank); return 0 end
    function C.modfactionrank(ref, faction, amount)
        rankTable(ref)[faction] = trunc(C.getfactionrank(ref, faction) + amount)
        return 0
    end
    function C.getdisposition(ref, other)
        return 50 + (state.disposition[ref] or 0)
    end
    function C.moddisposition(ref, other, amount)
        state.disposition[ref] = (state.disposition[ref] or 0) + trunc(amount)
        return 0
    end
    function C.gettalkedtopc(ref) return state.talked and state.talked[ref] and 1 or 0 end
    function C.getdead(ref) return host.isDead and host.isDead(ref) and 1 or 0 end
    function C.getdeadcount(base) return host.deadCount and host.deadCount(base) or 0 end
    function C.getdisabled(ref) return host.isDisabled and host.isDisabled(ref) and 1 or 0 end
    function C.getactorvalue(ref, name)
        if host.actorValue then return host.actorValue(ref, name) end
        return 0
    end
    function C.isguard(ref) return actor(baseOf(ref)).guard and 1 or 0 end
    function C.getplayercontrolsdisabled() return 0 end
    function C.getisplayablerace() return 1 end
    function C.getpcexpelled() return 0 end
    function C.getcrimegold() return 0 end
    function C.getinsamecell() return 0 end

    -- -- places ------------------------------------------------------------------
    -- `host.cell(ref)` -> {world = formId, x = n, y = n} for an exterior cell, {interior = formId} otherwise.
    -- Placeholder CELLs ("dummy cell for GetInCell") stand for a worldspace or a patch of exterior
    -- cells (see tes4_gamedata.cells); the original's rule for them is not measured.
    function C.getincell(ref, cell)
        local where = host.cell and host.cell(ref)
        if not where then return 0 end
        if where.interior then return where.interior == cell and 1 or 0 end
        local area = data.index.areas and data.index.areas[cell]
        if area then
            if area.world ~= where.world then return 0 end
            if area.cells and not area.cells[where.x .. ',' .. where.y] then return 0 end
            return 1
        end
        local grid = data.index.cells[where.world or 0]
        return grid and grid[where.x .. ',' .. where.y] == cell and 1 or 0
    end
    function C.isininterior(ref)
        local where = host.cell and host.cell(ref)
        return where and where.interior and 1 or 0
    end
    function C.getdistance(ref, other) return host.distance and host.distance(ref, other) or 0 end

    -- -- items ----------------------------------------------------------------------
    function C.additem(ref, base, count) host.addItem(ref or PLAYER, base, trunc(count)); return 0 end
    function C.removeitem(ref, base, count) host.removeItem(ref or PLAYER, base, trunc(count)); return 0 end
    function C.getitemcount(ref, base) return host.itemCount(ref or PLAYER, base) end
    function C.getgold(ref) return host.itemCount(ref or PLAYER, GOLD) end

    -- -- references -------------------------------------------------------------------
    function C.enable(ref) if host.setEnabled then host.setEnabled(ref, true) end; return 0 end
    function C.disable(ref) if host.setEnabled then host.setEnabled(ref, false) end; return 0 end

    -- Commands that only change presentation or AI we do not model yet. Accepting them
    -- silently keeps quest and dialogue flow intact, but they are counted in rt.stubbed so a
    -- build can list what was reached without an effect. They are not claimed as implemented.
    rt.stubbed = {}
    for _, name in ipairs({ 'evaluatepackage', 'setessential', 'setalert', 'modpcfame', 'modpcinfamy', 'setownership',
        'setdestroyed', 'addscriptpackage', 'removescriptpackage', 'modfactionreaction', 'pickidle', 'look', 'lock',
        'unlock', 'setav', 'modav', 'forceav', 'addspell', 'removespell', 'playsound', 'say', 'sayto', 'playgroup',
        'reset3dstate', 'enablelinkedpathpoints', 'disablelinkedpathpoints', 'startconversation' }) do
        if not rawget(C, name) then
            C[name] = function()
                rt.stubbed[name] = (rt.stubbed[name] or 0) + 1
                return 0
            end
        end
    end
end
