bpl
===

Bob's Programming Language, implemented for CS331 at Oberlin College

## Implementation

### Scanner
Scan a bpl program named `filename`:

    s = Scanner(filename)
    # bootstrap by manually asking for the first token
    s.get_next_token()
    while s.next_token.typ != TokenType.EOF:
        print(s.next_token)  # do something with the current token
        s.get_next_token()

As per Bob's instructions, `s.get_next_token()` grabs the next token
from the input file and assigns it to `s.next_token`.  Note that you
must explicitly ask for the first token by running `s.next_token` to
bootstrap the scanning process (the constructor does not do this for
you).

An example bpl program file has been provided.  To scan it and print the
output, run `python test.py` from the `scanner` directory.
