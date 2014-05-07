int x[3];

void main(void)
{
  int i;

  x[0] = 10;
  x[1] = 15;
  x[2] = 20;

  i = 0;
  while (i < 3) {
    write(x[i]);
    i = i + 1;
  }

  writeln();
}
