class ParseTreeNode():
    """Represents a node in the parse-tree.  Inherited by more specific
    parse tree node classes.

    """
    # Node 'kinds' represent the particular type of parse tree node, defined by
    # our grammar rules.
    FUN_DEC = 0
    VAR_DEC = 1
    ARR_DEC = 2
    COMP_STMT = 3
    EXPR_STMT = 4
    IF_STMT = 5
    WHILE_STMT = 6
    RET_STMT = 7
    WRITE_STMT = 8
    WRITELN_STMT = 9
    VAR_EXP = 10
    ARR_EXP = 11
    ADDR_EXP = 12
    DEREF_EXP = 13
    FUN_CALL_EXP = 14
    READ_EXP = 15
    ASSIGN_EXP = 16
    COMP_EXP = 17
    ARITH_EXP = 18
    NEG_EXP = 19
    INT_EXP = 20
    STR_EXP = 21

    constants = {
        0: 'FUN_DEC',
        1: 'VAR_DEC',
        2: 'ARR_DEC',
        3: 'COMP_STMT',
        4: 'EXPR_STMT',
        5: 'IF_STMT',
        6: 'WHILE_STMT',
        7: 'RET_STMT',
        8: 'WRITE_STMT',
        9: 'WRITELN_STMT',
        10: 'VAR_EXP',
        11: 'ARR_EXP',
        12: 'ADDR_EXP',
        13: 'DEREF_EXP',
        14: 'FUN_CALL_EXP',
        15: 'READ_EXP',
        16: 'ASSIGN_EXP',
        17: 'COMP_EXP',
        18: 'ARITH_EXP',
        19: 'NEG_EXP',
        20: 'INT_EXP',
        21: 'STR_EXP'
    }

    def __init__(self, kind, line_number, nxt=None):
        """Initializes a parse tree node.

        :kind: The kind of grammar node we are.
        :line_number: This node's line number.
        :nxt: The next tree node.

        """
        self.kind = kind
        self.line_number = line_number
        self.nxt = nxt

    def base_str(self):
        return '%s (Line: %d)' % (
            self.constants[self.kind],
            self.line_number
        )

    def __str__(self):
        return '%s\n%s' % (self.base_str(), self.nxt)


#######################
#  Declaration Nodes  #
#######################

class DecNode(ParseTreeNode):
    """Represents a declaration node in the parse tree."""

    def __init__(self, kind, line_number, name, typ, nxt=None):
        """Initializes a Declaration node.

        :name: The name of the represented variable/function.
        :typ: Represents variable type for variable declarations and return
        type for function declarations.

        """
        ParseTreeNode.__init__(self, kind, line_number, nxt)
        self.name = name
        self.typ = typ


class FunDecNode(DecNode):
    """Represents a function declaration node in the parse tree."""

    def __init__(self, kind, line_number, name, typ, params, body, nxt=None):
        """Initialize a function declaration node.

        :params: A DecNode representing function parameters.
        :body: A CompStmtNode representing the function's body.

        """
        DecNode.__init__(self, kind, line_number, name, typ, nxt)
        self.params = params
        self.body = body

    def __str__(self):
        return '%s, Name: %s, Return Type: [%s]\nParams:\n%s\nBody:\n%s\n%s' % (
            self.base_str(),
            self.name,
            self.typ,
            indent(self.params),
            indent(self.body),
            self.nxt
        )


class VarDecNode(DecNode):
    """Represents a variable declaration node in the parse tree."""

    def __init__(self, kind, line_number, name, typ, is_pointer=False, nxt=None):
        """Initialize a variable declaration node.

        :is_pointer: Whether we're declaring a pointer or not.

        """
        DecNode.__init__(self, kind, line_number, name, typ, nxt)
        self.is_pointer = is_pointer

    def __str__(self):
        return '%s%s, Name: %s, Type: [%s]\n%s' % (
            self.base_str(),
            ' *pointer*' if self.is_pointer else '',
            self.name,
            self.typ,
            self.nxt
        )


class ArrDecNode(VarDecNode):
    """Represents an array declaration node in the parse tree."""

    def __init__(self, kind, line_number, name, typ, size, nxt=None):
        """Initialize an array declaration node.

        :size: Size of the array.

        """
        VarDecNode.__init__(
            self, kind, line_number, name, typ, is_pointer=False, nxt=nxt
        )
        self.size = size

    def __str__(self):
        return '%s, Name: %s, Type: [%s], Size: %s\n%s' % (
            self.base_str(),
            self.name,
            self.typ,
            self.size,
            self.nxt
        )


#####################
#  Statement Nodes  #
#####################

class StmtNode(ParseTreeNode):
    """Represents a statement node in the parse tree."""

    def __init__(self, kind, line_number, nxt=None):
        ParseTreeNode.__init__(self, kind, line_number, nxt)


class ExpStmtNode(StmtNode):
    """Represents an expression statement node in the parse tree."""

    def __init__(self, kind, line_number, expr, nxt=None):
        """Initialize an if statement node.

        :expr: The expression that this statement represents.

        """
        StmtNode.__init__(self, kind, line_number, nxt)
        self.expr = expr

    def __str__(self):
        return '%s\nExpression:\n%s\n%s' % (
            self.base_str(),
            indent(self.expr),
            self.nxt
        )


class IfStmtNode(StmtNode):
    """Represents an if statement node in the parse tree."""

    def __init__(self, kind, line_number, cond, true_body, false_body, nxt=None):
        """Initialize an if statement node.

        :cond: The if statement's conditional expression.
        :true_body: The statement to be executed when the condition is true.
        :false_body: The statement to be executed when the condition is false.

        """
        StmtNode.__init__(self, kind, line_number, nxt)
        self.cond = cond
        self.true_body = true_body
        self.false_body = false_body

    def __str__(self):
        return '%s\nCondition:\n%s\nTrue Body:\n%s\nFalse Body:\n%s\n%s' % (
            self.base_str(),
            indent(self.cond),
            indent(self.true_body),
            indent(self.false_body),
            self.nxt
        )


class WhileStmtNode(StmtNode):
    """Represents a while statement node in the parse tree."""

    def __init__(self, kind, line_number, cond, body, nxt=None):
        """Initialize a while statement node.

        :cond: The while statement's conditional expression.
        :body: The statement to be executed while the condition is true.

        """
        StmtNode.__init__(self, kind, line_number, nxt)
        self.cond = cond
        self.body = body

    def __str__(self):
        return '%s\nCondition:\n%s\nBody:\n%s\n%s' % (
            self.base_str(),
            indent(self.cond),
            indent(self.body),
            self.nxt
        )


class CompStmtNode(StmtNode):
    """Represents a compound statement node in the parse tree."""

    def __init__(self, kind, line_number, local_decs, stmt_list, nxt=None):
        """Initialize a compound statement node.

        :local_decs: A list of local declarations, beginning with a declaration
        node.
        :stmt_list: A list of statements, beginning with a statement node.

        """
        StmtNode.__init__(self, kind, line_number, nxt)
        self.local_decs = local_decs
        self.stmt_list = stmt_list

    def __str__(self):
        return '%s\nLocal Declarations:\n%s\nStatement List:\n%s\n%s' % (
            self.base_str(),
            indent(self.local_decs),
            indent(self.stmt_list),
            self.nxt
        )


class RetStmtNode(StmtNode):
    """Represents a return statement node in the parse tree."""

    def __init__(self, kind, line_number, val, nxt=None):
        """Initializes a return statement node.

        :val: The expression who'se value we're returning.

        """
        StmtNode.__init__(self, kind, line_number, nxt)
        self.val = val

    def __str__(self):
        return '%s\nReturn Value:\n%s\n%s' % (
            self.base_str(),
            indent(self.val),
            self.nxt
        )

class WriteStmtNode(StmtNode):
    """Represents a write statement node in the parse tree."""

    def __init__(self, kind, line_number, expr, nxt=None):
        """Initializes a write statement node.

        :expr: The expression who'se value we're writing.

        """
        StmtNode.__init__(self, kind, line_number, nxt)
        self.expr = expr

    def __str__(self):
        return '%s\nValue:\n%s\n%s' % (
            self.base_str(),
            indent(self.expr),
            self.nxt
        )


class WritelnStmtNode(StmtNode):
    """Represents a writeln statement node in the parse tree."""

    def __init__(self, kind, line_number, nxt=None):
        """Initializes a writeln statement node."""
        StmtNode.__init__(self, kind, line_number, nxt)


######################
#  Expression Nodes  #
######################

class ExpNode(ParseTreeNode):
    """Represents an expression node in the parse tree."""

    def __init__(self, kind, line_number, nxt=None):
        """Initializes an expression node."""
        ParseTreeNode.__init__(self, kind, line_number, nxt)


class IntExpNode(ExpNode):
    """Represents an integer expression node in the parse tree."""

    def __init__(self, kind, line_number, val, nxt=None):
        """Initializes an integer expression node.

        :val: Integer value that this node represents.

        """
        ExpNode.__init__(self, kind, line_number, nxt)
        self.val = val

    def __str__(self):
        return '%s, Value: %s\n%s' % (self.base_str(), self.val, self.nxt)


class StrExpNode(ExpNode):
    """Represents a string expression node in the parse tree."""

    def __init__(self, kind, line_number, val, nxt=None):
        """Initializes a string expression node.

        :val: String value that this node represents.

        """
        ExpNode.__init__(self, kind, line_number, nxt)
        self.val = val

    def __str__(self):
        return '%s, Value: \"%s\"\n%s' % (self.base_str(), self.val, self.nxt)


class OpExpNode(ExpNode):
    """Represents an operator expression node in the parse tree.  This
    could be something like:

    `a = b`, `a + b`, or `a > b`

    :kind:'s of this node can be (TODO)
    """

    def __init__(self, kind, line_number, op, l_exp, r_exp, nxt=None):
        """Initializes a variable expression node.

        :op: A token representing the operator.
        :l_exp: The left expression.
        :r_exp: The right expression.

        """
        ExpNode.__init__(self, kind, line_number, nxt)
        self.op = op
        self.l_exp = l_exp
        self.r_exp = r_exp

    def __str__(self):
        return '%s, Operator: [%s]\nLeft Expression:\n%s\nRight Expression:\n%s\n%s' % (
            self.base_str(),
            self.op,
            indent(self.l_exp),
            indent(self.r_exp),
            self.nxt
        )


class FunCallExpNode(ExpNode):
    """Represents a function call node in the parse tree."""

    def __init__(self, kind, line_number, name, params, nxt=None):
        """Initializes a function call node.

        :name: The string name of the function.
        :params: An expression node representing the list of
        parameters to the function call.

        """
        ExpNode.__init__(self, kind, line_number, nxt)
        self.name = name
        self.params = params

    def __str__(self):
        return '%s, Name: %s\nParams:\n%s\n%s' % (
            self.base_str(),
            self.name,
            indent(self.params),
            self.nxt
        )


class ReadExpNode(ExpNode):
    """Represents a read node in the parse tree."""

    def __init__(self, kind, line_number, nxt=None):
        """Initializes a read expression node."""
        ExpNode.__init__(self, kind, line_number, nxt)


class VarExpNode(ExpNode):
    """Represents a variable expression node in the parse tree."""

    def __init__(self, kind, line_number, name, nxt=None):
        """Initializes a variable expression node.

        :name: The string name of this variable.

        """
        ExpNode.__init__(self, kind, line_number, nxt)
        self.name = name

    def __str__(self):
        return '%s, Name: %s\n%s' % (self.base_str(), self.name, self.nxt)


class ArrExpNode(ExpNode):
    """Represents an array expression node in the parse tree."""

    def __init__(self, kind, line_number, name, index, nxt=None):
        """Initializes an array expression node.

        :name: The string name of this array.
        :index: An expression node who'se value indexes this array.

        """
        ExpNode.__init__(self, kind, line_number, nxt)
        self.name = name
        self.index = index

    def __str__(self):
        return '%s, Name: %s\nIndex:\n%s\n%s' % (
            self.base_str(), self.name, indent(self.index), self.nxt
        )


class AddrExpNode(ExpNode):
    """Represents an address node in the parse tree."""

    def __init__(self, kind, line_number, exp, nxt=None):
        """Initializes an address expression node.

        :exp: The expression who'se address we're referencing

        """
        ExpNode.__init__(self, kind, line_number, nxt)
        self.exp = exp

    def __str__(self):
        return '%s\nExpression:\n%s\n%s' % (
            self.base_str(), indent(self.exp), self.nxt
        )


class DerefExpNode(ExpNode):
    """Represents a dereference node in the parse tree."""

    def __init__(self, kind, line_number, exp, nxt=None):
        """Initializes a dereference expression node.

        :exp: The expression which we're dereferencing

        """
        ExpNode.__init__(self, kind, line_number, nxt)
        self.exp = exp

    def __str__(self):
        return '%s\nExpression:\n%s\n%s' % (
            self.base_str(), indent(self.exp), self.nxt
        )


class NegExpNode(ExpNode):
    """Represents a negated node in the parse tree."""

    def __init__(self, kind, line_number, exp, nxt=None):
        """Initializes a negated expression node.

        :exp: The expression which we're negating

        """
        ExpNode.__init__(self, kind, line_number, nxt)
        self.exp = exp

    def __str__(self):
        return '%s\nExpression:\n%s\n%s' % (
            self.base_str(),
            indent(self.exp),
            self.nxt
        )


def indent(s):
    """Returns the indented string representation of :s: by putting a pipe
    and one space before each line.

    """
    if s is None:
        return None

    indented = ''
    for line in str(s).splitlines():
        indented += "| %s\n" % line
    return indented[:-1]
