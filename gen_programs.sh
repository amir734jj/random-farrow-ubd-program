#!/usr/bin/env bash
mkdir -p programs
for n in $(seq 10 10 1000); do
    if [[ ! -f "programs/${n}.program" ]]; then
        python3 get_farrow.py --depth="$n" > "programs/${n}.program"
    fi
done
