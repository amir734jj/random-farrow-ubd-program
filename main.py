#!/usr/bin/env python3
"""
Benchmark Farrow's use-before-declaration (UBD) example across APS evaluators.

Commands:
    generate    Generate random .program files at various nesting depths
    run         Run programs against DYNAMIC, STATIC, and SYNTH evaluators
    check       Compare output hashes across evaluators
    times       Display a timing table across evaluators
    clean       Remove all generated output directories
"""

import argparse
import hashlib
import os
import random
import string
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from pathlib import Path

sys.setrecursionlimit(100000)

ROOT_DIR = Path(__file__).resolve().parent
APS_DIR = ROOT_DIR / ".." / "aps" / "examples" / "scala"
PROGRAMS_DIR = ROOT_DIR / "programs"
EVALUATORS = ["DYNAMIC", "STATIC"]


# ---------------------------------------------------------------------------
# Program generator
# ---------------------------------------------------------------------------

class ProgramGenerator:
    OPS = ["+", "-", "*", "/"]

    class Kind(Enum):
        GOOD = "good"
        UBD = "ubd"
        DUP = "dup"
        BLOCK = "block"

    def __init__(self, depth=2):
        self.depth = depth
        self.num_vars = 5 + depth * 5
        self.var_pool = self._make_var_pool(self.num_vars)

    @staticmethod
    def _make_var_pool(n):
        names = []
        for i in range(n):
            name = ""
            x = i
            while True:
                name = string.ascii_lowercase[x % 26] + name
                x = x // 26 - 1
                if x < 0:
                    break
            names.append(name)
        random.shuffle(names)
        return names

    def _random_expr(self, declared, force_good=False):
        parts = []
        num_terms = random.choices([1, 2, 3], weights=[2, 5, 3])[0]
        for i in range(num_terms):
            op = None
            if i > 0:
                op = random.choice(self.OPS)
                parts.append(op)
            if op == "/":
                parts.append(str(random.randint(1, 100)))
                continue
            use_literal = random.random() < 0.3
            if use_literal:
                parts.append(str(random.randint(1, 100)))
            elif force_good:
                if declared:
                    parts.append(random.choice(list(declared)))
                else:
                    parts.append(str(random.randint(1, 100)))
            else:
                undeclared = [v for v in self.var_pool if v not in declared]
                if undeclared:
                    parts.append(random.choice(undeclared))
                else:
                    parts.append(str(random.randint(1, 100)))
        return " ".join(parts)

    def _generate_block(self, declared, current_depth, indent=0, must_reach=True):
        Kind = self.Kind
        lines = []
        pad = "  " * indent
        num_stmts = random.randint(3, 7)
        local_declared = set(declared)
        max_depth_reached = current_depth

        if current_depth < self.depth:
            if must_reach:
                kinds = [Kind.BLOCK] + [
                    random.choices([Kind.GOOD, Kind.UBD, Kind.DUP, Kind.BLOCK], weights=[50, 17, 17, 16])[0]
                    for _ in range(num_stmts - 1)
                ]
                random.shuffle(kinds)
            else:
                kinds = [
                    random.choices([Kind.GOOD, Kind.UBD, Kind.DUP, Kind.BLOCK], weights=[50, 17, 17, 16])[0]
                    for _ in range(num_stmts)
                ]
        else:
            kinds = [
                random.choices([Kind.GOOD, Kind.UBD, Kind.DUP], weights=[50, 25, 25])[0]
                for _ in range(num_stmts)
            ]

        spine_used = not must_reach

        for kind in kinds:
            if kind == Kind.BLOCK:
                lines.append(f"{pad}{{")
                child_must_reach = must_reach and not spine_used
                if child_must_reach:
                    spine_used = True
                inner, inner_depth = self._generate_block(
                    local_declared, current_depth + 1, indent + 1, must_reach=child_must_reach
                )
                lines.extend(inner)
                lines.append(f"{pad}}}")
                max_depth_reached = max(max_depth_reached, inner_depth)
                continue

            if kind == Kind.GOOD:
                undeclared_vars = [v for v in self.var_pool if v not in local_declared]
                lhs = random.choice(undeclared_vars) if undeclared_vars else random.choice(self.var_pool)
                rhs = self._random_expr(local_declared, force_good=True)
            elif kind == Kind.UBD:
                lhs = random.choice(self.var_pool)
                rhs = self._random_expr(local_declared, force_good=False)
            elif kind == Kind.DUP:
                if local_declared:
                    lhs = random.choice(list(local_declared))
                    rhs = self._random_expr(local_declared, force_good=True)
                else:
                    lhs = random.choice(self.var_pool)
                    rhs = self._random_expr(local_declared, force_good=False)

            lines.append(f"{pad}{lhs} = {rhs};")
            local_declared.add(lhs)

        return lines, max_depth_reached

    def generate(self):
        lines, _ = self._generate_block(set(), current_depth=0)
        header = f"// Validating Farrow's use-before-declaration (depth={self.depth}, vars={self.num_vars})"
        return header + "\n" + "\n".join(lines)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def result_dir(evaluator: str, program_name: str) -> Path:
    return ROOT_DIR / evaluator.lower() / program_name


def is_done(evaluator: str, prog: Path) -> bool:
    d = result_dir(evaluator, prog.name)
    hash_file = d / "hash"
    output_file = d / "output"
    time_file = d / "time"
    if not (hash_file.exists() and output_file.exists() and time_file.exists()):
        return False
    return hash_file.read_text().strip() == sha256_file(prog)


# ---------------------------------------------------------------------------
# Command interface
# ---------------------------------------------------------------------------

class Command:
    name: str = ""
    help: str = ""

    def configure(self, parser: argparse.ArgumentParser):
        pass

    def run(self, args: argparse.Namespace):
        raise NotImplementedError


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

class GenerateCommand(Command):
    name = "generate"
    help = "Generate random .program files"

    def configure(self, parser):
        parser.add_argument("--start", type=int, default=10, help="Starting depth (default: 10)")
        parser.add_argument("--stop", type=int, default=100, help="Ending depth (default: 100)")
        parser.add_argument("--step", type=int, default=10, help="Depth step (default: 10)")
        parser.add_argument("--force", action="store_true", help="Overwrite existing programs")

    def run(self, args):
        PROGRAMS_DIR.mkdir(exist_ok=True)
        depths = range(args.start, args.stop + 1, args.step)

        for depth in depths:
            out = PROGRAMS_DIR / f"{depth}.program"
            if out.exists() and not args.force:
                print(f"  {out.name} already exists, skipping")
                continue
            print(f"  Generating {out.name} (depth={depth}) ...")
            out.write_text(ProgramGenerator(depth).generate() + "\n")

        print(f"Done. {len(list(PROGRAMS_DIR.glob('*.program')))} program(s) in {PROGRAMS_DIR}")


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

class RunCommand(Command):
    name = "run"
    help = "Run programs against evaluators"

    def configure(self, parser):
        parser.add_argument("-j", "--jobs", type=int, default=0, help="Parallel jobs (default: cpu count)")
        parser.add_argument("-e", "--evaluators", nargs="+", help="Evaluators to run (default: all)")

    @staticmethod
    def _run_one(prog: Path, evaluator: str, aps_dir: Path) -> dict:
        name = prog.name

        if is_done(evaluator, prog):
            return {"name": name, "evaluator": evaluator, "status": "SKIPPED", "elapsed": 0.0}

        d = result_dir(evaluator, name)
        d.mkdir(parents=True, exist_ok=True)

        output_file = d / "output"
        hash_file = d / "hash"
        time_file = d / "time"

        cmd = ["make", "--no-print-directory",
               f"EVALUATOR={evaluator}", f"ARGS={prog}",
               "NestedUbdDriver.run"]

        start = time.monotonic()
        with open(output_file, "w") as out_f:
            result = subprocess.run(cmd, cwd=aps_dir, stdout=out_f, stderr=subprocess.STDOUT)
        elapsed = time.monotonic() - start

        status = "OK" if result.returncode == 0 else f"FAILED (exit {result.returncode})"

        time_file.write_text(f"{elapsed:.3f}\n")
        if result.returncode == 0:
            hash_file.write_text(sha256_file(prog) + "\n")
        else:
            hash_file.unlink(missing_ok=True)

        return {"name": name, "evaluator": evaluator, "status": status, "elapsed": elapsed}

    def run(self, args):
        if not APS_DIR.is_dir():
            print(f"ERROR: APS directory not found: {APS_DIR}", file=sys.stderr)
            sys.exit(1)

        programs = sorted(PROGRAMS_DIR.glob("*.program"), key=lambda p: int(p.stem))
        if not programs:
            print(f"ERROR: No *.program files in {PROGRAMS_DIR}. Run 'generate' first.", file=sys.stderr)
            sys.exit(1)

        batch_size = args.jobs or os.cpu_count() or 4
        evaluators = [e.upper() for e in args.evaluators] if args.evaluators else EVALUATORS

        print(f"Found {len(programs)} program(s), batch size {batch_size}")
        print()

        for evaluator in evaluators:
            (ROOT_DIR / evaluator.lower()).mkdir(exist_ok=True)

            print(f"=== Running with EVALUATOR={evaluator} ===")

            subprocess.run(
                ["make", "--no-print-directory", f"EVALUATOR={evaluator}", "clean"],
                cwd=APS_DIR, check=True,
            )
            subprocess.run(
                ["make", "--no-print-directory", f"EVALUATOR={evaluator}", "NestedUbdDriver.class"],
                cwd=APS_DIR, check=True,
            )

            aps_dir = APS_DIR.resolve()

            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                futures = [
                    executor.submit(self._run_one, prog, evaluator, aps_dir)
                    for prog in programs
                ]
                for future in as_completed(futures):
                    r = future.result()
                    elapsed_str = f"{r['elapsed']:.3f}"
                    if r["status"] == "SKIPPED":
                        print(f"  {r['name']} -> {evaluator} ... SKIPPED")
                    else:
                        print(f"  {r['name']} -> {evaluator} ... {r['status']} ({elapsed_str}s)")

            print()


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------

class CheckCommand(Command):
    name = "check"
    help = "Compare output hashes across evaluators"

    def configure(self, parser):
        parser.add_argument("--reference", default="dynamic", help="Reference evaluator (default: dynamic)")

    def run(self, args):
        reference = args.reference.lower()
        others = [e.lower() for e in EVALUATORS if e.lower() != reference]
        all_pass = True

        ref_dir = ROOT_DIR / reference
        if not ref_dir.exists():
            print(f"ERROR: Reference directory not found: {ref_dir}", file=sys.stderr)
            sys.exit(1)

        program_dirs = sorted(
            [d for d in ref_dir.iterdir() if d.is_dir()],
            key=lambda d: int(d.name.split(".")[0])
        )

        for prog_dir in program_dirs:
            name = prog_dir.name
            ref_output = prog_dir / "output"
            if not ref_output.exists():
                continue

            ref_hash = sha256_file(ref_output)
            fail = False

            for other in others:
                other_output = ROOT_DIR / other / name / "output"
                if not other_output.exists():
                    print(f"  MISSING: {name} in {other}")
                    fail = True
                elif sha256_file(other_output) != ref_hash:
                    print(f"  MISMATCH: {name} ({reference} vs {other})")
                    fail = True

            if not fail:
                print(f"  OK: {name}")
            else:
                all_pass = False

        if all_pass:
            print("\nAll outputs match.")
        else:
            sys.exit(1)


# ---------------------------------------------------------------------------
# times
# ---------------------------------------------------------------------------

class TimesCommand(Command):
    name = "times"
    help = "Display timing table"

    def run(self, args):
        COL_W = 14

        # Collect all program names across evaluators
        times = {}
        programs_seen = set()

        for ev in EVALUATORS:
            ev_dir = ROOT_DIR / ev.lower()
            if not ev_dir.exists():
                continue
            for prog_dir in ev_dir.iterdir():
                if not prog_dir.is_dir():
                    continue
                time_file = prog_dir / "time"
                if time_file.exists():
                    programs_seen.add(prog_dir.name)
                    times[(prog_dir.name, ev)] = time_file.read_text().strip()

        if not programs_seen:
            print("No timing data found. Run 'run' first.", file=sys.stderr)
            sys.exit(1)

        sorted_programs = sorted(programs_seen, key=lambda p: int(p.split(".")[0]))

        print(f"{'Program':<{COL_W}}", end="")
        for ev in EVALUATORS:
            print(f"{ev:<{COL_W}}", end="")
        print()

        print(f"{'-------':<{COL_W}}", end="")
        for _ in EVALUATORS:
            print(f"{'-------':<{COL_W}}", end="")
        print()

        for prog in sorted_programs:
            print(f"{prog:<{COL_W}}", end="")
            for ev in EVALUATORS:
                val = times.get((prog, ev), "N/A")
                print(f"{val + 's':<{COL_W}}", end="")
            print()


# ---------------------------------------------------------------------------
# clean
# ---------------------------------------------------------------------------

class CleanCommand(Command):
    name = "clean"
    help = "Remove generated output directories"

    def configure(self, parser):
        parser.add_argument("--programs", action="store_true", help="Also remove programs/")

    def run(self, args):
        import shutil
        for ev in EVALUATORS:
            d = ROOT_DIR / ev.lower()
            if d.exists():
                shutil.rmtree(d)
                print(f"  Removed {d}")
        if args.programs and PROGRAMS_DIR.exists():
            shutil.rmtree(PROGRAMS_DIR)
            print(f"  Removed {PROGRAMS_DIR}")
        print("Done.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

COMMANDS = [GenerateCommand(), RunCommand(), CheckCommand(), TimesCommand(), CleanCommand()]


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Farrow UBD across APS evaluators.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    for cmd in COMMANDS:
        p = sub.add_parser(cmd.name, help=cmd.help)
        cmd.configure(p)
        p.set_defaults(cmd_obj=cmd)

    args = parser.parse_args()
    args.cmd_obj.run(args)


if __name__ == "__main__":
    main()
