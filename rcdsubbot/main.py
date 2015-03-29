import argparse

from lexer import Lexer
from parser import Parser
import syntax
import core


def process_command(cmd, ctx):
    if isinstance(cmd, syntax.Eval):
        term_type = core.typeof(cmd.term, ctx)
        term = core.evaluate(ctx, cmd.term)
        syntax.printtm(term, ctx)
        print(": ", end="")
        syntax.printty(term_type)
        print("")
    elif isinstance(cmd, syntax.Bind):
        if isinstance(cmd.binding, syntax.VarBind):
            print(cmd.name, end="")
            print(": ", end="")
            syntax.printty(cmd.binding.type)
            print("")
        syntax.addbinding(ctx, cmd.name, cmd.binding)

def parse_file(f):
    with open(f, 'r') as f:
        text = f.read()
    parser = Parser()
    return parser.parse(text, f)

def process_file(f):
    cmds = parse_file(f)
    ctx = []
    for cmd in cmds:
        process_command(cmd, ctx)

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("file", help="Input file")
    args = arg_parser.parse_args()
    process_file(args.file)

if __name__ == '__main__':
    main()