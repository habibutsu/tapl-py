from syntax import *

class NoRuleApplies(RuntimeError):
    pass

def isval(term):
    return isinstance(term, TmAbs)

def evaluate1(ctx, term):
    if isinstance(term, TmApp):
        if isval(term.left) and isval(term.right):
            return termSubstTop(term.right, term.left.term)
        elif isval(term.left):
            right = evaluate1(ctx, term.right)
            return TmApp(term.info, term.left, right)
        else:
            left = evaluate1(ctx, term.left)
            return TmApp(term.info, left, term.right)
    else:
        raise NoRuleApplies

def evaluate(ctx, term):
    try:
        return evaluate(ctx, evaluate1(ctx, term))
    except NoRuleApplies:
        return term