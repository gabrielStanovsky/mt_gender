#!/bin/bash
# Usage:
#   evaluate_language.sh <corpus> <lang-code> <translation system>
#
# e.g.,
# ../scripts/evaluate_language.sh ../data/agg/en.txt es google

set -e

# Parse parameters
dataset=$1
lang=$2
trans_sys=$3
prefix=adj.en-$lang

# Prepare files for translation
cut -f3 $dataset > ./tmp.in            # Extract sentences
mkdir -p ../translations/$trans_sys/
mkdir -p ../data/human/$lang

# Translate
trans_fn=../translations/$trans_sys/$prefix.txt
if [ ! -f $trans_fn ]; then
    python translate.py --trans=$trans_sys --in=./tmp.in --src=en --tgt=$2 --out=$trans_fn
else
    echo "Not translating since translation file exists: $trans_fn"
fi

# Align
align_fn=forward.$prefix.align
../../fast_align/build/fast_align -i $trans_fn  -d -o -v > $align_fn

# Evaluate
mkdir -p ../data/human/$trans_sys/$lang/
out_fn=../data/human/$trans_sys/$lang/${lang}.pred.csv
python load_alignments.py --ds=$dataset  --bi=$trans_fn --align=$align_fn --lang=$lang --out=$out_fn

# Prepare files for human annots
# human_fn=../data/human/$trans_sys/$lang/${lang}.in.csv
# python human_annots.py --ds=$dataset --bi=$trans_fn --out=$human_fn
