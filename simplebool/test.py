import unittest
from parser import Parser
from lexer import Lexer
import syntax

class LexerTestCase(unittest.TestCase):

    def setUp(self):
        self.lexer = Lexer()

    def test_if(self):
        self.lexer.lexer.input(
            "lambda x:Bool->Bool. if x false then true else false")
        tokens = []
        while True:
            tok = self.lexer.lexer.token()
            tokens.append(tok)
            if not tok: break

        self.assertEqual(tokens[0].type, "LAMBDA")
        self.assertEqual(tokens[1].type, "LCID")
        self.assertEqual(tokens[2].type, "COLON")
        self.assertEqual(tokens[3].type, "BOOL")
        self.assertEqual(tokens[4].type, "ARROW")
        self.assertEqual(tokens[5].type, "BOOL")
        self.assertEqual(tokens[6].type, "DOT")
        self.assertEqual(tokens[7].type, "IF")
        self.assertEqual(tokens[8].type, "LCID")
        self.assertEqual(tokens[9].type, "FALSE")
        self.assertEqual(tokens[10].type, "THEN")
        self.assertEqual(tokens[11].type, "TRUE")
        self.assertEqual(tokens[12].type, "ELSE")
        self.assertEqual(tokens[13].type, "FALSE")

class ParserTestCase(unittest.TestCase):
    
    def setUp(self):
        self.parser = Parser()

    def test_binding(self):
        ast = self.parser.parse("x:Bool;")
        self.assertEqual(len(ast), 1)
        elem = ast[0]
        self.assertIsInstance(
            elem, syntax.Bind)
        self.assertEqual(
            elem.name, "x")
        self.assertIsInstance(
            elem.binding, syntax.VarBind)
        self.assertIsInstance(
            elem.binding.type, syntax.TyBool)

    def test_simple(self):
        ast = self.parser.parse("lambda x:Bool. x;")
        self.assertEqual(len(ast), 1)
        self.assertIsInstance(
            ast[0], syntax.Eval)
        self.assertIsInstance(
            ast[0].term, syntax.TmAbs)

        # Abstraction
        self.assertIsInstance(
            ast[0].term.type, syntax.TyBool)
        self.assertIsInstance(
            ast[0].term.term, syntax.TmVar)

    def test_arrow(self):
        ast = self.parser.parse("lambda x:Bool -> Bool. x;")

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


if __name__ == '__main__':
    unittest.main()