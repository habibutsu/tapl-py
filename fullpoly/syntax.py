from collections import namedtuple

# ----------------------------------------------------------------------
# Datatypes

# Types

TyVar = namedtuple("TyVar", ["index", "ctxlength"])
TyId = namedtuple("TyId", ["name"])
TyArr = namedtuple("TyArr", ["left", "right"])
TyString = namedtuple("TyString", [])
TyUnit = namedtuple("TyUnit", [])
TyRecord = namedtuple("TyRecord", ["fields"])
TyBool = namedtuple("TyBool", [])
TyFloat = namedtuple("TyFloat", [])
TyNat = namedtuple("TyNat", [])
TySome = namedtuple("TySome", ["name", "type"])
TyAll = namedtuple("TyAll", ["name", "type"])

# Terms
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
TmTrue = namedtuple("TmTrue", ["info"])
TmFalse = namedtuple("TmFalse", ["info"])
TmIf = namedtuple("TmIf", ["info", "term_condition", "term_then", "term_else"])
TmFloat = namedtuple("TmFloat", ["info", "value"])
TmTimesfloat = namedtuple("TmTimesfloat", ["info", "term1", "term2"])
TmZero = namedtuple("TmZero", ["info"])
TmSucc = namedtuple("TmSucc", ["info", "term"])
TmPred = namedtuple("TmPred", ["info", "term"])
TmIsZero = namedtuple("TmIsZero", ["info", "term"])
TmInert = namedtuple("TmInert", ["info", "type"])
TmPack = namedtuple("TmPack", ["info", "witness_type", "term", "type"])
TmUnpack = namedtuple("TmUnpack", ["info", "ty_name", "var_name", "let_term", "in_term"])
TmTAbs = namedtuple("TmTAbs", ["info", "name", "term"])
TmTApp = namedtuple("TmTApp", ["info", "term", "type"])

# Bindings
NameBind = namedtuple("NameBind", [])
TyVarBind = namedtuple("TyVarBind", [])
VarBind = namedtuple("VarBind", ["type"])
TmAbbBind = namedtuple("TmAbbBind", ["term", "type"])
TyAbbBind = namedtuple("TyAbbBind", ["type"])

# Commands

Eval = namedtuple("Eval", ["info", "term"])
Bind = namedtuple("Bind", ["info", "name", "binding"])
SomeBind = namedtuple("SomeBind", ["info", "ty_name", "var_name", "term"])

class Info(namedtuple("Info", ["filename", "lineno"])):

    def __repr__(self):
        return '<%s:%s>' % self

# ----------------------------------------------------------------------
# Tools


def when(guard):

    def when_decorator(func):
        func.guard = guard
        return func

    return when_decorator


class PairVisitor:

    def visit(self, term1, term2, *args, **kwargs):
        props = [
            "visit_%s_%s" % (
                type(term1).__name__,
                type(term2).__name__),
            "visit_%s__" % type(term1).__name__,
            "visit__%s" % type(term2).__name__,
            "visit__"]

        method = None
        for method_name in props:
            method = getattr(self, method_name, None)
            if method is not None:

                has_guard = hasattr(method, "guard")
                if has_guard:
                    if method.guard(self, term1, term2):
                        return method(term1, term2, *args, **kwargs)
                else:
                    return method(term1, term2, *args, **kwargs)

        raise AttributeError(
            "Object '%s' has no suitable attribute for '%s', '%s'" %
            (type(self).__name__, term1, term2))


class Visitor:

    def visit(self, term, *args, **kwargs):
        method_name = 'visit_' + type(term).__name__
        method = getattr(
            self, method_name,
            getattr(self, 'visit__', None))

        if method is None:
            raise AttributeError(
                "Object '%s' has no suitable attribute for '%s'" %
                (type(self).__name__, term))
        return method(term, *args, **kwargs)

# ----------------------------------------------------------------------
# Context management

from contextlib import contextmanager

# Experimental alternative implementation of context
class Context:

    def __init__(self):
        self._storage = []
        self._map = {}

    def __getitem__(self, index):
        try:
            return self._storage[-1 - index]
        except IndexError:
            raise RuntimeError(
                "Variable lookup failure: offset: %d, ctx size: %d" %
                (index, len(self._storage)))

    def __len__(self):
        return len(self._storage)

    @contextmanager
    def mgr_addbinding(self, name, bind):
        self.addbinding(name, bind)
        yield
        self.pop()

    def addbinding(self, name, bind):
        self._storage.append((name, bind))
        self._map[name] = len(self._storage) - 1

    def pop(self):
        (name, _) = self._storage.pop()
        del self._map[name]

    def addname(self, name):
        return self.addbinding(name, NameBind())

    def isnamebound(self, name):
        return name in self._map

    def name2index(self, name):
        """
        pos:   0, 1, 2, 3
        index: 3, 2, 1, 0
        items: A, B, C, D

        A -> 4-(0+1) = 3
        B -> 4-(1+1) = 2
        ...
        """
        if not self.isnamebound:
            raise ValueError("Identifier '%s' is unbound" % name)

        pos = self._map[name] + 1
        return len(self._storage) - pos

    def index2name(self, index):
        (name, _) = self[index]
        return name

    def pickfreshname(self, name):
        new_name = str(name)
        while self.isnamebound(new_name):
            new_name += "'"
        return new_name

@contextmanager
def mgr_addbinding(ctx, name, bind):
    ctx.append((name, bind))
    yield
    ctx.pop()

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

@contextmanager
def mgr_pickfreshname(ctx, name):
    new_name = str(name)
    while isnamebound(ctx, new_name):
        new_name += "'"
    addname(ctx, new_name)
    yield new_name
    ctx.pop()

def pickfreshname(ctx, name):
    new_name = str(name)
    while isnamebound(ctx, new_name):
        new_name += "'"
    return (ctx + [(new_name, NameBind())], new_name)

def get_ctx_item(ctx, index):
    try:
        return ctx[-1 - index]
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

"""
The shifting function below takes a "cutoff" parameter
'c' that controls which variables should be shifted.
It starts off at 0 (meaning all variables should be shifted)
and gets incremented by one every time the shifting function
goes through a binder (see section 6.2 Shifting and Substitution)
"""

class TypeMap(Visitor):
    """
    Analogue of function 'tymap' from ML-implementation
    """

    cutoff = None
    onvar = None

    def __init__(self, cutoff, onvar):
        self.cutoff = cutoff
        self.onvar = onvar

    @contextmanager
    def inc_cutoff(self):
        self.cutoff += 1
        yield
        self.cutoff -= 1

    def visit_TyVar(self, tyT):
        return self.onvar(
            self.cutoff, tyT.index, tyT.ctxlength)

    def visit_TyId(self, tyT):
        return tyT

    def visit_TyString(self, tyT):
        return tyT

    def visit_TyUnit(self, tyT):
        return tyT

    def visit_TyFloat(self, tyT):
        return tyT

    def visit_TyBool(self, tyT):
        return tyT

    def visit_TyNat(self, tyT):
        return tyT

    def visit_TyArr(self, tyT):
        left = self.visit(tyT.left)
        right = self.visit(tyT.right)
        return TyArr(left, right)

    def visit_TySome(self, tyT):
        with self.inc_cutoff():
            return TySome(tyT.name, self.visit(tyT.type))

    def visit_TyAll(self, tyT):
        with self.inc_cutoff():
            return TyAll(tyT.name, self.visit(tyT.type))

    def visit_TyRecord(self, tyT):
        fields = [(li, self.visit(tyTi)) for li, tyTi in tyT.fields]
        return TyRecord(fields)


class TermMap(Visitor):
    """
    Analogue of function 'tmmap' from ML-implementation
    """
    cutoff = None
    onvar = None
    ontype = None

    def __init__(self, cutoff, onvar, ontype):
        self.cutoff = cutoff
        self.onvar = onvar
        self.ontype = ontype

    @contextmanager
    def inc_cutoff(self):
        self.cutoff += 1
        yield
        self.cutoff -= 1

    def visit_TmInert(self, t):
        return TmInert(tyT.info, self.ontype(self.cutoff, tyT))

    def visit_TmVar(self, t):
        return self.onvar(t.info, self.cutoff, t.index, t.ctxlength)

    def visit_TmAbs(self, t):
        with self.inc_cutoff():
            term = self.visit(t.term)
        return TmAbs(
            t.info, t.name,
            self.ontype(self.cutoff, t.type), term)

    def visit_TmApp(self, t):
        return TmApp(t.info, self.visit(t.left), self.visit(t.right))

    def visit_TmLet(self, t):
        let_term = self.visit(t.let_term)
        with self.inc_cutoff():
            in_term = self.visit(t.in_term)
        return t._replace(let_term=let_term, in_term=in_term)

    def visit_TmFix(self, t):
        return t._replace(term=self.visit(t.term))

    def visit_TmString(self, t):
        return t

    def visit_TmUnit(self, t):
        return t

    def visit_TmTrue(self, t):
        return t

    def visit_TmFalse(self, t):
        return t

    def visit_TmIf(self, t):
        return TmIf(
                t.info,
                self.visit(t.term_condition),
                self.visit(t.term_then),
                self.visit(t.term_else))

    def visit_TmAscribe(self, t):
        raise NotImplementedError

    def visit_TmFloat(self, t):
        return t

    def visit_TmTimesfloat(self, t):
        raise NotImplementedError

    def visit_TmZero(self, t):
        return t

    def visit_TmSucc(self, t):
        raise NotImplementedError

    def visit_TmPred(self, t):
        raise NotImplementedError

    def visit_TmIsZero(self, t):
        raise NotImplementedError

    def visit_TmPack(self, t):
        raise NotImplementedError

    def visit_TmUnpack(self, t):
        raise NotImplementedError

    def visit_TmTAbs(self, t):
        with self.inc_cutoff():
            return TmTAbs(t.info, t.name, self.visit(t.term))

    def visit_TmTApp(self, t):
        return TmTApp(
            self.info,
            self.visit(t.term),
            self.ontype(self.cutoff, t.type))

    def visit_TmProj(self, t):
        return t._replace(
            term=self.visit(t.term))

    def visit_TmRecord(self, t):
        fields = [(li, self.visit(ti)) for li, ti in t.fields]
        return TmRecord(t.info, fields)


def typeShiftAbove(d, c, tyT):
    """
    The d-place shift of a term t above cutoff c
    """
    tymap = TypeMap(
        onvar=lambda c, x, n: TyVar(x+d, n+d) if x >= c else TyVar(x, n+d),
        cutoff=c)
    return tymap.visit(tyT)

def termShiftAbove(d, c, t):
    tmmap = TermMap(
        cutoff = c,
        onvar = lambda info, c, x, n: \
            TmVar(info, x+d, n+d) if x >= c else TmVar(info, x, n+d),
        ontype = lambda c, tyT: typeShiftAbove(d, c, tyT)
        )
    return tmmap.visit(t)

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
    tmmap = TermMap(
        cutoff = j,
        onvar = lambda info, c, x, n: \
            termShift(c, s) if x == j+c else TmVar(info, x, n),
        ontype = lambda j, tyT: tyT,
        )
    return tmmap.visit(t)

def termSubstTop(s, t):
    return termShift(-1, termSubst(0, termShift(1, s), t))

def typeSubst(tyS, j, tyT):
    tymap = TypeMap(
        onvar=lambda j, x, n: \
            typeShift(j, tyS) if x == j else TyVar(x, n),
        cutoff=j)
    return tymap.visit(tyT)


def typeSubstTop(tyS, tyT):
    return typeShift(
        -1, typeSubst(typeShift(1, tyS), 0, tyT))

def tytermSubst(tyS, j, t):
    tmmap = TermMap(
        onvar = lambda info, c, x, n: TmVar(info, x, n),
        ontype = lambda j, tyT: typeSubst(tyS, j, tyT),
        cutoff = j
    )
    return tmmap.visit(t)

def tytermSubstTop(tyS, t):
    return termShift(-1, tytermSubst(typeShift(1, tyS), 0, t))

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


class TypesPrinter(Visitor):

    # Type

    def visit_TyAll(self, term):
        with mgr_pickfreshname(self.ctx, term.name) as name:
            print("All ", end="")
            print(name, end="")
            print(".", end="")
            printty(self.ctx, term.type)

    # ArrowType

    def visit_TyArr(self, term):
        printty(self.ctx, term.left)
        print(" -> ", end="")
        printty(self.ctx, term.right)

    # AType

    def visit_TyVar(self, term):
        if len(self.ctx) == term.ctxlength:
            print(index2name(self.ctx, term.index), end="")
        else:
            print(
                "[bad index: " + str(term.index) + "/" + str(term.ctxlength)
                + " in {" + " ".join(map(str, self.ctx)) + " }]")

    def visit_TyId(self, term):
        print(term.name, end="")

    def visit_TyString(self, term):
        print("String", end="")

    def visit_TyUnit(self, term):
        print("Unit", end="")

    def visit_TyRecord(self, term):
        print("{", end="")
        fields_length = len(term.fields)-1
        for (num, (name, tyT)) in enumerate(reversed(term.fields)):
            if type(name) is str:
                print(name + ":", end="")
            printty(self.ctx, tyT)
            if num < fields_length:
                print(",", end="")
        print("}", end="")

    def visit_TyBool(self, term):
        print("Bool", end="")

    def visit_TyFloat(self, term):
        print("Float", end="")

    def visit_TyNat(self, term):
        print("Nat", end="")

    def visit_TySome(self, term):
        with mgr_pickfreshname(self.ctx, term.name) as name:
            print("{Some ", end="")
            print(name, end="")
            print(".", end="")
            printty(self.ctx, term.type)
            print("}", end="")


def printty(ctx, term):
    visitor = TypesPrinter()
    visitor.ctx = ctx
    visitor.visit(term)


class TermsPrinter(Visitor):

    def visit_TmVar(self, term):
        if len(self.ctx) == term.ctxlength:
            print(index2name(self.ctx, term.index), end="")
        else:
            print(
                "[bad index: " + str(term.index) + "/" + str(term.ctxlength)
                + " in {" + ",".join(map(str, self.ctx)) + " }]")

    def visit_TmAbs(self, term):
        (new_ctx, name) = pickfreshname(self.ctx, term.name)
        print("(", end="")
        print("lambda %s" % name, end="")
        print(": ", end="")
        printty(self.ctx, term.type)
        print(" . ", end="")
        printtm(new_ctx, term.term)
        print(")", end="")

    # AppTerm

    def visit_TmTAbs(self, term):
        (new_ctx, name) = pickfreshname(self.ctx, term.name)
        print("lambda ", end="")
        print(name, end="")
        print(".", end="")
        printtm(new_ctx, term.term)

    def visit_TmApp(self, term):
        print("(", end="")
        printtm(self.ctx, term.left)
        print(" ", end="")
        printtm(self.ctx, term.right)
        print(")", end="")

    def visit_TmTimesfloat(self, term):
        raise NotImplementedError

    def visit_TmPred(self, term):
        raise NotImplementedError

    def visit_TmIsZero(self, term):
        raise NotImplementedError

    def visit_TmTag(self, term):
        print("Tag", term)

    def visit_TmIf(self, term):
        print("if", end="")
        printtm(self.ctx, term.term_condition)
        print(" then ", end="")
        printtm(self.ctx, term.term_then)
        print(" else")

    # ATerm

    def visit_TmString(self, term):
        print("\"" + self.value + "\"", end="")

    def visit_TmUnit(self, term):
        raise NotImplementedError

    def visit_TmRecord(self, term):
        print("{", end="")
        fields_length = len(term.fields)-1
        for (num, (name, term)) in enumerate(reversed(term.fields)):
            if type(name) is str:
                print(name + "=", end="")
            printtm(self.ctx, term)
            if num < fields_length:
                print(",", end="")
        print("}", end="")

    def visit_TmTrue(self, term):
        print("true", end="")

    def visit_TmFalse(self, term):
        print("false", end="")

    def visit_TmFloat(self, term):
        print(term.value, end="")

    def visit_TmZero(self, term):
        print("0", end="")

    def visit_TmSucc(self, term):
        raise NotImplementedError

    def visit_TmPack(self, term):
        print("{*", end="")
        printty(self.ctx, term.witness_type)
        print(",", end="")
        self.visit(term.term)
        print("} as ", end="")
        printty(self.ctx, term.type)


def printtm(ctx, term):
    visitor = TermsPrinter()
    visitor.ctx = ctx
    visitor.visit(term)
