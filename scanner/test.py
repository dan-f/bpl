from scanner import Scanner
from token import TokenType


if __name__ == '__main__':
    s = Scanner('example.bpl')

    # the 'Bob' way:
    s.get_next_token()
    while s.next_token.typ != TokenType.EOF:
        print(s.next_token)
        s.get_next_token()

    # a more pythonic way:
    # for token in s.tokens:
        # print token
