# random-farrow-ubd-program
Random programs to benchmark the time complexity of Farrow's use-before-declaration (UBD) example across three APS evaluator implementations: **dynamic**, **static**, and **synth**.

See [this grammar](https://github.com/boyland/aps/blob/master/examples/farrow-ubd.y)

## Repository structure

| Path | Description |
|------|-------------|
| `get_farrow.py` | Generates a random Farrow-UBD program at a given nesting depth |
| `gen_programs.sh` | Generates `10.program` … `100.program` (depths 10–100, step 10) |
| `run_all.sh` | Runs every `*.program` against all three evaluators, saves outputs and timing logs, then diffs results |
| `check_outputs.sh` | Compares `dynamic/`, `static/`, and `synth/` outputs for correctness |
| `*.program` | Generated test programs (committed) |
| `dynamic/` `static/` `synth/` | **Generated — not committed** (ignored by `.gitignore`) |

## Usage

### 1. Generate programs
```bash
./gen_programs.sh
```

### 2. Run all evaluators and compare
```bash
./run_all.sh
```
This will:
- Run each `*.program` with `EVALUATOR=DYNAMIC`, `STATIC`, and `SYNTH` via `make FarrowUbdDriver.run`
- Save outputs to `dynamic/*.program.output`, `static/*.program.output`, `synth/*.program.output`
- Write per-evaluator timing logs: `dynamic/timing-dynamic.log`, `static/timing-static.log`, `synth/timing-synth.log`
- Run `check_outputs.sh` to diff all three sets of outputs

### 3. Check outputs only
```bash
./check_outputs.sh
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
