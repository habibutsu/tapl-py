import ply.lex as lex
import re

class Lexer:

    _unescape_tokens = [
        # Symbols
        ("_", "USCORE"),
        # ("'", "APOSTROPHE"),
        #("\"", "DQUOTE"),
        # ("!", "BANG"),
        # ("#", "HASH"),
        # ("$", "TRIANGLE"),
        # ("*", "STAR"),
        ("|", "VBAR"),
        (".", "DOT"),
        (";", "SEMI"),
        (",", "COMMA"),
        # ("/", "SLASH"),
        (":", "COLON"),
        # ("::", "COLONCOLON"),
        ("=", "EQ"),
        # ("==", "EQEQ"),
        ("[", "LSQUARE"),
        ("<", "LT"),
        ("{", "LCURLY"), 
        ("(", "LPAREN"), 
        # ("<-", "LEFTARROW"), 
        # ("{|", "LCURLYBAR"), 
        # ("[|", "LSQUAREBAR"), 
        ("}", "RCURLY"),
        (")", "RPAREN"),
        ("]", "RSQUARE"),
        (">", "GT"),
        # ("|}", "BARRCURLY"),
        # ("|>", "BARGT"),
        # ("|]", "BARRSQUARE"),

        # Special compound symbols:
        # (":=", "COLONEQ"),
        ("->", "ARROW"),
        # ("=>", "DARROW"),
        ("==>", "DDARROW"),
    ]

    _tokens = (
        #(r"[a-z_][a-z_0-9]*", "LCID"),
        #(r"[A-Z_][A-Z_0-9]*", "UCID"),
    )

    reserved = {

        "as": "AS",
        "Bool": "BOOL",
        "case": "CASE",
        "else": "ELSE",
        "false": "FALSE",
        "fix": "FIX",
        "Float": "UFLOAT",
        "if": "IF",
        "in": "IN",
        "inert": "INERT",
        "iszero": "ISZERO",
        "lambda" : "LAMBDA",
        "let": "LET",
        "letrec": "LETREC",
        "Nat": "NAT",
        "of": "OF",
        "pred": "PRED",
        "String": "USTRING",
        "succ": "SUCC",
        "then": "THEN",
        "timesfloat": "TIMESFLOAT",
        "true": "TRUE",
        # "type": "TYPE",
        "unit": "UNIT",
        "Unit": "UUNIT",
    }

    tokens = [
        "LCID",
        "UCID",
        "INTV",
        "FLOATV",
        "STRINGV"
    ]


    def __init__(self, **kwargs):
        self.tokens = list(self.tokens)
        for value, name in self._unescape_tokens:
            self.tokens.append(name)
            setattr(self, "t_%s" % name, re.escape(value))

        for value, name in self._tokens:
            self.tokens.append(name)
            attr_name = "t_%s" % name
            if not hasattr(self, attr_name):
                setattr(self, attr_name, value)

        self.tokens += self.reserved.values()
        self.lexer = lex.lex(module=self, **kwargs)

    def t_createID(self, t):
        r'[A-Za-z_][A-Za-z_0-9]*'
        ttype = self.reserved.get(t.value)
        if ttype is None:
            if t.value[0].isupper():
                ttype = "UCID"
            else:
                ttype = "LCID"
        t.type = ttype
        return t

    def t_comment(self, t):
        r'(/\*(.|\n)*?\*/)|(//.*)'
        pass

    # Define a rule so we can track line numbers
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # A string containing ignored characters (spaces and tabs)
    t_ignore  = ' \t'

    # Error handling rule
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    def t_FLOATV(self, t):
        r'([0-9]+\.[0-9]+)'
        t.value = float(t.value)
        return t

    def t_INTV(self, t):
        r'([0-9]+)'
        t.value = int(t.value)
        return t

    def t_STRINGV(self ,t):
        r'"(.*?)"'
        t.value = t.value[1:-1]
        return t
