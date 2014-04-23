from bpl.parser.parser import Parser
from bpl.type_checker.type_checker import TypeChecker
from bpl.code_gen.code_gen import CodeGenerator
from subprocess import call
import sys

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for filename in sys.argv[1:]:
            p = Parser(filename)
            p.parse()
            t = TypeChecker(p.filename, p.tree, DEBUG=True)
            t.type_check()
            c = CodeGenerator(t.filename, t.tree, DEBUG=True)
            c.gen_all()
            prog_name = p.filename[:-4]
            assembly_name = prog_name + '.s'
            call(['gcc', '-g', assembly_name, '-o', prog_name])
    else:
        p = Parser('bpl/test/code_gen_example.bpl')
        p.parse()
        t = TypeChecker(p.filename, p.tree)
        t.type_check()
        c = CodeGenerator(t.filename, t.tree, DEBUG=True)
        c.gen_all()
        prog_name = p.filename[:-4]
        assembly_name = prog_name + '.s'
        call(['gcc', '-g', assembly_name, '-o', prog_name])
