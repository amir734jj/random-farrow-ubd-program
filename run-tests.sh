#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

usage() {
    echo "Usage: $0 [--clean]"
}

CLEAN=false
while (($#)); do
    case "$1" in
        --clean)
            CLEAN=true
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

# Define the test cases: "DriverName|OutputPrefix|ExtraGenerateFlags"
# (Leave ExtraGenerateFlags empty if not needed)
TEST_CASES=(
    "FarrowUbdDriver|farrow-ubd|--no-siblings"
    "FarrowUbdFiberDriver|farrow-ubd-fiber|--no-siblings"
    "NestedUbdDriver|nested-ubd|"
    "NestedUbdFiberDriver|nested-ubd-fiber|"
)

APS_DIR="./aps-june15/examples/scala"

if [[ "$CLEAN" == true ]]; then
    echo "Cleaning previous test results..."
    python3 main.py clean --programs
    rm -f -- farrow-ubd.out farrow-ubd-fiber.out nested-ubd.out nested-ubd-fiber.out
fi

for case in "${TEST_CASES[@]}"; do
    # Split the string by the pipe delimiter
    IFS="|" read -r DRIVER OUT_PREFIX EXTRA_FLAGS <<< "$case"
    OUT_FILE="${OUT_PREFIX}.out"
    
    echo "========================================="
    echo "Running tests for: $DRIVER"
    echo "Output file: $OUT_FILE"
    echo "========================================="

    # 1. Clean up old output and programs
    rm -f "$OUT_FILE"
    python3 main.py clean --programs

    # 2. Generate (evaluates if EXTRA_FLAGS like --no-siblings is present)
    EXTRA_ARGS=()
    if [[ -n "$EXTRA_FLAGS" ]]; then
        EXTRA_ARGS+=("$EXTRA_FLAGS")
    fi
    python3 main.py generate "${EXTRA_ARGS[@]}" --stop 100

    # 3. Run the driver
    python3 main.py run --aps-dir "$APS_DIR" --driver "$DRIVER"

    # 4. Check and record times into the specific output file
    python3 main.py check > "$OUT_FILE"
    echo "" >> "$OUT_FILE"
    python3 main.py times >> "$OUT_FILE"
done

echo "All tests completed!"
