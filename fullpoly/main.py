#!/usr/bin/env python3

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
            syntax.printty(core.typeof(ctx, b.term), ctx)
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
            return syntax.TmAbbBind(b.term, core.typeof(ctx, b.term))
        tyT = core.typeof(ctx, b.term)
        if core.tyeqv(ctx, tyT, b.type):
            return b
        raise RuntimeError("Type of binding does not match declared type")
    raise NotImplementedError(b)


def process_command(cmd, ctx):
    type_cmd = type(cmd)
    if type_cmd is syntax.Eval:
        term_type = core.typeof(ctx, cmd.term)
        term = core.evaluate(ctx, cmd.term)
        syntax.printtm(ctx, term)
        print(": ", end="")
        syntax.printty(ctx, term_type)
        print("")
    elif type_cmd is syntax.Bind:
        bind = checkbinding(cmd.binding, ctx)
        bind = core.evalbinding(ctx, bind)
        print(cmd.name, end="")
        print(" ", end="")
        prbindingty(bind, ctx)
        print("")
        syntax.addbinding(ctx, cmd.name, bind)
    elif type_cmd is syntax.SomeBind:
        tyT = core.typeof(ctx, cmd.term)
        styT = core.simplifyty(ctx, tyT)
        if type(styT) is not syntax.TySome:
            raise RuntimeError(
                cmd.term.info, "Existential type expected")

        tyBody = styT.type
        term = core.evaluate(ctx, cmd.term)
        if type(term) is syntax.TmPack:
            b = syntax.TmAbbBind(
                syntax.termShift(1, term.term), tyBody)
        else:
            b = syntax.VarBind(tyBody)
        print(cmd.ty_name)
        print(cmd.var_name, end="")
        print(" : ", end="")

        syntax.addbinding(ctx, cmd.ty_name, syntax.TyVarBind())
        syntax.printty(ctx, tyBody)
        syntax.addbinding(ctx, cmd.var_name, b)
        print("")
    else:
        raise RuntimeError("Unknown command", cmd)

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