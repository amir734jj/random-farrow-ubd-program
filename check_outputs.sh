#!/usr/bin/env bash
# Check that output_sha256 values match across all evaluators' timing CSVs.
# Compares dynamic vs static and dynamic vs synth for each program.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REFERENCE="dynamic"
OTHERS=(static synth)

ref_csv="$SCRIPT_DIR/$REFERENCE/timing-${REFERENCE}.csv"

if [[ ! -f "$ref_csv" ]]; then
    echo "ERROR: Reference CSV not found: $ref_csv" >&2
    exit 1
fi

# Parse CSV: extract program -> output_sha256 mapping
get_hashes() {
    local csv="$1"
    # Skip header, extract program and output_sha256 (columns 1 and 5)
    tail -n +2 "$csv" | while IFS=, read -r program seconds status sha256 output_sha256; do
        echo "$program $output_sha256"
    done
}

declare -A REF_HASHES
while read -r prog hash; do
    REF_HASHES["$prog"]="$hash"
done < <(get_hashes "$ref_csv")

all_pass=true

for prog in "${!REF_HASHES[@]}"; do
    ref_hash="${REF_HASHES[$prog]}"
    fail=false

    for other in "${OTHERS[@]}"; do
        other_csv="$SCRIPT_DIR/$other/timing-${other}.csv"
        if [[ ! -f "$other_csv" ]]; then
            echo "MISSING: $other_csv"
            fail=true
            continue
        fi

        other_hash=$(get_hashes "$other_csv" | grep "^$prog " | cut -d' ' -f2)
        if [[ -z "$other_hash" ]]; then
            echo "MISSING: $prog in $other_csv"
            fail=true
        elif [[ "$ref_hash" != "$other_hash" ]]; then
            echo "MISMATCH: $prog ($REFERENCE vs $other)"
            fail=true
        fi
    done

    if ! $fail; then
        echo "OK: $prog"
    fi

    $fail && all_pass=false
done

if $all_pass; then
    echo "All outputs match."
    exit 0
else
    exit 1
fi
