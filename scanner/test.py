from scanner import Scanner
from token import TokenType


if __name__ == '__main__':
    s = Scanner('example.bpl')

    # bootstrap by manually asking for the first token
    s.get_next_token()
    while s.next_token.typ != TokenType.EOF:
        print(s.next_token)
        s.get_next_token()
