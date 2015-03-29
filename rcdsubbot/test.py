import unittest
from parser import Parser
from lexer import Lexer
import syntax
import core

class ParserTestCase(unittest.TestCase):
    
    def setUp(self):
        self.parser = Parser()

    def test_simple(self):
        ast = self.parser.parse("lambda x:Top. x;")
        self.assertEqual(len(ast), 1)
        self.assertIsInstance(
            ast[0], syntax.Eval)
        self.assertIsInstance(
            ast[0].term, syntax.TmAbs)

        # Abstraction
        self.assertIsInstance(
            ast[0].term.type, syntax.TyTop)
        self.assertIsInstance(
            ast[0].term.term, syntax.TmVar)

    def test_arrow(self):
        ast = self.parser.parse("lambda x:Top -> Top. x;")

        self.assertEqual(len(ast), 1)
        self.assertIsInstance(
            ast[0], syntax.Eval)
        self.assertIsInstance(
            ast[0].term, syntax.TmAbs)

        #Abstraction
        self.assertIsInstance(
            ast[0].term.type, syntax.TyArr)
        self.assertIsInstance(
            ast[0].term.term, syntax.TmVar)

    def test_TmRecord(self):
        ast = self.parser.parse("x:Top; y:Top; {x=x, y=y};")
        self.assertEqual(type(ast[0]), syntax.Bind)
        self.assertEqual(type(ast[1]), syntax.Bind)
        self.assertEqual(type(ast[2]), syntax.Eval)
        self.assertEqual(type(ast[2].term), syntax.TmRecord)


class TypeOfTestCase(unittest.TestCase):
    def setUp(self):
        self.parser = Parser()

    def test_record_match_ok(self):
        ast = self.parser.parse(
            "v1:Top; v2:Top; (lambda x:{Top, Top}. x.1) {v1, v2};")
        ctx = self.parser._ctx
        self.assertEqual(type(ast[0]), syntax.Bind)
        self.assertEqual(type(ast[1]), syntax.Bind)
        self.assertEqual(type(ast[2]), syntax.Eval)
        self.assertIsInstance(
            core.typeof(ast[2].term, ctx), syntax.TyTop)

    def test_record_match_error(self):
        ast = self.parser.parse(
            "v1:Top; v2:Top; (lambda x:{Top, Top}. x.1) {l1=v1, l2=v2};")
        ctx = self.parser._ctx
        self.assertEqual(type(ast[0]), syntax.Bind)
        self.assertEqual(type(ast[1]), syntax.Bind)
        self.assertEqual(type(ast[2]), syntax.Eval)
        with self.assertRaises(RuntimeError) as e:
            core.typeof(ast[2].term, ctx)


if __name__ == '__main__':
    unittest.main()