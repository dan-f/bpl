int global;

int fact(int n)
{
  if (n == 1)
    return 1;
  else
    return n * fact(n - 1);
}

void main(void)
{
  int x;

  /* multiply 2^33 to prove we can handle 64 bit multiplication */
  global = 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2
    * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2 * 2;
  write(global);

  /* 64-bit division! */
  x = 9000000000;
  write(x / 2);
  write(x % 2000000000);

  writeln();
}
