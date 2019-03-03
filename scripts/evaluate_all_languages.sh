#!/bin/bash
# Usage:
#   evaluate_all_languages.sh <output-folder>
set -e

out_folder=$1
corpus_fn=../data/aggregates/en.txt

# Problematic (no morphology?): "de" "pt"
# Slightly less problematic (different morph tags?):  "nl"

#langs=("ar" "de" "uk" "he" "ru" "it" "fr" "es")
langs=("ar" "uk" "he" "ru" "it" "fr" "es")
mt_systems=("aws" "bing" "google" "systran" )

# Make sure systran has all translations
for lang in ${langs[@]}
do
    echo "Translating $lang with systran..."
    ../scripts/systran_language.sh $corpus_fn $lang
done

for trans_sys in ${mt_systems[@]}
do
    for lang in ${langs[@]}
    do
        echo "evaluating $trans_sys, $lang"
        if [[ "$lang" == "uk" && "$trans_sys" == "aws" ]]; then
            echo "skipping.."
            continue
        fi
        # Run evaluation
        mkdir -p $out_folder/$trans_sys
        out_file=$out_folder/$trans_sys/$lang.log
        echo "Evaluating $lang into $out_file"
        ../scripts/evaluate_language.sh $corpus_fn $lang $trans_sys > $out_file
    done
done

echo "DONE!"
