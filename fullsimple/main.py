import argparse

from lexer import Lexer
from parser import Parser
import syntax
import core

def prbindingty(b, ctx):
    type_b = type(b)
    if type_b in [syntax.NameBind, syntax.TyVarBind]:
        pass
    elif type_b is syntax.VarBind:
        print(": ", end="")
        syntax.printty(b.type, ctx)
    elif type_b is syntax.TmAbbBind:
        print(": ", end="")
        if b.type is None:
            syntax.printty(core.typeof(b.term, ctx), ctx)
        else:
            syntax.printty(b.type, ctx)
    elif type_b is syntax.TyAbbBind:
        print(":: *", end="")
    else:
        raise NotImplementedError(b)

def checkbinding(b, ctx):
    type_b = type(b)

    simple_types = [
        syntax.NameBind, syntax.VarBind, syntax.TyAbbBind, syntax.TyVarBind]

    if type_b in simple_types:
        return b
    elif type_b is syntax.TmAbbBind:
        if b.type is None:
            return syntax.TmAbbBind(b.term, core.typeof(b.term, ctx))
        tyT = core.typeof(b.term, ctx)
        if core.tyeqv(ctx, tyT, b.type):
            return b
        raise RuntimeError("Type of binding does not match declared type")
    raise NotImplementedError(b)


def process_command(cmd, ctx):
    type_cmd = type(cmd)
    if type_cmd is syntax.Eval:
        term_type = core.typeof(cmd.term, ctx)
        term = core.evaluate(ctx, cmd.term)
        syntax.printtm(term, ctx)
        print(": ", end="")
        syntax.printty(term_type, ctx)
        print("")
    elif type_cmd is syntax.Bind:
        bind = checkbinding(cmd.binding, ctx)
        bind = core.evalbinding(ctx, bind)
        print(cmd.name, end="")
        print(" ", end="")
        prbindingty(bind, ctx)
        print("")
        syntax.addbinding(ctx, cmd.name, bind)

def parse_file(f):
    with open(f, 'r') as fd:
        text = fd.read()
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