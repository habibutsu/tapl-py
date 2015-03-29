import ply.yacc as yacc

from lexer import Lexer

import syntax

"""
Commands
            : Command SEMI
            | Command SEMI Commands

Command
            : Term
            | LCID Binder

Binder
            : COLON Type

Type
            : ArrowType

AType       : LPAREN Type RPAREN
            | BOOL
            | NAT
            | UCID

ArrowType   : AType ARROW ArrowType
            | AType

Term        
            : AppTerm
            | LAMBDA LCID COLON Type new_scope DOT Term end_scope
            | LAMBDA USCORE COLON Type new_scope DOT Term end_scope
            | IF Term THEN Term ELSE Term

AppTerm     
            : ATerm
            | SUCC ATerm
            | PRED ATerm
            | ISZERO ATerm
            | AppTerm ATerm

ATerm
            : LPAREN Term RPAREN
            | TRUE
            | FALSE
            | INTV
            | LCID
"""

class Parser:

    def __init__(self, debug=False):
        self.lexer = Lexer()
        self.tokens = self.lexer.tokens
        self.debug = debug
        self.parser = yacc.yacc(module=self, debug=debug)

    def parse(self, text, filename=""):
        self._ctx = []
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

    def p_Command_LCID_Binder(self, p):
        "Command : LCID Binder"
        self.addbinding(p[1], p[2])

        p[0] = syntax.Bind(self._info(p), p[1], p[2])

    def p_Command_Term(self, p):
        "Command : Term"
        p[0] = syntax.Eval(self._info(p), p[1])

# Binder

    def p_Binder_COLON_Type(self, p):
        "Binder : COLON Type"
        p[0] = syntax.VarBind(p[2])

# Type

    def p_Type_ArrowType(self, p):
        "Type : ArrowType"
        p[0] = p[1]

# AType

    def p_AType_Complex(self, p):
        "AType : LPAREN Type RPAREN"
        p[0] = p[2]

    def p_AType_BOOL(Self, p):
        "AType : BOOL"
        p[0] = syntax.TyBool()

    def p_AType_NAT(self, p):
        "AType : NAT"
        p[0] = syntax.TyNat()

    def p_AType_UCID(Self, p):
        "AType : UCID"
        p[0] = syntax.TyId(p[1])

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
        
    def p_Term_LAMBDA_LCID(self, p):
        "Term : LAMBDA LCID COLON Type lambda_new_scope DOT Term lambda_end_scope"
        p[0] = syntax.TmAbs(
            self._info(p), p[2], p[4], p[7])

    def p_Term_LAMBDA_USCORE(self, p):
        "Term : LAMBDA USCORE COLON Type lambda_new_scope DOT Term lambda_end_scope"
        p[0] = syntax.TmAbs(self._info(p), "_", p[4], p[7])

    def p_lambda_new_scope(self, p):
        "lambda_new_scope :"
        self.addname(p[-3])

    def p_lambda_end_scope(self, p):
        "lambda_end_scope :"
        self._ctx.pop()

    def p_IF_Term_THEN_Term_ELSE_Term(self, p):
        "Term : IF Term THEN Term ELSE Term"
        p[0] = syntax.TmIf(self._info(p), p[2], p[4], p[6])

# AppTerm

    def p_AppTerm_ATerm(self, p):
        "AppTerm : ATerm"
        p[0] = p[1]

    def p_AppTerm_SUCC_ATerm(self, p):
        "AppTerm : SUCC ATerm"
        p[0] = syntax.TmSucc(self._info(p), p[2])

    def p_AppTerm_PRED_ATerm(self, p):
        "AppTerm : PRED ATerm"
        p[0] = syntax.TmPred(self._info(p), p[2])

    def p_AppTerm_ISZERO_ATerm(self, p):
        "AppTerm : ISZERO ATerm"
        p[0] = syntax.TmIsZero(self._info(p), p[2])

    def p_AppTerm_AppTerm_ATerm(self, p):
        "AppTerm : AppTerm ATerm"
        p[0] = syntax.TmApp(self._info(p), p[1], p[2])

# ATerm

    def p_ATerm_Term(self, p):
        "ATerm : LPAREN Term RPAREN"
        p[0] = p[2]

    def p_ATerm_TRUE(self, p):
        "ATerm : TRUE"
        p[0] = syntax.TmTrue(self._info(p))

    def p_ATerm_FALSE(self, p):
        "ATerm : FALSE"
        p[0] = syntax.TmFalse(self._info(p))

    def p_ATerm_INTV(self, p):
        "ATerm : INTV"
        info = self._info(p)
        t = syntax.TmZero(info)
        for i in range(0, p[1]):
            t = syntax.TmSucc(info, t)
        p[0] = t

    def p_ATerm_LCID(self, p):
        "ATerm : LCID"
        p[0] = syntax.TmVar(
            self._info(p),
            self.name2index(p, p[1]),
            len(self._ctx))

# Common helper functions

    def p_error(self, p):
        print(p)
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
