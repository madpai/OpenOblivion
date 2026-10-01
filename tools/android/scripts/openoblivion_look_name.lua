-- SPDX-License-Identifier: GPL-3.0-only
-- Top-center name of whatever the center look ray would activate.
-- Does not move the player, change collision, or activate the target.
local M = {}

-- Oblivion.esm's GMST group (file offset 764, 20-byte TES4 group header,
-- 382 records, zlib when flag 0x00040000) has no EDID iMaxActivateDist.
-- The phone content list loads template.omwgame first. That TES3 GMST
-- NAME is iMaxActivateDist and INTV is 0x000000C0 (192), at file offset
-- 20776. core.getGMST reads the same ESM::GameSetting store as
-- World::getMaxActivationDistance (worldimp.cpp). Store::find throws if
-- the record is missing; this measured 192 is only the nil fallback.
-- OpenCS lists the same 192 at defaultgmsts.cpp:1955 and is not the game.
M.fallbackActivationDistance = 192

-- World::feetToGameUnits uses std::ceil(Constants::UnitsPerFoot).
-- UnitsPerFoot is 21.33333333f in components/misc/constants.hpp.
M.unitsPerFoot = math.ceil(21.33333333)

-- Only a real record name is shown. Falling back to recordId paints a form id
-- on TES4 statics (they have no tooltip) and on TES4 actors, whose display
-- name is not bound in this Lua API. The engine tooltip still draws those
-- actor names; see the Bandit label in docs/media/android-vilverin-stairs.jpg.
function M.displayName(name, _recordId)
    if type(name) ~= 'string' then return nil end
    local trimmed = name:match('^%s*(.-)%s*$')
    if trimmed == nil or trimmed == '' then return nil end
    return trimmed
end

-- hitDistance is from the camera, or nil on a miss. cameraDistance is the
-- third-person pullback added to the ray and subtracted from the hit, matching
-- World::getFocusObject. Hits with focus distance greater than
-- iMaxActivateDist are rejected unless telekinesis applies.
function M.plateText(name, recordId, hitDistance, activationDistance, cameraDistance, telekinesisUnits, allowsTelekinesis)
    if type(hitDistance) ~= 'number' or type(activationDistance) ~= 'number' then return nil end
    cameraDistance = cameraDistance or 0
    local extra = 0
    if allowsTelekinesis and type(telekinesisUnits) == 'number' and telekinesisUnits > 0 then
        extra = telekinesisUnits
    end
    if hitDistance - cameraDistance > activationDistance + extra then return nil end
    return M.displayName(name, recordId)
end

local cameraOk, camera = pcall(require, 'openmw.camera')
if not cameraOk then
    if type(camera) ~= 'string' or not camera:find("module 'openmw.camera' not found", 1, true) then
        error(camera)
    end
    return M
end

local core = require('openmw.core')
local nearby = require('openmw.nearby')
local self = require('openmw.self')
local types = require('openmw.types')
local ui = require('openmw.ui')
local util = require('openmw.util')

local LAYER = 'OpenOblivionLookName'
local plate
local labelProps
local rootProps
local crosshair = false
local shownKey = nil
local activationCache

local function oneLine(value)
    local text = tostring(value or '')
    text = text:gsub('[%c]', ' ')
    return text
end

local function activationDistance()
    if activationCache ~= nil then return activationCache end
    local value = core.getGMST('iMaxActivateDist')
    if type(value) ~= 'number' then value = M.fallbackActivationDistance end
    activationCache = value
    return value
end

local function telekinesisUnits()
    local ok, effect = pcall(function()
        return types.Actor.activeEffects(self):getEffect(core.magic.EFFECT_TYPE.Telekinesis)
    end)
    if not ok or effect == nil or type(effect.magnitude) ~= 'number' or effect.magnitude <= 0 then
        return 0
    end
    return effect.magnitude * M.unitsPerFoot
end

-- Morrowind actors and unlocked trap-free teleport doors refuse telekinesis
-- (Actor::allowTelekinesis, Door::allowTelekinesis). ESM4 classes keep the
-- default, which allows it. This build has no Lua type for ESM4 actors.
local function allowsTelekinesis(object)
    if types.NPC.objectIsInstance(object) or types.Creature.objectIsInstance(object) then
        return false
    end
    if types.Door.objectIsInstance(object) then
        local trap = types.Lockable.getTrapSpell(object)
        if types.Door.isTeleport(object) and not types.Lockable.isLocked(object) and not trap then
            return false
        end
    end
    return true
end

local function readName(object)
    local recordId = object.recordId
    local name
    local recordType = object.type
    if recordType and recordType.record then
        local ok, record = pcall(recordType.record, object)
        if ok and record ~= nil and type(record.name) == 'string' then name = record.name end
    end
    return name, recordId
end

local function announce(text, recordId, key)
    if key == shownKey then return end
    local previous = shownKey
    shownKey = key
    if text == nil then
        if previous ~= nil then print('OPENOBLIVION_LOOK_NAME cleared') end
        return
    end
    print('OPENOBLIVION_LOOK_NAME name=' .. oneLine(text) .. ' id=' .. oneLine(recordId))
end

-- HUD in openmw_layers.xml has pick=true, so a widget there can take touches.
-- This layer is created with interactive=false (Layer::insert setPick).
local function ensurePlate()
    if ui.layers.indexOf(LAYER) == nil then
        ui.layers.insertAfter('HUD', LAYER, { interactive = false })
        return nil
    end
    if plate then return plate end
    labelProps = {
        text = '',
        textSize = 24,
        textColor = util.color.rgb(1, 1, 1),
        textAlignH = ui.ALIGNMENT.Center,
        textAlignV = ui.ALIGNMENT.Center,
        textShadow = true,
        textShadowColor = util.color.rgb(0, 0, 0),
        autoSize = false,
        wordWrap = true,
        multiline = true,
        relativeSize = util.vector2(1, 1),
    }
    rootProps = {
        position = util.vector2(0, 4),
        relativePosition = util.vector2(0.5, 0),
        anchor = util.vector2(0.5, 0),
        size = util.vector2(400, 56),
        visible = false,
    }
    plate = ui.create {
        layer = LAYER,
        type = ui.TYPE.Widget,
        props = rootProps,
        content = ui.content {
            {
                type = ui.TYPE.Image,
                props = {
                    resource = ui.texture { path = 'white' },
                    color = util.color.rgb(0, 0, 0),
                    alpha = 0.72,
                    relativeSize = util.vector2(1, 1),
                },
            },
            { name = 'label', type = ui.TYPE.Text, props = labelProps },
        },
    }
    return plate
end

local function showPlate(text)
    local element = ensurePlate()
    if not labelProps then return end
    labelProps.text = text or ''
    rootProps.visible = text ~= nil
    if element then element:update() end
end

-- castRenderingRay is legal in player onFrame: synchronizedUpdate sets
-- mProcessingInputEvents around that handler (luamanagerimp.cpp). It throws
-- from onUpdate. The ray matches World::getFocusObject's center viewport ray.
local function query()
    local activation = activationDistance()
    local cameraDistance = camera.getThirdPersonDistance()
    local extra = telekinesisUnits()
    local origin = camera.getPosition()
    local direction = camera.viewportToWorldVector(util.vector2(0.5, 0.5))
    local dirLength = direction:length()
    if dirLength <= 1e-4 then return nil, nil, nil end
    local reach = activation + cameraDistance + extra
    local hit = nearby.castRenderingRay(origin, origin + direction * (reach / dirLength), { ignore = self })
    if not hit.hit or not hit.hitObject or not hit.hitPos then return nil, nil, nil end
    local object = hit.hitObject
    if object.id == self.id then return nil, nil, nil end
    if object.isValid and not object:isValid() then return nil, nil, nil end
    local name, recordId = readName(object)
    local hitDistance = (hit.hitPos - origin):length()
    local text = M.plateText(name, recordId, hitDistance, activation, cameraDistance, extra,
        allowsTelekinesis(object))
    local key = text and (tostring(object.id) .. '\0' .. text) or nil
    return text, recordId, key
end

return {
    engineHandlers = {
        onFrame = function()
            if not crosshair then
                camera.showCrosshair(true)
                crosshair = true
            end
            if not self.cell then
                showPlate(nil)
                announce(nil, nil, nil)
                return
            end
            local text, recordId, key = query()
            showPlate(text)
            announce(text, recordId, key)
        end,
    },
}
