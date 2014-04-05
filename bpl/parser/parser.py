from bpl.parser.parsetree import *
from bpl.scanner.scanner import Scanner
from bpl.scanner.token import TokenType


class Parser():
    def __init__(self, filename, tree=None):
        """Initialize a parser to parse the contents of :filename:."""
        self.filename = filename
        self.scan = Scanner(filename)
        self.scan.get_next_token()  # grab our first token
        self.tree = tree

    def expect(self, *args):
        """Verify that the current token's type matches what is expected.
        If the tokentypes match, advance the scanner.
        Otherwise throw an error.

        :*args: The first n-1 args are any acceptable TokenTypes, and
        the last is the message of the Exception we will throw if the
        types do not match.

        """
        current_token = self.cur_token()
        message = args[-1]
        token_types = args[:-1]
        if current_token.typ not in token_types:
            raise ParseException('%s:%d: Expected %s, but got %s: \"%s\"\n%s' %
                                 (self.scan.filename,
                                  self.cur_token().line,
                                  [TokenType.constants[token_type]
                                   for token_type in token_types],
                                  TokenType.constants[current_token.typ],
                                  current_token.val,
                                  message))
        self.consume()
        return current_token

    def cur_token(self):
        """Wrapper for :self.scan.next_token:.  I find the 'next' terminology
        confusing.  For the sake of clarity in this parser, we'll call
        the 'current' token the one being currently examined.

        """
        return self.scan.next_token

    def consume(self):
        """Gets the next token from :self.scan: and returns the consumed one.

        """
        last_token = self.cur_token()
        self.scan.get_next_token()
        return last_token

    def parse(self):
        """Construct our parse tree and save it to self.tree"""
        tree = self.dec_list()
        self.expect(TokenType.EOF, 'unexpected token at end of file')
        self.tree = tree

    def dec_list(self):
        """Parse a top-level declaration list"""
        head = self.declaration()
        cur = head
        while self.cur_token().typ in TokenType.DataTypes:
            cur.nxt = self.declaration()
            cur = cur.nxt
        return head

    def dec_header(self):
        """Parses the type and name (e.g. `int x`) of declarations."""
        type_token = self.expect(
            TokenType.INT, TokenType.STRING, TokenType.VOID,
            'unexpected type identifier'
        )
        line = type_token.line
        typ = BPLType(TokenType.constants[type_token.typ])
        is_pointer = False
        if self.cur_token().typ is TokenType.STAR:
            is_pointer = True
            typ.address()
            self.consume()
        var = self.expect(
            TokenType.ID,
            'unexpected variable name'
        ).val
        return typ, var, is_pointer, line

    def local_decs(self):
        """Parses a list of local variable declarations (returns a VarDecNode
        who'se self.nxt field may be another statement).

        """
        def assert_local(dec):
            """Verify that :dec: is a valid local declaration"""
            if dec.kind not in (ParseTreeNode.VAR_DEC, ParseTreeNode.ARR_DEC):
                raise ParseException(
                    '%s:%d: Local declaration must be variable or array' % (
                        self.scan.filename,
                        dec.line_number
                    )
                )
            return dec

        head = None
        if self.cur_token().typ in TokenType.DataTypes:
            head = assert_local(self.declaration())
            cur = head
            while self.cur_token().typ in TokenType.DataTypes:
                cur.nxt = assert_local(self.declaration())
                cur = cur.nxt
        return head

    def declaration(self):
        """Parses variable, array, and function declarations."""
        typ, name, is_pointer, line = self.dec_header()
        if not is_pointer:
            if self.cur_token().typ is TokenType.LSQUARE:
                # array declaration
                self.consume()
                size = self.expect(
                    TokenType.NUM,
                    'Array declaration must declare capacity as a number'
                ).val
                self.expect(
                    TokenType.RSQUARE,
                    'Missing closing bracket for array declaration'
                )
                self.expect(
                    TokenType.SEMI,
                    'Missing semicolon at end of array declaration'
                )
                return ArrDecNode(
                    kind=ParseTreeNode.ARR_DEC,
                    line_number=line,
                    name=name,
                    typ=typ,
                    size=size
                )
            if self.cur_token().typ is TokenType.LPAREN:
                # function declaration
                self.consume()
                args = self.params()
                self.expect(
                    TokenType.RPAREN,
                    'Missing closing paren in function declaration'
                )
                body = self.compound_statement()
                return FunDecNode(
                    kind=ParseTreeNode.FUN_DEC,
                    line_number=line,
                    name=name,
                    typ=typ,
                    params=args,
                    body=body
                )
        self.expect(
            TokenType.SEMI,
            'Missing semicolon at end of variable declaration'
        )
        return VarDecNode(
            kind=ParseTreeNode.VAR_DEC,
            line_number=line,
            name=name,
            typ=typ,
            is_pointer=is_pointer
        )

    def params(self):
        """Parses function params."""
        if self.cur_token().typ is TokenType.VOID:
            self.consume()
            return None
        return self.param_list()

    def param_list(self):
        """Parses a function's parameter list (returns a declaration node
        who'se self.nxt field may be another declaration node).

        """
        head = self.param()
        cur = head
        while self.cur_token().typ is TokenType.COMMA:
            self.consume()
            cur.nxt = self.param_list()
            cur = cur.nxt
        return head

    def param(self):
        """Parses a function parameter."""
        typ, name, is_pointer, line = self.dec_header()
        if not is_pointer and self.cur_token().typ is TokenType.LSQUARE:
            # array declaration
            self.consume()
            self.expect(
                TokenType.RSQUARE,
                'Array parameter must end in closing bracket'
            )
            return ArrDecNode(
                kind=ParseTreeNode.ARR_DEC,
                line_number=line,
                name=name,
                typ=typ,
                size=None
            )
        return VarDecNode(
            kind=ParseTreeNode.VAR_DEC,
            line_number=line,
            name=name,
            typ=typ,
            is_pointer=is_pointer
        )

    def statement(self):
        """Parses a statement."""
        if self.cur_token().typ is TokenType.LCURLY:
            return self.compound_statement()
        elif self.cur_token().typ is TokenType.WHILE:
            return self.while_statement()
        elif self.cur_token().typ is TokenType.IF:
            return self.if_statement()
        elif self.cur_token().typ is TokenType.RETURN:
            return self.return_statement()
        elif self.cur_token().typ is TokenType.WRITE:
            return self.write_statement()
        elif self.cur_token().typ is TokenType.WRITELN:
            return self.writeln_statement()
        else:
            return self.expression_statement()

    def compound_statement(self):
        """Parses a compound statement."""
        curly_token = self.expect(
            TokenType.LCURLY, 'compound statement must begin with left curly'
        )
        line = curly_token.line
        local_decs = self.local_decs()
        stmt_list = self.statement_list()
        self.expect(
            TokenType.RCURLY, 'compound statement must end with right curly'
        )
        return CompStmtNode(
            kind=ParseTreeNode.COMP_STMT,
            line_number=line,
            local_decs=local_decs,
            stmt_list=stmt_list
        )

    def while_statement(self):
        """Parses a while statement."""
        while_token = self.expect(
            TokenType.WHILE,
            'while statement must start with keyword \"while\"'
        )
        self.expect(
            TokenType.LPAREN,
            'conditional must be parenthesized'
        )
        cond = self.expression()
        self.expect(
            TokenType.RPAREN,
            'missing closing parenthesis in while condition'
        )
        body = self.statement()
        return WhileStmtNode(
            kind=ParseTreeNode.WHILE_STMT,
            line_number=while_token.line,
            cond=cond,
            body=body
        )

    def if_statement(self):
        """Parses an if statement."""
        if_token = self.expect(
            TokenType.IF,
            'if statement must start with keyword \"if\"'
        )
        self.expect(
            TokenType.LPAREN,
            'conditional must be parenthesized'
        )
        cond = self.expression()
        self.expect(
            TokenType.RPAREN,
            'missing closing parenthesis in if condition'
        )
        true_body = self.statement()
        false_body = None
        if self.cur_token().typ is TokenType.ELSE:
            self.consume()
            false_body = self.statement()
        return IfStmtNode(
            kind=ParseTreeNode.IF_STMT,
            line_number=if_token.line,
            cond=cond,
            true_body=true_body,
            false_body=false_body
        )

    def return_statement(self):
        """Parses a return statement."""
        ret_token = self.expect(
            TokenType.RETURN,
            'Return statement must begin with \"return\"'
        )
        if self.cur_token().typ is TokenType.SEMI:
            self.consume()
            return RetStmtNode(
                kind=ParseTreeNode.RET_STMT,
                line_number=ret_token.line,
                val=None
            )
        exp = self.expression()
        self.expect(
            TokenType.SEMI,
            'Return statement must end in semicolon'
        )
        return RetStmtNode(
            kind=ParseTreeNode.RET_STMT,
            line_number=ret_token.line,
            val=exp
        )

    def write_statement(self):
        """Parses a write statement."""
        write_token = self.expect(
            TokenType.WRITE,
            'Write statement must begin with \"write\"'
        )
        self.expect(
            TokenType.LPAREN,
            'Missing open paren after \"write\"'
        )
        exp = self.expression()
        self.expect(
            TokenType.RPAREN,
            'Missing close paren after write statement\'s expression'
        )
        self.expect(
            TokenType.SEMI,
            'Missing semicolon at end of write statement'
        )
        return WriteStmtNode(
            kind=ParseTreeNode.WRITE_STMT,
            line_number=write_token.line,
            expr=exp
        )

    def writeln_statement(self):
        """Parses a writeln statement"""
        write_token = self.expect(
            TokenType.WRITELN,
            'Writeln statement must begin with \"writeln\"'
        )
        self.expect(
            TokenType.LPAREN,
            'Missing open paren after \"writeln\"'
        )
        self.expect(
            TokenType.RPAREN,
            'Writeln statement takes no arguments'
        )
        self.expect(
            TokenType.SEMI,
            'Missing semicolon at end of writeln statement'
        )
        return WritelnStmtNode(
            kind=ParseTreeNode.WRITELN_STMT,
            line_number=write_token.line
        )

    def statement_list(self):
        """Parses a statement list (returns a statement node who'se self.nxt
        field may be another statement).

        """
        head = None
        if self.cur_token().typ != TokenType.RCURLY:
            head = self.statement()
            cur = head
            while self.cur_token().typ != TokenType.RCURLY:
                cur.nxt = self.statement_list()
                cur = cur.nxt
        return head

    def expression_statement(self):
        """Parses an expression statement."""
        exp = self.expression()
        self.expect(
            TokenType.SEMI, 'expression statement must end with semicolon'
        )
        return ExpStmtNode(
            kind=ParseTreeNode.EXPR_STMT,
            line_number=exp.line_number,
            expr=exp
        )

    def expression(self):
        """Parses an expression."""
        # It's too hard to determine whether we're looking at an E or
        # a Var when parsing, as it requires a lot of lookahead.
        # Since VAR's productions are also generated by E
        # non-terminals, we're going to parse the left hand side of
        # the expression as an E and then make sure we're not doing
        # something dumb like `5 = 6` before returning the expression.
        first_exp = self.E()
        if self.cur_token().typ is TokenType.EQUAL:
            # assignment expression
            if first_exp.kind not in (ParseTreeNode.VAR_EXP,
                                      ParseTreeNode.ARR_EXP,
                                      ParseTreeNode.DEREF_EXP):
                raise ParseException(
                    '%s:%d: Cannot assign to %s' % (
                        self.scan.filename,
                        first_exp.line_number,
                        ParseTreeNode.constants[first_exp.kind]
                    )
                )
            op = self.consume()
            next_exp = self.expression()
            return OpExpNode(
                kind=ParseTreeNode.ASSIGN_EXP,
                line_number=first_exp.line_number,
                op=op,
                l_exp=first_exp,
                r_exp=next_exp
            )
        elif self.cur_token().typ in TokenType.Relops:
            # relational expression
            op = self.consume()
            next_exp = self.expression()
            return OpExpNode(
                kind=ParseTreeNode.COMP_EXP,
                line_number=first_exp.line_number,
                op=op,
                l_exp=first_exp,
                r_exp=next_exp
            )
        # not an assignment or comparison statement.
        # just return the first E() we grabbed
        return first_exp

    def E(self):
        """Parses an expression produced by BPL's E non-terminal."""
        # Note that we're modifying the recursive descent algorithm
        # here for left-recursive rules.
        #
        # I.e. even though we have E -> E + T | T, we know that the
        # first E eventually goes to a T, so instead of first asking
        # for an E, we ask for a T.
        t = self.T()
        while self.cur_token().typ in (TokenType.PLUS, TokenType.MINUS):
            # add/sub expression
            op = self.consume()
            t1 = OpExpNode(
                kind=ParseTreeNode.ARITH_EXP,
                line_number=t.line_number,
                op=op,
                l_exp=t,
                r_exp=self.T()
            )
            t = t1
        return t

    def T(self):
        """Parses an expression produced by BPL's T non-terminal."""
        f = self.F()
        while self.cur_token().typ in (TokenType.STAR,
                                       TokenType.SLASH,
                                       TokenType.MOD):
            op = self.consume()
            f1 = OpExpNode(
                kind=ParseTreeNode.ARITH_EXP,
                line_number=f.line_number,
                op=op,
                l_exp=f,
                r_exp=self.F()
            )
            f = f1
        return f

    def F(self):
        """Parses an expression produced by BPL's F non-terminal."""
        line = self.cur_token().line
        if self.cur_token().typ is TokenType.MINUS:
            # negation expression
            self.consume()
            fact = self.factor()
            return NegExpNode(
                kind=ParseTreeNode.NEG_EXP,
                line_number=line,
                exp=fact
            )
        elif self.cur_token().typ is TokenType.AMP:
            self.consume()
            fact = self.factor()
            return AddrExpNode(
                kind=ParseTreeNode.ADDR_EXP,
                line_number=line,
                exp=fact
            )
        elif self.cur_token().typ is TokenType.STAR:
            self.consume()
            fact = self.factor()
            return DerefExpNode(
                kind=ParseTreeNode.DEREF_EXP,
                line_number=line,
                exp=fact
            )
        return self.factor()

    def factor(self):
        """Parses an expression produced by BPL's Factor non-terminal."""
        if self.cur_token().typ is TokenType.ID:
            name = self.consume()
            line = name.line
            if self.cur_token().typ is TokenType.LSQUARE:
                # array expression
                self.consume()
                index = self.expression()
                self.expect(
                    TokenType.RSQUARE,
                    'Missing closing square bracket for array reference'
                )
                return ArrExpNode(
                    kind=ParseTreeNode.ARR_EXP,
                    line_number=line,
                    name=name.val,
                    index=index
                )
            elif self.cur_token().typ is TokenType.LPAREN:
                # function call expression
                self.consume()
                args = self.args()
                self.expect(
                    TokenType.RPAREN,
                    'Missing closing paren at function call'
                )
                return FunCallExpNode(
                    kind=ParseTreeNode.FUN_CALL_EXP,
                    line_number=line,
                    name=name.val,
                    params=args
                )
            else:
                # variable expression
                return VarExpNode(
                    kind=ParseTreeNode.VAR_EXP,
                    line_number=line,
                    name=name.val
                )
        elif self.cur_token().typ is TokenType.READ:
            # read expression
            line = self.consume().line
            self.expect(
                TokenType.LPAREN,
                'Missing opening paren at read expression'
            )
            self.expect(
                TokenType.RPAREN,
                'Missing closing paren at read expression'
            )
            return ReadExpNode(
                kind=ParseTreeNode.READ_EXP,
                line_number=line
            )
        elif self.cur_token().typ is TokenType.STAR:
            # dereference expression
            line = self.consume().line
            return DerefExpNode(
                kind=ParseTreeNode.DEREF_EXP,
                line_number=line,
                exp=self.var()
            )
        elif self.cur_token().typ is TokenType.NUM:
            # number expression
            num = self.consume()
            return IntExpNode(
                kind=ParseTreeNode.INT_EXP,
                line_number=num.line,
                val=num.val
            )
        elif self.cur_token().typ is TokenType.STRLIT:
            # string expression
            string = self.consume()
            return StrExpNode(
                kind=ParseTreeNode.STR_EXP,
                line_number=string.line,
                val=string.val
            )
        elif self.cur_token().typ is TokenType.LPAREN:
            self.consume()
            exp = self.expression()
            self.expect(
                TokenType.RPAREN,
                'Parenthesized expression must end in right paren'
            )
            return exp
        # Not looking at a factor!
        raise ParseException(
            '%s:%d: Unexpected token parsing factor: %s' % (
                self.scan.filename,
                self.cur_token().line,
                self.cur_token()
            )
        )

    def args(self):
        """Parse a function's arguments, if any."""
        if self.cur_token().typ is TokenType.RPAREN:
            # empty args list
            return None
        return self.args_list()

    def args_list(self):
        """Parse a list of function arguments."""
        head = self.expression()
        cur = head
        while self.cur_token().typ is TokenType.COMMA:
            self.consume()
            cur.nxt = self.args_list()
            cur = cur.nxt
        return head

    def var(self):
        """Parse a variable expression."""
        name = self.expect(TokenType.ID, 'var expression must be an ID')
        return VarExpNode(
            kind=ParseTreeNode.VAR_EXP,
            line=name.line,
            name=name.val
        )


class BPLType():
    """Represents the types in BPL"""
    INT = 0
    STRING = 1
    VOID = 2
    INT_PTR = 3
    STR_PTR = 4
    INT_ARR = 5
    STR_ARR = 6

    constants = {
        0: "INT",
        1: "STRING",
        2: "VOID",
        3: "INT_PTR",
        4: "STR_PTR",
        5: "INT_ARR",
        6: "STR_ARR"
    }

    def __init__(self, type_string):
        """Initialize this BPLType from a string describing it's type.'"""
        if type_string == 'INT':
            self.typ = self.INT
        elif type_string == 'STRING':
            self.typ = self.STRING
        elif type_string == 'VOID':
            self.typ = self.VOID

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.typ == other.typ
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return '%s' % self.constants[self.typ]

    def is_pointer(self):
        return True if self.typ in (BPLType.INT_PTR, BPLType.STR_PTR) else False

    def address(self):
        if self.typ == self.INT:
            self.typ = self.INT_PTR
        elif self.typ == self.STRING:
            self.typ = self.STR_PTR

    def deref(self):
        if self.typ == self.INT_PTR:
            self.typ = self.INT
        elif self.typ == self.STR_PTR:
            self.typ = self.STRING


class ParseException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)
