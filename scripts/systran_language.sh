#!/bin/bash
# Usage:
#   systran_language.sh <corpus> <lang-code>
set -e

# Parse parameters
dataset=$1
lang=$2
trans_sys=systran
prefix=en-$lang

# Prepare files for translation
cut -f3 $dataset > ./tmp.in            # Extract sentences
mkdir -p ../translations/$trans_sys/
mkdir -p ../data/human/$trans_sys/$lang/

# Translate
trans_fn=../translations/$trans_sys/$prefix.txt
if [ ! -f $trans_fn ]; then
    ../../translation-api-python-client/.venv2.7/bin/python systran_translate.py \
                                                            --in=./tmp.in \
                                                            --src=en \
                                                            --tgt=$2 \
                                                            --out=$trans_fn
else
    echo "Not translating since translation file exists: $trans_fn"
fi

