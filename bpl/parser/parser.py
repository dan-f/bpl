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
        cur_token = self.scan.next_token
        message = args[-1]
        token_types = args[:-1]
        if cur_token.typ not in token_types:
            raise ParseException('%s\nExpected %s, but got %s: \"%s\"' %
                                 (message,
                                  [TokenType.constants[token_type]
                                   for token_type in token_types],
                                  TokenType.constants[cur_token.typ],
                                  cur_token.val))
        self.scan.get_next_token()
        return cur_token

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
        if self.scan.next_token.typ in TokenType.DataTypes:
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
        if self.scan.next_token.typ == TokenType.LCURLY:
            return self.compound_statement()
        elif self.scan.next_token.typ == TokenType.WHILE:
            return self.while_statement()
        elif self.scan.next_token.typ == TokenType.IF:
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
            ParseTreeNode.COMP_STMT,
            line,
            local_decs,
            stmt_list
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
            ParseTreeNode.WHILE_STMT,
            while_token.line,
            cond,
            body
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
        if self.scan.next_token.typ == TokenType.ELSE:
            self.scan.get_next_token()
            false_body = self.statement()
        return IfStmtNode(
            ParseTreeNode.IF_STMT,
            if_token.line,
            cond,
            true_body,
            false_body
        )

    def statement_list(self):
        stmt = None
        if self.scan.next_token.typ != TokenType.RCURLY:
            stmt = self.statement()
            stmt.nxt = self.statement_list()
        return stmt

    def expression_statement(self):
        exp = self.expression()
        self.expect(
            TokenType.SEMI, 'expression statement must end with semicolon'
        )
        return ExpStmtNode(
            ParseTreeNode.EXPR_STMT,
            exp.line_number,
            exp
        )

    def expression(self):
        return self.id()

    def id(self):
        id = self.expect(TokenType.ID, 'ID expression must be an id')
        return VarExpNode(
            ParseTreeNode.VAR,
            id.line,
            id.val
        )
