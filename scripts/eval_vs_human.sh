#!/bin/bash
# Usage:
#   eval_vs_human.sh <output-folder>
set -e

out_folder=$1

for lang in "he" "es" "fr"
do
    gold_fn=../data/human/google/$lang/$lang.gold.csv
    pred_fn=../data/human/google/$lang/$lang.pred.csv
    out_fn=$out_folder/google.$lang.log
    echo "Evaluating $lang into $out_fn"
    python eval_human.py --gold=$gold_fn --pred=$pred_fn --debug &> $out_fn
done

echo "DONE!"
