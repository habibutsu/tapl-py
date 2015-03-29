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
            : SLASH

Term        
            : AppTerm
            | LAMBDA LCID new_scope DOT Term end_scope
            | LAMBDA USCORE new_scope DOT Term end_scope

AppTerm     
            : ATerm
            | AppTerm ATerm

ATerm
            : LPAREN Term RPAREN
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
        self.filename = filename
        return self.parser.parse(
            text, debug=self.debug, lexer=self.lexer.lexer, tracking=True)

    def p_error(self, p):
        print("Syntax error at '%s'" % p.value)

    def p_Commands_Command(self, p):
        "Commands : Command SEMI"
        p[0] = [p[1]]
        
    def p_Commands_Command_Commands(self, p):
        "Commands : Command SEMI Commands"
        p[0] = [p[1]] + p[3]
        
    def p_Command(self, p):
        "Command : LCID Binder"
        self.addbinding(p[1], p[2])
        p[0] = syntax.Bind(self._info(p.lineno(1)), p[1], p[2])

    def p_Command_id(self, p):
        "Command : Term"
        p[0] = syntax.Eval(self._info(p.lineno(1)), p[1])
        
    def p_Binder(self, p):
        "Binder : SLASH"
        p[0] = syntax.NameBind()

    def p_Term_AppTerm(self, p):
        "Term : AppTerm"
        p[0] = p[1]
        
    def p_Term_LAMBDA_LCID(self, p):
        "Term : LAMBDA LCID new_scope DOT Term end_scope"
        p[0] = syntax.TmAbs(self._info(p.lineno(1)), p[2], p[5])

    def p_Term_LAMBDA_USCORE(self, p):
        "Term : LAMBDA USCORE new_scope DOT Term end_scope"
        p[0] = syntax.TmAbs(self._info(p.lineno(1)), "_", p[5])

    def p_new_scope(self, p):
        "new_scope :"
        self.addname(p[-1])

    def p_end_scope(self, p):
        "end_scope :"
        self._ctx.pop()

    def p_AppTerm_ATerm(self, p):
        "AppTerm : ATerm"
        p[0] = p[1]

    def p_AppTerm_AppTerm_ATerm(self, p):
        "AppTerm : AppTerm ATerm"
        p[0] = syntax.TmApp(self._info(p.lineno(1)), p[1], p[2])

    def p_ATerm_Term(self, p):
        "ATerm : LPAREN Term RPAREN"
        p[0] = p[2]

    def p_ATerm_id(self, p):
        "ATerm : LCID"
        p[0] = syntax.TmVar(
            self._info(p.lineno(1)), self.name2index(p[1]), len(self._ctx))

    def addbinding(self, name, bind):
        syntax.addbinding(self._ctx, name, bind)

    def addname(self, name):
        self.addbinding(name, syntax.NameBind())

    def isnamebound(self, name):
        return syntax.isnamebound(self._ctx, name)

    def name2index(self, name):
        return syntax.name2index(self._ctx, name)

    def _info(self, lineno):
        return syntax.Info(self.filename, lineno)
