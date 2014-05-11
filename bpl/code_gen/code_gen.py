from bpl.parser.parser import BPLType
from bpl.parser.parsetree import ParseTreeNode as TN
from bpl.scanner.token import TokenType
from itertools import count


class Register():
    """Represents a register's string representation.  Alows us to handle
    offset here rather than in code generation functions.

    """
    def __init__(self, name):
        self.name = 'r{0}'.format(name)

    def offset(self, val):
        return '{val}(%{self.name})'.format(self=self, val=val)

    def __str__(self):
        return '%{self.name}'.format(self=self)


class Label():
    """Simply represents a label, allowing us to grab its immediate
    representation (i.e. label preceded by a dollar) so that we don't
    have to do that all over the place in our code.

    """
    def __init__(self, name):
        self.name = name

    def immediate(self):
        return '${self.name}'.format(self=self)

    def offset(self, val):
        return '{val}({self.name})'.format(self=self, val=val)

    def __str__(self):
        return self.name


class CodeGenerator():
    WORD_SIZE = 8               # x86-64 word size is 8 bytes

    # registers
    fp = Register('bp') # frame pointer
    sp = Register('sp') # stack pointer
    acc = Register('ax') # accumulator
    div = Register('bx') # when dividing, put divisors here
    rem = Register('dx') # when dividing, remainders end up here
    fmt = Register('di') # when printing, put format strings here
    out = Register('si') # when printing, put values to be printed here
    trash = Register('12') # spare register


    # string labels for immediate use
    write_int_label = Label('.WriteIntString')
    write_line_label = Label('.WritelnString')
    write_string_label = Label('.WriteStringString')
    arr_overflow_label = Label('.ArrayOverflowString')
    read_int_label = Label('.ReadIntString')

    def __init__(self, filename, tree, DEBUG=False):
        """Initialize a code generator object.

        :filename: The filename of the bpl program being compiled.
        :tree: The AST produced by the bpl type checker.

        """
        self.filename = filename
        self.tree = tree
        self.DEBUG = DEBUG
        self.string_dict = {}
        self.string_label_count = count()
        self.control_label_count = count()
        self.assembly_filename = '%s.s' % self.filename[:-4]

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
                    if local_dec.kind == TN.ARR_DEC:
                        dec_offset -= self.WORD_SIZE * (local_dec.size - 1)
                        local_dec.offset = dec_offset
                        self.print_debug('local var {0} assigned offset {1}'.format(local_dec.name, local_dec.offset))
                        dec_offset -= self.WORD_SIZE
                    else:
                        local_dec.offset = dec_offset
                        self.print_debug('local var {0} assigned offset {1}'.format(local_dec.name, local_dec.offset))
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

    def build_string_dict(self, node=None):
        """Construct the global string dictionary."""
        if node is None:
            map(self.build_string_dict, self.tree)
        elif node.kind == TN.STR_EXP:
            self.string_dict[node.val] = self.new_string_label()
        elif node.kind == TN.FUN_DEC:
            self.build_string_dict(node.body)
        elif node.kind == TN.COMP_STMT:
            if node.stmt_list is not None:
                map(self.build_string_dict, node.stmt_list)
        elif node.kind == TN.EXPR_STMT:
            self.build_string_dict(node.expr)
        elif node.kind == TN.IF_STMT:
            if node.true_body is not None:
                self.build_string_dict(node.true_body)
            if node.false_body is not None:
                self.build_string_dict(node.false_body)
        elif node.kind == TN.WHILE_STMT:
            self.build_string_dict(node.body)
        elif node.kind == TN.RET_STMT:
            self.build_string_dict(node.val)
        elif node.kind == TN.WRITE_STMT:
            self.build_string_dict(node.expr)
        elif node.kind == TN.ASSIGN_EXP:
            self.build_string_dict(node.r_exp)
        elif node.kind == TN.FUN_CALL_EXP:
            if node.params is not None:
                map(self.build_string_dict, node.params)
        elif node.kind in (TN.ADDR_EXP, TN.DEREF_EXP):
            self.build_string_dict(node.exp)

    def gen_all(self):
        """Generate code for self.tree."""
        # for now just generate code for the header and functions
        self.assembly_file = open(self.assembly_filename, 'w')
        self.assembly_file.truncate()
        self.assign_offsets()
        self.gen_header()
        for dec in self.tree:
            if dec.kind == TN.FUN_DEC:
                self.gen_func(dec)
        self.assembly_file.close()

    def gen_header(self):
        """Generate assembly header."""
        # allocate global variables
        alloc_instr = '\t.comm {0}, {1}, {2}\n'
        for dec in self.tree:
            if dec.kind == TN.VAR_DEC:
                self.write_to_assembly(alloc_instr.format(dec.name, self.WORD_SIZE, 64))
            elif dec.kind == TN.ARR_DEC:
                self.write_to_assembly(alloc_instr.format(dec.name, dec.size * self.WORD_SIZE, 64))
        self.write_to_assembly('\t.section .rodata\n')
        # allocate strings
        self.build_string_dict()
        for string, label in self.string_dict.iteritems():
            self.write_to_assembly('\t{}: .string "{}"\n'.format(label, string))
        self.write_to_assembly('\t{}: .string "%lld "\n'.format(self.write_int_label))
        self.write_to_assembly('\t{}: .string "\\n"\n'.format(self.write_line_label))
        self.write_to_assembly('\t{}: .string "%s "\n'.format(self.write_string_label))
        self.write_to_assembly('\t{}: .string "You fell off the end of an array.\\n"\n'.format(self.arr_overflow_label))
        self.write_to_assembly('\t{}: .string "%d"\n'.format(self.read_int_label))
        self.write_to_assembly('\t.text\n')
        self.write_to_assembly('\t.globl main\n')

    def gen_func(self, func):
        """Generate code for a function tree node :func:."""
        self.write_label(func.name)
        self.write_instr('mov', self.sp, self.fp, 'move sp into fp')
        self.write_instr('sub', func.locals_size, self.sp, 'allocate local vars')
        func.ret_label = '.{0}_ret'.format(func.name)
        self.gen_stmt(func.body, func)
        self.write_label(func.ret_label)
        self.write_instr('add', func.locals_size, self.sp, 'deallocate local vars')
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
            self.write_instr('mov', self.acc, self.out, 'move val for printing')
            if stmt.expr.typ == BPLType('INT'):
                self.write_instr('mov', self.write_int_label.immediate(), self.fmt)
            elif stmt.expr.typ == BPLType('STRING'):
                self.write_instr('mov', self.write_string_label.immediate(), self.fmt)
        elif stmt.kind == TN.WRITELN_STMT:
            self.write_instr('mov', self.write_line_label.immediate(), self.fmt)
        self.write_instr('mov', 0, self.acc)
        self.write_instr('call', 'printf')

    def gen_if_stmt(self, stmt, func):
        """Generate code for an if statement :stmt:."""
        self.gen_expr(stmt.cond)
        true_label = self.new_control_label()
        continue_label = self.new_control_label()
        self.write_instr('cmp', 0, self.acc)
        self.write_instr('jne', true_label)
        if stmt.false_body is not None:
            self.gen_stmt(stmt.false_body, func)
        self.write_instr('jmp', continue_label)
        self.write_label(true_label)
        self.gen_stmt(stmt.true_body, func)
        self.write_label(continue_label)

    def gen_while_stmt(self, stmt, func):
        """Generate code for a while statement :stmt:."""
        cond_label = self.new_control_label()
        continue_label = self.new_control_label()
        self.write_label(cond_label)
        self.gen_expr(stmt.cond)
        self.write_instr('cmp', 0, self.acc, 'check while condition')
        self.write_instr('je', continue_label)
        self.gen_stmt(stmt.body, func)
        self.write_instr('jmp', cond_label)
        self.write_label(continue_label)

    def gen_expr(self, expr):
        """Generate code for an expression :expr:."""
        if expr.kind == TN.VAR_EXP:
            self.gen_var_expr(expr)
        elif expr.kind == TN.ARR_EXP:
            self.gen_arr_expr(expr)
        elif expr.kind == TN.ADDR_EXP:
            self.gen_addr_expr(expr)
        elif expr.kind == TN.DEREF_EXP:
            self.gen_deref_expr(expr)
        elif expr.kind == TN.FUN_CALL_EXP:
            self.gen_funcall_expr(expr)
        elif expr.kind == TN.READ_EXP:
            self.gen_read_expr(expr)
        elif expr.kind == TN.ASSIGN_EXP:
            self.gen_assign_expr(expr)
        elif expr.kind in (TN.ARITH_EXP, TN.COMP_EXP):
            self.gen_binary_expr(expr)
        elif expr.kind == TN.NEG_EXP:
            self.gen_neg_expr(expr)
        elif expr.kind == TN.INT_EXP:
            self.write_instr('mov', expr.val, self.acc)
        elif expr.kind == TN.STR_EXP:
            self.write_instr('mov', self.string_dict[expr.val].immediate(), self.acc)

    def gen_var_expr(self, expr):
        """Generate code for a variable expression :expr:."""
        if expr.dec.kind == TN.VAR_DEC:
            self.gen_var_addr(expr)
            self.write_instr('mov', self.trash.offset(0), self.acc)
        elif expr.dec.kind == TN.ARR_DEC:
            self.gen_arr_base_addr(expr)
            self.write_instr('mov', self.trash, self.acc)

    def gen_arr_expr(self, expr):
        """Generate code for an array indexing expression :expr:."""
        self.gen_arr_addr(expr)
        self.write_instr('mov', self.trash.offset(0), self.acc)

    def gen_addr_expr(self, expr):
        """Generate code for an address expression :expr:."""
        if self.expr.exp.kind == TN.VAR_EXP:
            self.gen_var_addr(expr.exp)
        elif self.expr.exp.kind == TN.ARR_EXP:
            self.gen_arr_addr(expr.exp)
        self.write_instr('mov', self.trash, self.acc)

    def gen_deref_expr(self, expr):
        """Generate code for a dereference expression :expr:."""
        self.gen_expr(expr.exp)  # put address in the accumulator
        self.write_instr('mov', self.acc.offset(0), self.acc)

    def gen_funcall_expr(self, expr):
        """Generate code for a function call expression :expr:."""
        # push args on stack in reverse order
        args = [arg for arg in expr.params]
        for arg in reversed(args):
            self.gen_expr(arg)
            self.write_instr('push', self.acc, comment='push arg')
        self.write_instr('push', self.fp, comment='save fp')
        self.write_instr('call', expr.name)
        self.write_instr('pop', self.fp, comment='restore fp')
        self.write_instr('add', len(args) * self.WORD_SIZE, self.sp, comment='pop args')

    def gen_read_expr(self, expr):
        """Generate code for a read expression :expr:"""
        self.write_instr('sub', 40 * self.WORD_SIZE, self.sp)
        self.write_instr('lea', self.sp.offset(24 * self.WORD_SIZE), self.out)
        self.write_instr('mov', self.read_int_label.immediate(), self.fmt)
        self.write_instr('call', 'scanf')
        self.write_instr('mov', self.sp.offset(24 * self.WORD_SIZE), self.acc)
        self.write_instr('add', 40 * self.WORD_SIZE, self.sp)

    def gen_assign_expr(self, expr):
        """Generate code for an assignment expression :expr:."""
        self.gen_expr(expr.r_exp)
        self.write_instr('push', self.acc)
        self.gen_l_value(expr.l_exp)  # l_value now in trash
        self.write_instr('pop', self.acc)  # pop RHS into acc
        self.write_instr('mov', self.acc, self.trash.offset(0))  # assign RHS to l_value

    def gen_l_value(self, expr):
        """Generates code to put the address of a variable or array expression
        :expr: into the trash register.

        """
        if expr.kind == TN.VAR_EXP:
            self.gen_var_addr(expr)
        elif expr.kind == TN.ARR_EXP:
            self.gen_arr_addr(expr)
        elif expr.kind == TN.DEREF_EXP:
            self.gen_expr(expr.exp)  # acc now contains address of expression we want to dereference
            self.write_instr('mov', self.acc, self.trash)

    def gen_var_addr(self, expr):
        """Helper function to put the address of the variable represented by
        variable expression :expr: in the trash register.

        """
        if expr.dec.is_global:
            self.write_instr('lea', expr.name, self.trash)
        else:
            self.write_instr('lea', self.fp.offset(expr.dec.offset), self.trash)

    def gen_arr_addr(self, expr):
        """Helper function to put the address of the array represented by array
        expression :expr: in the trash register.

        """
        self.gen_expr(expr.index)  # evaluate array index
        self.write_instr('imul', self.WORD_SIZE, self.acc)  # compute offset of array bucket
        self.gen_arr_base_addr(expr)  # put base address of array in trash
        self.write_instr('add', self.acc, self.trash)  # address of array bucket now in trash

    def gen_arr_base_addr(self, expr):
        """Helper function; given a variable/array expression :expr:, generate
        code to compute the base address of the array in the trash register.

        """
        if expr.dec.is_global:
            self.write_instr('lea', expr.name, self.trash)
        else:
            # either parameter or local var
            is_param = expr.dec.offset > 0
            if is_param:
                self.write_instr('mov', self.fp.offset(expr.dec.offset), self.trash)
            else:
                self.write_instr('lea', self.fp.offset(expr.dec.offset), self.trash)

    def gen_binary_expr(self, expr):
        """Generate code for a binary expression :expr: (i.e. an OpExpNode).
        This is either an arithmetic expression or a comparison
        expression.

        """
        self.gen_expr(expr.l_exp)
        self.write_instr('push', self.acc, comment='push LHS')
        self.gen_expr(expr.r_exp)
        if expr.kind == TN.ARITH_EXP:
            self.gen_arith_expr(expr)
        elif expr.kind == TN.COMP_EXP:
            self.gen_comp_expr(expr)
        self.write_instr('add', self.WORD_SIZE, self.sp, comment='pop LHS from stack')

    def gen_arith_expr(self, expr):
        """Generate code for an arithmetic expression"""
        if expr.op.typ == TokenType.PLUS:
            self.write_instr('add', self.sp.offset(0), self.acc, comment='perform addition')
        elif expr.op.typ == TokenType.MINUS:
            self.write_instr('sub', self.acc, self.sp.offset(0), comment='perform subtraction')
            self.write_instr('mov', self.sp.offset(0), self.acc)
        elif expr.op.typ == TokenType.STAR:
            self.write_instr('imul', self.sp.offset(0), self.acc, comment='perform multiplication')
        elif expr.op.typ in (TokenType.SLASH, TokenType.MOD):
            # dividend is on top of stack, divisor is in accumulator
            self.write_instr('mov', self.acc, self.div, comment='move divisor')
            self.write_instr('mov', self.sp.offset(0), self.acc, comment='move dividend')
            self.write_instr('cqto')
            self.write_instr('idiv', self.div, comment='perform division')
            # quotient is now in accumulator
            if expr.op.typ == TokenType.MOD:
                # place remainder in accumulator
                self.write_instr('mov', self.rem, self.acc)

    def gen_comp_expr(self, expr):
        """Generate code for a comparison expression.  If the comparison is
        true, leave 1 in the accumulator, otherwise 0.

        """
        self.write_instr(
            'cmp', self.acc, self.sp.offset(0),
            comment='LHS {0} RHS'.format(TokenType.constants[expr.op.typ])
        )
        false_label = self.new_control_label()
        continue_label = self.new_control_label()
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
        self.write_instr('mov', 1, self.acc) # true
        self.write_instr('jmp', continue_label)
        self.write_label(false_label)
        self.write_instr('mov', 0, self.acc) # false
        self.write_label(continue_label)

    def gen_neg_expr(self, expr):
        """Generate code for a negation expression :expr:."""
        self.gen_expr(expr.exp)
        self.write_instr('push', self.acc)
        self.write_instr('mov', 0, self.acc)
        self.write_instr('sub', self.sp.offset(0), self.acc)
        self.write_instr('add', self.WORD_SIZE, self.sp)

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

    def write_label(self, label):
        """Write a label with name :label: to file."""
        self.write_to_assembly('{0}:\n'.format(label))

    def new_control_label(self):
        """Return a new, unique label name."""
        return Label('.L{}'.format(self.control_label_count.next()))

    def new_string_label(self):
        """Return a new, unique label name."""
        return Label('.S{}'.format(self.string_label_count.next()))

    def write_to_assembly(self, data):
        """Appends :data: to assembly file."""
        self.assembly_file.write(data)

    def print_debug(self, message):
        if self.DEBUG:
            print('{0}: {1}'.format(self.filename, message))
