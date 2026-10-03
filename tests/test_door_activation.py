#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Same-cell TES4 doors stay open until used again."""
import sys
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/android'))
import build_personal


class DoorActivationTest(unittest.TestCase):
    def test_five_second_stub_becomes_a_toggle(self):
        patched = build_personal.same_cell_doors_stay_open(build_personal.DOOR_FIVE_SECOND_STUB + "\nreturn {}\n")
        self.assertIn("door.enabled = not door.enabled", patched)
        self.assertIn("OPENOBLIVION_DOOR toggle", patched)
        self.assertIn("types.ESM4Door.playSequence", patched)
        self.assertIn("OPENOBLIVION_DOOR swing sequence=", patched)
        self.assertIn("'Forward'", patched)
        self.assertIn("'Backward'", patched)
        self.assertNotIn("newSimulationTimer", patched)
        self.assertNotIn("require('openmw.async')", patched)
        self.assertIn("actor:teleport", patched)
        self.assertEqual(patched, build_personal.same_cell_doors_stay_open(patched))

    def test_unknown_handler_is_rejected(self):
        with self.assertRaises(ValueError):
            build_personal.same_cell_doors_stay_open("local function ESM4DoorActivation() end\n")

    def test_actual_handler_fallback_sequence_and_teleport(self):
        lua = shutil.which('luajit') or shutil.which('lua5.1') or shutil.which('lua')
        self.assertIsNotNone(lua, 'Lua is required for the handler behavior fixture')
        setup = """
local Door = {}
local sounds, sequences, teleports = {}, {}, 0
Door.record = function() return {openSound = 'open', closeSound = 'close'} end
Door.isTeleport = function(d) return d.teleport end
Door.destCell = function() return 'OriginalCell' end
Door.destPosition = function() return {} end
Door.destRotation = function() return {} end
package.preload['openmw.types'] = function() return {ESM4Door = Door} end
package.preload['openmw.core'] = function() return {sound = {
    playSound3d = function(name) sounds[#sounds + 1] = name end}} end
package.preload['openmw.world'] = function() return {} end
package.preload['openmw_aux.util'] = function() return {} end
"""
        checks = """
local actor = {teleport = function() teleports = teleports + 1 end}
local fallback = {id = 'original-fallback', enabled = true}
assert(ESM4DoorActivation(fallback, actor) == false and not fallback.enabled)
assert(ESM4DoorActivation(fallback, actor) == false and fallback.enabled)
Door.playSequence = function(_, name) sequences[#sequences + 1] = name; return true end
local animated = {id = 'original-animated', enabled = true}
ESM4DoorActivation(animated, actor); ESM4DoorActivation(animated, actor)
assert(animated.enabled and sequences[1] == 'Open' and sequences[2] == 'Close')
assert(sounds[#sounds] == 'close')
local beforeSounds, beforeSequences = #sounds, #sequences
Door.isSequencePlaying = function(_, name) return name == 'Close' end
assert(ESM4DoorActivation(animated, actor) == false)
assert(animated.enabled and #sounds == beforeSounds and #sequences == beforeSequences)
Door.isSequencePlaying = nil
Door.playSequence = function() error('unsupported sequence') end
local broken = {id = 'original-broken', enabled = true}
ESM4DoorActivation(broken, actor); assert(not broken.enabled)
local teleport = {id = 'original-teleport', enabled = true, teleport = true}
ESM4DoorActivation(teleport, actor); assert(teleports == 1 and teleport.enabled)
print('door behavior passed')
"""
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / 'original-door.lua'
            script.write_text(setup + build_personal.DOOR_STAYS_OPEN + checks)
            result = subprocess.run([lua, str(script)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('door behavior passed', result.stdout)


if __name__ == '__main__':
    unittest.main()
