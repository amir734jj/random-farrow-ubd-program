#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

failed=0

run_benchmark() {
  local driver=$1 gen_flags=$2 out=$3

  echo "=== $driver ==="
  python3 main.py clean --programs
  python3 main.py generate --stop 200 $gen_flags
  python3 main.py run --driver "$driver"
  echo "# Result for $driver" > "$out"
  python3 main.py check >> "$out"
  python3 main.py times >> "$out"

  if grep -q 'All outputs match' "$out"; then
    echo "PASS: $out"
  else
    echo "FAIL: $out"
    failed=1
  fi
  echo
}

run_benchmark FarrowUbdDriver      "--no-siblings" farrow-ubd.out
run_benchmark FarrowUbdFiberDriver  "--no-siblings" farrow-ubd-fiber.out
run_benchmark NestedUbdDriver       ""              nested-ubd.out
run_benchmark NestedUbdFiberDriver  ""              nested-ubd-fiber.out

if [ $failed -ne 0 ]; then
  echo "SOME BENCHMARKS FAILED"
  exit 1
fi
echo "ALL BENCHMARKS PASSED"
