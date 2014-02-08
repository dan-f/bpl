from token import TokenType, Token


class Scanner():
    """A scanner class to tokenize BPL programs.

    Calls to :get_next_token: set an instance variable, :next_token:, which is
    a Token object representing the current token from the input program.  It
    is important to note that :next_token: does not exist until the first call
    to :get_next_token:.

    Alternatively, the instance variable :tokens:, a generator, can be used to
    access the input program's tokens as an iterable sequence.
    """

    def __init__(self, filename):
        """Initialize a scanner which reads from :filename:"""
        self.filename = filename
        self.tokens = self._next_token_gen()

    def get_next_token(self):
        """Grabs the next token from :tokens: and saves it to :next_token:"""
        self.next_token = self.tokens.next()

    def _next_token_gen(self):
        """Returns a generator to iterate over Token objects for every token in
        :filename:.

        The generator tokenizes the input program using a simple DFA algorithm.
        """
        with open(self.filename) as f:
            # keep track of our current buffer index and line number
            buf = f.read()
            i = 0
            line = 1

            # the 'states' for our DFA
            START   = 0
            KEY_ID  = 1
            NUMBER  = 2
            STRLIT  = 3
            SYMBOL  = 4
            COMMENT = 5

            # the current token's string value
            cur_str = ''

            state = START

            while i < len(buf):
                # We're in the start state if we've either just begun
                # scanning or just accepted a token.  Otherwise, we're
                # in one of the other five states corresponding to the
                # type of token we're reading in.
                if state == START:
                    # skip whitespace, count newlines
                    if buf[i].isspace():
                        if buf[i] == '\n':
                            line += 1
                        i += 1
                        continue
                    # comment
                    if i < len(buf) - 1 and buf[i] == '/' and buf[i+1] == '*':
                        state = COMMENT
                        i += 2
                    # string literal
                    elif buf[i] == '\"':
                        state = STRLIT
                        i += 1
                    # keyword or id
                    elif buf[i].isalnum():
                        cur_str += buf[i]
                        state = KEY_ID
                        i += 1
                    # symbol
                    elif [sym for sym in TokenType.Symbols
                          if sym.startswith(cur_str + buf[i])]:
                        cur_str += buf[i]
                        state = SYMBOL
                        i += 1
                    # number
                    elif buf[i].isdigit():
                        cur_str += buf[i]
                        state = NUMBER
                        i += 1
                    else:
                        raise Exception('Unknown character %s at %s:%d:%d'
                                        % (buf[i], self.filename, line, i))

                elif state == COMMENT:
                    if buf[i] != '*':
                        i += 1
                    elif i < len(buf) - 1 and buf[i+1] == '/':
                        i += 2
                        state = START

                elif state == STRLIT:
                    if buf[i] != '\"':
                        cur_str += buf[i]
                    else:
                        yield Token(TokenType.STRLIT, cur_str, line)
                        cur_str = ''
                        state = START
                    i += 1

                elif state == KEY_ID:
                    if buf[i].isalnum():
                        cur_str += buf[i]
                        i += 1
                    else:
                        if cur_str in TokenType.Keywords:
                            yield Token(TokenType.Keywords[cur_str],
                                        cur_str,
                                        line)
                        else:
                            yield Token(TokenType.ID, cur_str, line)
                        cur_str = ''
                        state = START

                elif state == SYMBOL:
                    matches = [sym for sym in TokenType.Symbols
                               if sym.startswith(cur_str + buf[i])]
                    if matches:
                        cur_str += buf[i]
                        i += 1
                    else:
                        yield Token(TokenType.Symbols[cur_str], cur_str, line)
                        cur_str = ''
                        state = START

                elif state == NUMBER:
                    if buf[i].isdigit():
                        cur_str += buf[i]
                        i += 1
                    else:
                        yield Token(TokenType.NUM, cur_str, line)
                        cur_str = ''
                        state = START

            yield Token(TokenType.EOF, 'EOF', line)
