from functools import reduce

from syntax import *
from collections import namedtuple

class NoRuleApplies(RuntimeError):
    pass

# ------------------------   EVALUATION  ------------------------

def isnumericval(term):
    t_term = type(term)
    if t_term is TmZero:
        return True
    elif t_term is TmSucc:
        return isnumericval(term.term)
    return False


def isval(term):
    t_term = type(term)
    if t_term is TmTrue:
        return True
    elif t_term is TmFalse:
        return True
    elif isnumericval(term):
        return True
    elif t_term is TmAbs:
        return True
    return False


class Evaluate(Visitor):

    def visit_TmApp(term, ctx):
        if isval(term.left) and isval(term.right):
            return termSubstTop(term.right, term.left.term)
        elif isval(term.left):
            right = evaluate1(term.right, ctx)
            return term._replace(right=right)
        else:
            left = evaluate1(term.left, ctx)
            return term._replace(left=left)

    def visit_TmIf(term, ctx): 
        t_cond = type(term.term_condition)
        if t_cond is TmTrue:
            return term.term_then
        elif t_cond is TmFalse:
            return term.term_else
        t = evaluate1(term.term_condition, ctx)
        return term._replace(term_condition=t)

    def visit_TmSucc(term, ctx):
        t = evaluate1(term.term, ctx)
        return term._replace(term=t)

    def visit_TmPred(term, ctx):
        t_term = type(term.term)
        if t_term is TmZero:
            return TmZero(None)
        elif t_term is TmSucc and isnumericval(term.term):
            return term.term

        t = evaluate1(term.term, ctx)
        return TmPred(term.info, t)

    def visit_TmIsZero(term, ctx):
        t_term = type(term.term)
        if t_term is TmZero:
            return TmTrue(None)
        elif t_term is TmSucc and isnumericval(term.term):
            return TmFalse(None)

        t = evaluate1(term.term, ctx)
        return TmIsZero(term.info, t)

    def visit_ANY(term, ctx):
        raise NoRuleApplies

evaluate1 = Evaluate.visit


def evaluate(ctx, term):
    try:
        return evaluate(ctx, evaluate1(term, ctx))
    except NoRuleApplies:
        return term

# ------------------------   TYPING  ------------------------

combineconstr = list.extend

def uvargen():
    n = 0
    while True:
        yield "?X%s" % n
        n += 1


class Reconstruction(Visitor):

    def visit_TmVar(term, ctx, nextuvar):
        tyT = getTypeFromContext(ctx, term.index)
        return (tyT, [])

    def visit_TmAbs(term, ctx, nextuvar):
        "lambda <name>:<type>. <term>"

        typeLeft = term.type
        addbinding(ctx, term.name, VarBind(typeLeft))
        (typeRight, contsr) = recon(term.term, ctx, nextuvar)
        ctx.pop()
        return (TyArr(typeLeft, typeRight), contsr)

    def visit_TmApp(term, ctx, nextuvar):
        """
        (t1 t2) with t1: T1, t2: T2
        return: type X and constraint T1 = T2 -> X
        
        see 22.3 Constraint-Based Typing
        """
        (typeLeft, constrLeft) = recon(term.left, ctx, nextuvar)
        (typeRight, constrRight) = recon(term.right, ctx, nextuvar)
        tyX = nextuvar()
        # typeLeft should be is 'arrow' from typeRight to X
        newconstr = [(typeLeft, TyArr(typeRight, TyId(tyX)))]
        constr = newconstr + constrLeft + constrRight
        return (TyId(tyX), constr)

    def visit_TmZero(term, ctx, nextuvar):
        return (TyNat(), [])

    def visit_TmSucc(term, ctx, nextuvar):
        (tyT, constr) = recon(term.term, ctx, nextuvar)
        return (TyNat(), [(tyT, TyNat())] + constr)

    def visit_TmPred(term, ctx, nextuvar):
        (tyT, constr) = recon(term.term, ctx, nextuvar)
        return (TyNat(), [(tyT, TyNat())] + constr)

    def visit_TmIsZero(term, ctx, nextuvar):
        (tyT, constr) = recon(term.term, ctx, nextuvar)
        return (TyNat(), [(tyT, TyNat())] + constr)

    def visit_TmTrue(term, ctx, nextuvar):
        return (TyBool(), [])

    def visit_TmFalse(term, ctx, nextuvar):
        return (TyBool(), [])

    def visit_TmIf(term, ctx, nextuvar):
        (tyT1, constr1) = recon(term.term_condition, ctx, nextuvar)
        (tyT2, constr2) = recon(term.term_then, ctx, nextuvar)
        (tyT3, constr3) = recon(term.term_else, ctx, nextuvar)
        newconstr = [(tyT1,TyBool()), (tyT2,tyT3)]
        constr = newconstr + constr1 + constr2 + constr3
        return (tyT3, constr)

recon = Reconstruction.visit

class SubstituteInTy(Visitor):

    def visit_TyArr(term, tyX, tyT):
        return TyArr(
            substinty(term.left, tyX, tyT),
            substinty(term.right, tyX, tyT))

    def visit_TyNat(term, tyX, tyT):
        return term

    def visit_TyBool(term, tyX, tyT):
        return term

    def visit_TyId(term, tyX, tyT):
        if term.name == tyX:
            return tyT
        return term

substinty = SubstituteInTy.visit

def applysubst(constr, tyT):
    tyS = tyT
    for (tyC1, tyC2) in reversed(constr):
        tyX = tyC1.name
        tyS = substinty(tyS, tyX, tyC2)
    return tyS

def substinconstr(tyT, tyX,  constr):
    return list(map(
        lambda tyS: (
            substinty(tyS[0], tyX, tyT),
            substinty(tyS[1], tyX, tyT)),
        constr))


class OccursIn(Visitor):

    def visit_TyArr(term, tyX):
        return (
            occursin(term.left, tyX)
            or occursin(term.right, tyX))

    def visit_TyNat(term, tyX):
        return False

    def visit_TyBool(term, tyX):
        return False

    def visit_TyId(term, tyX):
        return term.name == tyX

occursin = OccursIn.visit


def unify(ctx, constr_in):
    if not constr_in:
        return constr_in
    constr = list(constr_in)
    (tyS, tyT) = constr[0]
    rest = constr[1:]
    t_tyS = type(tyS)
    t_tyT = type(tyT)
    if t_tyT is TyId:
        tyX = tyT.name
        if tyS == tyT:
            return unify(ctx, rest)
        elif occursin(tyS, tyX):
            raise RuntimeError("Circular constraints")
        else:
            upd = unify(ctx, substinconstr(tyS, tyX, rest))
            upd.append((TyId(tyX),tyS))
            return upd
    elif t_tyS is TyId:
        tyX = tyS.name
        if tyT == tyS:
            return unify(ctx, rest)
        elif occursin(tyT, tyX):
            raise RuntimeError("Circular constraints")
        else:
            upd = unify(ctx, substinconstr(tyT, tyX, rest))
            upd.append((TyId(tyX),tyT))
            return upd
    elif t_tyS is TyNat and t_tyT is TyNat:
        return unify(ctx, rest)
    elif t_tyS is TyBool and t_tyT is TyBool:
        return unify(ctx, rest)
    elif t_tyS is TyArr and t_tyT is TyArr:
        upd = [(tyS.left, tyT.left), (tyS.right, tyT.right)]
        upd.extend(rest)
        return unify(ctx, upd)
    
    raise RuntimeError("Unsolvable constraints")
