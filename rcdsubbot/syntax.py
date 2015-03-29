from collections import namedtuple

# ----------------------------------------------------------------------
# Datatypes

# Types

TyTop = namedtuple("TyTop", [])
TyBot = namedtuple("TyBot", [])
TyRecord = namedtuple("TyRecord", ["fields"])
TyArr = namedtuple("TyArr", ["left", "right"])


# Terms

TmVar = namedtuple("TmVar", ["info", "index", "ctxlength"])
TmAbs = namedtuple("TmAbs", ["info", "name", "type", "term"])
TmApp = namedtuple("TmApp", ["info", "left", "right"])
TmRecord = namedtuple("TmRecord", ["info", "fields"])
TmProj = namedtuple("TmProj", ["info", "term", "name"])

# Bindings

NameBind = namedtuple("NameBind", [])
VarBind = namedtuple("VarBind", ["type"])

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

def get_ctx_item(ctx, index):
    try:
        return ctx[len(ctx) - index - 1]
    except IndexError:
        raise RuntimeError(
            "Variable lookup failure: offset: %d, ctx size: %d" %
            (index, len(ctx)))

def index2name(ctx, index):
    (name, _) = get_ctx_item(ctx, index)
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
        ty_t = type(t)
        if ty_t is TmVar:
            return onvar(t.info, c, t.index, t.ctxlength)
        elif ty_t is TmAbs:
            return TmAbs(t.info, t.name, t.type, walk((c+1), t.term))
        elif ty_t is TmApp:
            return TmApp(t.info, walk(c, t.left), walk(c, t.right))
        elif ty_t is TmProj:
            return TmProj(t.info,  walk(c, t.term), t.name)
        elif ty_t is TmRecord:
            fields = [(li, walk(c, ti)) for li, ti in t.fields]
            return TmRecord(t.info, fields)
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
# Context management (continued)

def getbinding(ctx, index):
    (_, binding) = get_ctx_item(ctx, index)
    return binding

def getTypeFromContext(ctx, index):
    binding = getbinding(ctx, index)
    if isinstance(binding, VarBind):
        return binding.type
    else:
        raise RuntimeError(
            "Wrong kind of binding for variable %s" % 
            index2name(ctx, index))
        raise

# ----------------------------------------------------------------------
# Printing

class Info(namedtuple("Info", ["filename", "lineno"])):

    def __repr__(self):
        return '<%s:%s>' % self


class Visitor:

    @classmethod
    def visit(cls, term, *args, **kwargs):
        method_name = 'visit_' + type(term).__name__
        method = getattr(cls, method_name, getattr(cls, 'visit__', None))

        if method is None:
            raise AttributeError(
                "type object '%s' has no attribute '%s'" %
                (cls.__name__, method_name))
        return method(term, *args, **kwargs)



class TypesPrinter(Visitor):

    def visit_TyArr(term):
        printty(term.left)
        print(" -> ", end="")
        printty(term.right)

    def visit_TyBool(term):
        print("Bool", end="")

    def visit_TyTop(term):
        print("Top", end="")

    def visit_TyBot(term):
        print("Bot", end="")

printty = TypesPrinter.visit


class TermsPrinter(Visitor):

    def visit_TmVar(self, ctx):
        if len(ctx) == self.ctxlength:
            print(index2name(ctx, self.index), end="")
        else:
            print(
                "[bad index: " + str(self.index) + "/" + str(self.ctxlength)
                + " in {" + " ".join(map(str, ctx)) + " }]")

    def visit_TmAbs(self, ctx):
        (new_ctx, name) = pickfreshname(ctx, self.name)
        print("(", end="")
        print("lambda %s" % name, end="")
        print(": ", end="")
        printty(self.type)
        print(" . ", end="")
        printtm(self.term, new_ctx)
        print(")", end="")

    def visit_TmApp(self, ctx):
        print("(", end="")
        printtm(self.left, ctx)
        print(" ", end="")
        printtm(self.right, ctx)
        print(")", end="")

    def visit_TmTrue(self, ctx):
        print("true", end="")

    def visit_TmFalse(self, ctx):
        print("false", end="")

    def visit_TmIf(self):
        print("if", end="")
        printtm(self.term_condition)
        print(" then ", end="")
        printtm(self.term_then)
        print(" else")


printtm = TermsPrinter.visit
