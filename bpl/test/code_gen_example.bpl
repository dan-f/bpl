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
  int y;
  x = y = 5;
  write(fact(x));
  writeln();
}
