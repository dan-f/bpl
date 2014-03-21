from bpl.parser.parser import ParseTreeNode
from bpl.parser.parsetree import *


class TypeChecker():
    def __init__(self, filename, tree, DEBUG=False):
        self.filename = filename
        self.tree = tree
        self.DEBUG = DEBUG
        # A stack of dicts where the top dict represents symbols
        # declared in the current scope.
        self.symbol_tables = []

    def type_check(self):
        self.link_all_refs(self.tree)
        # bottom_up(tree)

    def link_all_refs(self):
        """Links all symbol references in the parse tree (i.e. variable/array
        references, function calls) with their declarations.

        """
        # grab global declarations
        self.symbol_tables.append({})
        map(self.add_dec, self.tree)

        # link in all functions
        for dec in self.tree:
            if dec.kind == ParseTreeNode.FUN_DEC:
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
        if stmt.kind == ParseTreeNode.EXPR_STMT:
            self.link_expr(stmt.expr)
        elif stmt.kind == ParseTreeNode.COMP_STMT:
            self.link_comp_stmt(stmt)
        elif stmt.kind == ParseTreeNode.IF_STMT:
            self.link_if_stmt(stmt)
        elif stmt.kind == ParseTreeNode.WHILE_STMT:
            self.link_while_stmt(stmt)
        elif stmt.kind == ParseTreeNode.RET_STMT:
            if stmt.val is not None:
                self.link_expr(stmt.val)
        elif stmt.kind == ParseTreeNode.WRITE_STMT:
            self.link_expr(stmt.expr)

    def link_comp_stmt(self, comp_stmt, push_table=True):
        """Visit a compound statement, adding its local declarations to our
        symbol table, and linking its symbol references to their
        declarations.  If :push_table: is True, push a new symbol
        table onto the global stack.  :push_table: should only be
        False when called by link_function, as the local declarations
        'continue' the parameter declarations.

        """
        if push_table:
            self.symbol_tables.append({})

        # grab local declarations
        if comp_stmt.local_decs is not None:
            map(self.add_dec, comp_stmt.local_decs)

        # link any symbol references to their original declarations
        for stmt in comp_stmt.stmt_list:
            self.link_stmt(stmt)

        if push_table:
            self.symbol_tables.pop()

    def link_if_stmt(self, stmt):
        """Link references in an if statement."""
        self.link_expr(stmt.cond)
        self.link_stmt(stmt.true_body)
        if stmt.false_body is not None:
            self.link_stmt(stmt.false_body)

    def link_while_stmt(self, stmt):
        self.link_expr(stmt.cond)
        self.link_stmt(stmt.body)

    def link_expr(self, expr):
        """Link references in an expression."""
        if expr.kind in (ParseTreeNode.VAR_EXP, ParseTreeNode.ARR_EXP):
            self.link_to_dec(expr)
            if self.DEBUG:
                self.print_link(expr)
        elif expr.kind == ParseTreeNode.FUN_CALL_EXP:
            self.link_to_dec(expr, function=True)
            if self.DEBUG:
                self.print_link(expr)
            map(self.link_expr, expr.params)
        elif expr.kind in (ParseTreeNode.ADDR_EXP,
                           ParseTreeNode.DEREF_EXP,
                           ParseTreeNode.NEG_EXP):
            self.link_expr(expr.exp)
        elif isinstance(expr, OpExpNode):
            self.link_expr(expr.l_exp)
            self.link_expr(expr.r_exp)

    def add_dec(self, dec):
        """Add :dec.name: -> :dec: to the top-level symbol table."""
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

    def print_link(self, node):
        """Prints a ParseTreeNode's original declaration.  Used for debugging.

        """
        print('%s:%d: Symbol \"%s\" linked to declaration on line %d' %
              (self.filename,
               node.line_number,
               node.name,
               node.dec.line_number))


class TypeException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)
