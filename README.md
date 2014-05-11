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

### Compiling
From the top-level directory, run my compiler like this `./bplc [-s]
[-o OUTFILE] infile`, where `infile` is the bpl program you want to compile, and
`OUTFILE` is the name for the output executable when the optional `-o` flag is
used.


### Testing
Always run tests from the top-level directory.  To test a module `foo`, run
`python -m bpl.test.foo_test`.  For example, run `python -m
bpl.test.scanner_test` to test the scanner.  You can also run `python -m
bpl.test.foo_test file_1 file_2 ... file_n` to test multiple bpl source files.

### Scanner
Scan a bpl program named `filename` as follows:

    s = Scanner(filename)
    # bootstrap by manually asking for the first token
    s.get_next_token()  # may raise ScanException
    while s.next_token.typ != TokenType.EOF:
        print(s.next_token)  # do something with the current token
        s.get_next_token()

As per Bob's instructions, `s.get_next_token()` grabs the next token from the
input file and assigns it to `s.next_token`.  Note that you must explicitly ask
for the first token by running `s.next_token` to bootstrap the scanning process
(the constructor does not do this for you).

### Parser
Parse a bpl program named `filename` as follows:

    p = Parser(filename)
    p.parse()  # p.tree is the resulting parse tree
               # this may throw a ParseException

### Type Checker
Type-check a parse tree named `tree` (generated from a bpl file named
`filename`) as follows:

    t = TypeChecker(filename, tree, DEBUG=False)  # set DEBUG to True for
                                                  # verbose printing
    t.type_check()

### Code Generator
Generate assembly code for a type-checked parse tree named `tree` (generated
from a bpl file named `filename`) as follows:

    c = CodeGenerator(filename, tree, DEBUG=False)
    c.gen_code()
