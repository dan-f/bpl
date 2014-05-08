void f(int a[])
{
  int i;
  i = 0;
  while (i < 3) {
    a[i] = a[i] * 10;
    i = i + 1;
  }
}

void main(void)
{
  int x[3];
  int i;

  i = 0;
  while (i < 3) {
    x[i] = i + 1;
    write(x[i]);
    i = i + 1;
  }
  writeln();

  f(x);                         /* question - x is parsed as a
                                 * variable expression... is that
                                 * alright? It seems like it would
                                 * make more sense if it parsed as an
                                 * array expression with no index
                                 * expression... but the parser
                                 * wouldn't be able to figure that out
                                 * without a symbol table.  My
                                 * workaround in gen_var_expr() seems
                                 * to work, though. */

  i = 0;
  while (i < 3) {
    write(x[i]);
    i = i + 1;
  }
  writeln();
}
