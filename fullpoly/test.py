import unittest
from parser import Parser
from lexer import Lexer
import syntax
from syntax import *
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

    def test_tuple_type(self):
        tokens = self.lexer_tokens("x:{Bool, Bool}")
        self.assertEqual(tokens, [
            'LCID', 'COLON', 'LCURLY', 'BOOL', 'COMMA', 'BOOL', 'RCURLY'
        ])

    def test_type_ascribe(self):
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

    def test_let_in(self):
        ast = self.parser.parse("let x=true in x;")
        elem = ast[0]
        self.assertIsInstance(
            elem, syntax.Eval)
        self.assertIsInstance(
            elem.term, syntax.TmLet)
        self.assertIsInstance(
            elem.term.let_term, syntax.TmTrue)
        self.assertIsInstance(
            elem.term.in_term, syntax.TmVar)

    def test_type_abstraction(self):
        ast = self.parser.parse("lambda X. lambda x:X. x;")
        elem = ast[0]
        self.assertIsInstance(elem, syntax.Eval)
        self.assertIsInstance(elem.term, syntax.TmTAbs)
        self.assertEqual(elem.term.name, "X")
        self.assertIsInstance(elem.term.term, syntax.TmAbs)
        self.assertIsInstance(elem.term.term.type, syntax.TyVar)
        self.assertIsInstance(elem.term.term.term, syntax.TmVar)

    def test_type_application(self):
        ast = self.parser.parse(
            "(lambda X. lambda x:X. x) [All X.X->X];")
        elem = ast[0]
        fi = Info("", 1)
        expected_term = TmTApp(fi,
            TmTAbs(fi, "X",
                TmAbs(fi, "x", TyVar(0, 1), TmVar(fi, 0, 2))),
            TyAll(
                "X", TyArr(TyVar(0, 1), TyVar(0, 1))))
        self.assertSequenceEqual(elem.term, expected_term)

    def test_pack(self):
        ast = self.parser.parse(
            """{* Nat, {c=0, f=lambda x:Nat. x}}
                as {Some X, {c:X, f:X->Nat}};""")
        elem = ast[0]
        fi = Info("", 1)
        expected_term = TmPack(fi,
            TyNat(),
            TmRecord(fi, [
                ('f', TmAbs(fi, 'x', TyNat(), TmVar(fi, 0, 1))),
                ('c', TmZero(fi))]),
            TySome('X', TyRecord([
                            ('f', TyArr(TyVar(0, 1), TyNat())),
                            ('c', TyVar(0, 1))])))
        self.assertSequenceEqual(elem.term, expected_term)

    # def test_pack_alternative(self):
    #     ast = self.parser.parse(
    #         """
    #             pack X = Nat
    #             with {c=0, f=lambda x:Nat.x}
    #             as {c:X, f:X->Nat};""")
    #     ast = self.parser.parse(
    #         """
    #             pack X = Nat
    #             with (lambda x:Nat. x) as X->Nat;""")
    #     elem = ast[0]
    #     print(elem.term)


    def test_pack_all(self):
        ast = self.parser.parse(
            """{* All Y.Y, lambda x:(All Y.Y). x}
                as {Some X,X->X};""")
        elem = ast[0]
        fi = Info("", 1)
        expected_term = TmPack(fi,
            TyAll('Y', TyVar(0, 1)),
            TmAbs(
                fi, 'x',
                TyAll('Y', TyVar(0, 1)),
                TmVar(fi, 0, 1)),
            TySome('X', TyArr(TyVar(0, 1), TyVar(0, 1))))
        self.assertSequenceEqual(elem.term, expected_term)

    def test_unpack_let(self):
        ast = self.parser.parse(
            """
            let {X, ops} = {*
                Nat,
                {c=0, f=lambda x:Nat. x}
            }
            as {Some X, {c:X, f:X->Nat}}
            in (ops.f ops.c);""".replace("\n", " "))
        elem = ast[0]
        fi = Info("", 1)
        expected_term = TmUnpack(fi, 'X', 'ops',
            TmPack(fi, TyNat(),
                TmRecord(fi, [
                    ('f', TmAbs(
                        fi, 'x', TyNat(), TmVar(fi, 0, 1))),
                    ('c', TmZero(fi))]),
                TySome('X',
                    TyRecord([
                        ('f', TyArr(TyVar(0, 1), TyNat())),
                        ('c', TyVar(0, 1))]))),
            TmApp(fi,
                TmProj(fi, TmVar(fi, 0, 2), 'f'),
                TmProj(fi, TmVar(fi, 0, 2), 'c')))

        self.assertSequenceEqual(
            elem.term, expected_term)

    def test_unpack(self):
        ast = self.parser.parse(
            """{X, ops} = {* Nat, {c=0, f=lambda x:Nat. x}}
                as {Some X, {c:X, f:X->Nat}};""")

class EvaluateTestCase(unittest.TestCase):

    def setUp(self):
        self.parser = Parser()

    def test_let_in(self):
        ast = self.parser.parse("let x=true in x;")
        elem = ast[0]
        ctx = self.parser._ctx
        term = core.evaluate(ctx, elem.term)
        self.assertIsInstance(term, syntax.TmTrue)

    def test_abstraction(self):
        ast = self.parser.parse("lambda x:X. x;")
        elem = ast[0]
        term_type = core.typeof([], elem.term)
        term = core.evaluate([], elem.term)
        self.assertIsInstance(term_type, syntax.TyArr)
        self.assertIsInstance(term_type.left, syntax.TyId)
        self.assertIsInstance(term_type.right, syntax.TyId)

    def test_type_abstraction(self):
        ast = self.parser.parse("lambda X. lambda x:X. x;")
        elem = ast[0]
        term = core.evaluate([], elem.term)
        term_type = core.typeof([], elem.term)

        self.assertIsInstance(term_type, syntax.TyAll)
        self.assertEqual(term_type.name, "X")
        self.assertIsInstance(term_type.type, syntax.TyArr)
        self.assertIsInstance(term_type.type.left, syntax.TyVar)
        self.assertIsInstance(term_type.type.right, syntax.TyVar)

        ast = self.parser.parse(
            "(lambda X. lambda x:X. x) [All X.X->X];")
        elem = ast[0]
        term_type = core.typeof([], elem.term)
        """
        Expected type
        TyArr(
            TyAll("X", TyArr(TyVar(0, 1), TyVar(0, 1))),
            TyAll("X", TyArr(TyVar(0, 1), TyVar(0, 1))))
        """
        self.assertIsInstance(term_type, syntax.TyArr)
        self.assertIsInstance(term_type.left, syntax.TyAll)
        self.assertIsInstance(term_type.right, syntax.TyAll)
        self.assertEqual(term_type.left.name, "X")
        self.assertEqual(term_type.right.name, "X")

        left_type = term_type.left.type
        right_type = term_type.right.type
        self.assertIsInstance(left_type, syntax.TyArr)
        self.assertIsInstance(right_type, syntax.TyArr)

        self.assertIsInstance(left_type.left, syntax.TyVar)
        self.assertIsInstance(left_type.right, syntax.TyVar)

        self.assertIsInstance(right_type.left, syntax.TyVar)
        self.assertIsInstance(right_type.right, syntax.TyVar)

        term = core.evaluate([], elem.term)
        """
        Expected term
        TmAbs(
            "x", TyAll("X", TyArr(TyVar(0, 1), TyVar(0, 1))),
            TmVar(0, 1))
        """
        self.assertIsInstance(term, syntax.TmAbs)
        self.assertEqual(term.name, "x")
        self.assertIsInstance(term.type, syntax.TyAll)
        self.assertIsInstance(term.term, syntax.TmVar)

    def test_pack(self):
        ast = self.parser.parse(
            """{* Nat, {c=0, f=lambda x:Nat. x}}
                    as {Some X, {c:X, f:X->Nat}};""")
        elem = ast[0]
        term_type = core.typeof([], elem.term)
        term = core.evaluate([], elem.term)

    def test_pack_all(self):
        ast = self.parser.parse(
            """{* All Y.Y, lambda x:(All Y.Y). x}
                as {Some X,X->X};""")
        elem = ast[0]
        term_type = core.typeof([], elem.term)
        term = core.evaluate([], elem.term)

        self.assertSequenceEqual(
            term_type,
            TySome('X', TyArr(TyVar(0, 1), TyVar(0, 1))))

    def test_unpac_let(self):
        ast = self.parser.parse(
            """
            let {X, ops} = {*
                Nat,
                {c=0, f=lambda x:Nat. x}
            }
            as {Some X, {c:X, f:X->Nat}}
            in (ops.f ops.c);""".replace("\n", " "))
        elem = ast[0]
        term_type = core.typeof([], elem.term)
        self.assertSequenceEqual(term_type, TyNat())
        term = core.evaluate([], elem.term)
        self.assertIsInstance(term, TmZero)

if __name__ == '__main__':
    unittest.main()