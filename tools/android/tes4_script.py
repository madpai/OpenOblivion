#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Compile classic TES4 script source to Lua.

Oblivion keeps the source text of every script (SCTX) beside its bytecode. This
module parses that text with the exact parameter lists of the executable's
command table (see tes4_commands.py) and writes a Lua module for the
OpenOblivion script runtime (overlay/scripts/openoblivion_tes4_script.lua).

Three kinds of source are compiled:

* a script (`scn Name`, variables, `Begin <Block>` ... `End` blocks),
* a fragment (the statements of a dialogue result or a quest stage, no header),
* a condition-free expression is not needed: conditions are tables, not source.

Identifiers (quests, factions, objects, ...) are resolved to FormIDs at compile
time through a resolver, so the runtime never sees editor IDs. Commands are
called as `C.<name>(target, args...)`; commands the runtime does not implement
are logged once and ignored there, not here. Every unparseable construct is
reported with its line and compiled as a no-op, never silently dropped.
"""
import json
import re

PLAYER_REFERENCE = 0x14

BLOCK_TYPES = {
    'gamemode', 'menumode', 'onactivate', 'onadd', 'ondeath', 'onequip', 'onhit', 'onhitwith', 'onload',
    'onmagiceffecthit', 'onmurder', 'onpackagechange', 'onpackagedone', 'onpackageend', 'onpackagestart', 'onreset',
    'onsell', 'onstartcombat', 'ontrigger', 'ontriggeractor', 'ontriggermob', 'onunequip', 'scripteffectfinish',
    'scripteffectstart', 'scripteffectupdate', 'onalarm', 'ondrop', 'onactorequip', 'onactorunequip', 'onknockout',
    'onvampirefeed', 'onbribe',
}
VARIABLE_TYPES = {'short', 'long', 'float', 'ref', 'int'}
# Commands that take any number of extra expression arguments after their string (format arguments).
VARIADIC = {'message', 'messagebox', 'messageboxex', 'messageex'}
# Parameter types whose argument is a plain word, passed to the runtime as a lower-case string.
WORD_TYPES = {'ActorValue', 'Axis', 'Sex', 'AnimationGroup', 'VariableName', 'CrimeType', 'FormType'}
EXPRESSION_TYPES = {'Integer', 'Float', 'Stage'}
STRING_TYPES = {'String'}

TOKEN = re.compile(r'''\s*(?:(?P<str>"[^"]*")|(?P<num>(?:\d+\.\d*|\.\d+|\d+)(?![A-Za-z_]))'''
                   r'''|(?P<id>[A-Za-z_0-9]+)|(?P<op>==|!=|>=|<=|&&|\|\||[-+*/%!<>()=,.:^]))''')


class ScriptError(Exception):
    pass


class Command:
    def __init__(self, row):
        self.name = row['name']
        self.short = row.get('short') or ''
        self.opcode = row['opcode']
        self.parent = bool(row['parent'])
        self.params = [(p['type'], bool(p['optional'])) for p in row['params']]
        self.lua = re.sub(r'[^a-z0-9_]', '_', self.name.lower())


class CommandTable:
    def __init__(self, rows):
        self.by_name = {}
        self.by_opcode = {}
        for row in rows:
            command = Command(row)
            self.by_opcode[command.opcode] = command
            self.by_name[command.name.lower()] = command
            if command.short:
                self.by_name.setdefault(command.short.lower(), command)

    @classmethod
    def load(cls, path):
        with open(path) as stream:
            return cls(json.load(stream))

    def get(self, word):
        return self.by_name.get(word.lower())


class Tokens:
    def __init__(self, line_number, text):
        self.line = line_number
        self.text = text
        self.items = []
        position = 0
        text = text.rstrip()
        while position < len(text):
            match = TOKEN.match(text, position)
            if not match:
                if text[position:].strip() == '':
                    break
                raise ScriptError(f'line {line_number}: cannot read {text[position:position + 12]!r}')
            position = match.end()
            kind = match.lastgroup
            self.items.append((kind, match.group(kind)))
        self.index = 0

    def done(self):
        return self.index >= len(self.items)

    def peek(self, offset=0):
        i = self.index + offset
        return self.items[i] if i < len(self.items) else (None, None)

    def next(self):
        if self.done():
            raise ScriptError(f'line {self.line}: statement ends early')
        token = self.items[self.index]
        self.index += 1
        return token

    def accept(self, value):
        kind, text = self.peek()
        if text is not None and text.lower() == value:
            self.index += 1
            return True
        return False

    def expect(self, value):
        if not self.accept(value):
            raise ScriptError(f'line {self.line}: expected {value!r}, found {self.peek()[1]!r}')


def strip_comment(line):
    quoted = False
    for i, char in enumerate(line):
        if char == '"':
            quoted = not quoted
        elif char == ';' and not quoted:
            return line[:i]
    return line


def lua_string(text):
    out = ['"']
    for char in text:
        if char in '"\\':
            out.append('\\' + char)
        elif char == '\n':
            out.append('\\n')
        elif char == '\r':
            continue
        elif ord(char) < 32 or ord(char) > 126:
            out.append('\\%d' % ord(char) if ord(char) < 256 else '?')
        else:
            out.append(char)
    out.append('"')
    return ''.join(out)


class Resolver:
    """Maps editor IDs to FormIDs. Subclass or duck-type in the packager."""

    def form(self, word):
        """Return (formid, record type name) or None."""
        return None

    def quest_script(self, quest_formid):
        """Return {variable: type} of the quest's script, or None."""
        return None

    def reference_script(self, word):
        """Return {variable: type} of the script attached to a named reference, or None."""
        return None


class Compiler:
    def __init__(self, table, resolver, name='script'):
        self.table = table
        self.resolver = resolver
        self.name = name
        self.warnings = []
        self.variables = {}
        self.variable_order = []
        self.out = []
        self.depth = 0
        self.stack = []
        self.blocks = []
        self.in_block = False
        self.ops = []  # statement-level opcodes, for checking against compiled scripts

    # -- output -----------------------------------------------------------
    def emit(self, text):
        self.out.append('  ' * (self.depth + 2) + text)

    def warn(self, tokens, message):
        self.warnings.append(f'{self.name}:{tokens.line}: {message}')

    # -- identifier helpers -----------------------------------------------
    def local(self, word):
        word = word.lower()
        return self.variables.get(word)

    def form(self, tokens, word, allow_missing=False):
        if word.lower() in ('player', 'playerref'):
            return PLAYER_REFERENCE, 'REFR'
        found = self.resolver.form(word)
        if found is None:
            if not allow_missing:
                self.warn(tokens, f'unknown form {word}')
            return None
        return found

    def form_code(self, tokens, word):
        """Code for an identifier used where an object, ref or record is expected."""
        if self.local(word) is not None:
            return f'v.{word.lower()}'
        found = self.form(tokens, word)
        return str(found[0]) if found else '0'

    # -- expressions ------------------------------------------------------
    PRECEDENCE = {'||': 1, '&&': 2, '==': 3, '!=': 3, '<': 3, '>': 3, '<=': 3, '>=': 3, '+': 4, '-': 4,
                  '*': 5, '/': 5, '%': 5, '^': 6}

    def expression(self, tokens, minimum=1):
        left = self.unary(tokens)
        while True:
            kind, text = tokens.peek()
            if kind != 'op' or text not in self.PRECEDENCE or self.PRECEDENCE[text] < minimum:
                return left
            tokens.next()
            right = self.expression(tokens, self.PRECEDENCE[text] + 1)
            left = self.binary(text, left, right)

    @staticmethod
    def binary(op, a, b):
        if op == '&&':
            return f'((({a}) ~= 0 and ({b}) ~= 0) and 1 or 0)'
        if op == '||':
            return f'((({a}) ~= 0 or ({b}) ~= 0) and 1 or 0)'
        if op in ('==', '<', '>', '<=', '>='):
            return f'((({a}) {op} ({b})) and 1 or 0)'
        if op == '!=':
            return f'((({a}) ~= ({b})) and 1 or 0)'
        if op == '%':
            return f'math.fmod({a}, {b})'
        if op == '^':
            return f'(({a}) ^ ({b}))'
        return f'(({a}) {op} ({b}))'

    def unary(self, tokens):
        kind, text = tokens.peek()
        if kind == 'op' and text == '-':
            tokens.next()
            return f'(-({self.unary(tokens)}))'
        if kind == 'op' and text == '!':
            tokens.next()
            return f'((({self.unary(tokens)}) == 0) and 1 or 0)'
        return self.primary(tokens)

    def primary(self, tokens):
        kind, text = tokens.next()
        if kind == 'num':
            return text if '.' in text else text
        if kind == 'str':
            return lua_string(text[1:-1])
        if kind == 'op' and text == '(':
            inner = self.expression(tokens)
            tokens.expect(')')
            return f'({inner})'
        if kind == 'id':
            return self.identifier(tokens, text)
        raise ScriptError(f'line {tokens.line}: unexpected {text!r}')

    def identifier(self, tokens, word):
        # prefix.member
        if tokens.peek() == ('op', '.') and tokens.peek(1)[0] == 'id':
            tokens.next()
            member = tokens.next()[1]
            return self.qualified(tokens, word, member)
        command = None if self.local(word) else self.table.get(word)
        if command is not None:
            return self.call(tokens, command, None, as_value=True)
        if self.local(word) is not None:
            return f'v.{word.lower()}'
        found = self.form(tokens, word, allow_missing=True)
        if found is not None:
            if found[1] == 'GLOB':
                return f'rt.gget({found[0]})'
            return str(found[0])
        self.warn(tokens, f'unknown identifier {word}')
        return '0'

    def target_code(self, tokens, prefix):
        if prefix.lower() == 'player':
            return str(PLAYER_REFERENCE)
        if self.local(prefix) is not None:
            return f'v.{prefix.lower()}'
        found = self.form(tokens, prefix)
        return str(found[0]) if found else '0'

    def qualified(self, tokens, prefix, member, as_value=True):
        command = self.table.get(member)
        found = None if self.local(prefix) is not None else self.form(tokens, prefix, allow_missing=True)
        is_quest = found is not None and found[1] == 'QUST'
        if command is not None and not is_quest:
            return self.call(tokens, command, self.target_code(tokens, prefix), as_value)
        if is_quest:
            return f'rt.qget({found[0]}, {lua_string(member.lower())})'
        # a script variable of another reference
        if prefix.lower() == 'player' or self.local(prefix) is not None or found is not None:
            return f'rt.rget({self.target_code(tokens, prefix)}, {lua_string(member.lower())})'
        self.warn(tokens, f'unknown {prefix}.{member}')
        return '0'

    def call(self, tokens, command, target, as_value):
        arguments = []
        for index, (type_name, optional) in enumerate(command.params):
            if tokens.done() or not self.starts_argument(tokens):
                if not optional:
                    self.warn(tokens, f'{command.name} is missing parameter {index + 1}')
                    arguments.append('0')
                    continue
                break
            arguments.append(self.argument(tokens, type_name))
            tokens.accept(',')
        if command.name.lower() in VARIADIC:
            while not tokens.done() and self.starts_argument(tokens):
                arguments.append(self.unary(tokens))
                tokens.accept(',')
        head = []
        if command.parent:
            head.append(target if target is not None else 'S.ref')
        call = f'C.{command.lua}({", ".join(head + arguments)})'
        return f'N({call})' if as_value else call

    @staticmethod
    def starts_argument(tokens):
        kind, text = tokens.peek()
        if kind in ('num', 'str', 'id'):
            return True
        return kind == 'op' and text in ('(', '-', ',')

    def argument(self, tokens, type_name):
        tokens.accept(',')
        kind, text = tokens.peek()
        if type_name in EXPRESSION_TYPES:
            return self.unary(tokens)
        if type_name in STRING_TYPES:
            if kind == 'str':
                tokens.next()
                return lua_string(text[1:-1])
            return self.unary(tokens)
        if type_name in WORD_TYPES:
            if kind == 'id':
                tokens.next()
                if self.local(text) is not None:
                    return f'v.{text.lower()}'
                return lua_string(text.lower())
            return self.unary(tokens)
        # records, references and objects
        if kind == 'id':
            tokens.next()
            if tokens.peek() == ('op', '.') and tokens.peek(1)[0] == 'id':
                tokens.next()
                member = tokens.next()[1]
                return self.qualified(tokens, text, member)
            if self.local(text) is not None:
                return f'v.{text.lower()}'
            return self.form_code(tokens, text)
        if kind == 'num':
            tokens.next()
            return text
        return self.unary(tokens)

    # -- statements -------------------------------------------------------
    def declare(self, tokens, kind):
        name = tokens.next()[1].lower()
        self.variables[name] = kind
        self.variable_order.append((name, kind))

    def assign(self, tokens):
        kind, word = tokens.next()
        target = None
        if tokens.peek() == ('op', '.') and tokens.peek(1)[0] == 'id':
            tokens.next()
            member = tokens.next()[1].lower()
            found = None if self.local(word) is not None else self.form(tokens, word, allow_missing=True)
            if found is not None and found[1] == 'QUST':
                script = self.resolver.quest_script(found[0]) or {}
                target = ('q', found[0], member, script.get(member, 'float'))
            else:
                target = ('r', self.target_code(tokens, word), member, 'float')
        elif self.local(word) is not None:
            target = ('l', word.lower(), None, self.local(word))
        else:
            found = self.form(tokens, word, allow_missing=True)
            if found is not None and found[1] == 'GLOB':
                target = ('g', found[0], None, 'float')
            else:
                self.warn(tokens, f'cannot set {word}')
        tokens.expect('to')
        value = self.expression(tokens)
        if target is None:
            return
        if target[3] in ('short', 'long'):
            value = f'rt.trunc({value})'
        if target[0] == 'l':
            self.emit(f'v.{target[1]} = {value}')
        elif target[0] == 'q':
            self.emit(f'rt.qset({target[1]}, {lua_string(target[2])}, {value})')
        elif target[0] == 'g':
            self.emit(f'rt.gset({target[1]}, {value})')
        else:
            self.emit(f'rt.rset({target[1]}, {lua_string(target[2])}, {value})')

    def statement(self, tokens):
        kind, word = tokens.peek()
        low = word.lower() if word else ''
        if kind == 'id' and self.local(word) is None:
            if low in VARIABLE_TYPES:
                tokens.next()
                self.declare(tokens, 'long' if low == 'int' else low)
                return
            if low in ('scn', 'scriptname'):
                self.ops.append(0x1D)
                return
            if low == 'begin':
                tokens.next()
                self.ops.append(0x10)
                self.begin(tokens)
                return
            if low == 'end' and self.in_block:
                tokens.next()
                while self.stack:  # a script that forgot its Endifs still has to yield valid Lua
                    self.stack.pop()
                    self.depth -= 1
                    self.emit('end')
                    self.warn(tokens, 'unclosed If at End')
                self.depth -= 1
                self.emit('end,')
                self.in_block = False
                self.ops.append(0x11)
                return
            if low == 'if':
                tokens.next()
                self.ops.append(0x16)
                self.emit(f'if ({self.expression(tokens)}) ~= 0 then')
                self.depth += 1
                self.stack.append(['if', False])
                return
            if low in ('elseif', 'else') and self.stack and self.stack[-1][1]:
                tokens.next()  # Lua allows nothing after an Else but its Endif
                self.ops.append(0x18 if low == 'elseif' else 0x17)
                self.warn(tokens, f'{low} after Else')
                return
            if low in ('elseif', 'else', 'endif', 'endwhile') and not self.stack:
                # shipped scripts contain stray Else/Endif lines; the original compiler counted them
                # as statements but they have no If to belong to
                tokens.next()
                self.ops.append({'elseif': 0x18, 'else': 0x17}.get(low, 0x19))
                self.warn(tokens, f'{low} without If')
                return
            if low == 'elseif':
                tokens.next()
                self.ops.append(0x18)
                self.depth -= 1
                self.emit(f'elseif ({self.expression(tokens)}) ~= 0 then')
                self.depth += 1
                return
            if low == 'else':
                tokens.next()
                self.ops.append(0x17)
                self.stack[-1][1] = True
                self.depth -= 1
                self.emit('else')
                self.depth += 1
                return
            if low in ('endif', 'endwhile'):
                tokens.next()
                self.ops.append(0x19)
                if self.stack:
                    self.stack.pop()
                self.depth -= 1
                self.emit('end')
                return
            if low == 'while':
                tokens.next()
                self.emit(f'while ({self.expression(tokens)}) ~= 0 do')
                self.depth += 1
                self.stack.append(['while', False])
                return
            if low == 'return':
                tokens.next()
                self.ops.append(0x1E)
                self.emit('do return end')
                return
            if low == 'set':
                tokens.next()
                self.ops.append(0x15)
                self.assign(tokens)
                return
        # a command, optionally with a reference prefix
        kind, word = tokens.next()
        if kind != 'id':
            raise ScriptError(f'line {tokens.line}: cannot start a statement with {word!r}')
        if tokens.peek() == ('op', '.') and tokens.peek(1)[0] == 'id':
            tokens.next()
            member = tokens.next()[1]
            command = self.table.get(member)
            if command is None:
                raise ScriptError(f'line {tokens.line}: unknown command {word}.{member}')
            self.ops.extend((0x1C, command.opcode))  # 0x1C: the statement runs on a reference
            self.emit(self.call(tokens, command, self.target_code(tokens, word), as_value=False))
        else:
            command = self.table.get(word)
            if command is None:
                raise ScriptError(f'line {tokens.line}: unknown command {word}')
            self.ops.append(command.opcode)
            self.emit(self.call(tokens, command, None, as_value=False))

    def begin(self, tokens):
        kind, block = tokens.next()
        block = block.lower()
        if block not in BLOCK_TYPES:
            raise ScriptError(f'line {tokens.line}: unknown block {block}')
        key = block
        if not tokens.done():
            _, parameter = tokens.next()
            found = self.form(tokens, parameter, allow_missing=True)
            if found is not None:
                key = f'{block}:{found[0]}'
        if self.in_block:
            raise ScriptError(f'line {tokens.line}: Begin inside a block')
        self.in_block = True
        self.stack = []
        self.depth = 0
        self.emit(f'[{lua_string(key)}] = function(S, v)')
        self.depth += 1
        self.blocks.append(key)

    # -- drivers ----------------------------------------------------------
    def run(self, source, header):
        for number, raw in enumerate(source.replace('\r\n', '\n').replace('\r', '\n').split('\n'), 1):
            line = strip_comment(raw).strip()
            if not line:
                continue
            try:
                tokens = Tokens(number, line)
                if tokens.done():
                    continue
                self.statement(tokens)
            except ScriptError as error:
                self.warnings.append(f'{self.name}: {error}')
                self.emit(f'-- skipped: {line[:80]}'.replace('\n', ' '))
        if self.in_block:
            self.warnings.append(f'{self.name}: block not closed')
            self.depth = 1
            self.emit('end,')

    def finish(self, body_lines, extra=''):
        return '\n'.join(body_lines)


class Result:
    """Lua source plus what the compiler learned about the script."""

    def __init__(self, lua, expr, variables, warnings, ops, blocks):
        self.lua = lua  # a standalone module: return function(rt) ... end
        self.expr = expr  # the same value as a Lua expression using the upvalues rt, C, N
        self.variables = variables  # [(name, type)] in declaration order
        self.warnings = warnings
        self.ops = ops  # statement-level opcodes (0x10 Begin, 0x16 If, command opcodes, ...)
        self.blocks = blocks  # block keys such as 'gamemode' or 'onpackagechange:1234'


def module(expr):
    return f'return function(rt)\n  local C, N = rt.C, rt.N\n  return {expr}\nend\n'


def compile_script(source, table, resolver, name='script'):
    """Compile a full script (`scn`, variables, `Begin` blocks) to a table {vars, blocks}."""
    compiler = Compiler(table, resolver, name)
    compiler.run(source, True)
    declared = ', '.join(f'{{{lua_string(n)}, {lua_string(t)}}}' for n, t in compiler.variable_order)
    lines = ['{', f'    vars = {{{declared}}},', '    blocks = {']
    lines += compiler.out
    lines += ['    },', '  }']
    expr = '\n'.join(lines)
    return Result(module(expr), expr, compiler.variable_order, compiler.warnings, compiler.ops, compiler.blocks)


def compile_fragment(source, table, resolver, name='fragment'):
    """Compile statements without a header (a dialogue result or a quest stage) to a function(S, v)."""
    compiler = Compiler(table, resolver, name)
    compiler.run(source, False)
    lines = ['function(S, v)']
    lines += compiler.out
    lines += ['  end']
    expr = '\n'.join(lines)
    return Result(module(expr), expr, compiler.variable_order, compiler.warnings, compiler.ops, compiler.blocks)
