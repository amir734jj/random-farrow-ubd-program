# random-farrow-ubd-program
Random programs to benchmark the time complexity of Farrow's use-before-declaration (UBD) example across three APS evaluator implementations: **dynamic**, **static**, and **synth**.

See [this grammar](https://github.com/boyland/aps/blob/master/examples/farrow-ubd.y)

## Repository structure

| Path | Description |
|------|-------------|
| `main.py` | CLI entry point — run `python3 main.py <command>` |
| `get_farrow.py` | Generates a random Farrow-UBD program at a given nesting depth |
| `programs/` | **Generated** — test program files (ignored by `.gitignore`) |
| `dynamic/` `static/` `synth/` | **Generated** — per-program result folders (ignored by `.gitignore`) |

## Usage

### 1. Generate programs
```bash
python3 main.py generate                        # depths 10–100 step 10
python3 main.py generate --start 10 --stop 500 --step 10
python3 main.py generate --force                # overwrite existing
```

### 2. Run all evaluators
```bash
python3 main.py run                             # all evaluators, auto batch size
python3 main.py run -j 4                        # limit to 4 parallel jobs
python3 main.py run -e STATIC DYNAMIC           # specific evaluators only
```
This will:
- Compile once per evaluator via `make`
- Run each program in parallel batches
- Store results per program in `<evaluator>/<program>/` folders
- Skip programs that already succeeded with the same input hash

Each program folder contains:
```
dynamic/10.program/
  hash      # sha256 of the input .program file
  output    # full stdout+stderr (streamed directly to disk)
  time      # elapsed seconds
```

### 3. Compare outputs across evaluators
```bash
python3 main.py check                           # compare against dynamic
python3 main.py check --reference static        # compare against static
```

### 4. Show timing table
```bash
python3 main.py times
```

### 5. Clean generated files
```bash
python3 main.py clean                           # remove output directories
python3 main.py clean --programs                # also remove programs/
```

## Example program (depth=1)
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
