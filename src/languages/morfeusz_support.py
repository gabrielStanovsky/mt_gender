""" Usage:
    <file-name> --in=IN_FILE --out=OUT_FILE [--debug]
"""

from collections import Counter
import logging
from docopt import docopt
import spacy
from spacy.tokens.token import Token

from languages.util import GENDER, MORFEUSZ_GENDER_TYPES, MORFEUSZ_GENDER_TAG_POSITION


class MorfeuszPredictor:
    """
    Class for Morfeusz -- Polish Morphology Analyzer
    """

    def __init__(self):
        """
        Init spacy with morfeusz2.
        https://github.com/ipipan/spacy-pl
        http://morfeusz.sgjp.pl/
        """
        import morfeusz2
        self.lang = "pl"
        self.cache = {}    # Store calculated professions
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

        gold, src_index, src_sent, src_profession = ds_entry
        if profession not in self.cache:
            self.cache[profession] = self._get_gender(profession)

        return self.cache[profession]

    def _get_gender(self, profession: str) -> GENDER:
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
            # No observed gendered words - return neutral
            return GENDER.neutral

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
                morfeusz_gender = features[MORFEUSZ_GENDER_TAG_POSITION -1]
            else:
                return GENDER.neutral

        return MORFEUSZ_GENDER_TYPES[morfeusz_gender]


if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    inp_fn = args["--in"]
    out_fn = args["--out"]
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    logging.info("DONE")
