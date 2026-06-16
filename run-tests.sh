#!/bin/bash

# Define the test cases: "DriverName|OutputPrefix|ExtraGenerateFlags"
# (Leave ExtraGenerateFlags empty if not needed)
TEST_CASES=(
    "FarrowUbdDriver|farrow-ubd|--no-siblings"
    "FarrowUbdFiberDriver|farrow-ubd-fiber|--no-siblings"
    "NestedUbdDriver|nested-ubd|"
    "NestedUbdFiberDriver|nested-ubd-fiber|"
)

APS_DIR="$HOME/workspace/aps-june15/examples/scala"

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
    python3 main.py generate $EXTRA_FLAGS --stop 150

    # 3. Run the driver
    python3 main.py run --aps-dir "$APS_DIR" --driver "$DRIVER"

    # 4. Check and record times into the specific output file
    python3 main.py check > "$OUT_FILE"
    echo "" >> "$OUT_FILE"
    python3 main.py times >> "$OUT_FILE"
done

echo "All tests completed!"
