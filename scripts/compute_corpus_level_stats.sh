#!/bin/sh
## compute_corpus_level_stats.sh
set -e

python compute_corpus_level_stats.py --in=../new_outputs/covid/ --out=../new_outputs/covid/corpus_level.csv
python compute_corpus_level_stats.py --in=../new_outputs/pubmed/ --out=../new_outputs/pubmed/corpus_level.csv
python compute_corpus_level_stats.py --in=../new_outputs/wiki/ --out=../new_outputs/wiki/corpus_level.csv
