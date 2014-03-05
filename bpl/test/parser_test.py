from bpl.parser.parser import Parser

if __name__ == '__main__':
    p = Parser('bpl/test/parse_declarations.bpl')
    p.parse()
    print
    print(p.tree)
