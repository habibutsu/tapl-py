from syntax import *
# ------------------------   EVALUATION  ------------------------

class NoRuleApplies(RuntimeError):
    pass

def isval(term):
    if type(term) is TmTrue:
        return True
    elif isinstance(term, TmFalse):
        return True
    elif isinstance(term, TmAbs):
        return True
    elif isinstance(term, TmRecord):
        return all(map(lambda t: isval(t[1]), term.fields))
    else:
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

    def visit_TmIf(term, ctx):
        if isinstance(term.term_condition, TmTrue):
            return term.term_then
        elif isinstance(term.term_condition, TmFalse):
            return term.term_else
        else:
            new_term_condition = evaluate(ctx, term.term_condition)
            return TmIf(
                term.info,
                new_term_condition,
                term.term_then, term.term_else)

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

def evalbinding(ctx, b):
    type_b = type(b)
    if type_b is TmAbbBind:
       term = evaluate(ctx, b.term)
       return TmAbbBind(term, b.type)
    return b

def istyabb(ctx, i):
    # FIXME: may be implement with using gettyabb
    b = getbinding(ctx, i)
    if isinstance(b, TyAbbBind):
        return True
    return False

def gettyabb(ctx, i):
    b = getbinding(ctx, i)
    if isinstance(b, TyAbbBind):
        return b.type
    raise NoRuleApplies

def computety(ctx, tyT):
    if isinstance(tyT, TyVar):
        return gettyabb(ctx, tyT.index)
    else:
        raise NoRuleApplies

def simplifyty(ctx, tyT):
    # TODO: unfold into cycle
    try:
        tyT1 = computety(ctx, tyT)
        return simplifyty(ctx, tyT1)
    except NoRuleApplies:
        return tyT

def tyeqv(ctx, tyS, tyT):
    tyS = simplifyty(ctx, tyS)
    tyT = simplifyty(ctx, tyT)
    if type(tyS) == type(tyT):

        if type(tyS) is TyId:
            return tyS.name == tyT.name
        elif type(tyS) is TyVar:
            return tyS.index == tyT.index
        elif type(tyS) is TyArr:
            return tyeqv(tyS.left, tyT.left) & tyeq(tyS.right, tyT.right)
        elif type(tyS) is TyRecord:
            if len(tyS.fields) != len(tyT.fields):
                return False
            # NOTE: positionally dependent
            # See notes in 11.8 Records
            for ((name1, tyS1), (name2,tyT1)) in zip(tyS.fields, tyT.fields):
                if not tyeqv(ctx, tyS1, tyT1):
                    return False
            return True
        elif type(tyS) is TyVariant:
            raise NotImplementedError(tyS, tyS)
        elif type(tyS) in [TyString, TyUnit, TyFloat, TyBool, TyNat]:
            return True
        else:
            raise NotImplementedError(tyS, tyS)
    else:
        return False

# ------------------------   TYPING  ------------------------

class Typeof(Visitor):

    def visit_TmVar(term, ctx):
        return getTypeFromContext(ctx, term.index)

    def visit_TmAbs(term, ctx):
        addbinding(ctx, term.name, VarBind(term.type))
        typeLeft = term.type
        typeRight = typeof(term.term, ctx)
        ctx.pop()
        return TyArr(typeLeft, typeRight)

    def visit_TmApp(term, ctx):
        typeLeft = typeof(term.left, ctx)
        typeRight = typeof(term.right, ctx)
        typeLeft_ = simplifyty(ctx, typeLeft)
        if isinstance(typeLeft_, TyArr):
            if tyeqv(ctx, typeRight, typeLeft_.left):
                return typeLeft_.right
            else:
                raise RuntimeError(
                    "Parameter type mismatch",
                    term.info, typeLeft, typeRight)
        else:
            raise RuntimeError("Arrow type expected")

    def visit_TmTrue(term, ctx):
        return TyBool()

    def visit_TmFalse(term, ctx):
        return TyBool()

    def visit_TmString(term, ctx):
        return TyString()

    def visit_TmIf(term, ctx):
        typeCond = typeof(term.term_condition, ctx)
        if isinstance(typeCond, TyBool):
            typeThen = typeof(term.term_then, ctx)
            typeElse = typeof(term.term_else, ctx)
            if type(typeThen) == type(typeElse):
                return typeThen
            else:
                raise RuntimeError(
                    term.info, "arms of conditional have different types")
        else:
            raise RuntimeError(term.info, "guard of conditional not a boolean")

    def visit_TmRecord(term, ctx):
        fieldtys = [(li, typeof(ti, ctx)) for li, ti in term.fields]
        return TyRecord(fieldtys)

    def visit_TmProj(term, ctx):
        s_term = simplifyty(ctx, typeof(term.term, ctx))
        if type(s_term) is not TyRecord:
            raise RuntimeError(term.info, "Expected record type")
        for (name, tf) in s_term.fields:
            if name == term.name: 
                return tf
        raise RuntimeError(
            term.info, "label " + str(term.name) + " not found")

    def visit_TmTag(term, ctx):
        s_term = simplifyty(ctx, term.type)

        tyTi = typeof(term.term, ctx)
        if type(s_term) is not TyVariant:
            raise RuntimeError(term.info, "Annotation is not a variant type")

        tyTiExpected = None
        for (name, tf) in s_term.fields:
            if name == term.tag:
                tyTiExpected = tf

        if tyTiExpected is None:
            raise RuntimeError(
                term.info, "label " + str(term.name) + " not found")

        if tyeqv(ctx, tyTi, tyTiExpected):
            return term.type
        else:
            raise RuntimeError(
                term.info,
                "field does not have expected type - expected %s in fact %s"
                    % (tyTiExpected, tyTi))

typeof = Typeof.visit

