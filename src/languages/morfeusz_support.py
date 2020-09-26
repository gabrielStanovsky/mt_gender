""" Usage:
    <file-name> --in=IN_FILE --out=OUT_FILE [--debug]
"""

from collections import Counter
import logging
from docopt import docopt
import spacy
from spacy.tokens.token import Token
import re
import json

from languages.util import GENDER, MORFEUSZ_GENDER_TYPES, MORFEUSZ_GENDER_TAG_POSITION, WB_GENDER_TYPES


class MorfeuszPredictor:
    """
    Class for Morfeusz -- Polish Morphology Analyzer
    """

    pl_variants_fn = "./languages/pl_variants.json"

    def __init__(self):
        """
        Init spacy with morfeusz2.
        https://github.com/ipipan/spacy-pl
        http://morfeusz.sgjp.pl/
        """
        import morfeusz2
        self.lang = "pl"
        self.cache = {}    # Store calculated professions

        with open(self.pl_variants_fn, 'r') as var_json:
            self.variants = json.load(var_json)

        if spacy.util.is_package('pl_spacy_model_morfeusz_big'):
            self.nlp = spacy.load('pl_spacy_model_morfeusz_big', disable=["parser", "ner"])
        elif spacy.util.is_package('pl_spacy_model_morfeusz'):
            self.nlp = spacy.load('pl_spacy_model_morfeusz', disable=["parser", "ner"])
        else:
            raise FileNotFoundError("Spacy model with Morfeusz not found.\n"
                                    "To run analysis for Polish install Morfeusz from: http://morfeusz.sgjp.pl/\n"
                                    "and download Spacy model with Morfeusz from: https://github.com/ipipan/spacy-pl")

    def get_gender(self, profession: str, translated_sent = None, entity_index = None, ds_entry = None) -> GENDER:
        """
        Predict gender of an input profession.
        """

        gold_gender, src_index, src_sent, src_profession = ds_entry
        src_profession = src_profession.lower()
        src_profession_split = src_profession.split(' ')
        if len(src_profession_split) > 1 and src_profession_split[0] in ('a', 'an', 'the'):
            src_profession = ' '.join(src_profession_split[1:])

        if src_profession in ('child', 'someone', 'advisee', 'mover') \
                or gold_gender == 'neutral':
            return GENDER.ignore

        gender = self._get_gender(profession, translated_sent, gold_gender, src_profession)


        return gender

    def _get_gender(self, profession: str, translated_sent: str, gold_gender: str, src_profession: str) -> GENDER:
        # initially try to resolve problem based on exact manual rules
        gender = self._get_gender_manual_rules(translated_sent, gold_gender, src_profession)

        if gender is not GENDER.unknown:
            return gender

        return self._get_gender_automatically(profession)

    def _get_gender_manual_rules(self, translated_sent: str, gold_gender: str, src_profession: str) -> GENDER:
        # Rules defined and checked by Tomasz Limisiewicz

        translated_sent = translated_sent.lower()

        found_gender = GENDER.unknown

        male = src_profession + "-male"
        female = src_profession + "-female"

        both_possible = False
        if male in self.variants:
            for form in self.variants[male]:
                # don't match when profession is preceded by `mrs.` in Polish `pani`, `panią`
                if re.search(form + "(\W|$)", translated_sent, flags=re.UNICODE) and \
                        not re.search("(pani|panią) " + form + "(\W|$)", translated_sent, flags=re.UNICODE):
                    found_gender = GENDER.male
                    break

        if female in self.variants:
            for form in self.variants[female]:
                if re.search(form + "(\W|$)", translated_sent, flags=re.UNICODE):
                    if found_gender == GENDER.male:
                        found_gender = GENDER.unknown
                        both_possible = True
                    else:
                        found_gender = GENDER.female
                    break

        # our morphology analysis cannot analyze whole sentence, therefore if both are possible, mark it as correct
        # it is quite uncommon for Polish
        if both_possible:
            if gold_gender == "male":
                return GENDER.male
            else:
                return GENDER.female

        return found_gender

    def _get_gender_automatically(self, profession: str) -> GENDER:
        """
        Predict gender, without using cache
        """
        if not profession.strip():
            # Empty string
            return GENDER.unknown

        tokens = self.nlp(profession)
        observed_genders = [self.get_gender_from_token(tok) for tok in tokens]
        observed_genders = [gender for gender in observed_genders if gender]

        if not observed_genders:
            return GENDER.unknown

        # Return the most commonly observed gender
        return Counter(observed_genders).most_common()[0][0]

    @staticmethod
    def get_gender_from_token(token: Token):
        """
        Get gender indication from spacy token with morfeusz, if it exists
        """
        features = token._.feats.split(':')
        if len(features) < MORFEUSZ_GENDER_TAG_POSITION + 1:
            return None

        morfeusz_gender = features[MORFEUSZ_GENDER_TAG_POSITION]
        if morfeusz_gender not in MORFEUSZ_GENDER_TYPES:
            if features[MORFEUSZ_GENDER_TAG_POSITION - 1] in MORFEUSZ_GENDER_TYPES:
                morfeusz_gender = features[MORFEUSZ_GENDER_TAG_POSITION - 1]
            else:
                return GENDER.unknown

        return MORFEUSZ_GENDER_TYPES[morfeusz_gender]


if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    inp_fn = args["--in"]
    out_fn = args["--out"]
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.info("DONE")
