from syntax import *

class NoRuleApplies(RuntimeError):
    pass

# ------------------------   EVALUATION  ------------------------

def isval(term):
    if isinstance(term, TmTrue):
        return True
    elif isinstance(term, TmFalse):
        return True
    else:
        return isinstance(term, TmAbs)

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
    
    def visit__(term, ctx):
        raise NoRuleApplies

evaluate1 = Evaluate.visit


def evaluate(ctx, term):
    try:
        return evaluate(ctx, evaluate1(term, ctx))
    except NoRuleApplies:
        return term

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

        if type(typeLeft) is TyArr:
            if type(typeRight) == type(typeLeft.left):
                return typeLeft.right
            else:
                raise RuntimeError(
                    "Parameter type mismatch", term.info, term)
        else:
            raise RuntimeError("Arrow type expected")

    def visit_TmTrue(term, ctx):
        return TyBool()

    def visit_TmFalse(term, ctx):
        return TyBool()

    def visit_TmIf(term, ctx):
        typeCond = typeof(term.term_condition, ctx)
        if type(typeCond) is TyBool:
            typeThen = typeof(term.term_then, ctx)
            typeElse = typeof(term.term_else, ctx)
            if type(typeThen) == type(typeElse):
                return typeThen
            else:
                raise RuntimeError(
                    term.info, "arms of conditional have different types")
        else:
            raise RuntimeError(term.info, "guard of conditional not a boolean")


typeof = Typeof.visit
