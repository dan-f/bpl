from bpl.scanner.scanner import Scanner
from bpl.scanner.token import TokenType
import sys

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for filename in sys.argv[1:]:
            s = Scanner(filename)

            # bootstrap by manually asking for the first token
            s.get_next_token()
            while s.next_token.typ != TokenType.EOF:
                print(s.next_token)
                s.get_next_token()
    else:
        s = Scanner('bpl/test/scan_example.bpl')

        s.get_next_token()
        while s.next_token.typ != TokenType.EOF:
            print(s.next_token)
            s.get_next_token()
