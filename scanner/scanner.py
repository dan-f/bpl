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
            buf = f.read()

            # the 'states' for our DFA
            in_keyw_or_id = False
            in_num        = False
            in_str        = False
            in_sym        = False
            in_comm       = False

            # the current token's string
            cur_str = ''

            # keep track of our current buffer index and line number
            i = 0
            line = 1

            while i < len(buf):
                # the following cases suppose we're in the middle of a token
                if in_comm:
                    if buf[i] != '*':
                        i += 1
                    elif i < len(buf) - 1 and buf[i+1] == '/':
                        i += 2
                        in_comm = False

                elif in_str:
                    if buf[i] != '\"':
                        cur_str += buf[i]
                    else:
                        yield Token(TokenType.STRLIT, cur_str, line)
                        cur_str = ''
                        in_str = False
                    i += 1

                elif in_keyw_or_id:
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
                        in_keyw_or_id = False

                elif in_sym:
                    matches = [sym for sym in TokenType.Symbols
                               if sym.startswith(cur_str + buf[i])]
                    if matches:
                        cur_str += buf[i]
                        i += 1
                    else:
                        yield Token(TokenType.Symbols[cur_str], cur_str, line)
                        cur_str = ''
                        in_sym = False

                elif in_num:
                    if buf[i].isdigit():
                        cur_str += buf[i]
                        i += 1
                    else:
                        yield Token(TokenType.NUM, cur_str, line)
                        cur_str = ''
                        in_num = False

                else:
                    # the following cases suppose we're in no state (either
                    # beginning scanning or just accepted a string)

                    # skip whitespace, count newlines
                    if buf[i].isspace():
                        if buf[i] == '\n':
                            line += 1
                        i += 1
                        continue

                    # comment
                    if i < len(buf) - 1 and buf[i] == '/' and buf[i+1] == '*':
                        in_comm = True
                        i += 2
                    # string literal
                    elif buf[i] == '\"':
                        in_str = True
                        i += 1
                    # keyword or id
                    elif buf[i].isalnum():
                        cur_str += buf[i]
                        in_keyw_or_id = True
                        i += 1
                    # symbol
                    elif [sym for sym in TokenType.Symbols
                          if sym.startswith(cur_str + buf[i])]:
                        cur_str += buf[i]
                        in_sym = True
                        i += 1
                    # number
                    elif buf[i].isdigit():
                        cur_str += buf[i]
                        in_num = True
                        i += 1
                    else:
                        raise Exception('Unknown character %s at %s:%d:%d'
                                        % (buf[i], self.filename, line, i))
            yield Token(TokenType.EOF, 'EOF', line)
