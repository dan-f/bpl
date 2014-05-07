string s1;
string s2;

void swap_ints(int *x, int *y)
{
  int tmp;
  tmp = *x;
  *x = *y;
  *y = tmp;
}

void swap_strings(string *x, string *y)
{
  string tmp;
  tmp = *x;
  *x = *y;
  *y = tmp;
}

void main(void)
{
  int a;
  int b;

  a = 0;
  b = 1;

  s1 = "foo";
  s2 = "bar";

  /* swap integers using pointers */
  write(a);
  write(b);

  swap_ints(&a, &b);

  write(a);
  write(b);

  writeln();
  writeln();

  /* swap strings using pointers */
  write(s1);
  write(s2);

  swap_strings(&s1, &s2);

  write(s1);
  write(s2);

  writeln();
}
