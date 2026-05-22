#!/usr/bin/env bash
# Run all *.program files against APS using DYNAMIC, STATIC, and SYNTH evaluators,
# save outputs to the appropriate directories, then diff with check_outputs.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APS_DIR="/home/amir/workspace/synth-functions-pr-final/examples/scala"

# Verify the APS directory exists
if [[ ! -d "$APS_DIR" ]]; then
    echo "ERROR: APS directory not found: $APS_DIR" >&2
    exit 1
fi

declare -A EVALUATOR_DIRS=(
    [DYNAMIC]="$SCRIPT_DIR/dynamic"
    [STATIC]="$SCRIPT_DIR/static"
    [SYNTH]="$SCRIPT_DIR/synth"
)

# Ensure output directories exist
for dir in "${EVALUATOR_DIRS[@]}"; do
    mkdir -p "$dir"
done

# Collect all program files in numeric order
mapfile -t PROGRAMS < <(ls "$SCRIPT_DIR"/*.program 2>/dev/null | sort -t/ -k1 -V)

if [[ ${#PROGRAMS[@]} -eq 0 ]]; then
    echo "ERROR: No *.program files found in $SCRIPT_DIR" >&2
    exit 1
fi

echo "Found ${#PROGRAMS[@]} program(s): $(basename -a "${PROGRAMS[@]}" | tr '\n' ' ')"
echo

for evaluator in DYNAMIC STATIC SYNTH; do
    out_dir="${EVALUATOR_DIRS[$evaluator]}"
    timing_log="$out_dir/timing-${evaluator,,}.log"
    echo "=== Running with EVALUATOR=$evaluator ==="
    > "$timing_log"  # truncate/create
    rm -f "$out_dir"/*

    for prog in "${PROGRAMS[@]}"; do
        name="$(basename "$prog")"
        out_file="$out_dir/${name}.output"

        echo -n "  $name -> $evaluator ... "
        start=$(date +%s%3N)
        if make -C "$APS_DIR" --no-print-directory \
               EVALUATOR="$evaluator" ARGS="$prog" \
               NestedUbdDriver.run > "$out_file" 2>&1; then
            status="OK"
        else
            status="FAILED (exit $?)"
        fi
        end=$(date +%s%3N)
        elapsed_ms=$(( end - start ))
        elapsed=$(printf "%.3f" "$(echo "scale=3; $elapsed_ms / 1000" | bc)")
        echo "$name: $elapsed seconds" >> "$timing_log"
        echo "$status (${elapsed}s)"
    done
    echo "  Timing written to $timing_log"
    echo
done
