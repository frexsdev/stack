#!/usr/bin/env python3

import sys
import pickle
import argparse
from enum import IntEnum, auto
from prompt_toolkit import prompt

class Op(IntEnum):
    PUSH = auto()
    ADD = auto()
    DUMP = auto()
    EQUALS = auto()
    IF = auto()
    ELSE = auto()
    END = auto()
    COUNT = auto()

class Vm:
    def __init__(self, program=[], stack=[]):
        self.program = program
        self.stack = stack
        self.ip = 0

    def execute(self):
        while self.ip < len(self.program):
            self.execute_op()
    
    def current_op(self):
        return self.program[self.ip]

    def skip_until(self, op):
        while self.current_op() != op:
            self.ip += 1

    def execute_op(self):
        assert Op.COUNT == 8, "unexhaustive handling of operations"

        op = self.current_op()
        if op == Op.PUSH:
            self.ip += 1
            self.stack.append(self.current_op())
        elif op == Op.ADD:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a + b)
        elif op == Op.DUMP:
            x = self.stack.pop()
            print(x)
        elif op == Op.EQUALS:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a == b)
        elif op == Op.IF:
            cond = self.stack.pop()
            if cond:
                self.ip += 1
                while self.current_op() != Op.END:
                    if self.current_op() == Op.ELSE:
                        self.skip_until(Op.END)
                    else: 
                        self.execute_op()
            else:
                while self.current_op() != Op.END:
                    self.ip += 1
                    if self.current_op() == Op.ELSE:
                        self.ip += 1
                        self.skip_until(Op.END)
        else:
            assert False, "unreachable"

        self.ip += 1
    
    def load_from_file(self, file_path):
        with open(file_path, 'rb') as f:
            self.program = pickle.load(f)

    def save_to_file(self, file_path):
        with open(file_path, 'wb') as f:
            pickle.dump(self.program, f)

def lex(code):
    program = []
    words = [word
              for word in code.split(' ')
              if len(word) > 0]
    for word in words:
        if word == '+':
            program.append(Op.ADD)
        elif word == '.':
            program.append(Op.DUMP)
        elif word == '=':
            program.append(Op.EQUALS)
        elif word == 'if':
            program.append(Op.IF)
        elif word == 'else':
            program.append(Op.ELSE)
        elif word == 'end':
            program.append(Op.END)
        else:
            program.append(Op.PUSH)
            try: 
                program.append(int(word))
            except ValueError:
                try: 
                    program.append(float(word))
                except ValueError:
                    raise Exception('unknown word: %s' % bytes(word, 'utf-8'))
    return program

def lex_file(file_path):
    with open(file_path, 'r') as f:
        lines = [line 
                 for line in f.read().split('\n')
                 if len(line) > 0]
        code = ' '.join(lines)
        return lex(code)

def repl():
    stack = []
    while True:
        try:
            line = prompt('> ')
            program = lex(line)
            vm = Vm(program, stack)
            vm.execute()
            print(vm.stack)
        except (KeyboardInterrupt, EOFError):
            exit(0)
        except Exception as e:
            print('error: ' + str(e), file=sys.stderr)

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='subcommands', dest='subparser_name')

    execute_names = ['execute', 'e']
    execute = subparsers.add_parser(execute_names[0], 
                                    help='execute a .out file', 
                                    aliases=execute_names[1:])
    execute.add_argument('input_file', help='the file to execute')

    compile_names = ['compile', 'c']
    compile = subparsers.add_parser(compile_names[0], 
                                    help='compile a .stk file', 
                                    aliases=compile_names[1:])
    compile.add_argument('input_file', help='the file to compile')
    compile.add_argument('-r', '--run', 
                         help='execute the compiled flag',
                         action='store_true')
    compile.add_argument('-o', '--output',
                         help='the output file path',
                         default='output.out')

    args = parser.parse_args()

    try:
        if args.subparser_name in execute_names:
            vm = Vm()
            vm.load_from_file(args.input_file)
            vm.execute()
        elif args.subparser_name in compile_names:
            program = lex_file(args.input_file)
            vm = Vm(program)
            vm.save_to_file(args.output)

            if args.run:
                vm.load_from_file(args.output)
                vm.execute()
        else:
            repl()
    except Exception as e:
        print('error: %s' % e, file=sys.stderr)
        exit(1)

if __name__ == '__main__':
    main()
