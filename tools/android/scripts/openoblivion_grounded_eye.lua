-- SPDX-License-Identifier: GPL-3.0-only
-- Original bounded eye-height filter. It never changes the actor or controls.
local M = {}

function M.new()
    local previous, height
    local filter = {}

    function filter.reset()
        previous, height = nil, nil
    end

    function filter.update(p, cell, grounded, jumping, swimming, dt)
        local reset = not previous or previous.cell ~= cell
            or not grounded or not previous.grounded or jumping or swimming
            or dt <= 0 or dt > 0.25
        if previous then
            reset = reset or math.abs(p.z - previous.z) > 62
                or (p.x - previous.x)^2 + (p.y - previous.y)^2 > 128^2
        end
        if reset then
            height = p.z
        else
            -- 100 ms exponential response is independent of frame cadence.
            -- Clamp lag so a long slope cannot detach the view from the body.
            height = p.z + (height - p.z) * math.exp(-dt / 0.1)
            height = math.max(p.z - 48, math.min(p.z + 48, height))
        end
        previous = {x=p.x, y=p.y, z=p.z, cell=cell, grounded=grounded}
        return height - p.z
    end

    return filter
end

return M
