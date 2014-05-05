int global;
string foo;

string returns_a_string(string s)
{
  string foo;
  foo = "barstring";
  return foo;
}

void main(void)
{
  foo = "foostring";
  write(returns_a_string(foo));
  write(foo);
  writeln();
}
