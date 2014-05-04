from bpl.parser.parser import BPLType, ParseTreeNode as PTN
from bpl.parser.parsetree import *
from copy import copy


class TypeChecker():
    def __init__(self, filename, tree, DEBUG=False):
        """Initialize a type checker object.
        :filename: The filename of the bpl program being compiled.
        :tree: The AST produced by the bpl parser.
        :DEBUG: When true, print debugging info during execution.

        """
        self.filename = filename
        self.tree = tree
        self.DEBUG = DEBUG
        # A stack of dicts where the top dict represents symbols
        # declared in the current scope.
        self.symbol_tables = []

    def type_check(self):
        """Type check the AST."""
        self.link_all_refs()
        self.check_ast()

    def link_all_refs(self):
        """Links all symbol references in the parse tree (i.e. variable/array
        references, function calls) with their declarations.

        """
        # grab global declarations
        self.symbol_tables.append({})
        map(self.add_dec, self.tree)

        # link in all functions
        for dec in self.tree:
            if dec.kind == PTN.FUN_DEC:
                self.link_function(dec)

        # pop the global symbol table
        self.symbol_tables.pop()

    def link_function(self, func):
        """Link symbol references in function bodies."""
        self.symbol_tables.append({})
        # grab param declarations
        if func.params is not None:
            map(self.add_dec, func.params)
        # link function body/local decs
        self.link_comp_stmt(func.body, push_table=False)
        self.symbol_tables.pop()

    def link_stmt(self, stmt):
        """Link symbol references in statements."""
        if stmt.kind == PTN.EXPR_STMT:
            self.link_expr(stmt.expr)
        elif stmt.kind == PTN.COMP_STMT:
            self.link_comp_stmt(stmt)
        elif stmt.kind == PTN.IF_STMT:
            self.link_if_stmt(stmt)
        elif stmt.kind == PTN.WHILE_STMT:
            self.link_while_stmt(stmt)
        elif stmt.kind == PTN.RET_STMT:
            if stmt.val is not None:
                self.link_expr(stmt.val)
        elif stmt.kind == PTN.WRITE_STMT:
            self.link_expr(stmt.expr)

    def link_comp_stmt(self, comp_stmt, push_table=True):
        """Visit a compound statement, adding its local declarations to our
        symbol table, and linking its symbol references to their
        declarations.  If :push_table: is True, push a new symbol
        table onto the global stack.  :push_table: should only be
        False when called by link_function, as the local declarations
        'continue' the same scope as the parameter declarations.

        """
        if push_table:
            self.symbol_tables.append({})

        # grab local declarations
        if comp_stmt.local_decs is not None:
            map(self.add_dec, comp_stmt.local_decs)

        # link any symbol references to their original declarations
        if comp_stmt.stmt_list is not None:
            map(self.link_stmt, comp_stmt.stmt_list)
        # for stmt in comp_stmt.stmt_list:
        #     self.link_stmt(stmt)

        if push_table:
            self.symbol_tables.pop()

    def link_if_stmt(self, stmt):
        """Link references in an if statement."""
        self.link_expr(stmt.cond)
        self.link_stmt(stmt.true_body)
        if stmt.false_body is not None:
            self.link_stmt(stmt.false_body)

    def link_while_stmt(self, stmt):
        """Link references in a while statement."""
        self.link_expr(stmt.cond)
        self.link_stmt(stmt.body)

    def link_expr(self, expr):
        """Link references in an expression."""
        if expr.kind in (PTN.VAR_EXP, PTN.ARR_EXP):
            self.link_to_dec(expr)
            self.print_debug(expr.line_number, self.link_message(expr))
        elif expr.kind == PTN.FUN_CALL_EXP:
            self.link_to_dec(expr, function=True)
            self.print_debug(expr.line_number, self.link_message(expr))
            if expr.params is not None:
                map(self.link_expr, expr.params)
        elif expr.kind in (PTN.ADDR_EXP,
                           PTN.DEREF_EXP,
                           PTN.NEG_EXP):
            self.link_expr(expr.exp)
        elif isinstance(expr, OpExpNode):
            self.link_expr(expr.l_exp)
            self.link_expr(expr.r_exp)

    def add_dec(self, dec):
        """Add :dec.name: -> :dec: to the top-level symbol table."""
        # can't have an array declaration with size < 1
        if dec.kind == PTN.ARR_DEC and dec.size < 1:
            raise TypeException(
                '%s:%d: Array declaration must have size of at least 1.' % (
                    self.filename,
                    dec.line_number
                )
            )
        # mark global declarations
        dec.is_global = True if dec in self.tree else False
        self.symbol_tables[-1][dec.name] = dec

    def get_dec(self, symbol, function=False):
        """Returns the original declaration of :symbol:, or None if not found.
        If :function: is True, we're being asked for a function
        definition, so we look at the bottom of the stack for the
        global function definition.

        """
        if function:
            if symbol in self.symbol_tables[0]:
                return self.symbol_tables[0][symbol]
            else:
                return None
        else:
            # Search from top of stack downwards
            for table in reversed(self.symbol_tables):
                if symbol in table:
                    return table[symbol]
            return None

    def link_to_dec(self, node, function=False):
        """Point :node.dec: to its original declaration.  If :function: is
        True, we want to link to a function declaration in the global
        symbol table.  If no declaration is found in the symbol table,
        raise a TypeException.

        """
        dec = self.get_dec(node.name, function)
        if dec is not None:
            node.dec = dec
        else:
            raise TypeException('%s:%d: Name \"%s\" is undefined.' %
                                (self.filename,
                                 node.line_number,
                                 node.name))

    def link_message(self, node):
        """Returns a debugging message describing :node:'s original
        declaration.  Used for debugging.

        """
        return 'Symbol \"%s\" linked to declaration on line %d' % (
            node.name,
            node.dec.line_number
        )

    def check_ast(self):
        """Type check the AST"""
        map(lambda x: self.check_func(x) if x.kind is PTN.FUN_DEC else None,
            self.tree)

    def check_func(self, func):
        """Type check a function declaration :func:."""
        # make sure func.typ is equal to return value
        ret_type = func.typ
        self.check_comp_stmt(func.body, ret_type)
        self.print_debug(
            func.line_number,
            'Function declaration [%s] assigned type %s.' % (
                func.name, func.typ
            )
        )

    def check_stmt(self, stmt, ret_type=None):
        """Type check a generic statement :stmt:.  When :ret_type: is passed,
        verify that the type of any return statement matches
        :ret_type:.

        """
        if stmt.kind == PTN.EXPR_STMT:
            self.check_expr(stmt.expr)
        elif stmt.kind == PTN.COMP_STMT:
            self.check_comp_stmt(stmt, ret_type)
        elif stmt.kind == PTN.IF_STMT:
            self.check_expr(stmt.cond)
            self.check_stmt(stmt.true_body)
            if stmt.false_body is not None:
                self.check_stmt(stmt.false_body)
        elif stmt.kind == PTN.WHILE_STMT:
            self.check_expr(stmt.cond)
            self.check_stmt(stmt.body)
        elif stmt.kind == PTN.RET_STMT:
            self.check_ret_stmt(stmt, ret_type)
        elif stmt.kind == PTN.WRITE_STMT:
            self.check_expr(stmt.expr)
            if stmt.expr.typ not in (BPLType('INT'), BPLType('STRING')):
                raise TypeException('%s:%d: Cannot write type [%s].' %
                                    (self.filename,
                                     stmt.line_number,
                                     stmt.expr.typ))

    def check_comp_stmt(self, stmt, ret_type=None):
        """Type check a compound statement :stmt:.  When :ret_type: is passed,
        verify that the type of any return statement matches
        :ret_type:.

        """
        if stmt.stmt_list is not None:
            map(lambda x: self.check_stmt(x, ret_type), stmt.stmt_list)

    def check_ret_stmt(self, stmt, ret_type):
        """Type check a return statement :stmt:"""
        ret_val = stmt.val
        if ret_type == BPLType('VOID'):
            if ret_val is not None:
                raise TypeException('%s:%d: Cannot return value from void function.' %
                                    (self.filename,
                                     stmt.line_number))
        else:
            if ret_val is not None:
                self.check_expr(stmt.val)
                self.expect_type_match(
                    ret_type,
                    'Returned value does not match declared type',
                    stmt.val
                )
            else:
                raise TypeException('%s:%d: Missing return value.' %
                                    (self.filename,
                                     stmt.line_number))

    def check_expr(self, expr):
        """Verify type-correctness of generic expression :expr:"""
        if expr.kind == PTN.VAR_EXP:
            self.check_var_expr(expr)
        elif expr.kind == PTN.ARR_EXP:
            self.check_arr_expr(expr)
        elif expr.kind == PTN.ADDR_EXP:
            self.check_addr_expr(expr)
        elif expr.kind == PTN.DEREF_EXP:
            self.check_deref_expr(expr)
        elif expr.kind == PTN.FUN_CALL_EXP:
            self.check_funcall_expr(expr)
        elif expr.kind == PTN.READ_EXP:
            self.check_read_expr(expr)
        elif expr.kind == PTN.ASSIGN_EXP:
            self.check_assign_expr(expr)
        elif expr.kind == PTN.COMP_EXP:
            self.check_comp_expr(expr)
        elif expr.kind == PTN.ARITH_EXP:
            self.check_arith_expr(expr)
        elif expr.kind == PTN.NEG_EXP:
            self.check_neg_expr(expr)
        elif expr.kind == PTN.INT_EXP:
            self.check_int_expr(expr)
        elif expr.kind == PTN.STR_EXP:
            self.check_str_expr(expr)

    def check_var_expr(self, expr):
        """Verify type-correctness of var expression :expr:"""
        expr.typ = expr.dec.typ
        if expr.typ == BPLType('VOID'):
            raise TypeException('%s:%d: Cannot declare void variable.' %
                                (self.filename,
                                 expr.line_number))
        self.print_debug(
            expr.line_number,
            'Variable expression [%s] assigned type %s.' % (
                expr.name, expr.typ
            )
        )

    def check_arr_expr(self, expr):
        """Verify type-correctness of array expression :expr:"""
        self.check_expr(expr.index)
        self.expect_type_match(
            BPLType('INT'),
            'Array index expression must evaluate to int',
            expr.index
        )
        expr.typ = expr.dec.typ
        if expr.typ == BPLType('VOID'):
            raise TypeException('%s:%d: Cannot declare void array.' %
                                (self.filename,
                                 stmt.line_number))
        self.print_debug(
            expr.line_number,
            'Array expression [%s] assigned type %s.' % (
                expr.name, expr.typ
            )
        )

    def check_addr_expr(self, expr):
        """Verify type-correctness of address expression :expr:"""
        self.check_expr(expr.exp)
        # can only address variables or array elements
        if expr.exp.kind in (PTN.VAR_EXP, PTN.ARR_EXP):
            expr.typ = copy(expr.exp.typ)
            expr.typ.address()
            self.print_debug(
                expr.line_number,
                'Address expression assigned type %s.' % (expr.typ)
            )
        else:
            raise TypeException('%s:%d: Can\'t address type [%s].' %
                                (self.filename,
                                 expr.line_number,
                                 expr.exp.typ))

    def check_deref_expr(self, expr):
        """Verify type-correctness of dereference expression :expr:"""
        self.check_expr(expr.exp)
        if expr.exp.typ.is_pointer():
            expr.typ = copy(expr.exp.typ)
            expr.typ.deref()
            self.print_debug(
                expr.line_number,
                'Dereference expression assigned type %s.' % (expr.typ)
            )
        else:
            raise TypeException('%s:%d: Can\'t dereference type [%s].' %
                                (self.filename,
                                 expr.line_number,
                                 expr.exp.typ))

    def check_funcall_expr(self, expr):
        """Verify type-correctness of function call expression :expr:"""
        # verify same number of args and params
        args = expr.params
        params = expr.dec.params
        args_length = 0
        params_length = 0
        if args is not None:
            for arg in args:
                args_length += 1
        if params is not None:
            for param in params:
                params_length += 1
        if params_length != args_length:
            raise TypeException(
                '%s:%d: Wrong number of arguments given for function [%s] (%d expected, %d given)' % (
                    self.filename,
                    expr.line_number,
                    expr.name,
                    params_length,
                    args_length
                )
            )
        # verify types of args match corresponding types of params
        if params_length > 0:
            map(self.check_arg_vs_param, expr.params, expr.dec.params)
        expr.typ = expr.dec.typ
        self.print_debug(
            expr.line_number,
            'Function call expression [%s] assigned type %s.' % (
                expr.name, expr.typ
            )
        )

    def check_read_expr(self, expr):
        """Verify type-correctness of read expression :expr:"""
        expr.typ = BPLType('INT')
        self.print_debug(
            expr.line_number,
            'Read expression assigned type %s.' % (expr.typ)
        )

    def check_assign_expr(self, expr):
        """Verify type-correctness of assignment expression :expr:"""
        self.check_expr(expr.l_exp)
        self.check_expr(expr.r_exp)
        if expr.l_exp.kind in (PTN.VAR_EXP, PTN.ARR_EXP, PTN.DEREF_EXP):
            self.expect_type_match(
                None,
                'Left/Right hand sides of assignment expression don\'t match',
                expr.l_exp,
                expr.r_exp
            )
            expr.typ = expr.l_exp.typ
        else:
            raise TypeException(
                '%s:%d: Left-hand side (kind [%s]) of assignment expression is unassignable' % (
                    self.filename,
                    expr.line_number,
                    expr.l_exp.kind
                )
            )
        self.print_debug(
            expr.line_number,
            'Assignment expression assigned type %s.' % (expr.typ)
        )

    def check_arith_expr(self, expr):
        """Verify type-correctness of assignment expression :expr:"""
        self.check_expr(expr.l_exp)
        self.check_expr(expr.r_exp)
        self.expect_type_match(
            BPLType('INT'),
            'Arithmetic expression must operate on INT types',
            expr.l_exp,
            expr.r_exp
        )
        expr.typ = expr.l_exp.typ
        self.print_debug(
            expr.line_number,
            'Arithmetic expression assigned type %s.' % (expr.typ)
        )

    def check_comp_expr(self, expr):
        """Verify type-correctness of comparison expression :expr:"""
        self.check_expr(expr.l_exp)
        self.check_expr(expr.r_exp)
        self.expect_type_match(
            BPLType('INT'),
            'Comparison expression must operate on INT types',
            expr.l_exp,
            expr.r_exp
        )
        expr.typ = BPLType('INT')
        self.print_debug(
            expr.line_number,
            'Comparison expression assigned type %s.' % (expr.typ)
        )

    def check_neg_expr(self, expr):
        """Verify type-correctness of negation expression :expr:"""
        self.check_expr(expr.exp)
        self.expect_type_match(
            BPLType('INT'),
            'Negation expression must operate on integer type',
            expr.exp
        )
        expr.typ = expr.exp.typ
        self.print_debug(
            expr.line_number,
            'Negation expression assigned type %s.' % (expr.typ)
        )

    def check_int_expr(self, expr):
        """Verify type-correctness of integer expression :expr:"""
        expr.typ = BPLType('INT')
        self.print_debug(
            expr.line_number,
            'Integer expression %s assigned type %s.' % (expr.val, expr.typ)
        )

    def check_str_expr(self, expr):
        """Verify type-correctness of integer expression :expr:"""
        expr.typ = BPLType('STRING')
        self.print_debug(
            expr.line_number,
            'String expression assigned type %s.' % (expr.typ)
        )

    def check_arg_vs_param(self, arg, param):
        """Verify that :arg: and :param: have the same type, where :arg: is an
        argument in a function call, and :param: is the corresponding
        parameter in the function declaration.

        """
        self.check_expr(arg)
        self.expect_type_match(
            None,
            'Function argument doesn\'t match declared type %s' % (
                param.typ
            ),
            arg,
            param
        )

    def expect_type_match(self, expected_type, message, *tree_nodes):
        """Verify that all ParseTreeNodes in :tree_nodes: have the same type
        as each other, comparing their types to :expected_type: if
        given.  If types don't match, raise a TypeException containing
        message :message:.

        """
        if expected_type is None:
            expected_type = tree_nodes[0].typ

        for tree_node in tree_nodes:
            if tree_node.typ != expected_type:
                raise TypeException(
                    '%s:%d: Mismatched types; expected %s, but got %s\n%s' % (
                        self.filename,
                        tree_node.line_number,
                        expected_type,
                        tree_node.typ,
                        message
                    )
                )

    def print_debug(self, line_number, message):
        """Print :message: if self.DEBUG is True."""
        if self.DEBUG:
            print('%s:%d: %s' % (self.filename, line_number, message))


class TypeException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)
