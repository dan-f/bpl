# TODO: ask Bob about read nodes (both expression and statement) - Should these
# nodes have a field for their values?  We don't know their values until run
# time, right?
class ParseTreeNode():
    """Represents a node in the parse-tree.  Inherited by more specific
    parse tree node classes.

    """
    # Node 'kinds' represent the particular type of parse tree node, defined by
    # our grammar rules.
    PROG       = 0
    DEC_LIST   = 1
    DEC        = 2
    VAR_DEC    = 3
    TYPE_SPEC  = 4
    FUN_DEC    = 5
    PARAMS     = 6
    PARAM_LIST = 7
    PARAM      = 8
    COMP_STMT  = 9
    LOCAL_DECS = 10
    STMT_LIST  = 11
    STMT       = 12
    EXPR_STMT  = 13
    IF_STMT    = 14
    WHILE_STMT = 15
    RET_STMT   = 16
    WRITE_STMT = 17
    EXPR       = 18
    VAR        = 19
    COMP_EXP   = 20
    RELOP      = 21
    E          = 22
    ADDOP      = 23
    T          = 24
    MULOP      = 25
    F          = 26
    FACTOR     = 27
    FUN_CALL   = 28
    ARGS       = 29
    ARG_LIST   = 30

    constants = {
        0  : 'PROG',
        1  : 'DEC_LIST',
        2  : 'DEC',
        3  : 'VAR_DEC',
        4  : 'TYPE_SPEC',
        5  : 'FUN_DEC',
        6  : 'PARAMS',
        7  : 'PARAM_LIST',
        8  : 'PARAM',
        9  : 'COMP_STMT',
        10 : 'LOCAL_DECS',
        11 : 'STMT_LIST',
        12 : 'STMT',
        13 : 'EXPR_STMT',
        14 : 'IF_STMT',
        15 : 'WHILE_STMT',
        16 : 'RET_STMT',
        17 : 'WRITE_STMT',
        18 : 'EXPR',
        19 : 'VAR',
        20 : 'COMP_EXP',
        21 : 'RELOP',
        22 : 'E',
        23 : 'ADDOP',
        24 : 'T',
        25 : 'MULOP',
        26 : 'F',
        27 : 'FACTOR',
        28 : 'FUN_CALL',
        29 : 'ARGS',
        30 : 'ARG_LIST'
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
        return 'Kind: %s, Line: %d\n' % (
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


class VarDecNode(DecNode):
    """Represents a variable declaration node in the parse tree."""

    def __init__(self, kind, line_number, name, typ, is_pointer=False, nxt=None):
        """Initialize a variable declaration node.

        :is_pointer: Whether we're declaring a pointer or not.

        """
        DecNode.__init__(self, kind, line_number, name, typ, nxt)
        self.is_pointer = is_pointer


class ArrayDecNode(VarDecNode):
    """Represents an array declaration node in the parse tree."""

    def __init__(self, kind, line_number, name, typ, size, nxt=None):
        """Initialize a variable declaration node.

        :size: Size of the array.

        """
        VarDecNode.__init__(
            self, kind, line_number, name, typ, is_pointer=False, nxt=nxt
        )
        self.size = size


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
        return '%sExpression:\n%s\n%s' % (
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
        return '%sLocal Declarations:\n%s\nStatement List:\n%s\n%s' % (
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


class ReadStmtNode(StmtNode):
    """Represents a read statement node in the parse tree."""

    def __init__(self, kind, line_number, nxt=None):
        """Initializes a read statement node."""
        StmtNode.__init__(self, kind, line_number, nxt)


class WriteStmtNode(StmtNode):
    """Represents a write statement node in the parse tree."""

    def __init__(self, kind, line_number, val, nxt=None):
        """Initializes a write statement node.

        :val: The expression who'se value we're writing.

        """
        StmtNode.__init__(self, kind, line_number, nxt)
        self.val = val


class WritelnStmtNode(StmtNode):
    """Represents a writeln statement node in the parse tree."""

    def __init__(self, kind, line_number, val, nxt=None):
        """Initializes a writeln statement node.

        :val: The expression who'se value we're writing.

        """
        StmtNode.__init__(self, kind, line_number, nxt)
        self.val = val


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


class StrExpNode(ExpNode):
    """Represents a string expression node in the parse tree."""

    def __init__(self, kind, line_number, val, nxt=None):
        """Initializes a string expression node.

        :val: String value that this node represents.

        """
        ExpNode.__init__(self, kind, line_number, nxt)
        self.val = val


class VarExpNode(ExpNode):
    """Represents a variable expression node in the parse tree."""

    def __init__(self, kind, line_number, name, nxt=None):
        """Initializes a variable expression node.

        :name: The string name of this variable.

        """
        ExpNode.__init__(self, kind, line_number, nxt)
        self.name = name

    def __str__(self):
        return '%sName: %s\n%s' % (self.base_str(), self.name, self.nxt)


class OpExpNode(ExpNode):
    """Represents an operator expression node in the parse tree."""

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


class FunCallExpNode(ExpNode):
    """Represents a function call node in the parse tree."""

    def __init__(self, kind, line_number, params, nxt=None):
        """Initializes a function call node.

        :params: An expression node representing the list of
        parameters to the function call.

        """
        ExpNode.__init__(self, kind, line_number, nxt)
        self.params = params


class ReadExpNode(ExpNode):
    """Represents a read node in the parse tree."""

    def __init__(self, kind, line_number, nxt=None):
        """Initializes a read expression node."""
        ExpNode.__init__(self, kind, line_number, nxt)


class AddrExpNode(ExpNode):
    """Represents an address node in the parse tree."""

    def __init__(self, kind, line_number, var, nxt=None):
        """Initializes an address expression node.

        :var: The variable who'se address we're referencing

        """
        ExpNode.__init__(self, kind, line_number, nxt)
        self.var = var


class DerefExpNode(ExpNode):
    """Represents a dereference node in the parse tree."""

    def __init__(self, kind, line_number, var, nxt=None):
        """Initializes a dereference expression node.

        :var: The variable who we're dereferencing

        """
        ExpNode.__init__(self, kind, line_number, nxt)
        self.var = var


def indent(s):
    """Returns the indented string representation of :s: by putting a pipe
    and one space before each line.

    """
    if s is None:
        return None

    indented = ''
    for line in str(s).splitlines():
        indented += "| %s\n" % line
    return indented
