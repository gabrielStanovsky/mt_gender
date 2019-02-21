#!/bin/bash
# Usage:
#   ../scripts/create_english_dataset.sh
set -e

# Convert the two datatset
python convert_winobias_to_winogender.py --in=../data/winobias.all.txt --out=../data/aggregates/en_winobias.txt
python fix_dataset.py --in=../../winogender-schemas/data/all_sentences.tsv --out=../data/aggregates/en_winogender.txt

# Concat
cat ../data/aggregates/en_winobias.txt ../data/aggregates/en_winogender.txt > ../data/aggregates/en.txt

echo "DONE!"
