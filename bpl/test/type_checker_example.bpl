int x;
string *y;

int f(int a) {
  int b;
  int f;
  f = 10;                       /* Refers to int f */
  f(10);                        /* Refers to func f */

  if (a) {
    int zoo;
    zoo;
  } else {
    int x;
    int y;
    while (x) {
      y;
    }
  }

  return x + y;
}
