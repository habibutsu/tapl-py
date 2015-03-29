from collections import namedtuple

# ----------------------------------------------------------------------
# Datatypes

# Terms

TmVar = namedtuple("TmVar", ["info", "index", "ctxlength"])
TmAbs = namedtuple("TmAbs", ["info", "name", "term"])
TmApp = namedtuple("TmApp", ["info", "left", "right"])

# Bindings

NameBind = namedtuple("NameBind", [])

# Commands

Bind = namedtuple("Bind", ["info", "name", "binding"])
Eval = namedtuple("Eval", ["info", "term"])

# ----------------------------------------------------------------------
# Context management

def addbinding(ctx, name, bind):
    ctx.append((name, bind))
    return ctx

def addname(ctx, name):
    return addbinding(ctx, name, NameBind())

def isnamebound(ctx, name):
    for ctx_name, _ in ctx:
        if ctx_name == name:
            return True
    return False

def pickfreshname(ctx, name):
    new_name = str(name)
    while isnamebound(ctx, new_name):
        new_name += "'"
    return ctx + [(new_name, NameBind())], new_name


def index2name(ctx, index):
    try:
        (name, _) = ctx[len(ctx) - index - 1]
    except IndexError:
        print("Variable lookup failure: offset: %d, ctx size: %d" % (index, len(ctx)))
        raise
    return name

def name2index(ctx, name):
    for index, (v, _) in enumerate(reversed(ctx)):
        if name == v:
            return index
    raise ValueError("Identifier %s is unbound" % name)

# ----------------------------------------------------------------------
# Shifting

def tmmap(onvar, c, t):
    def walk(c, t):
        if isinstance(t, TmVar):
            return onvar(t.info, c, t.index, t.ctxlength)
        elif isinstance(t, TmAbs):
            return TmAbs(t.info, t.name, walk((c+1), t.term))
        elif isinstance(t, TmApp):
            return TmApp(t.info, walk(c, t.left), walk(c, t.right))
    return walk(c, t)

def termShiftAbove(d, c, t):
    return tmmap(
        lambda info, c, x, n: TmVar(info, x+d, n+d) if x >= c else TmVar(info, x, n+d),
        c, t
    )

def termShift(d, t):
    return termShiftAbove(d, 0, t)

# ----------------------------------------------------------------------
# Substitution

def termSubst(j, s, t):
    return tmmap(
        lambda info, c, x, n: termShift(c, s) if x == j+c else TmVar(info, x, n),
        0, t
    )

def termSubstTop(s, t):
    return termShift(-1, termSubst(0, termShift(1, s), t))

# ----------------------------------------------------------------------
# Printing

class Info(namedtuple("Info", ["filename", "lineno"])):

    def __repr__(self):
        return '<%s:%s>' % self


class Visitor:

    @classmethod
    def visit(cls, term, *args, **kwargs):
        method_name = 'visit_' + term.__class__.__name__
        method = getattr(cls, method_name)
        return method(term, *args, **kwargs)


class TermsPrinter(Visitor):

    def visit_TmVar(self, ctx):
        if len(ctx) == self.ctxlength:
            print(index2name(ctx, term.index), end="")
        else:
            print(
                "[bad index: " + str(self.index) + "/" + str(self.ctxlength)
                + " in {" + " ".join(map(str, ctx)) + " }]")

    def visit_TmAbs(self, ctx):
        (_ctx, _name) = pickfreshname(ctx, self.name)
        print("(", end="")
        print("lambda %s." % _name, end="")
        printtm(self.term, _ctx)
        print(")", end="")

    def visit_TmApp(self, ctx):
        print("(", end="")
        printtm(self.left, ctx)
        print(" ", end="")
        printtm(self.right, ctx)
        print(")", end="")

printtm = TermsPrinter.visit

class TermsNoNamePrinter(Visitor):

    def visit_TmVar(self):
        print(self.index, end="")

    def visit_TmAbs(self):
        print("(", end="")
        print("lambda.", end="")
        print_noname(self.term)
        print(")", end="")

    def visit_TmApp(self):
        print("(", end="")
        print_noname(self.left)
        print(" ", end="")
        print_noname(self.right)
        print(")", end="")

printtm_noname = TermsNoNamePrinter.visit