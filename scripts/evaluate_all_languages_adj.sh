#!/bin/bash
# Usage:
#   evaluate_all_languages.sh <corpus> <output-folder>
set -e

corpus_fn=$1 # ../data/aggregates/en.txt
out_folder=$2


# Problematic (no morphology?): "de" "pt"
# Slightly less problematic (different morph tags?):  "nl"


langs=("ar" "uk" "he" "ru" "it" "fr" "es" "de")
#langs=("de")
#mt_systems=("sota" "aws" "bing" "google" "systran" )
mt_systems=("google" "bing")

# Make sure systran has all translations
# for lang in ${langs[@]}
# do
#     echo "Translating $lang with systran..."
#     ../scripts/systran_language.sh $corpus_fn $lang
# done

for trans_sys in ${mt_systems[@]}
do
    for lang in ${langs[@]}
    do
        echo "evaluating $trans_sys, $lang"
        if [[ "$lang" == "uk" && "$trans_sys" == "aws" ]]; then
            echo "skipping.."
            continue
        fi

        if [[ "$trans_sys" == "sota" ]]; then
            if [[ "$lang" != "de" && "$lang" != "fr" ]]; then
                echo "skipping.."
                continue
            fi
        fi

        # Run evaluation
        mkdir -p $out_folder/$trans_sys
        out_file=$out_folder/$trans_sys/$lang.log
        echo "Evaluating $lang into $out_file"
        ../scripts/evaluate_language_adj.sh $corpus_fn $lang $trans_sys > $out_file
    done
done

echo "DONE!"
