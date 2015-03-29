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

PathTerm    : PathTerm DOT LCID
            | PathTerm DOT INTV
            | ATerm

Type
            : ArrowType

AType       : LPAREN Type RPAREN
            | LCURLY FieldTypes RCURLY
            | TTOP
            | TBOT

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

AppTerm     
            : PathTerm
            | AppTerm PathTerm

ATerm
            : LPAREN Term RPAREN
            | LCID
            | LCURLY Fields RCURLY

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

    def p_AType_LCURLY_FieldTypes_RCURLY(self, p):
        "AType : LCURLY AType_LCURLY FieldTypes RCURLY AType_RCURLY"
        p[0] = syntax.TyRecord(p[3])

    def p_AType_TTOP(self, p):
        "AType : TTOP"
        p[0] = syntax.TyTop()

    def p_AType_TBOT(self, p):
        "AType : TBOT"
        p[0] = syntax.TyBot()

    # Helper functions

    def p_AType_LCURLY(self, p):
        "AType_LCURLY :"
        self._scope_comma_cnt.append(0)

    def p_AType_RCURLY(self, p):
        "AType_RCURLY :"
        self._scope_comma_cnt.pop()

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

# AppTerm

    def p_AppTerm_PathTerm(self, p):
        "AppTerm : PathTerm"
        p[0] = p[1]

    def p_AppTerm_AppTerm_PathTerm(self, p):
        "AppTerm : AppTerm PathTerm"
        p[0] = syntax.TmApp(self._info(p), p[1], p[2])

# PathTerm

    def p_PathTerm_DOT_LCID(self, p):
        "PathTerm : PathTerm DOT LCID"
        p[0] = syntax.TmProj(self._info(p), p[1], p[3])

    def p_PathTerm_DOT_INTV(self, p):
        "PathTerm : PathTerm DOT INTV"
        p[0] = syntax.TmProj(self._info(p), p[1], int(p[3]))

    def p_PathTerm_Aterm(self, p):
        "PathTerm : ATerm"
        p[0] = p[1]

# ATerm

    def p_ATerm_Term(self, p):
        "ATerm : LPAREN Term RPAREN"
        p[0] = p[2]

    def p_ATerm_LCID(self, p):
        "ATerm : LCID"
        p[0] = syntax.TmVar(
            self._info(p),
            self.name2index(p[1]),
            len(self._ctx))

    def p_ATerm_Fields(self, p):
        "ATerm : LCURLY ATerm_LCURLY Fields RCURLY ATerm_RCURLY"
        p[0] = syntax.TmRecord(self._info(p), p[3])

    # Helpers

    def p_ATerm_LCURLY(self, p):
        "ATerm_LCURLY :"
        self._scope_comma_cnt.append(0)

    def p_ATerm_RCURLY(self, p):
        "ATerm_RCURLY :"
        self._scope_comma_cnt.pop()

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

# Common helper functions

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

    def name2index(self, name):
        return syntax.name2index(self._ctx, name)

    def _info(self, p):
        return syntax.Info(self.filename, p.lineno(1))
