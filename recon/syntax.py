from collections import namedtuple

# ----------------------------------------------------------------------
# Datatypes

# Types

TyBool = namedtuple("TyBool", [])
TyNat = namedtuple("TyNat", [])
TyArr = namedtuple("TyArr", ["left", "right"])
TyId = namedtuple("TyId", ["name"])


# Terms

TmTrue = namedtuple("TmTrue", ["info"])
TmFalse = namedtuple("TmFalse", ["info"])
TmIf = namedtuple("TmIf", ["info", "term_condition", "term_then", "term_else"])
TmZero = namedtuple("TmZero", ["info"])
TmSucc = namedtuple("TmSucc", ["info", "term"])
TmPred = namedtuple("TmPred", ["info", "term"])
TmIsZero = namedtuple("TmIsZero", ["info", "term"])
TmVar = namedtuple("TmVar", ["info", "index", "ctxlength"])
TmAbs = namedtuple("TmAbs", ["info", "name", "type", "term"])
TmApp = namedtuple("TmApp", ["info", "left", "right"])

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
        type_t = type(t)
        if type_t is TmVar:
            return onvar(t.info, c, t.index, t.ctxlength)
        elif type_t is TmAbs:
            return TmAbs(t.info, t.name, t.type, walk((c+1), t.term))
        elif type_t is TmApp:
            return TmApp(t.info, walk(c, t.left), walk(c, t.right))
        elif type_t is TmTrue:
            return t
        elif type_t is TmFalse:
            return t
        elif type_t is TmIf:
            return TmIf(
                t.info,
                walk(c, t.term_condition),
                walk(c, t.term_then),
                walk(c, t.term_else))
        elif type_t is TmZero:
            return t
        elif type_t is TmSucc:
            return TmSucc(t.info, walk(c, t.term))
        elif type_t is TmPred:
            return TmPred(t.info, walk(c, t.term))
        elif type_t is TmIsZero:
            return TmIsZero(t.info, walk(c, t.term))
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
        method_name = 'visit_' + term.__class__.__name__
        default_name = getattr(cls, 'visit_ANY', None)
        method = getattr(cls, method_name, default_name)

        if method is None:
            raise AttributeError(
                "type object '%s' has no attribute '%s'" %
                (cls.__name__, method_name))
        return method(term, *args, **kwargs)


class TypesPrinter(Visitor):

    def visit_TyArr(self):
        printty(self.left)
        print(" -> ", end="")
        printty(self.right)

    def visit_TyBool(self):
        print("Bool", end="")

    def visit_TyNat(self):
        print("Nat", end="")

    def visit_TyId(self):
        print(self.name, end="")


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

    def visit_TmIf(self, ctx):
        print("if", end="")
        printtm(self.term_condition, ctx)
        print(" then ", end="")
        printtm(self.term_then, ctx)
        print(" else ", end="")
        printtm(self.term_else, ctx)

    def visit_TmPred(self, ctx):
        print("pred ", end="")
        printtm(self.term)

    def visit_TmIsZero(self, ctx):
        print("iszero ", end="")
        printtm(self.term)

    def visit_TmZero(self, ctx):
        print("0", end="")

    def visit_TmSucc(self, ctx):
        num = 1
        t = self
        while type(t.term) is TmSucc:
            num += 1
            t = t.term
        if type(t.term) is TmZero:
            print(str(num), end="")
        else:
            print("(succ ", end="")
            printtm(t.term, ctx)
            print(")", end="")

printtm = TermsPrinter.visit
