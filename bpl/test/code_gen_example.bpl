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
  global = 5;
  write(*(&global));
  write(fact(global));
  writeln();
}
