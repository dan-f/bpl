from bpl.parser.parser import Parser
import sys

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for filename in sys.argv[1:]:
            p = Parser(filename)
            p.parse()
            print
            print(p.tree)
    else:
        p = Parser('bpl/test/parse_example.bpl')
        p.parse()
        print
        print(p.tree)
