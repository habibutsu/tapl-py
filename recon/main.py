import argparse

from lexer import Lexer
from parser import Parser
import syntax
import core


def process_command(cmd, ctx, constr, nextuvar):
    if type(cmd) is syntax.Eval:
        # Step 1 - Reconstruction
        (tyT, constr_t) = core.recon(cmd.term, ctx, nextuvar)
        term = core.evaluate(ctx, cmd.term)
        core.combineconstr(constr, constr_t)
        #Step 2 - Unification (Inference)
        unify_constr = core.unify(ctx, constr)
        constr.clear()
        constr.extend(unify_constr)

        tyT_inf = core.applysubst(constr, tyT)
        # Printing
        syntax.printtm(term, ctx)
        print(": ", end="")
        syntax.printty(tyT_inf)
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
    constr = []
    iuvargen = core.uvargen()
    nextuvar = lambda: next(iuvargen)
    for cmd in cmds:
        process_command(cmd, ctx, constr, nextuvar)

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("file", help="Input file")
    args = arg_parser.parse_args()
    process_file(args.file)

if __name__ == '__main__':
    main()