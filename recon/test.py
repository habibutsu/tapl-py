import unittest
from parser import Parser
from lexer import Lexer
import syntax
import core

class ParserTestCase(unittest.TestCase):
    
    def setUp(self):
        self.parser = Parser()

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


class ReconstructionTestCase(unittest.TestCase):
    def setUp(self):
        self.parser = Parser()

    def test_arrow(self):
        """
        Constraints:
            Bool -> Bool ==> Bool -> 0X
            (Bool -> Bool) -> 0X ==> (Bool -> Bool) -> 1X
        After unify:
            0X ==> Bool,
            1X ==> 0X
        """
        ast = self.parser.parse(
            "(lambda x: Bool -> Bool. x true)(lambda y: Bool. y);")
        cmd = ast[0]
        ctx = []
        iuvargen = core.uvargen()
        nextuvar = lambda: next(iuvargen)
        (tyT, constr) = core.recon(cmd.term, ctx, nextuvar)
        unify_constr = core.unify(ctx, constr)
        self.assertEqual(len(unify_constr), 2)
        self.assertIsInstance(unify_constr[0][0], syntax.TyId)
        self.assertIsInstance(unify_constr[0][1], syntax.TyBool)
        self.assertIsInstance(unify_constr[1][0], syntax.TyId)
        self.assertIsInstance(unify_constr[1][1], syntax.TyId)

        self.assertEqual(unify_constr[0][0].name, "?X0")
        self.assertEqual(unify_constr[1][0].name, "?X1")
        self.assertEqual(unify_constr[1][1].name, "?X0")

        tyT = core.applysubst(unify_constr, tyT)
        self.assertIsInstance(tyT, syntax.TyBool)

    def test_if_statement(self):
        ast = self.parser.parse(
            "((lambda x:Bool. if x then false else true) false);")
        cmd = ast[0]
        ctx = []
        iuvargen = core.uvargen()
        nextuvar = lambda: next(iuvargen)
        (tyT, constr) = core.recon(cmd.term, ctx, nextuvar)
        unify_constr = core.unify(ctx, constr)
        tyT = core.applysubst(unify_constr, tyT)
        self.assertIsInstance(tyT, syntax.TyBool)

    def _print_constr(self, constr):
        for (num, (t1, t2)) in enumerate(constr):
            print("%s. " % num, end="")
            syntax.printty(t1)
            print(" ==> ", end="")
            syntax.printty(t2)
            print("")

    def test_abs(self):
        """
        (lambda x:X->X. x 0) (lambda y:Nat. y);

        Type:
            1X
        Constraints:
            0. X -> X -> ?X0 ==> Nat -> Nat -> ?X1
            1. X -> X ==> Nat -> 0X

        Unification:
        1
            X -> X ==> Nat -> Nat
            ?X0 ==> ?X1
            X -> X ==> Nat -> 0X

        2
            X ==> Nat
            X ==> Nat
            ?X0 ==> ?X1
            X -> X ==> Nat -> ?X0

        3
            ...

        N
            0. ?X0=Nat
            1. ?X1=?X0
            2. X=Nat}

        Result:
            Nat
        """
        source = "(lambda x:X->X. x 0) (lambda y:Nat. y);"
        ast = self.parser.parse(source)
        cmd = ast[0]
        ctx = []
        iuvargen = core.uvargen()
        nextuvar = lambda: next(iuvargen)
        (tyT, constr) = core.recon(cmd.term, ctx, nextuvar)
        syntax.printty(tyT)
        unify_constr = core.unify(ctx, constr)
        tyT = core.applysubst(unify_constr, tyT)
        self.assertIsInstance(tyT, syntax.TyNat)

if __name__ == '__main__':
    unittest.main()