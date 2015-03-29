from collections import namedtuple

# ----------------------------------------------------------------------
# Datatypes

# Types

TyVar = namedtuple("TyVar", ["index", "ctxlength"])
TyId = namedtuple("TyId", ["name"])
TyArr = namedtuple("TyArr", ["left", "right"])
TyUnit = namedtuple("TyUnit", [])
TyRecord = namedtuple("TyRecord", ["fields"])
TyVariant = namedtuple("TyVariant", ["fields"])
TyBool = namedtuple("TyBool", [])
TyString = namedtuple("TyString", [])
TyFloat = namedtuple("TyFloat", [])
TyNat = namedtuple("TyNat", [])

# Terms

TmTrue = namedtuple("TmTrue", ["info"])
TmFalse = namedtuple("TmFalse", ["info"])
TmIf = namedtuple("TmIf", ["info", "term_condition", "term_then", "term_else"])
TmCase = namedtuple("TmCase", ["info", "term", "cases"])
TmTag = namedtuple("TmTag", ["info", "tag", "term", "type"])
TmVar = namedtuple("TmVar", ["info", "index", "ctxlength"])
TmAbs = namedtuple("TmAbs", ["info", "name", "type", "term"])
TmApp = namedtuple("TmApp", ["info", "left", "right"])
TmLet = namedtuple("TmLet", ["info", "name", "let_term", "in_term"])
TmFix = namedtuple("TmFix", ["info", "term"])
TmString = namedtuple("TmString", ["info", "value"])
TmUnit = namedtuple("TmUnit", ["info"])
TmAscribe = namedtuple("TmAscribe", ["info", "term", "type"])
TmRecord = namedtuple("TmRecord", ["info", "fields"])
TmProj = namedtuple("TmProj", ["info", "term", "name"])
TmFloat = namedtuple("TmFloat", ["info", "value"])
TmTimesfloat = namedtuple("TmTimesfloat", ["info", "term1", "term2"])
TmZero = namedtuple("TmZero", ["info"])
TmSucc = namedtuple("TmSucc", ["info", "term"])
TmPred = namedtuple("TmPred", ["info", "term"])
TmIsZero = namedtuple("TmIsZero", ["info", "term"])
TmInert = namedtuple("TmInert", ["info", "term"])

# Bindings

NameBind = namedtuple("NameBind", [])
TyVarBind = namedtuple("TyVarBind", [])
VarBind = namedtuple("VarBind", ["type"])
TmAbbBind = namedtuple("TmAbbBind", ["term", "type"])
TyAbbBind = namedtuple("TyAbbBind", ["type"])

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
    raise ValueError("Identifier '%s' is unbound" % name)

# ----------------------------------------------------------------------
# Shifting

def tymap(onvar, c, tyT):
    def walk(c, tyT):
        t_tyT = type(tyT)
        if t_tyT is TyVar:
            return onvar(c, tyT.index, tyT.ctxlength)
        elif t_tyT is TyId:
            return tyT
        elif t_tyT is TyString:
            return tyT
        elif t_tyT is TyUnit:
            return tyT
        elif t_tyT is TyRecord:
            fields = [(li, walk(c, tyTi)) for li, tyTi in tyT.fields]
            return TyRecord(fields)
        elif t_tyT is TyFloat:
            return tyT
        elif t_tyT is TyBool:
            return tyT
        elif t_tyT is TyNat:
            return tyT
        elif t_tyT is TyArr:
            left = walk(c, tyT.left)
            right = walk(c, tyT.right)
            return TyArr(left, right)
        elif t_tyT is TyVariant:
            fields = [(li, walk(c, tyTi)) for li, tyTi in tyT.fields]
            return TyVariant(fields)

    return walk(c, tyT)

def tmmap(onvar, c, t):
    def walk(c, t):
        ty_t = type(t)
        if ty_t is TmVar:
            return onvar(t.info, c, t.index, t.ctxlength)
        elif ty_t is TmAbs:
            return TmAbs(t.info, t.name, t.type, walk((c+1), t.term))
        elif ty_t is TmApp:
            return TmApp(t.info, walk(c, t.left), walk(c, t.right))
        elif ty_t is TmTrue:
            return t
        elif ty_t is TmFalse:
            return t
        elif ty_t is TmString:
            return t
        elif ty_t is TmIf:
            return TmIf(
                t.info,
                walk(c, t.term_condition),
                walk(c, t.term_then),
                walk(c, t.term_else))
        elif ty_t is TmRecord:
                fields = [(li, walk(c, ti)) for li, ti in t.fields]
                return TmRecord(t.info, fields)
        elif ty_t is TmTag:
            return TmTag(
                t.info,
                t.name,
                walk(c, t.term),
                ontype(c, t.type))
        elif ty_t is TmProj:
            pass
        raise NotImplementedError(t)
    return walk(c, t)

def typeShiftAbove(d, c, tyT):
    return tymap(
        lambda c, x, n: TyVar(x+d, n+d) if x >= c else TyVar(x, n+d),
        c, tyT
    )

def termShiftAbove(d, c, t):
    return tmmap(
        lambda info, c, x, n: TmVar(info, x+d, n+d) if x >= c else TmVar(info, x, n+d),
        c, t
    )

def typeShift(d, tyT):
    return typeShiftAbove(d, 0, tyT)

def termShift(d, t):
    return termShiftAbove(d, 0, t)


def bindingshift(d, bind):
    tyb = type(bind)
    if tyb is NameBind:
        return bind
    elif tyb is TyVarBind:
        return bind
    elif tyb is VarBind:
        return VarBind(typeShift(d, bind.type))
    elif tyb is TyAbbBind:
        return TyAbbBind(typeShift(d, bind.type))
    elif tyb is TmAbbBind:
        tyT_opt = typeShift(d, bind.type) if bind.type else None
        return TmAbbBind(termShift(d, bind.term), tyT_opt)
    raise NotImplementedError(bind)

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
    return bindingshift(index+1, binding)

def getTypeFromContext(ctx, index):
    binding = getbinding(ctx, index)
    typeb = type(binding)
    if typeb is VarBind:
        return binding.type
    elif typeb is TmAbbBind:
        if binding.type:
            return binding.type
        raise RuntimeError(
            "No type recorded for variable '%s'" % index2name(ctx, index))
    else:
        raise RuntimeError(
            "Wrong kind of binding for variable %s" % index2name(ctx, index))
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
        method = getattr(cls, method_name, getattr(cls, 'visit__', None))

        if method is None:
            raise AttributeError(
                "type object '%s' has no attribute '%s'" %
                (cls.__name__, method_name))
        return method(term, *args, **kwargs)


class TypesPrinter(Visitor):

    def visit_TyVar(self, ctx):
        if len(ctx) == self.ctxlength:
            print(index2name(ctx, self.index), end="")
        else:
            print(
                "[bad index: " + str(self.index) + "/" + str(self.ctxlength)
                + " in {" + " ".join(map(str, ctx)) + " }]")

    def visit_TyId(self, ctx):
        raise NotImplementedError()

    def visit_TyArr(self, ctx):
        printty(self.left, ctx)
        print(" -> ", end="")
        printty(self.right, ctx)

    def visit_TyUnit(self,ctx):
        print("Unit", end="")

    def visit_TyRecord(self, ctx):
        print("{", end="")
        fields_length = len(self.fields)-1
        for (num, (name, tyT)) in enumerate(reversed(self.fields)):
            if type(name) is str:
                print(name + ":", end="")
            printty(tyT, ctx)
            if num < fields_length:
                print(",", end="")
        print("}", end="")

    def visit_TyVariant(self, ctx):
        print("<", end="")
        fields_length = len(self.fields)-1
        for (num, (name, tyT)) in enumerate(reversed(self.fields)):
            print(name + ":", end="")
            printty(tyT, ctx)
            if num < fields_length:
                print(",", end="")
        print(">", end="")

    def visit_TyBool(self, ctx):
        print("Bool", end="")

    def visit_TyString(self, ctx):
        print("String", end="")

    def visit_TyFloat(self, ctx):
        print("Float", end="")

    def visit_TyNat(self, ctx):
        print("Nat", end="")

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
        printty(self.type, ctx)
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

    def visit_TmTag(self, ctx):
        print("Tag", self)

    def visit_TmIf(self, ctx):
        print("if", end="")
        printtm(self.term_condition)
        print(" then ", end="")
        printtm(self.term_then)
        print(" else")

    def visit_TmString(self, ctx):
        print("\"" + self.value + "\"", end="")

    def visit_TmRecord(self, ctx):
        print("{", end="")
        fields_length = len(self.fields)-1
        for (num, (name, term)) in enumerate(reversed(self.fields)):
            if type(name) is str:
                print(name + "=", end="")
            printtm(term, ctx)
            if num < fields_length:
                print(",", end="")
        print("}", end="")


printtm = TermsPrinter.visit
