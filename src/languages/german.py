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
import spacy

# Local imports
from languages.util import GENDER, get_gender_from_token
#=-----

DE_DETERMINERS = {"der": GENDER.male, "ein": GENDER.male, "dem": GENDER.male, #"den": GENDER.male, 
                  "einen": GENDER.male, "des": GENDER.male, "er": GENDER.male, "seiner": GENDER.male,
                  "ihn": GENDER.male, "seinen": GENDER.male, "ihm": GENDER.male, "ihren": GENDER.male,
                  "die": GENDER.female, "eine": GENDER.female, "einer": GENDER.female, "seinem": GENDER.male,
                  "ihrem": GENDER.male, "sein": GENDER.male,
                  "sie": GENDER.female, "seine": GENDER.female, "ihrer": GENDER.female, 
                  "ihr": GENDER.neutral, "ihre": GENDER.neutral, "das": GENDER.neutral,
                  "jemanden": GENDER.neutral} 


# German professions with only one possible gender
GERMAN_EXCEPTION = {"nurse": GENDER.female,
                    "the nurse": GENDER.female}


class GermanPredictor:
    """
    German gender predictor
    """
    def __init__(self):
        """
        Init spacy for the specified language code.
        """
        self.lang = "de"
        self.cache = {}    # Store calculated professions genders
        self.nlp = spacy.load("de", disable = ["parser", "ner"])

    def get_gender(self, profession: str, translated_sent, entity_index, ds_entry) -> GENDER:
        """
        Predict gender of an input profession.
        """
        gold, src_index, src_sent, src_profession = ds_entry
        src_profession = src_profession.lower()
        if src_profession in GERMAN_EXCEPTION:
            return GERMAN_EXCEPTION[src_profession]
    
        if entity_index == -1:
            return GENDER.male
        words = [word.text for word in self.nlp(translated_sent)]
        profession_words = [word.text for word in self.nlp(profession)]
        if any([word.endswith("in") for word in profession_words]):
#            pdb.set_trace()
            return GENDER.female
        dets = self.get_determiners(words)
        if len(dets) < 2:
            logging.warn(f"less than two dets found: {translated_sent}")
        if len(dets) == 0:
            return GENDER.male
        closest_det = min(dets, key = lambda elem: abs(elem[0] - entity_index))
        identified_gender = DE_DETERMINERS[closest_det[1]]
        return identified_gender

    def get_determiners(self, words):
        """
        Get a list of (index, determiners)
        given a list of words.
        """
        determiners = [(word_ind, word.lower()) for (word_ind, word) in enumerate(words)
                       if word.lower() in DE_DETERMINERS]
        return determiners

    def _get_gender(self, profession: str) -> GENDER:
        """
        Predict gender, without using cache
        """
        if not profession.strip():
            # Empty string
            return GENDER.unknown

        toks = self.nlp(profession)
        observed_genders = [gender for gender in map(get_gender_from_token, toks)
                            if gender is not None]

        if not observed_genders:
            # No observed gendered words - return unknown
            return GENDER.unknown

        # Return the most commonly observed gender
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
