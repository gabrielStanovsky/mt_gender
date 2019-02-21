#!/bin/bash
# Usage:
#   evaluate_language.sh <corpus> <lang-code>
#
# e.g.,
# ../scripts/evaluate_language.sh ../data/agg/en.txt es

set -e

# Parse parameters
dataset=$1
lang=$2
prefix=en-$lang

# Prepare files for translation
cut -f3 $dataset > ./tmp.in            # Extract sentences
mkdir -p ../translations/google/
mkdir -p ../data/human/$lang

# Translate
trans_fn=../translations/google/$prefix.txt
if [ ! -f $trans_fn ]; then
    python google_translate.py --in=./tmp.in --src=en --tgt=$2 --out=$trans_fn
else
    echo "Not translating since translation file exists: $trans_fn"
fi

# Align
align_fn=forward.$prefix.align
../../fast_align/build/fast_align -i $trans_fn  -d -o -v > $align_fn

# Evaluate
out_fn=../data/human/$lang/${lang}.pred.csv
python load_alignments.py --ds=$dataset  --bi=$trans_fn --align=$align_fn --lang=$lang --out=$out_fn

# Prepare files for human annots
human_fn=../data/human/$lang/${lang}.in.csv
python human_annots.py --ds=$dataset --bi=$trans_fn --seed=seed.txt --out=$human_fn
