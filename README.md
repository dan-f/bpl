bpl
===

Bob's Programming Language, implemented for CS331 at Oberlin College.

Developed with Python 2.7.6.

### Structure
The project is layed out as follows:

    .                           # top-level directory.  Run tests from here!
    ├── README.md
    └── bpl                     # bpl python package
        ├── __init__.py
        ├── __init__.pyc
        ├── scanner             # scanner package
        │   ├── __init__.py
        │   ├── __init__.pyc
        │   ├── scanner.py
        │   ├── scanner.pyc
        │   ├── token.py
        │   └── token.pyc
        |
        | ...
        |
        └── test                # test package
            ├── __init__.py
            ├── __init__.pyc
            ├── example.bpl
            └── scanner_test.py

### Testing
Always run tests from the top-level directory.  To test a module
`foo`, run `python -m bpl.test.foo_test`.  For example, run `python -m
bpl.test.scanner_test` to test the scanner.

### Scanner
Scan a bpl program named `filename` as follows:

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
