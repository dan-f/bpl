from bpl.parser.parser import Parser
from bpl.type_checker.type_checker import TypeChecker
import sys

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for filename in sys.argv[1:]:
            p = Parser(filename)
            p.parse()
            t = TypeChecker(p.filename, p.tree, DEBUG=True)
            t.type_check()
    else:
        p = Parser('bpl/test/type_checker_example.bpl')
        p.parse()
        t = TypeChecker(p.filename, p.tree, DEBUG=True)
        t.type_check()
