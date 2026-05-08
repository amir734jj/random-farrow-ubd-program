#!/usr/bin/env bash
xargs -I{} sh -c 'python3 get_farrow.py --depth={} > {}.program' <<< "$(seq 10 10 100)"
