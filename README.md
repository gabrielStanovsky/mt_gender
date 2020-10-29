# Evaluating Gender Bias in Machine Translation

This repo contains code and data for reproducing the experiments in [Evaluating Gender Bias in Machine Translation](https://arxiv.org/abs/1906.00591) [Gabriel Stanovsky](https://gabrielstanovsky.github.io/), [Noah A. Smith](https://homes.cs.washington.edu/~nasmith/), and [Luke Zettlemoyer](https://www.cs.washington.edu/people/faculty/lsz), (ACL 2019), and [Gender Coreference and Bias Evaluation at WMT 2020](https://arxiv.org/pdf/2010.06018.pdf), Tom Kocmi, Tomasz Limisiewicz, Gabriel Stanovsky (WMT2020).

## Citing

```
@InProceedings{Stanovsky2019ACL,
  author    = {Gabriel Stanovsky and Noah A. Smith and Luke Zettlemoyer},
  title     = {Evaluating Gender Bias in Machine Translation},
  booktitle = {ACL},
  month     = {June},
  year      = {2019},
  address   = {Florence, Italy},
  publisher = {Association for Computational Linguistics}
}
```

## Requirements
* [fast_align](https://github.com/clab/fast_align): install and point an environment variable called `FAST_ALIGN_BASE` to its root folder (the one containing the `build` folder).

### Evaluation in Polish


* Download and install Morfeusz2. Bindings for python and instruction are available at: http://morfeusz.sgjp.pl/download/en
* Download custom spaCy model (name should being with `pl_spacy_model_morfeusz`) from http://zil.ipipan.waw.pl/SpacyPL
* Install downloaded spaCy model:

      python -m pip install PATH/TO/pl_spacy_model_morfeusz-x.x.x.tar.gz


## Install
`./install.sh`

## Running our experiments 
This is the entry point for all our experiments: [scripts/evaluate_all_languages.sh](scripts/evaluate_all_languages.sh).
Run all of the following from the  `src` folder. Output logs will be written to the given
path.
* For the general gender accuracy number, run:

        ../scripts/evaluate_all_languages.sh ../data/aggregates/en.txt  path/to/output/folder/

* For evaluating *pro*-sterotypical translations, run:

        ../scripts/evaluate_all_languages.sh ../data/aggregates/en_pro.txt  path/to/output/folder/

* For evaluating *anti*-sterotypical translations, run:

        ../scripts/evaluate_all_languages.sh ../data/aggregates/en_anti.txt  path/to/output/folder/

## Adding an MT system
1. Translate the file in `data/aggregates/en.txt` to the languages in our evaluation method.
2. Put the transalations in `translations/your-mt-system/en-targetLanguage.txt` where each sentence is in a new line, which has the following format `original-sentence ||| translated sentence`. See [this file](translations/aws/en-fr.txt) for an example.
3. Add your translator in the `mt_systems` enumeration in the [evaluation script](scripts/evaluate_all_languages.sh).

