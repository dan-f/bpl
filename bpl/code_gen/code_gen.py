from bpl.type_checker.type_checker import TypeChecker
from bpl.parser.parsetree import ParseTreeNode as TN


def registers(name):
    return Register32(name), Register64(name)


class Register():
    """Represents a register's string representation.  Alows us to handle
    offset here rather than in code generation functions.

    """
    def offset(self, val):
        return '{val}(%{self.name})'.format(self=self, val=val)

    def __str__(self):
        return '%{self.name}'.format(self=self)


class Register64(Register):
    def __init__(self, name):
        self.name = 'r{0}'.format(name)


class Register32(Register):
    def __init__(self, name):
        self.name = 'e{0}'.format(name)


class CodeGenerator():
    WORD_SIZE = 8               # x86-64 word size is 8 bytes

    # registers
    fp_32, fp_64 = registers('bp') # frame pointer
    sp_32, sp_64 = registers('sp') # stack pointer
    acc_32, acc_64 = registers('ax') # accumulator
    fmt_32, fmt_64 = registers('di') # format strings go here when printing
    str_32, str_64 = registers('si') # strings to be printed go here

    def __init__(self, filename, tree, DEBUG=False):
        """Initialize a code generator object.

        :filename: The filename of the bpl program being compiled.
        :tree: The AST produced by the bpl type checker.

        """
        self.filename = filename
        self.tree = tree
        self.DEBUG = DEBUG
        self.assembly_file = '%s.s' % self.filename

    def assign_offsets(self):
        """Walks through the parse tree :tree:, assigning
        offset-from-frame-pointer values to every variable declaration.

        """
        for dec in self.tree:
            if dec.kind == TN.FUN_DEC:
                self.assign_offsets_func(dec)

    def assign_offsets_func(self, func):
        """Assigns offset values to local variable/parameter declarations in a
        function declaration node :func:

        """
        param_offset = 2 * self.WORD_SIZE # parameters begin at 16(fp)
        if func.params is not None:
            for param in func.params:
                param.offset = param_offset
                self.print_debug('param {0} assigned offset {1}'.format(param.name, param.offset))
                param_offset += self.WORD_SIZE
        # assign offsets to local variables; first is at -self.WORD_SIZE
        local_offset = -self.WORD_SIZE
        self.assign_offsets_comp_stmt(func.body, local_offset)

    def assign_offsets_comp_stmt(self, stmt, start_offset):
        """Assign offset values to local variables in a compound statement.
        Returns the starting offset for the next compound statement.

        """
        if stmt.local_decs is not None:
            for local_dec in stmt.local_decs:
                local_dec.offset = start_offset
                self.print_debug('local var {0} assigned offset {1}'.format(local_dec.name, local_dec.offset))
                if local_dec.kind == TN.ARR_DEC:
                    start_offset -= self.WORD_SIZE * local_dec.size
                else:
                    start_offset -= self.WORD_SIZE
        # assign offsets to locals in nested compound statements
        if stmt.stmt_list is not None:
            for body_stmt in stmt.stmt_list:
                if body_stmt.kind == TN.IF_STMT:
                    start_offset = self.assign_offsets_comp_stmt(body_stmt.true_body, start_offset)
                    if body_stmt.false_body is not None:
                        start_offset = self.assign_offsets_comp_stmt(body_stmt.false_body, start_offset)
                elif body_stmt.kind == TN.WHILE_STMT:
                    start_offset = self.assign_offsets_comp_stmt(body_stmt.body, start_offset)
                elif body_stmt.kind == TN.COMP_STMT:
                    start_offset = self.assign_offsets_comp_stmt(body_stmt, start_offset)
        return start_offset

    def write_line(self, instr, source, dest=None, comment=None):
        """Generate an assembly instruction with one or two operands.  Offset
        formatting is handled by Register* classes.  If :source: or
        :dest: are integers, prepend a dollar to them for immediate
        mode.

        :instr: The assembly instruction.
        :source: The source operand.
        :dest: The destination operand.
        :comment: Optional assembly comment to append to the line.

        """
        # check for immediate mode
        if type(source) == int:
            source = '${0}'.format(source)
        if type(dest) == int:
            dest = '${0}'.format(dest)
        # build instruction
        statement = '\t{0} {1}'.format(instr, source)
        if dest is not None:
            statement += ', {2}'.format(dest)
        if comment is not None:
            statement += '\t# {0}\n'.format(comment)
        else:
            statement += '\n'
        # append instruction to assembly file
        with open(self.assembly_file, 'a') as f:
            f.write(statement)

    def print_debug(self, message):
        if self.DEBUG:
            print('{0}: {1}'.format(self.filename, message))
