/* Expression test cases
 * ---------------------
 * Recursive faith dictates that any valid nesting of these expressions
 * should work if the individual parts do. */
{
    /* assignment expression */
    x = 3;
    /* comparison expression */
    x > 3;
    /* E's */
    x + 3 - 4 + 5;		/* note left associativity */
    y1 * y2 / y3 % y4;
    /* T's */
    x * 3;
    x / 3;
    x % 3;
    /* F's */
    -x;
    &x;
    *x;
    /* Factors */
    (x);
    my_fun_call();
    my_fun_call(arg1, arg2, arg3);
    read();
    *x;
    x;
    x[3];
    3;
    "hello";
}
