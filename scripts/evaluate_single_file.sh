#!/bin/bash
# Usage:
#   evaluate_single_file.sh <gold> <predicted> <lang> <log>
#

set -e

# Parse parameters
gold=$1
pred=$2
lang=$3
log=$4

# Align
align_fn=${pred}.forward.align
if [ ! -f $align_fn ]; then
    $FAST_ALIGN_BASE/build/fast_align -i $pred  -d -o -v > $align_fn
else
    echo "Skipping alignment since file exists: $align_fn"
fi

# Evaluate
out_fn=${pred}.pred.csv
python load_alignments.py --ds=$gold  --bi=$pred --align=$align_fn --lang=$lang --out=$out_fn >> $log

