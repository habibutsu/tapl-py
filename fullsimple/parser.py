
import ply.yacc as yacc

from lexer import Lexer

import syntax

"""
Commands
            : Command SEMI
            | Command SEMI Commands

Command
            : Term
            | UCID TyBinder
            | LCID Binder

Binder
            : COLON Type
            | EQ Term

Type
            : ArrowType

AType       : LPAREN Type RPAREN
            | UCID
            | BOOL
            | LT FieldTypes GT
            | USTRING
            | UUNIT
            | LCURLY FieldTypes RCURLY
            | UFLOAT
            | NAT

TyBinder    :
            | EQ Type

FieldTypes  :
            | NEFieldTypes

NEFieldTypes:
            | FieldType
            | FieldType COMMA NEFieldTypes

FieldType   : LCID COLON Type
            | Type

ArrowType   : AType ARROW ArrowType
            | AType

Term        
            : AppTerm
            | LAMBDA LCID COLON Type new_scope DOT Term end_scope
            | LAMBDA USCORE COLON Type new_scope DOT Term end_scope
            | IF Term THEN Term ELSE Term
            | CASE Term OF Cases
            | LET LCID EQ Term IN Term
            | LET USCORE EQ Term IN Term
            | LETREC LCID COLON Type EQ Term IN Term

AppTerm     
            : PathTerm
            | AppTerm PathTerm
            | FIX PathTerm
            | TIMESFLOAT PathTerm PathTerm
            | SUCC PathTerm
            | PRED PathTerm
            | ISZERO PathTerm

AscribeTerm : ATerm AS Type
            | ATerm

PathTerm    : PathTerm DOT LCID
            | PathTerm DOT INTV
            | Ascribe

TermSeq     : Term
            | Term SEMI TermSeq

ATerm       : LPAREN TermSeq RPAREN
            | LCID
            | TRUE
            | FALSE
            | INERT LSQUARE Type RSQUARE
            | LT LCID EQ Term GT AS Type
            | STRINGV
            | UNIT
            | LCURLY Fields RCURLY
            | FLOATV
            | INTV

Cases
            : Case
            | Case VBAR Cases

Case
            : LT LCID EQ LCID GT DDARROW AppTerm

Fields
            :
            | NEFields

NEFields
            : Field
            | Field COMMA NEFields

Field
            : LCID EQ Term
            | Term
"""

class ParserException:
    pass

class Parser:

    def __init__(self, debug=False):
        self.lexer = Lexer()
        self.tokens = self.lexer.tokens
        self.debug = debug
        self.parser = yacc.yacc(module=self, debug=debug)

    def parse(self, text, filename="", ctx=None):
        self._ctx = ctx or []
        self._scope_comma_cnt = []
        self.filename = filename
        return self.parser.parse(
            text, debug=self.debug, lexer=self.lexer.lexer, tracking=True)

# Commands

    def p_Commands_Command(self, p):
        "Commands : Command SEMI"
        p[0] = [p[1]]
        
    def p_Commands_Command_Commands(self, p):
        "Commands : Command SEMI Commands"
        p[0] = [p[1]] + p[3]

# Command

    def p_Command_Term(self, p):
        "Command : Term"
        p[0] = syntax.Eval(self._info(p), p[1])

    def p_Command_UCID_TyBinder(self, p):
        "Command : UCID TyBinder"
        self.addbinding(p[1], p[2])
        p[0] = syntax.Bind(self._info(p), p[1], p[2])

    def p_Command_LCID_Binder(self, p):
        "Command : LCID Binder"
        self.addbinding(p[1], p[2])
        p[0] = syntax.Bind(self._info(p), p[1], p[2])

# Binder

    def p_Binder_COLON_Type(self, p):
        "Binder : COLON Type"
        p[0] = syntax.VarBind(p[2])

    def p_Binder_EQ_Term(self, p):
        "Binder : EQ Term"
        p[0] = syntax.TmAbbBind(p[2], None)

# Type

    def p_Type(self, p):
        "Type : ArrowType"
        p[0] = p[1]

# AType

    def p_AType_Complex(self, p):
        "AType : LPAREN Type RPAREN"
        p[0] = p[2]

    def p_AType_UCID(self, p):
        "AType : UCID"
        if self.isnamebound(p[1]):
            p[0] = syntax.TyVar(self.name2index(p, p[1]), len(self._ctx))
        else:
            p[0] = syntax.TyId(p[1])

    def p_AType_BOOL(self, p):
        "AType : BOOL"
        p[0] = syntax.TyBool()

    def p_AType_LT_FieldTypes_GT(self, p):
        "AType : LT AType_LT FieldTypes GT AType_GT"
        p[0] = syntax.TyVariant(p[3])

    def p_AType_USTRING(self, p):
        "AType : USTRING"
        p[0] = syntax.TyString()

    def p_AType_UUNIT(self, p):
        "AType : UUNIT"
        p[0] = syntax.TyUnit()

    def p_AType_LCURLY_FieldTypes_RCURLY(self, p):
        "AType : LCURLY AType_LCURLY FieldTypes RCURLY AType_RCURLY"
        p[0] = syntax.TyRecord(p[3])

    def p_AType_UFLOAT(self, p):
        "AType : UFLOAT"
        p[0] = syntax.TyFloat()

    def p_AType_NAT(self, p):
        "AType : NAT"
        p[0] = syntax.TyNat()

    # Helper functions

    def p_AType_LCURLY(self, p):
        "AType_LCURLY :"
        self._scope_comma_cnt.append(0)

    def p_AType_RCURLY(self, p):
        "AType_RCURLY :"
        self._scope_comma_cnt.pop()

    def p_AType_LT(self, p):
        "AType_LT :"
        self._scope_comma_cnt.append(0)

    def p_AType_GT(self, p):
        "AType_GT :"
        self._scope_comma_cnt.pop()

# TyBinder

    def p_TyBinder(self, p):
        "TyBinder :"
        p[0] = syntax.TyVarBind()

    def p_TyBinder_EQ_Type(self, p):
        "TyBinder : EQ Type"
        p[0] = syntax.TyAbbBind(p[2])

# FieldTypes

    def p_FieldTypes(self, p):
        "FieldTypes : "
        p[0] = []

    def p_FieldTypes_NEFieldTypes(self, p):
        "FieldTypes : NEFieldTypes"
        p[0] = p[1]

# NEFieldTypes

    def p_NEFieldTypes_FieldType(self, p):
        "NEFieldTypes : FieldType"
        p[0] = [p[1]]

    def p_NEFieldTypes_FieldType_COMMA_NEFieldTypes(self, p):
        "NEFieldTypes : FieldType COMMA FieldType_comma NEFieldTypes"
        p[4].append(p[1])
        p[0] = p[4]

    def p_FieldType_comma(self, p):
        "FieldType_comma :"
        self._scope_comma_cnt[-1] += 1

# FieldType

    def p_FieldType_LCID_COLON_Type(self, p):
        "FieldType : LCID COLON Type"
        p[0] = (p[1], p[3])

    def p_FieldType_Type(self, p):
        "FieldType : Type"
        i = self._scope_comma_cnt[-1]
        p[0] = (i+1, p[1])

# ArrowType

    def p_ArrowType_Arrow(self, p):
        "ArrowType : AType ARROW ArrowType"
        p[0] = syntax.TyArr(p[1], p[3])

    def p_ArrowType_AType(self, p):
        "ArrowType : AType"
        p[0] = p[1]

# Term

    def p_Term_AppTerm(self, p):
        "Term : AppTerm"
        p[0] = p[1]
        
    def p_Term_IF(self, p):
        "Term : IF Term THEN Term ELSE Term"
        p[0] = syntax.TmIf(self._info(p), p[2], p[4], p[6])

    def p_Term_CASE(self, p):
        "Term : CASE Term OF Cases"
        p[0] = syntax.TmCase(self._info(), p[2], p[4])

    def p_Term_LAMBDA_LCID(self, p):
        "Term : LAMBDA LCID COLON Type lambda_new_scope DOT Term lamda_end_scope"
        p[0] = syntax.TmAbs(
            self._info(p), p[2], p[4], p[7])

    def p_Term_LAMBDA_USCORE(self, p):
        "Term : LAMBDA USCORE COLON Type lambda_new_scope DOT Term lamda_end_scope"
        p[0] = syntax.TmAbs(self._info(p), "_", p[4], p[7])

    def p_lambda_new_scope(self, p):
        "lambda_new_scope :"
        self.addname(p[-3])

    def p_lamda_end_scope(self, p):
        "lamda_end_scope :"
        self._ctx.pop()

    def p_Term_LET_LCID_EQ_Term_IN_Term(self, p):
        "Term : LET LCID EQ Term IN let_new_scope Term let_end_scope"
        p[0] = syntax.TmLet(self._info(p), p[2], p[4], p[6])

    def p_Term_LET_USCORE_EQ_Term_IN_Term(self, p):
        "Term : LET USCORE EQ Term IN let_new_scope Term let_end_scope"
        p[0] = syntax.TmLet(self._info(p), "_", p[4], p[6])

    def p_let_new_scope(self, p):
        "let_new_scope :"
        self.addname(p[-4])

    def p_let_end_scope(self, p):
        "let_end_scope :"
        self._ctx.pop()

    def p_Term_LETREC_LCID_COLON_Type_EQ_Term_IN_Term(self, p):
        "Term : LETREC LCID COLON Type EQ Term IN Term"
        raise NotImplementedError

# AppTerm

    def p_AppTerm_AppTerm_ATerm(self, p):
        "AppTerm : AppTerm PathTerm"
        p[0] = syntax.TmApp(self._info(p), p[1], p[2])

    def p_AppTerm_PathTerm(self, p):
        "AppTerm : PathTerm"
        p[0] = p[1]

    def p_AppTerm_FIX_PathTerm(self, p):
        "AppTerm : FIX PathTerm"
        raise NotImplementedError()

    def p_AppTerm_TIMESFLOAT_PathTerm_PathTerm(self, p):
        "AppTerm : TIMESFLOAT PathTerm PathTerm"
        raise NotImplementedError

    def p_AppTerm_SUCC_PathTerm(self, p):
        "AppTerm : SUCC PathTerm"
        raise NotImplementedError()

    def p_AppTerm_PRED_PathTerm(self, p):
        "AppTerm : PRED PathTerm"
        raise NotImplementedError()

    def p_AppTerm_ISZERO_PathTerm(self, p):
        "AppTerm : ISZERO PathTerm"
        raise NotImplementedError()

# AscribeTerm

    def p_AscribeTerm_ATerm_AS_Type(self, p):
        "AscribeTerm : ATerm AS Type"
        p[0] = syntax.TmAscribe(self._info(p), p[1], p[3])

    def p_AscribeTerm_ATerm(self, p):
        "AscribeTerm : ATerm"
        p[0] = p[1]

# PathTerm

    def p_PathTerm_DOT_LCID(self, p):
        "PathTerm : PathTerm DOT LCID"
        p[0] = syntax.TmProj(self._info(p), p[1], p[3])

    def p_PathTerm_DOT_INTV(self, p):
        "PathTerm : PathTerm DOT INTV"
        p[0] = syntax.TmProj(self._info(p), p[1], int(p[3]))

    def p_PathTerm_AscribeTerm(self, p):
        "PathTerm : AscribeTerm"
        p[0] = p[1]

# TermSeq

    def p_TermSeq_Term(self, p):
        "TermSeq : Term"
        p[0] = p[1]

    def p_TermSeq_Term_SEMI_TermSeq(self, p):
        "TermSeq : Term SEMI TermSeq"
        raise NotImplementedError()

# ATerm
    def p_ATerm_LPAREN_TermSeq_RPAREN(self, p):
        "ATerm : LPAREN TermSeq RPAREN"
        p[0] = p[2]

    def p_ATerm_id(self, p):
        "ATerm : LCID"
        p[0] = syntax.TmVar(
            self._info(p),
            self.name2index(p, p[1]),
            len(self._ctx))

    def p_ATerm_TRUE(self, p):
        "ATerm : TRUE"
        p[0] = syntax.TmTrue(self._info(p))

    def p_ATerm_FALSE(self, p):
        "ATerm : FALSE"
        p[0] = syntax.TmFalse(self._info(p))

    def p_ATerm_INERT_LSQUARE_Type_RSQUARE(self, p):
        "ATerm : INERT LSQUARE Type RSQUARE"
        raise NotImplementedError()

    def p_ATerm_LT_LCID_EQ_Term_GT_AS_Type(self, p):
        "ATerm : LT LCID EQ Term GT AS Type"
        p[0] = syntax.TmTag(self._info(p), p[2], p[4], p[7])

    def p_ATerm_STRINGV(self, p):
        "ATerm : STRINGV"
        p[0] = syntax.TmString(self._info(p), p[1])

    def p_ATerm_UNIT(self, p):
        "ATerm : UNIT"
        p[0] = syntax.TmUnit(self._info(p))

    def p_ATerm_Fields(self, p):
        "ATerm : LCURLY ATerm_LCURLY Fields RCURLY ATerm_RCURLY"
        p[0] = syntax.TmRecord(self._info(p), p[3])

    def p_ATerm_FLOATV(self, p):
        "ATerm : FLOATV"
        p[0] = syntax.TmFloat(self._info(p), float(p[1]))

    def p_ATerm_INTV(self, p):
        "ATerm : INTV"
        p[0] = syntax.TmFloat(self._info(p), int(p[1]))

    # Helpers

    def p_ATerm_LCURLY(self, p):
        "ATerm_LCURLY :"
        self._scope_comma_cnt.append(0)

    def p_ATerm_RCURLY(self, p):
        "ATerm_RCURLY :"
        self._scope_comma_cnt.pop()

# Cases

    def p_Cases_Case(self, p):
        "Cases : Case"
        raise NotImplementedError()

    def p_Cases_Case_Cases(self, p):
        "Cases : Case VBAR Cases"
        raise NotImplementedError()

# Case

    def p_Case_LCID_LCID_AppTerm(self, p):
        "Case : LT LCID EQ LCID GT DDARROW AppTerm"
        raise NotImplementedError()

# Fields

    def p_Fields(self, p):
        "Fields :"
        p[0] = []

    def p_Fields_NEFields(self, p):
        "Fields : NEFields"
        p[0] = p[1]

# NEFields

    def p_NEFields_Field(self, p):
        "NEFields : Field"
        p[0] = [p[1]]

    def p_NEFields_Field_COMMA_NEFields(self, p):
        "NEFields : Field COMMA Field_comma NEFields"
        p[4].append(p[1])
        p[0] = p[4]

    def p_Field_comma(self, p):
        "Field_comma : "
        self._scope_comma_cnt[-1] += 1

# Field
    
    def p_Field_LCID_EQ_Term(self, p):
        "Field : LCID EQ Term"
        p[0] = (p[1], p[3])

    def p_Field_Term(self, p):
        "Field : Term"
        i = self._scope_comma_cnt[-1]
        p[0] = (i+1, p[1])

# Helper functions

    def p_error(self, p):
        self._error("Syntax error", self._info(p))

    def _error(self, msg, info):
        raise SystemError(msg, info)

    def addbinding(self, name, bind):
        syntax.addbinding(self._ctx, name, bind)

    def addname(self, name):
        self.addbinding(name, syntax.NameBind())

    def isnamebound(self, name):
        return syntax.isnamebound(self._ctx, name)

    def name2index(self, p, name):
        try:
            return syntax.name2index(self._ctx, name)
        except ValueError as e:
            msg = str(e)
        self._error(msg, self._info(p))

    def _info(self, p):
        return syntax.Info(self.filename, p.lineno(1))
