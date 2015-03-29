import ply.lex as lex
import re

class Lexer:

    _unescape_tokens = [
        # Symbols
        ("_", "USCORE"),
        # ("'", "APOSTROPHE"),
        # ("\"", "DQUOTE"),
        # ("!", "BANG"),
        # ("#", "HASH"),
        # ("$", "TRIANGLE"),
        # ("*", "STAR"),
        # ("|", "VBAR"),
        (".", "DOT"),
        (";", "SEMI"),
        # (",", "COMMA"),
        ("/", "SLASH"),
        # (":", "COLON"),
        # ("::", "COLONCOLON"),
        # ("=", "EQ"),
        # ("==", "EQEQ"),
        # ("[", "LSQUARE"),
        # ("<", "LT"),
        # ("{", "LCURLY"),
        ("(", "LPAREN"),
        # ("<-", "LEFTARROW"),
        # ("{|", "LCURLYBAR"),
        # ("[|", "LSQUAREBAR"),
        # ("}", "RCURLY"),
        (")", "RPAREN"),
        # ("]", "RSQUARE"),
        # (">", "GT"),
        # ("|}", "BARRCURLY"),
        # ("|>", "BARGT"),
        # ("|]", "BARRSQUARE"),

        # Special compound symbols:
        # (":=", "COLONEQ"),
        # ("->", "ARROW"),
        # ("=>", "DARROW"),
        # ("==>", "DDARROW"),
    ]

    _tokens = (
        # (r"[a-z_][a-z_0-9]*", "LCID"),
        # (r"[A-Z_][A-Z_0-9]*", "UCID"),
    )

    reserved = {
       'lambda' : 'LAMBDA',
    }

    tokens = ["LCID"]


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

    def t_LCID(self, t):
        r'[a-z_][a-z_0-9]*'
        t.type = self.reserved.get(t.value, 'LCID')
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

