#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""TES4 script compiler fixtures. Original source and a synthetic command table; no game data."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/android'))
import tes4_script
from tes4_script import CommandTable, Resolver, compile_fragment, compile_script


def command(name, opcode, params=(), parent=False, short=''):
    return {'name': name, 'short': short, 'opcode': opcode, 'parent': parent,
            'params': [{'type': t, 'optional': o} for t, o in params]}


TABLE = CommandTable([
    command('SetStage', 0x1039, [('Quest', False), ('Stage', False)]),
    command('GetStage', 0x103A, [('Quest', False)]),
    command('GetItemCount', 0x102F, [('ObjectID', False)], parent=True),
    command('AddItem', 0x1002, [('ObjectID', False), ('Integer', False)], parent=True),
    command('GetInCell', 0x1043, [('Cell', False)], parent=True),
    command('GetIsID', 0x1048, [('ObjectID', False)], parent=True),
    command('GetActorValue', 0x100E, [('ActorValue', False)], parent=True, short='GetAV'),
    command('Activate', 0x100D, [('ObjectReferenceID', True), ('Integer', True)], parent=True),
    command('MessageBox', 0x1000, [('String', False)]),
    command('Enable', 0x1021, parent=True),
    command('GetDead', 0x102E, parent=True),
    command('StopCombat', 0x1017, parent=True),
])

FORMS = {
    'mq02': (0x1E724, 'QUST'), 'gold001': (0xF, 'MISC'), 'chorrol': (0x1111, 'CELL'), 'jauffre': (0x2222, 'NPC_'),
    'pigref': (0x3333, 'REFR'), 'counter': (0x4444, 'GLOB'),
}


class FixtureResolver(Resolver):
    def form(self, word):
        return FORMS.get(word.lower())

    def quest_script(self, quest):
        return {'timer': 'float', 'step': 'short'} if quest == 0x1E724 else None


SCRIPT = '''scn Example
short step
float timer
ref target

; a comment
begin GameMode
	if getstage MQ02 == 20 && player.getincell chorrol == 1
		setstage MQ02 30
	elseif GetItemCount Gold001 >= 100 + 5 * 2
		set step to timer / 2
	else
		pigref.enable
	endif
	set MQ02.timer to 1.5
	set counter to counter + 1
end
'''


class CompilerTest(unittest.TestCase):
    def compile(self, source=SCRIPT):
        return compile_script(source, TABLE, FixtureResolver(), 'Example')

    def test_blocks_variables_and_statement_opcodes(self):
        result = self.compile()
        self.assertEqual(result.warnings, [])
        self.assertEqual(result.blocks, ['gamemode'])
        self.assertEqual(result.variables, [('step', 'short'), ('timer', 'float'), ('target', 'ref')])
        # scn, Begin, If, SetStage, ElseIf, Set, Else, (ref prefix, Enable), EndIf, Set, Set, End
        self.assertEqual(result.ops, [0x1D, 0x10, 0x16, 0x1039, 0x18, 0x15, 0x17, 0x1C, 0x1021, 0x19, 0x15, 0x15, 0x11])

    def test_lua_shape(self):
        lua = self.compile().lua
        self.assertIn('["gamemode"] = function(S, v)', lua)
        self.assertIn('C.getstage(124708)', lua)  # 0x1E724
        self.assertIn('C.setstage(124708, 30)', lua)
        self.assertIn('C.getincell(20, 4369)', lua)  # player is reference 0x14
        self.assertIn('C.getitemcount(S.ref, 15)', lua)  # implicit self for commands that need a parent
        self.assertIn('C.enable(13107)', lua)
        self.assertIn('rt.qset(124708, "timer", 1.5)', lua)
        self.assertIn('rt.gset(17476,', lua)
        self.assertIn('rt.trunc(', lua)  # step is a short

    def test_operator_precedence(self):
        lua = self.compile('float timer\nbegin GameMode\n set timer to 1 + 2 * 3\nend\n').lua
        self.assertIn('((1) + (((2) * (3))))', lua)

    def test_fragment_statements(self):
        result = compile_fragment('setstage MQ02 10\nplayer.additem gold001 100\nMessageBox "Hello"\n',
                                  TABLE, FixtureResolver(), 'result')
        self.assertEqual(result.warnings, [])
        self.assertEqual(result.ops, [0x1039, 0x1C, 0x1002, 0x1000])
        self.assertIn('C.setstage(124708, 10)', result.lua)
        self.assertIn('C.additem(20, 15, 100)', result.lua)
        self.assertIn('C.messagebox("Hello")', result.lua)

    def test_optional_arguments_stop_at_operators(self):
        lua = compile_script('begin GameMode\n if jauffre.activate == 0\n  jauffre.activate player 1\n endif\nend\n',
                             TABLE, FixtureResolver(), 'optional').lua
        self.assertIn('C.activate(8738, 20, 1)', lua)

    def test_word_parameters_and_short_names(self):
        lua = compile_script('float timer\nbegin GameMode\n if player.GetAV Strength > 40\n  set timer to 0\n endif\nend\n',
                             TABLE, FixtureResolver(), 'words').lua
        self.assertIn('C.getactorvalue(20, "strength")', lua)

    def test_unknown_names_warn_and_compile_as_no_ops(self):
        result = compile_fragment('frobnicate everything\nsetstage nowhere 5\n', TABLE, FixtureResolver(), 'bad')
        self.assertEqual(len(result.warnings), 2)
        self.assertIn('-- skipped: frobnicate everything', result.lua)
        self.assertIn('C.setstage(0, 5)', result.lua)  # unknown form -> 0, still a statement

    def test_extra_words_after_a_command_are_ignored_like_the_original(self):
        result = compile_fragment('jauffre.stopcombat player\n', TABLE, FixtureResolver(), 'extra')
        self.assertEqual(result.warnings, [])
        self.assertEqual(result.ops, [0x1C, 0x1017])

    @unittest.skipUnless(shutil.which('luajit'), 'luajit is not installed')
    def test_generated_lua_loads(self):
        for lua in (self.compile().lua,
                    compile_fragment('setstage MQ02 10\nif getstage MQ02 == 10\n player.additem gold001 1\nendif\n',
                                     TABLE, FixtureResolver(), 'x').lua):
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'chunk.lua'
                path.write_text(lua)
                result = subprocess.run(['luajit', '-bl', str(path)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
