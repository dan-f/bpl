from bpl.parser.parser import Parser
from bpl.type_checker.type_checker import TypeChecker

if __name__ == '__main__':
    p = Parser('bpl/test/type_checker_example.bpl')
    p.parse()
    t = TypeChecker(p.filename, p.tree, DEBUG=True)
    t.link_all_refs()
