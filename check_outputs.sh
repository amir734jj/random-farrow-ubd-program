#!/usr/bin/env bash
# Check that every *.program.output in dynamic/ matches static/ and synth/
# Comparison is order-insensitive: elements are sorted before diffing.

all_pass=true

for f in dynamic/*.program.output; do
    name=$(basename "$f")
    fail=false

    for other in static synth; do
        other_f="$other/$name"
        if [[ ! -f "$other_f" ]]; then
            echo "MISSING: $other_f"
            fail=true
            continue
        fi
        if ! diff -q <(cat "$f" | tr ',' '\n' | sort) <(cat "$other_f" | tr ',' '\n' | sort) > /dev/null 2>&1; then
            echo "MISMATCH: $f vs $other_f"
            diff <(cat "$f" | tr ',' '\n' | sort) <(cat "$other_f" | tr ',' '\n' | sort)
            fail=true
        fi
    done

    if ! $fail; then
        echo "OK: $name"
    fi

    $fail && all_pass=false
done

if $all_pass; then
    echo "All outputs match."
    exit 0
else
    exit 1
fi
