import unittest
from parser import Parser
from lexer import Lexer
import syntax
import core

class LexerTestCase(unittest.TestCase):

    def setUp(self):
        self.lexer = Lexer()

    def lexer_tokens(self, input):
        self.lexer.lexer.input(input)
        tokens = []
        while True:
            tok = self.lexer.lexer.token()
            if not tok: break
            tokens.append(tok.type)
        return tokens

    def test_if(self):
        tokens = self.lexer_tokens(
            "lambda x:Bool->Bool. if x false then true else false")

        self.assertEqual(tokens, [
            "LAMBDA", "LCID", "COLON", "BOOL",
            "ARROW", "BOOL", "DOT",
            "IF", "LCID", "FALSE", "THEN", "TRUE", "ELSE", "FALSE"
        ])

    def test_field_types(self):
        tokens = self.lexer_tokens("lambda x:<a:Bool,b:Bool>. x")
        self.assertEqual(tokens, [
            'LAMBDA', 'LCID', 'COLON', 'LT', 'LCID', 'COLON',
            'BOOL', 'COMMA', 'LCID', 'COLON', 'BOOL', 'GT', 'DOT', 'LCID'
        ])

    def test_let_int(self):
        tokens = self.lexer_tokens("let x=true in x")
        self.assertEqual(tokens, [
            'LET', 'LCID', 'EQ', 'TRUE', 'IN', 'LCID'
        ])

    def test_tuple(self):
        tokens = self.lexer_tokens("{true, false}.1")
        self.assertEqual(tokens, [
            'LCURLY', 'TRUE', 'COMMA', 'FALSE', 'RCURLY', 'DOT', 'INTV'
        ])

    def test_records(self):
        tokens = self.lexer_tokens("{x=true, y=false}.x")
        self.assertEqual(tokens, [
            'LCURLY', 'LCID', 'EQ', 'TRUE', 'COMMA',
            'LCID', 'EQ', 'FALSE', 'RCURLY', 'DOT', 'LCID'
        ])

    def test_string(self):
        tokens = self.lexer_tokens("\"hello\"")
        self.assertEqual(tokens, [
            'STRINGV'
        ])

    def test_timesfloat(self):
        tokens = self.lexer_tokens("timesfloat 2.0 3.14159")
        self.assertEqual(tokens, [
            'TIMESFLOAT', 'FLOATV', 'FLOATV'
        ])

    def test_case(self):
        tokens = self.lexer_tokens("""
            case a of
                <physical=x> ==> x.firstlast
                | <virtual=y> ==> y.name""")
        self.assertEqual(tokens, [
            'CASE', 'LCID', 'OF',
            'LT', 'LCID', 'EQ', 'LCID', 'GT', 'DDARROW', 'LCID', 'DOT', 'LCID',
            'VBAR', 'LT', 'LCID', 'EQ', 'LCID', 'GT', 'DDARROW', 'LCID', 'DOT', 'LCID'
        ])

    def test_tuple_type(self):
        tokens = self.lexer_tokens("x:{Bool, Bool}")
        self.assertEqual(tokens, [
            'LCID', 'COLON', 'LCURLY', 'BOOL', 'COMMA', 'BOOL', 'RCURLY'
        ])

    def test_(self):
        tokens = self.lexer_tokens(
            "tascribe = (lambda x:Bool. x) as FBool")
        self.assertEqual(tokens, [
            'LCID', 'EQ',
            'LPAREN',
            'LAMBDA', 'LCID', 'COLON', 'BOOL', 'DOT', 'LCID',
            'RPAREN',
            'AS', 'UCID'
        ])


class ParserTestCase(unittest.TestCase):

    def setUp(self):
        self.parser = Parser(debug=False)

    def test_tuple(self):
        ast = self.parser.parse("{true, {true, false}};")

        self.assertEqual(len(ast), 1)
        elem = ast[0]
        self.assertIsInstance(
            elem, syntax.Eval)
        self.assertIsInstance(
            elem.term, syntax.TmRecord)
        self.assertEqual(
            len(elem.term.fields), 2)
        self.assertEqual(
            elem.term.fields[1][0], 1)
        self.assertEqual(
            elem.term.fields[0][0], 2)

        self.assertIsInstance(
            elem.term.fields[1][1], syntax.TmTrue)
        self.assertIsInstance(
            elem.term.fields[0][1], syntax.TmRecord)
    
    def test_tuple_type(self):
        ast = self.parser.parse("x:{Bool, Bool};")
        self.assertEqual(len(ast), 1)
        elem = ast[0]
        self.assertIsInstance(
            elem, syntax.Bind)
        self.assertEqual(elem.name, "x")
        self.assertIsInstance(
            elem.binding, syntax.VarBind)

    def test_record(self):
        ast = self.parser.parse("{x=true, y=false};")

        self.assertEqual(len(ast), 1)
        elem = ast[0]
        self.assertIsInstance(
            elem, syntax.Eval)
        self.assertIsInstance(
            elem.term, syntax.TmRecord)

        self.assertEqual(
            len(elem.term.fields), 2)

        self.assertEqual(
            elem.term.fields[1][0], "x")
        self.assertEqual(
            elem.term.fields[0][0], "y")

        self.assertIsInstance(
            elem.term.fields[1][1], syntax.TmTrue)

        self.assertIsInstance(
            elem.term.fields[0][1], syntax.TmFalse)

    def test_proj(self):
        ast = self.parser.parse("{x=true, y=false}.x;")
        elem = ast[0]
        self.assertIsInstance(elem, syntax.Eval)
        self.assertIsInstance(elem.term, syntax.TmProj)
        ast = self.parser.parse("{true, false}.1;")
        elem = ast[0]
        self.assertIsInstance(elem, syntax.Eval)
        self.assertIsInstance(elem.term, syntax.TmProj)

    def test_bindr(self):
        ast = self.parser.parse("x:Bool;")
        elem = ast[0]
        self.assertEqual(type(elem), syntax.Bind)
        self.assertEqual(elem.name, "x")
        self.assertEqual(type(elem.binding), syntax.VarBind)
        self.assertEqual(type(elem.binding.type), syntax.TyBool)

    def test_type_binder(self):
        ast = self.parser.parse("MyBool = Bool;")
        elem = ast[0]
        self.assertEqual(type(elem), syntax.Bind)
        self.assertEqual(elem.name, "MyBool")
        self.assertEqual(type(elem.binding), syntax.TyAbbBind)
        self.assertEqual(type(elem.binding.type), syntax.TyBool)

        old_ctx = self.parser._ctx
        ast = self.parser.parse("x:MyBool;", ctx=old_ctx)
        elem = ast[0]
        self.assertEqual(type(elem), syntax.Bind)
        self.assertEqual(type(elem.binding.type), syntax.TyVar)
        self.assertEqual(elem.binding.type.index, 0)
        self.assertEqual(elem.binding.type.ctxlength, 1)

        ast = self.parser.parse("x:SomeType;")
        elem = ast[0]
        self.assertEqual(type(elem), syntax.Bind)
        self.assertEqual(type(elem.binding.type), syntax.TyId)
        self.assertEqual(elem.binding.type.name, "SomeType")

        ast = self.parser.parse("x:{SomeType, SomeType};")
        elem = ast[0]
        self.assertEqual(type(elem), syntax.Bind)
        self.assertEqual(type(elem.binding), syntax.VarBind)
        self.assertEqual(type(elem.binding.type), syntax.TyRecord)
        self.assertEqual(len(elem.binding.type.fields), 2)

    def test_ascribe(self):
        ast = self.parser.parse(
            "tascribe = (lambda x:Bool. x) as FBool;")
        elem = ast[0]
        self.assertEqual(type(elem), syntax.Bind)
        self.assertEqual(type(elem.binding), syntax.TmAbbBind)
        self.assertEqual(type(elem.binding.term), syntax.TmAscribe)

    def test_variant(self):
        ast = self.parser.parse(
            "PhysicalAddr = {firstlast:String, addr:String};")
        elem = ast[0]
        self.assertEqual(type(elem), syntax.Bind)
        self.assertEqual(type(elem.binding), syntax.TyAbbBind)
        self.assertEqual(type(elem.binding.type), syntax.TyRecord)


class TypeOfTestCase(unittest.TestCase):
    def setUp(self):
        self.parser = Parser()

    def test_record_type_mismatch(self):
        ast = self.parser.parse(
            "(lambda x:{Bool, Bool}. x.1) true;")
        elem = ast[0]
        ctx = []
        self.assertEqual(type(elem), syntax.Eval)
        with self.assertRaises(RuntimeError):
            core.typeof(elem.term, ctx)


class EvaluateTestCase(unittest.TestCase):

    def setUp(self):
        self.parser = Parser()

    def test_proj(self):
        ast = self.parser.parse("{x=true, y=false}.x;")
        elem = ast[0]
        ctx = []
        term = core.evaluate(ctx, elem.term)
        self.assertIsInstance(term, syntax.TmTrue)

        ast = self.parser.parse("{true, false}.2;")
        elem = ast[0]
        ctx = []
        term = core.evaluate(ctx, elem.term)
        self.assertIsInstance(term, syntax.TmFalse)

    def test_record(self):
        ast = self.parser.parse(
            "{(lambda x:Bool. x) true, (lambda x:Bool. x) false};")
        elem = ast[0]
        ctx = []
        term = core.evaluate(ctx, elem.term)
        self.assertIsInstance(term, syntax.TmRecord)
        self.assertIsInstance(term.fields[0][1], syntax.TmFalse)
        self.assertIsInstance(term.fields[1][1], syntax.TmTrue)

if __name__ == '__main__':
    unittest.main()