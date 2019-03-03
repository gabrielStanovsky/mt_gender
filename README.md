* Google translate:
  * [Installing and configuring google-translate](https://cloud.google.com/translate/docs/quickstart-client-libraries?authuser=1#client-libraries-install-python)
  * [Languages supported](https://cloud.google.com/translate/docs/languages)
cut -f3 ~/mt_gender/data/aggregates/en.txt | python spacy_tokenize.py | python interactive.py --path ./models/wmt18ensemble/nc_model/model.pt    ./models/wmt18ensemble/nc_model/ --beam 5 --source-lang en --target-lang de > mt_gender.de
cut -f3 ~/mt_gender/data/aggregates/en.txt | python spacy_tokenize.py | python interactive.py --path ./models/wmt14.en-fr.joined-dict.transformer/model.pt ./models/wmt14.en-fr.joined-dict.transformer --beam 5 --source-lang en --target-lang fr > mt_gender.fr
