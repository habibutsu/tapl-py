import unittest
from parser import Parser
import syntax
import core

class ParserTestCase(unittest.TestCase):

    def setUp(self):
        self.parser = Parser()

    def test_binding(self):
        ast = self.parser.parse("x/;")
        self.assertEqual(len(ast), 1)
        elem = ast[0]
        self.assertIsInstance(elem, syntax.Bind)
        self.assertEqual(elem.name, "x")
        self.assertIsInstance(elem.binding, syntax.NameBind)

    def test_abstraction(self):
        ast = self.parser.parse("lambda x.x;")
        self.assertEqual(len(ast), 1)
        elem = ast[0]
        self.assertIsInstance(elem, syntax.Eval)
        self.assertIsInstance(elem.term, syntax.TmAbs)

        self.assertEqual(elem.term.name, "x")
        self.assertIsInstance(elem.term.term, syntax.TmVar)
        self.assertEqual(elem.term.term.index, 0)

    def test_abstraction_with_unbound(self):
        self.assertRaises(
            ValueError,
            self.parser.parse, "lambda x.y;")

    def test_abstraction_with_bound(self):
        ast = self.parser.parse("y/; lambda x.y;")
        self.assertEqual(len(ast), 2)
        elem = ast[1]
        self.assertIsInstance(elem, syntax.Eval)
        self.assertIsInstance(elem.term, syntax.TmAbs)

        self.assertEqual(elem.term.name, "x")
        self.assertIsInstance(elem.term.term, syntax.TmVar)
        self.assertEqual(elem.term.term.index, 1)

    def test_application(self):
        ast = self.parser.parse("(lambda x.x) (lambda y. y);")
        self.assertEqual(len(ast), 1)

        elem = ast[0]
        self.assertIsInstance(elem, syntax.Eval)
        self.assertIsInstance(elem.term, syntax.TmApp)

        self.assertIsInstance(elem.term.left, syntax.TmAbs)
        self.assertIsInstance(elem.term.right, syntax.TmAbs)

    def test_abstraction_with_application(self):
        ast = self.parser.parse(
            "(lambda z. (lambda x. z x)) (lambda y.y);")

        self.assertEqual(len(ast), 1)
        elem = ast[0]
        self.assertIsInstance(
            elem, syntax.Eval)

        # application
        self.assertIsInstance(
            elem.term, syntax.TmApp)
        self.assertIsInstance(
            elem.term.left, syntax.TmAbs)
        self.assertIsInstance(
            elem.term.right, syntax.TmAbs)

        # right term of application
        right = elem.term.right
        self.assertIsInstance(right.term, syntax.TmVar)
        self.assertEqual(
            (right.term.index,
             right.term.ctxlength),
            (0,1))

        # left term of application
        left = elem.term.left
        # inner abstraction of left term: lambda x. z x
        left_abs = left.term
        self.assertIsInstance(left_abs, syntax.TmAbs)

        self.assertIsInstance(left_abs.term, syntax.TmApp)

        self.assertIsInstance(left_abs.term.left, syntax.TmVar)
        self.assertEqual(
            (left_abs.term.left.index,
             left_abs.term.left.ctxlength),
            (1,2))

        self.assertIsInstance(left_abs.term.right, syntax.TmVar)
        self.assertEqual(
            (left_abs.term.right.index,
             left_abs.term.right.ctxlength),
            (0,2))


class EvaluateTestCase(unittest.TestCase):

    def setUp(self):
        self.parser = Parser()

    def test_substitution(self):
        """
        (lambda. 2 0 1)(lambda. 0)

        1. shiftting on 1: lambda.0 -> lambda.0
        2. substitution: (lambda. 2 0 1)(lambda. 0) -> (2 (lambda.0) 1)
        3. shifting on -1: ( 2 (lambda.0) 1) -> (1 (lambda.0) 0)
        """
        ast = self.parser.parse("a/; b/; (lambda x. a x b)(lambda y.y);")
        ctx = self.parser._ctx
        elem = ast[2]
        term = core.evaluate(ctx, elem.term)
        self.assertEqual(type(term.left), syntax.TmApp)
        self.assertEqual(type(term.left.left), syntax.TmVar)
        self.assertEqual(term.left.left.index, 1)
        self.assertEqual(type(term.left.right), syntax.TmAbs)
        self.assertEqual(type(term.right), syntax.TmVar)
        self.assertEqual(term.right.index, 0)

        """
        lambda.(1 lambda.2 1) lambda.(1 0)

        1. shifting on 1: lambda.(1 0) - > lambda.(2 0)
        2. substitution:
            lambda.(1 lambda.2 1) lambda.(2 0) -> 1 lambda.(2 lambda.3 0)
        3. shifting -1:
            1 lambda.(2 lambda.3 0) -> 0 lambda.(1 lambda.2 0)
        """
        ast = self.parser.parse(
            "a/; (lambda x. a (lambda y. a x))(lambda z. a z);")
        ctx = self.parser._ctx
        elem = ast[1]
        term = core.evaluate(ctx, elem.term)
        self.assertEqual(type(term), syntax.TmApp)
        self.assertEqual(type(term.left), syntax.TmVar)
        self.assertEqual(term.left.index, 0)
        self.assertEqual(type(term.right), syntax.TmAbs)
        self.assertEqual(type(term.right.term), syntax.TmApp)
        self.assertEqual(type(term.right.term.left), syntax.TmVar)
        self.assertEqual(term.right.term.left.index, 1)
        self.assertEqual(type(term.right.term.right), syntax.TmAbs)
        self.assertEqual(type(term.right.term.right.term), syntax.TmApp)
        self.assertEqual(type(term.right.term.right.term.left), syntax.TmVar)
        self.assertEqual(term.right.term.right.term.left.index, 2)
        self.assertEqual(term.right.term.right.term.right.index, 0)

    def test_evaluate(self):
        ast = self.parser.parse(
            "(lambda z. (lambda x. z x)) (lambda y.y);")
        elem = ast[0]
        ctx = []
        term = core.evaluate(ctx, elem.term)
        # expected result: lambda x. (lambda y. y) x
        
        self.assertIsInstance(term, syntax.TmAbs)
        self.assertEqual(term.name, "x")

        self.assertIsInstance(term.term, syntax.TmApp)

        self.assertIsInstance(term.term.left, syntax.TmAbs)
        self.assertEqual(term.term.left.name, "y")

        self.assertIsInstance(term.term.right, syntax.TmVar)


if __name__ == '__main__':
    unittest.main()