class TokenType():
    """A stand-in for a proper enum.  Each class variable (other than
    :Keywords: and :Symbols:) identifies a possible token type in BPL.
    """

    # identifier, number, and string literals
    ID      = 0
    NUM     = 1
    STRLIT  = 2
    # keywords
    INT     = 3
    VOID    = 4
    STRING  = 5
    IF      = 6
    ELSE    = 7
    WHILE   = 8
    RETURN  = 9
    WRITE   = 10
    WRITELN = 11
    READ    = 12
    # special symbols
    EQUAL   = 13
    SEMI    = 14
    COMMA   = 15
    LSQUARE = 16
    RSQUARE = 17
    LCURLY  = 18
    RCURLY  = 19
    LPAREN  = 20
    RPAREN  = 21
    LESS    = 22
    LEQUAL  = 23
    BOOLEQ  = 24
    NEQUAL  = 25
    GEQUAL  = 26
    GREATER = 27
    PLUS    = 28
    MINUS   = 29
    STAR    = 30
    SLASH   = 31
    MOD     = 32
    AMP     = 33
    # end of file token
    EOF     = 34

    Keywords = {
        'int'     : INT,
        'void'    : VOID,
        'string'  : STRING,
        'if'      : IF,
        'else'    : ELSE,
        'while'   : WHILE,
        'return'  : RETURN,
        'write'   : WRITE,
        'writeln' : WRITELN,
        'read'    : READ
    }

    Symbols = {
        '='  : EQUAL,
        ';'  : SEMI,
        ','  : COMMA,
        '['  : LSQUARE,
        ']'  : RSQUARE,
        '{'  : LCURLY,
        '}'  : RCURLY,
        '('  : LPAREN,
        ')'  : RPAREN,
        '<'  : LESS,
        '<=' : LEQUAL,
        '==' : BOOLEQ,
        '!=' : NEQUAL,
        '>=' : GEQUAL,
        '>'  : GREATER,
        '+'  : PLUS,
        '-'  : MINUS,
        '*'  : STAR,
        '/'  : SLASH,
        '%'  : MOD,
        '&'  : AMP
    }


class Token():
    def __init__(self, typ, val, line):
        """Initializes a token of type :typ: representing the string :value:
        occurring on line :line:

        Automatically infers the TokenType.

        """
        self.typ  = typ
        self.val  = val
        self.line = line

    def __str__(self):
        return 'Kind: %s, Value: \"%s\", Line: %d' % (self.typ,
                                                      self.val,
                                                      self.line)
