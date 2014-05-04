from bpl.parser.parser import BPLType
from bpl.parser.parsetree import ParseTreeNode as TN
from bpl.scanner.token import TokenType


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
    div_32, div_64 = registers('bx') # when dividing, put dividends here
    rem_32, rem_64 = registers('dx') # when dividing, remainders end up here
    fmt_32, fmt_64 = registers('di') # when printing, put format strings here
    str_32, str_64 = registers('si') # when printing, put strings to be printed here


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
        self._label_counter = 0
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
        # assign offsets to local variables; first is at -self.WORD_SIZE
        local_offset = -self.WORD_SIZE
        # locals_size is the number of bytes to allocate for local
        # variables.  We have to shave off one word because
        # assign_offsets_stmt returns the offset of the *next*
        # variable declaration.
        func.locals_size = -(self.assign_offsets_stmt(func.body, local_offset)) - self.WORD_SIZE
        self.print_debug("local decs size: {0}".format(func.locals_size))

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
                        dec_offset -= self.WORD_SIZE * local_dec.size
                    else:
                        dec_offset -= self.WORD_SIZE
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
        self.assign_offsets()
        self.gen_header()
        for dec in self.tree:
            if dec.kind == TN.FUN_DEC:
                self.gen_func(dec)

    def gen_header(self):
        """Generate assembly header.  For now, just generates I/O string
        declarations.

        """
        # allocate global variables
        alloc_string = '\t.comm {0}, {1}, {2}\n'
        for dec in self.tree:
            if dec.kind == TN.VAR_DEC:
                self.write_to_assembly(alloc_string.format(dec.name, self.WORD_SIZE, 32))
            elif dec.kind == TN.ARR_DEC:
                self.write_to_assembly(alloc_string.format(dec.name, dec.size * self.WORD_SIZE, 32))
        self.write_to_assembly('\t.section .rodata\n')
        self.write_to_assembly('\t.WriteIntString: .string "%d "\n')
        self.write_to_assembly('\t.WritelnString: .string "\\n"\n')
        self.write_to_assembly('\t.WriteStringString: .string "%s "\n')
        self.write_to_assembly('\t.ArrayOverflowString: .string "You fell off the end of an array.\\n"\n')
        self.write_to_assembly('\t.ReadIntString: .string "%d"\n')
        self.write_to_assembly('\t.text\n')
        self.write_to_assembly('\t.globl main\n')

    def gen_func(self, func):
        """Generate code for a function tree node :func:."""
        self.write_label(func.name)
        self.write_instr('movq', self.sp_64, self.fp_64, 'move sp into fp')
        self.write_instr('subq', func.locals_size, self.sp_64, 'allocate local vars')
        func.ret_label = '.{0}_ret'.format(func.name)
        self.gen_stmt(func.body, func)
        self.write_label(func.ret_label)
        self.write_instr('addq', func.locals_size, self.sp_64, 'deallocate local vars')
        self.write_instr('ret')

    def gen_stmt(self, stmt, func):
        """Generate code for a statement tree node :stmt:.  :func: is the
        function that :stmt: belongs to.

        """
        if stmt.kind == TN.COMP_STMT:
            if stmt.stmt_list is not None:
                for body_stmt in stmt.stmt_list:
                    self.gen_stmt(body_stmt, func)
        elif stmt.kind in (TN.WRITE_STMT, TN.WRITELN_STMT):
            self.gen_write_stmt(stmt, func)
        elif stmt.kind == TN.IF_STMT:
            self.gen_if_stmt(stmt, func)
        elif stmt.kind == TN.WHILE_STMT:
            self.gen_while_stmt(stmt, func)
        elif stmt.kind == TN.RET_STMT:
            self.gen_expr(stmt.val)
            self.write_instr('jmp', func.ret_label)
        elif stmt.kind == TN.EXPR_STMT:
            self.gen_expr(stmt.expr)

    def gen_write_stmt(self, stmt, func):
        """Generate code for a write or writeln statement :stmt:."""
        if stmt.kind == TN.WRITE_STMT:
            self.gen_expr(stmt.expr)
            if stmt.expr.typ == BPLType('INT'):
                self.write_instr('movl', self.acc_32, self.str_32, 'move val for printing')
                self.write_instr('movq', self.imm_str_labels['write_int'], self.fmt_64)
        elif stmt.kind == TN.WRITELN_STMT:
            self.write_instr('movq', self.imm_str_labels['write_line'], self.fmt_64)
        self.write_instr('movl', 0, self.acc_32)
        self.write_instr('call', 'printf')

    def gen_if_stmt(self, stmt, func):
        """Generate code for an if statement :stmt:."""
        self.gen_expr(stmt.cond)
        true_label = self.new_label()
        continue_label = self.new_label()
        self.write_instr('cmpl', 0, self.acc_32)
        self.write_instr('jne', true_label)
        if stmt.false_body is not None:
            self.gen_stmt(stmt.false_body, func)
        self.write_instr('jmp', continue_label)
        self.write_label(true_label)
        self.gen_stmt(stmt.true_body, func)
        self.write_label(continue_label)

    def gen_while_stmt(self, stmt, func):
        """Generate code for a while statement :stmt:."""
        cond_label = self.new_label()
        continue_label = self.new_label()
        self.write_label(cond_label)
        self.gen_expr(stmt.cond)
        self.write_instr('cmpl', 0, self.acc_32, 'check while condition')
        self.write_instr('je', continue_label)
        self.gen_stmt(stmt.body, func)
        self.write_instr('jmp', cond_label)
        self.write_label(continue_label)

    def gen_expr(self, expr):
        """Generate code for an expression :expr:."""
        if expr.kind == TN.INT_EXP:
            self.write_instr('movq', expr.val, self.acc_64)
        elif expr.kind == TN.VAR_EXP:
            self.gen_var_expr(expr)
        elif expr.kind in (TN.ARITH_EXP, TN.COMP_EXP):
            self.gen_binary_expr(expr)
        elif expr.kind == TN.ASSIGN_EXP:
            self.gen_assign_expr(expr)
        elif expr.kind == TN.FUN_CALL_EXP:
            self.gen_funcall_expr(expr)
        elif expr.kind == TN.ADDR_EXP:
            self.gen_addr_expr(expr)
        elif expr.kind == TN.DEREF_EXP:
            self.gen_deref_expr(expr)

    def gen_var_expr(self, expr):
        """Generate code for a variable expression :expr:."""
        if expr.dec.is_global:
            self.write_instr('movq', expr.name, self.acc_64)
        else:
            self.write_instr('movq', self.fp_64.offset(expr.dec.offset), self.acc_64)

    def gen_binary_expr(self, expr):
        """Generate code for a binary expression :expr: (i.e. an OpExpNode).
        This is either an arithmetic expression or a comparison
        expression.

        """
        self.gen_expr(expr.l_exp)
        self.write_instr('push', self.acc_64, comment='push LHS')
        self.gen_expr(expr.r_exp)
        if expr.kind == TN.ARITH_EXP:
            self.gen_arith_expr(expr)
        elif expr.kind == TN.COMP_EXP:
            self.gen_comp_expr(expr)
        self.write_instr('addq', 8, self.sp_64, comment='pop LHS from stack')

    def gen_arith_expr(self, expr):
        """Generate code for an arithmetic expression"""
        if expr.op.typ == TokenType.PLUS:
            self.write_instr('addl', self.sp_64.offset(0), self.acc_32, comment='perform addition')
        elif expr.op.typ == TokenType.MINUS:
            self.write_instr('subl', self.acc_32, self.sp_64.offset(0), comment='perform subtraction')
            self.write_instr('movl', self.sp_64.offset(0), self.acc_32)
        elif expr.op.typ == TokenType.STAR:
            self.write_instr('imul', self.sp_64.offset(0), self.acc_32, comment='perform multiplication')
        elif expr.op.typ in (TokenType.SLASH, TokenType.MOD):
            # dividend is on top of stack, divisor is in accumulator
            self.write_instr('movl', self.acc_32, self.div_32, comment='move divisor')
            self.write_instr('movl', self.sp_64.offset(0), self.acc_32, comment='move dividend')
            self.write_instr('cltq')
            self.write_instr('cqto')
            self.write_instr('idivl', self.div_32, comment='perform division')
            # quotient is now in accumulator
            if expr.op.typ == TokenType.MOD:
                # place remainder in accumulator
                self.write_instr('movl', self.rem_32, self.acc_32)

    def gen_comp_expr(self, expr):
        """Generate code for a comparison expression.  If the comparison is
        true, leave 1 in the accumulator, otherwise 0.

        """
        self.write_instr(
            'cmpl', self.acc_32, self.sp_64.offset(0),
            comment='LHS {0} RHS'.format(TokenType.constants[expr.op.typ])
        )
        false_label = self.new_label()
        continue_label = self.new_label()
        if expr.op.typ == TokenType.BOOLEQ:
            jump_instr = 'jne'
        elif expr.op.typ == TokenType.NEQUAL:
            jump_instr = 'je'
        elif expr.op.typ == TokenType.LESS:
            jump_instr = 'jge'
        elif expr.op.typ == TokenType.LEQUAL:
            jump_instr = 'jg'
        elif expr.op.typ == TokenType.GREATER:
            jump_instr = 'jle'
        elif expr.op.typ == TokenType.GEQUAL:
            jump_instr = 'jl'
        self.write_instr(jump_instr, false_label)
        self.write_instr('movl', 1, self.acc_32) # true
        self.write_instr('jmp', continue_label)
        self.write_label(false_label)
        self.write_instr('movl', 0, self.acc_32) # false
        self.write_label(continue_label)

    def gen_assign_expr(self, expr):
        """Generate code for an assignment expression :expr:."""
        # TODO: support arrays and dereferences
        # (currently only supporting assignment to variable expressions)
        lhs = expr.l_exp
        self.gen_expr(expr.r_exp)
        if lhs.kind == TN.VAR_EXP:
            if lhs.dec.is_global:
                self.write_instr('movq', self.acc_64, lhs.name)
            else:
                var_offset = lhs.dec.offset
                self.write_instr('movq', self.acc_64, self.fp_64.offset(var_offset))
        elif lhs.kind == TN.ARR_EXP:
            pass
        elif lhs.kind == TN.DEREF_EXP:
            pass

    def gen_addr_expr(self, expr):
        """Generate code for an address expression :expr:."""
        # TODO: Support globals
        if expr.exp.kind == TN.VAR_EXP:
            if expr.exp.dec.is_global:
                address = expr.exp.name
            else:
                address = self.fp_64.offset(expr.exp.dec.offset)
        elif expr.exp.kind == TN.ARR_EXP:
            if expr.exp.dec.is_global:
                offset = expr.exp.index * self.WORD_SIZE
                address = '{}({})'.format(offset, expr.exp.name)
            else:
                offset = expr.exp.dec.offset + expr.exp.index * self.WORD_SIZE
                address = self.fp_64.offset(offset)
        self.write_instr('leaq', address, self.acc_64)

    def gen_deref_expr(self, expr):
        """Generate code for a dereference expression :expr:."""
        self.gen_expr(expr.exp)  # put address in the accumulator
        self.write_instr('movl', self.acc_64.offset(0), self.acc_32)

    def write_instr(self, instr, source=None, dest=None, comment=None):
        """Write an assembly instruction with one or two operands.  Offset
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
            # want column 32
            tab_len = 8
            num_tabs = 1 + (32 - (tab_len + len(statement))) / tab_len
            statement += '{0}# {1}\n'.format('\t' * num_tabs, comment)
        else:
            statement += '\n'
        self.write_to_assembly(statement)

    def gen_funcall_expr(self, expr):
        """Generate code for a function call expression :expr:."""
        # push args on stack in reverse order
        args = [arg for arg in expr.params]
        for arg in reversed(args):
            self.gen_expr(arg)
            # TODO: is it cool that we have to push 64 bit version?
            self.write_instr('push', self.acc_64, comment='push arg')
        self.write_instr('push', self.fp_64, comment='save fp')
        self.write_instr('call', expr.name)
        self.write_instr('pop', self.fp_64, comment='restore fp')
        self.write_instr('addq', len(args) * self.WORD_SIZE, self.sp_64, comment='pop args')

    def write_label(self, label):
        """Write a label with name :label: to file."""
        self.write_to_assembly('{0}:\n'.format(label))

    def new_label(self):
        """Return a new, unique label name."""
        label = '.L{0}'.format(self._label_counter)
        self._label_counter += 1
        return label

    def write_to_assembly(self, data):
        """Appends :data: to assembly file."""
        if self.DEBUG:
            print(data.rstrip())
        with open(self.assembly_file, 'a') as f:
            f.write(data)

    def print_debug(self, message):
        if self.DEBUG:
            print('{0}: {1}'.format(self.filename, message))
