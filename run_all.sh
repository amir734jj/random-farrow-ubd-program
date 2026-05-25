#!/usr/bin/env bash
# Run all *.program files against APS using DYNAMIC, STATIC, and SYNTH evaluators,
# save outputs to the appropriate directories, then diff with check_outputs.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APS_DIR="../aps/examples/scala"

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
mapfile -t PROGRAMS < <(ls "$SCRIPT_DIR"/programs/*.program 2>/dev/null | sort -t/ -k1 -V)

if [[ ${#PROGRAMS[@]} -eq 0 ]]; then
    echo "ERROR: No *.program files found in $SCRIPT_DIR/programs/" >&2
    exit 1
fi

echo "Found ${#PROGRAMS[@]} program(s): $(basename -a "${PROGRAMS[@]}" | tr '\n' ' ')"
echo

for evaluator in STATIC SYNTH DYNAMIC ; do
    out_dir="${EVALUATOR_DIRS[$evaluator]}"
    timing_log="$out_dir/timing-${evaluator,,}.log"
    echo "=== Running with EVALUATOR=$evaluator ==="

    # Clean and compile once before running programs to avoid race conditions
    make -C "$APS_DIR" --no-print-directory EVALUATOR="$evaluator" clean
    make -C "$APS_DIR" --no-print-directory EVALUATOR="$evaluator" NestedUbdDriver.class

    batch=0
    for prog in "${PROGRAMS[@]}"; do
        name="$(basename "$prog")"
        out_file="$out_dir/${name}.output"
        sha_file="$out_dir/${name}.sha256"
        prog_sha="$(sha256sum "$prog" | cut -d' ' -f1)"

        # Skip if already successfully completed with the same program file
        if [[ -f "$out_file" ]] && grep -q '^Finished\.$' "$out_file" \
           && [[ -f "$sha_file" ]] && [[ "$(cat "$sha_file")" == "$prog_sha" ]]; then
            echo "  $name -> $evaluator ... SKIPPED (already finished)"
            continue
        fi

        (
            start=$(date +%s%3N)
            if scala -J-Xss64m -cp "$APS_DIR:$APS_DIR/../../lib/aps-library.jar" \
                   NestedUbdDriver "$prog" > "$out_file" 2>&1; then
                status="OK"
                echo "$prog_sha" > "$sha_file"
            else
                status="FAILED (exit $?)"
                rm -f "$sha_file"
            fi
            end=$(date +%s%3N)
            elapsed_ms=$(( end - start ))
            elapsed=$(printf "%.3f" "$(echo "scale=3; $elapsed_ms / 1000" | bc)")
            echo "$name: $elapsed seconds" >> "$timing_log"
            echo "  $name -> $evaluator ... $status (${elapsed}s)"
        ) &

        batch=$((batch + 1))
        if (( batch % 10 == 0 )); then
            wait
        fi
    done
    wait
    echo "  Timing written to $timing_log"
    echo
done
