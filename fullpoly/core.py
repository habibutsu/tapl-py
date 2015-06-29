from syntax import *
# ------------------------   EVALUATION  ------------------------

class NoRuleApplies(RuntimeError):
    pass

def isnumericval(term):
    ty_term = type(term)
    if ty_term is TmZero:
        return True
    elif ty_term is TmSucc:
        isnumericval(term.term)
    return False

def isval(term):
    val_terms = [
        TmString,
        TmUnit,
        TmTrue,
        TmFalse,
        TmFloat,
        TmAbs,
        TmTAbs]
    ty_term = type(term)

    if ty_term in val_terms:
        return True
    elif isnumericval(term):
        return True
    elif ty_term is TmRecord:
        return all(map(lambda t: isval(t[1]), term.fields))
    elif ty_term is TmPack:
        return isval(term.term)
    else:
        return False

class Evaluate(Visitor):

    def visit_TmApp(self, term):
        if isval(term.left) and isval(term.right):
            return termSubstTop(term.right, term.left.term)
        elif isval(term.left):
            right = self.visit(term.right)
            return TmApp(term.info, term.left, right)
        else:
            left = self.visit(term.left)
            return TmApp(term.info, left, term.right)

    def visit_TmLet(self, term):
        if isval(term.let_term):
            return termSubstTop(term.let_term, term.in_term)
        let_term = self.visit(term.let_term)
        return TmLet(term.info, term.name, let_term, term.in_term)

    def visit_TmFix(self, term):
        raise NotImplementedError

    def visit_TmAscribe(self, term):
        raise NotImplementedError

    def visit_TmRecord(self, term):
        for (num, field) in enumerate(term.fields):
            f_term = self.visit(field[1])
            term.fields[num] = (field[0], f_term)
        return term

    def visit_TmProj(self, term):
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
            new_term = self.visit(term.term)
            return term._replace(term=new_term)
        raise NoRuleApplies

    def visit_TmIf(self, term):
        if isinstance(term.term_condition, TmTrue):
            return term.term_then
        elif isinstance(term.term_condition, TmFalse):
            return term.term_else
        else:
            new_term_condition = evaluate(self.ctx, term.term_condition)
            return TmIf(
                term.info,
                new_term_condition,
                term.term_then, term.term_else)

    def visit_TmTimesfloat(self, term):
        raise NotImplementedError

    def visit_TmSucc(self, term):
        raise NotImplementedError

    def visit_TmPred(self, term):
        raise NotImplementedError

    def visit_TmIsZero(self, term):
        raise NotImplementedError

    def visit_TmUnpack(self, term):

        if (type(term.let_term) is TmPack and
                isval(term.let_term.term)):
            return tytermSubstTop(
                term.let_term.witness_type,
                termSubstTop(
                    termShift(1, term.let_term.term),
                    term.in_term))

        new_term = self.visit(term.let_term)
        return self._replace(let_term=let_term)


    def visit_TmPack(self, term):
        new_term = self.visit(term.term)
        return term._replace(term=new_term)

    def visit_TmVar(self, term):
        b = getbinding(self.ctx, term.index)
        if type(b) is TmAbbBind:
            return b.term
        raise NoRuleApplies()

    def visit_TmTApp(self, term):
        if type(term.term) is TmTAbs:
            term_TmTAbs = term.term
            return tytermSubstTop(
                term.type, term_TmTAbs.term)
        new_term = self.visit(term.term)
        return term._replace(term=new_term)

    def visit__(self, term):
        raise NoRuleApplies

def evaluate1(ctx, term):
    visitor = Evaluate()
    visitor.ctx = ctx
    return visitor.visit(term)


def evaluate(ctx, term):
    eval_visitor = Evaluate()
    eval_visitor.ctx = ctx
    try:
        new_term = eval_visitor.visit(term)
        return evaluate(ctx, new_term)
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


class TypeEqVisitor(PairVisitor):

    simple_types = [
        TyString,
        TyUnit,
        TyFloat,
        TyBool,
        TyNat
    ]

    def visit__(self, tyS, tyT):
        """if types are equal and simple"""
        return (
            type(tyS) == type(tyT) and
            type(tyS) in self.simple_types)

    def visit_TyId_TyId(self, tyS, tyT):
        return tyS.name == tyT.name

    @when(lambda self, tyS, tyT: istyabb(self.ctx, tyS.index))
    def visit_TyVar__(self, tyS, tyT):
        return tyeqv(
            self.ctx, gettyabb(self.ctx, tyS.index), tyT)

    @when(lambda self, tyS, tyT: istyabb(self.ctx, tyT.index))
    def visit__TyVar(self, tyS, tyT):
        return tyeqv(
            self.ctx, tyS, gettyabb(self.ctx, tyT.index))

    def visit_TyVar_TyVar(self, tyS, tyT):
        return tyS.index == tyT.index

    def visit_TyArr_TyArr(self, tyS, tyT):
        return (
            tyeqv(self.ctx, tyS.left, tyT.left) and
            tyeqv(self.ctx, tyS.right, tyT.right))

    def visit_TySome_TySome(self, tyS, tyT):
        raise NotImplementedError

    def visit_TyRecord_TyRecord(self, tyS, tyT):
        if len(tyS.fields) != len(tyT.fields):
            return False
        # NOTE: positionally dependent
        # See notes in 11.8 Records
        for ((name1, tyS1), (name2,tyT1)) in zip(tyS.fields, tyT.fields):
            if not tyeqv(self.ctx, tyS1, tyT1):
                return False
        return True

    def visit_TyAll_TyAll(self, tyS, tyT):
        with mgr_addbinding(self.ctx, tyS.name, NameBind()):
            return self.visit(tyS.type, tyT.type)

def tyeqv(ctx, tyS, tyT):
    tyS = simplifyty(ctx, tyS)
    tyT = simplifyty(ctx, tyT)
    visitor = TypeEqVisitor()
    visitor.ctx = ctx
    return visitor.visit(tyS, tyT)

# ------------------------   TYPING  ------------------------

class Typeof(Visitor):

    def visit_TmVar(self, term):
        return getTypeFromContext(self.ctx, term.index)

    def visit_TmAbs(self, term):

        with mgr_addbinding(self.ctx, term.name, VarBind(term.type)):
            typeLeft = term.type
            typeRight = self.visit(term.term)

        # Note - Since types now contain variables, we
        # need to perform shift on -1
        return TyArr(typeLeft, typeShift(-1, typeRight))

    def visit_TmApp(self, term):
        typeLeft = self.visit(term.left)
        typeRight = self.visit(term.right)
        typeLeft_ = simplifyty(self.ctx, typeLeft)
        if isinstance(typeLeft_, TyArr):
            if tyeqv(self.ctx, typeRight, typeLeft_.left):
                return typeLeft_.right
            else:
                raise RuntimeError(
                    "Parameter type mismatch",
                    term.info, typeLeft, typeRight)
        else:
            raise RuntimeError("Arrow type expected")

    def visit_TmLet(self, term):
        raise NotImplementedError

    def visit_TmLet(self, term):
        raise NotImplementedError

    def visit_TmFix(self, term):
        raise NotImplementedError

    def visit_TmString(self, term):
        return TyString()

    def visit_TmUnit(self, term):
        raise NotImplementedError

    def visit_TmAscribe(self, term):
        raise NotImplementedError

    def visit_TmRecord(self, term):
        fieldtys = [(li, self.visit(ti)) for li, ti in term.fields]
        return TyRecord(fieldtys)

    def visit_TmProj(self, term):
        tyT = self.visit(term.term)
        s_term = simplifyty(self.ctx, tyT)
        if type(s_term) is not TyRecord:
            raise RuntimeError(term.info, "Expected record type")
        for (name, tf) in s_term.fields:
            if name == term.name:
                return tf
        raise RuntimeError(
            term.info, "label " + str(term.name) + " not found")

    def visit_TmTrue(self, term):
        return TyBool()

    def visit_TmFalse(self, term):
        return TyBool()

    def visit_TmIf(self, term):
        typeCond = self.visit(term.term_condition)
        if isinstance(typeCond, TyBool):
            typeThen = self.visit(term.term_then)
            typeElse = self.visit(term.term_else)
            if type(typeThen) == type(typeElse):
                return typeThen
            else:
                raise RuntimeError(
                    term.info, "arms of conditional have different types")
        else:
            raise RuntimeError(term.info, "guard of conditional not a boolean")

    def visit_TmFloat(self, term):
        return TyFloat()

    def visit_TmTimesFloat(self, term):
        raise NotImplementedError

    def visit_TmZero(self, term):
        return TyNat()

    def visit_TmSucc(self, term):
        tyT = self.visit(term.term)
        if tyeqv(selc.ctx, tyT, TyNat()):
            return TyNat()
        RuntimeError(
            term.info, "Argument of 'succ' is not a number")

    def visit_TmPred(self, term):
        tyT = self.visit(term.term)
        if tyeqv(selc.ctx, tyT, TyNat()):
            return TyNat()
        RuntimeError(
            term.info, "Argument of 'pred' is not a number")

    def visit_TmIsZero(self, term):
        tyT = self.visit(term.term)
        if tyeqv(selc.ctx, tyT, TyNat()):
            return TyBool()
        RuntimeError(
            term.info, "Argument of 'iszero' is not a number")

    def visit_TmPack(self, term):
        s_tyT = simplifyty(self.ctx, term.type)
        if type(s_tyT) is not TySome:
            raise RuntimeError(
                term.info, "Existential type expected")

        tyU1 = self.visit(term.term)
        tyU2 = typeSubstTop(term.witness_type, s_tyT.type)
        if tyeqv(self.ctx, tyU1, tyU2):
            return term.type

        raise RuntimeError(
            term.info, "Doesn't match declared type", tyU1, tyU2)

    def visit_TmUnpack(self, term):
        let_tyT = simplifyty(
            self.ctx, self.visit(term.let_term))

        if type(let_tyT) is not TySome:
            raise RuntimeError(
                term.info, "Existential type expected")

        with mgr_addbinding(
                self.ctx, term.ty_name, TyVarBind()):
            with mgr_addbinding(
                    self.ctx, term.var_name, VarBind(let_tyT.type)):
                in_tyT = self.visit(term.in_term)
                return typeShift(-2, in_tyT)

    def visit_TmTAbs(self, term):
        with mgr_addbinding(self.ctx, term.name, TyVarBind()):
            tyT = self.visit(term.term)

        return TyAll(term.name, tyT)

    def visit_TmTApp(self, term):
        tyT = self.visit(term.term)
        s_tyT = simplifyty(self.ctx, tyT)
        if type(s_tyT) is TyAll:
            return typeSubstTop(term.type, s_tyT.type)
        raise RuntimeError(term.info, "Universal type expected")

def typeof(ctx, term):
    visitor = Typeof()
    visitor.ctx = ctx
    return visitor.visit(term)
