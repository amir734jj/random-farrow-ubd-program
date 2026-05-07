# random-farrow-ubd-program
Random program to test time complexity of Farrow's UBD example

See [this grammar](https://github.com/boyland/aps/blob/master/examples/farrow-ubd.y)

Example
```
// Validating Farrow's use-before-declaration (depth=1, vars=10)
{
  f = c * b - h;
  e = d / 27 - 6;
  e = 65 + f;
  g = f + 70;
  g = g - g;
  e = 72 - f - f;
  e = e + f;
}
c = 74;
g = c - c;
e = c / c - c;
{
  g = g;
  e = 91 - j / 3;
  e = 25 * c;
  h = 4 + 90;
  d = e;
  j = c - h;
  e = d;
}
j = 46;
a = e + 2 + c;
```
