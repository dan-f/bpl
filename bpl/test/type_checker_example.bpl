int x;
int *y;
string z[40];

void f(void) {}

int expressions(int a, int b, int c) {
  /* variable expression */
  x;
  /* array expression */
  z[1];
  /* address expression */
  &x;
  /* dereference expression */
  *y;
  /* function call expression */
  f();
  expressions(x, x, x);
  /* read expression */
  read();
  /* assignment expression */
  x = 5;
  /* comparison expression */
  *y != x;
  /* arithmetic expression */
  x + 7- 4;
  /* negation expression */
  -x;
  /* int expression */
  5;
  /* string expression */
  "hello";
}

int statements(void) {
  /* if statement */
  if (1) {
    /* write statements */
    write("cool");
    write(1);
  } else {
    int x;
    /* expression statement */
    x = 3;
  }
  /* return statement */
  return 3;
}
