import argparse

from parser import Parser
import syntax
import core


def process_command(cmd, ctx):
    if isinstance(cmd, syntax.Eval):
        term = core.evaluate(ctx, cmd.term)
        syntax.printtm(term, ctx)
        print("")
    elif isinstance(cmd, syntax.Bind):
        print(cmd.name)
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