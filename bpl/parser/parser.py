from bpl.parser.parsetree import *
from bpl.scanner.scanner import Scanner
from bpl.scanner.token import TokenType

# Current supported grammar:
#     PROGRAM
#       -> STATEMENT
#     STATEMENT
#       -> EXPRESSION_STMT
#        | COMPOUND_STMT
#     EXPRESSION_STMT
#       -> EXPRESSION;
#     EXPRESSION
#       -> <id>


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
            raise ParseException('%s\nExpected %s, but got %s: \"%s\"' %
                                 (message,
                                  [TokenType.constants[token_type]
                                   for token_type in token_types],
                                  TokenType.constants[current_token.typ],
                                  current_token.val))
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

    def program(self):
        """Construct our parse tree and save it to self.tree"""
        tree = self.statement()
        self.expect(TokenType.EOF, 'unexpected token at end of file')
        self.tree = tree

    def dec_header(self):
        typ = self.expect(
            TokenType.INT, TokenType.STRING, TokenType.VOID,
            'unexpected type identifier'
        )
        var = self.expect(
            TokenType.ID,
            'unexpected variable name'
        )
        return typ, var.val

    def local_decs(self):
        v = None
        if self.cur_token().typ in TokenType.DataTypes:
            v = self.var_dec()
            v.nxt = self.local_decs()
        return v

    def var_dec(self):
        typ, name = self.dec_header()
        self.expect(
            TokenType.SEMI,
            'variable declaration must end in semicolon'
        )
        return VarDecNode(
            kind=ParseTreeNode.VAR_DEC,
            line_number=typ.line,
            name=name,
            typ=typ,
            is_pointer=False  # TODO: support pointers
        )

    def statement(self):
        if self.cur_token().typ == TokenType.LCURLY:
            return self.compound_statement()
        elif self.cur_token().typ == TokenType.WHILE:
            return self.while_statement()
        elif self.cur_token().typ == TokenType.IF:
            return self.if_statement()
        else:
            return self.expression_statement()

    def compound_statement(self):
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
        if self.cur_token().typ == TokenType.ELSE:
            self.consume()
            false_body = self.statement()
        return IfStmtNode(
            kind=ParseTreeNode.IF_STMT,
            line_number=if_token.line,
            cond=cond,
            true_body=true_body,
            false_body=false_body
        )

    def statement_list(self):
        stmt = None
        if self.cur_token().typ != TokenType.RCURLY:
            stmt = self.statement()
            stmt.nxt = self.statement_list()
        return stmt

    def expression_statement(self):
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
        # It's too hard to determine whether we're looking at an E or
        # a Var when parsing, as it requires a lot of lookahead.
        # Since VAR's productions are also generated by E
        # non-terminals, we're going to parse the left hand side of
        # the expression as an E and then make sure we're not doing
        # something dumb like `5 = 6` before returning the expression.
        first_exp = self.E()
        if self.cur_token().typ == TokenType.EQUAL:
            # assignment expression
            if first_exp.kind not in (ParseTreeNode.VAR_EXP,
                                      ParseTreeNode.ARR_EXP,
                                      ParseTreeNode.DEREF_EXP):
                raise ParseException(
                    'Left-hand side of assignment expression must be a \
                    variable, array, or dereference expression'
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
        # Note that we're modifying the recursive descent algorithm
        # here for left-recursive rules.
        #
        # I.e. even though we have E -> E + T | T, we know that the
        # first E eventually goes to a T, so instead of first asking
        # for an E, we ask for a T.
        t1 = self.T()
        if self.cur_token().typ in (TokenType.PLUS, TokenType.MINUS):
            # add/sub expression
            op = self.consume()
            t2 = self.E()
            return OpExpNode(
                kind=ParseTreeNode.MATH_EXP,
                line_number=t1.line_number,
                op=op,
                l_exp=t1,
                r_exp=t2
            )
        # if we haven't seen a +/-, just return the T
        return t1

    def T(self):
        f1 = self.F()
        if self.cur_token().typ in (TokenType.STAR,
                                    TokenType.SLASH,
                                    TokenType.MOD):
            op = self.consume()
            f2 = self.T()
            return OpExpNode(
                kind=ParseTreeNode.MATH_EXP,
                line_number=f1.line_number,
                op=op,
                l_exp=f1,
                r_exp=f2
            )
        return f1

    def F(self):
        line = self.cur_token().line
        if self.cur_token().typ is TokenType.MINUS:
            # negation expression
            self.consume()
            return NegExpNode(
                kind=ParseTreeNode.NEG_EXP,
                line_number=line,
                exp=self.factor()
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
            var_exp = self.var()
            return DerefExpNode(
                kind=ParseTreeNode.DEREF_EXP,
                line_number=line,
                exp=var_exp
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
            line = self.consume().line
            exp = self.expression()
            self.expect(
                TokenType.RPAREN,
                'Parenthesized expression must end in right paren'
            )
            return exp
        # Not looking at a factor!
        raise ParseException(
            'Unexpected token parsing factor: %s' %
            self.cur_token()
        )

    def args(self):
        if self.cur_token().typ is TokenType.RPAREN:
            # empty args list
            return None
        return self.args_list()

    def args_list(self):
        arg = self.expression()
        nxt = None
        if self.cur_token().typ is TokenType.COMMA:
            # consume the comma, and recursively build up our args list
            self.consume()
            nxt = self.args_list()
        arg.nxt = nxt
        return arg

    def var(self):
        name = self.expect(TokenType.ID, 'var expression must be an ID')
        return VarExpNode(
            kind=ParseTreeNode.VAR_EXP,
            line=name.line,
            name=name
        )


class ParseException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)
