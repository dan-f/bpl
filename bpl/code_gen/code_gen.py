from bpl.parser.parser import BPLType
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

    # string labels for immediate use
    # TODO: clean this up
    imm_str_labels = {
        'write_int': '$.WriteIntString',
        'write_line': '$.WritelnString',
        'write_string': '$.WriteSTringString',
        'arr_overflow': '$.ArrayOverflowString',
        'read_int': '$.ReadIntString'
    }

    def __init__(self, filename, tree, DEBUG=False):
        """Initialize a code generator object.

        :filename: The filename of the bpl program being compiled.
        :tree: The AST produced by the bpl type checker.

        """
        self.filename = filename
        self.tree = tree
        self.DEBUG = DEBUG
        self.assembly_file = '%s.s' % self.filename[:-4]
        with open(self.assembly_file, 'w') as f:
            f.truncate(0)

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
        # assign offsets to local variables; first is at self.WORD_SIZE
        local_offset = self.WORD_SIZE
        # locals_size is the number of bytes to allocate for local
        # variables.  We have to shave off one word because
        # assign_offsets_stmt returns the offset of the *next*
        # variable declaration.
        func.locals_size = self.assign_offsets_stmt(func.body, local_offset) - self.WORD_SIZE

    def assign_offsets_stmt(self, stmt, dec_offset):
        """Assign offset values to local variables in a compound statement.
        :dec_offset: is the offset of the first variable in :stmt:.
        Returns the starting offset for the next var declaration
        nested within :stmt:.

        """
        if stmt.kind == TN.COMP_STMT:
            if stmt.local_decs is not None:
                for local_dec in stmt.local_decs:
                    local_dec.offset = dec_offset
                    self.print_debug('local var {0} assigned offset {1}'.format(local_dec.name, local_dec.offset))
                    if local_dec.kind == TN.ARR_DEC:
                        dec_offset += self.WORD_SIZE * local_dec.size
                    else:
                        dec_offset += self.WORD_SIZE
            # assign offsets to locals in nested compound statements
            if stmt.stmt_list is not None:
                for body_stmt in stmt.stmt_list:
                    dec_offset = self.assign_offsets_stmt(body_stmt, dec_offset)
        elif stmt.kind == TN.IF_STMT:
            dec_offset = self.assign_offsets_stmt(stmt.true_body, dec_offset)
            if stmt.false_body is not None:
                dec_offset = self.assign_offsets_stmt(stmt.false_body, dec_offset)
        elif stmt.kind == TN.WHILE_STMT:
            dec_offset = self.assign_offsets_stmt(stmt.body, dec_offset)
        elif stmt.kind == TN.COMP_STMT:
            dec_offset = self.assign_offsets_stmt(stmt, dec_offset)
        return dec_offset

    def gen_all(self):
        """Generate code for self.tree."""
        # for now just generate code for the header and functions
        # TODO: stuff with global var declarations
        self.assign_offsets()
        self.gen_header()
        for dec in self.tree:
            if dec.kind == TN.FUN_DEC:
                self.gen_func(dec)

    def gen_header(self):
        """Generate assembly header.  For now, just generates I/O string
        declarations.

        """
        header = """\t.section .rodata
\t.WriteIntString: .string "%d "
\t.WritelnString: .string "\\n"
\t.WriteStringString: .string "%s "
\t.ArrayOverflowString: .string "You fell off the end of an array.\\n"
\t.ReadIntString: .string "%d"
\t.text
\t.globl main
"""
        self.write_to_assembly(header)

    def gen_func(self, func):
        """Generate code for a function tree node :func:."""
        self.write_label(func.name)
        self.write_line('movq', self.sp_64, self.fp_64, 'move sp into fp')
        self.write_line('subq', func.locals_size, self.sp_64, 'allocate local vars')
        self.gen_stmt(func.body)
        self.write_line('addq', func.locals_size, self.sp_64, 'deallocate local vars')
        self.write_line('ret')

    def gen_stmt(self, stmt):
        """Generate code for a statement tree node :stmt:."""
        if stmt.kind == TN.COMP_STMT:
            for body_stmt in stmt.stmt_list:
                self.gen_stmt(body_stmt)
        elif stmt.kind == TN.WRITE_STMT:
            self.gen_expr(stmt.expr)
            if stmt.expr.typ == BPLType('INT'):
                self.write_line('movq', self.acc_64, self.str_64, 'move val for printing')
                self.write_line('movq', self.imm_str_labels['write_int'], self.fmt_64)
                self.write_line('movq', 0, self.acc_64)
                self.write_line('call', 'printf')

    def gen_expr(self, expr):
        if expr.kind == TN.INT_EXP:
            self.write_line('movq', expr.val, self.acc_64)

    def write_line(self, instr, source=None, dest=None, comment=None):
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
        statement = '\t{0}'.format(instr)
        if source is not None:
            statement += ' {0}'.format(source)
        if dest is not None:
            statement += ', {0}'.format(dest)
        if comment is not None:
            statement += '\t# {0}\n'.format(comment)
        else:
            statement += '\n'
        self.write_to_assembly(statement)

    def write_label(self, label):
        """Generate a label."""
        self.write_to_assembly('{0}:\n'.format(label))

    def write_to_assembly(self, data):
        """Appends :data: to assembly file."""
        if self.DEBUG:
            print(data.rstrip())
        with open(self.assembly_file, 'a') as f:
            f.write(data)

    def print_debug(self, message):
        if self.DEBUG:
            print('{0}: {1}'.format(self.filename, message))
