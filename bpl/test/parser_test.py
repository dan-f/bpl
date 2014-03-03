from bpl.parser.parser import Parser

if __name__ == '__main__':
    p = Parser('bpl/test/parse_expressions.bpl')
    p.program()
    print
    print(p.tree)
