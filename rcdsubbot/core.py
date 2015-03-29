from syntax import *

class NoRuleApplies(RuntimeError):
    pass

# ------------------------   EVALUATION  ------------------------

def isval(term):
    if type(term) is TmAbs:
        return True
    if type(term) is TmRecord:
        return all(map(lambda t: isval(t[1]), term.fields))
    return False

class Evaluate(Visitor):

    def visit_TmApp(term, ctx):
        if isval(term.left) and isval(term.right):
            return termSubstTop(term.right, term.left.term)
        elif isval(term.left):
            right = evaluate1(term.right, ctx)
            return TmApp(term.info, term.left, right)
        else:
            left = evaluate1(term.left, ctx)
            return TmApp(term.info, left, term.right)

    def visit_TmRecord(term, ctx):
        for (num, field) in enumerate(term.fields):
            f_term = evaluate1(field[1], ctx)
            term.fields[num] = (field[0], f_term)
        return term

    def visit_TmProj(term, ctx):
        if type(term.term) is TmRecord:
            if isinstance(term.name, int):
                return term.term.fields[-term.name][1]
            # lookup by name
            # TODO: for increase perfomance may be used 'dict'
            for (name, value) in reversed(term.term.fields):
                if name == term.name:
                    return value
            raise NoRuleApplies("Not found")
        else:
            term.term = evaluate1(term.term, ctx)
            return term
        raise NoRuleApplies

    def visit__(term, ctx):
        raise NoRuleApplies


evaluate1 = Evaluate.visit


def evaluate(ctx, term):
    try:
        return evaluate(ctx, evaluate1(term, ctx))
    except NoRuleApplies:
        return term

# ------------------------   SUBTYPING  ------------------------

def subtype(tyS, tyT):
    t_tyS = type(tyS)
    t_tyT = type(tyT)

    if t_tyT is TyTop:
        return True

    if t_tyS is TyBot:
        return True

    if t_tyS is TyArr and t_tyT is TyArr:
        """ contravariant
        T1 <: S1
        S2 <: T2
        --------
        S1->S2 <: T1->T2

        (see '15.2 The Subtype Relation' page 184)
        """
        return subtype(tyT.left, tyS.left) and subtype(tyS.right, tyT.right)

    if t_tyS is TyRecord and t_tyT is TyRecord:
        # NOTE: positionally independent
        for (nameT, tyTi) in tyT.fields:
            for (nameS, tySi) in tyS.fields:
                if nameT == nameS: 
                    return subtype(tySi, tyTi)

    return False

# ------------------------   TYPING  ------------------------

class Typeof(Visitor):

    def visit_TmRecord(term, ctx):
        fieldtys = [(li, typeof(ti, ctx)) for li, ti in term.fields]
        return TyRecord(fieldtys)

    def visit_TmVar(term, ctx):
        return getTypeFromContext(ctx, term.index)

    def visit_TmAbs(term, ctx):
        addbinding(ctx, term.name, VarBind(term.type))
        typeLeft = term.type
        typeRight = typeof(term.term, ctx)
        ctx.pop()
        return TyArr(typeLeft, typeRight)

    def visit_TmApp(term, ctx):
        "(typeLeft.left -> typeLeft.right) typeRight"

        typeLeft = typeof(term.left, ctx)
        typeRight = typeof(term.right, ctx)

        if type(typeLeft) is TyArr:
            if subtype(typeRight, typeLeft.left):
                return typeLeft.right
            else:
                raise RuntimeError(
                    "Parameter type mismatch", term.info, term)
        elif type(typeLeft) is TyBot:
            return TyBot()
        else:
            raise RuntimeError("Arrow type expected", term.info, term)

    def visit_TmProj(term, ctx):
        t_term = typeof(term.term, ctx)

        if type(t_term) is TyBot:
            return TyBot()

        if type(t_term) is not TyRecord:
            raise RuntimeError("Expected record type", term.info, term)
            
        for (name, tf) in t_term.fields:
            if name == term.name: 
                return tf

        raise RuntimeError(
            "label " + str(term.name) + " not found", term.info)

typeof = Typeof.visit
