""" Usage:
    <file-name> --in=IN_FILE --out=OUT_FILE [--debug]
"""
# External imports
import logging
import pdb
from pprint import pprint
from pprint import pformat
from docopt import docopt
from collections import defaultdict
from operator import itemgetter
from tqdm import tqdm
from collections import Counter
import pymorphy2
from pymorphy2.tokenizers import simple_word_tokenize
from pymorphy2 import dawg

# Local imports
from languages.util import GENDER, PYMORPH_GENDER_TYPES
#=-----

class PymorphPredictor:
    """
    Class for PyMorph supported languages.
    These include Russian and Ukrainian.
    """
    def __init__(self, lang: str):
        """
        Init pymorph for the specified language code.
        https://pymorphy2.readthedocs.io/en/latest/user/guide.html
        """
        assert lang in ["uk", "ru"]
        self.lang = lang
        self.cache = {}    # Store calculated professions genders
        self.tagger = pymorphy2.MorphAnalyzer(lang = lang)

    def get_gender(self, profession: str, translated_sent = None, entity_index = None, ds_entry = None) -> GENDER:
        """
        Predict gender of an input profession.
        """
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

        toks = simple_word_tokenize(profession)

        observed_genders = [self.get_word_gender(tok) for tok in toks]

        if not observed_genders:
            # No observed gendered words - return unknown
            return GENDER.unknown

        # Return the most commonly observed gender
        return Counter(observed_genders).most_common()[0][0]

    def get_word_gender(self, word):
        """
        Get the most probable gender, based on the frequency of
        predictions.
        """
        morphs = self.tagger.parse(word)
        observed_genders = [PYMORPH_GENDER_TYPES[morph.tag.gender] for morph in morphs
                            if (morph.tag.gender is not None)]

        if not observed_genders:
            return GENDER.neutral

        if GENDER.female in observed_genders:
            return GENDER.female

        return Counter(observed_genders).most_common()[0][0]

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
