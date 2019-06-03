# Evaluating Gender Bias in Machine Translation

**NOTE**: this repo is a little bit messy, will be organized and cleaned in the next couple of weeks

This repo contains code and data for reproducing the experiments in "Evaluating Gender Bias in Machine Translation" (Stanovsky et al., 2019).

## Requirements
* [fast_align](https://github.com/clab/fast_align) -- install and point an environment variable called FAST_ALIGN_BASE to its root folder (the one containing a `build` folder).

## Install
`pip install -r requirements.txt`

## Running our experiments 
Run all of the following from the  `src` folder. Output logs will be written to the given
path.
* For the general accuracy number, run:

        ../scripts/evaluate_all_languages.sh ../data/aggregates/en.txt  path/to/output/folder/

* For evaluating *pro*-sterotypical translations, run:

        ../scripts/evaluate_all_languages.sh ../data/aggregates/en_pro.txt  path/to/output/folder/

* For evaluating *anti*-sterotypical translations, run:

        ../scripts/evaluate_all_languages.sh ../data/aggregates/en_anti.txt  path/to/output/folder/


## Extending this framework

### Adding an MT system

### Adding a language
