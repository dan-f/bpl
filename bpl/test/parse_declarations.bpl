/* Top-level variable declarations */
void x;
int *x;
int z[42];

/* Top-level function definition */
int fact(int x)
{
  /* Local decs */
  int a;
  string *b;
  void c[42];

  if (x == 1)
    return x;
  else
    return x * fact(x - 1);
}
