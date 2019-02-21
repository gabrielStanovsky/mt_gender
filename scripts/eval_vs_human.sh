#!/bin/bash
# Usage:
#   eval_vs_human.sh <output-folder>
set -e

out_folder=$1

for lang in  "es"
do
    gold_fn=../data/human/$lang/$lang.gold.csv
    pred_fn=../data/human/$lang/$lang.pred.csv
    out_fn=$out_folder/$lang.log
    echo "Evaluating $lang into $out_fn"
    python eval_human.py --gold=$gold_fn --pred=$pred_fn --seed=seed.txt --debug &> $out_fn
done

echo "DONE!"
