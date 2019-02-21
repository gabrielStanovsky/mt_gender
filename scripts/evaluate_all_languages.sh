#!/bin/bash
# Usage:
#   evaluate_all_languages.sh <output-folder>
set -e

out_folder=$1

# Problematic (no morphology?): "de" "pt"
# Slightly less problematic (different morph tags?):  "nl"
for lang in  "it" "es" "fr"
do
    # Make sure that spacy model is available
    python -m spacy download $lang

    # Run evaluation
    out_file=$out_folder/$lang.log
    echo "Evaluating $lang into $out_file"
    ../scripts/evaluate_language.sh ../data/aggregates/en.txt $lang >> $out_file
done

echo "DONE!"
