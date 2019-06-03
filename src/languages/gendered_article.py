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


class GenderedArticlePredictor:
    """
    Gendered article predictor, assumes spacy support.
    """
    def __init__(self, lang, determiner_func, exceptions):
        """
        Init spacy for the specified language code.
        """
        self.lang = lang
        self.cache = {}    # Store calculated professions genders
        import pdb
        self.nlp = spacy.load(lang, disable = ["parser", "ner"])
        self.get_determiners = determiner_func
        self.exceptions = exceptions

    def get_gender(self, profession: str, translated_sent, entity_index, ds_entry) -> GENDER:
        """
        Predict gender of an input profession.
        """
        gold, src_index, src_sent, src_profession = ds_entry
        src_profession = src_profession.lower()
        if src_profession in self.exceptions:
            return self.exceptions[src_profession]
        if entity_index == -1:
            return GENDER.male
        words = [word.text for word in self.nlp(translated_sent)]
        profession_words = [word.text for word in self.nlp(profession)]
        if any([word.endswith("in") for word in profession_words]):
            return GENDER.female
        dets = self.get_determiners(words)
        if len(dets) < 2:
            logging.warn(f"less than two dets found: {translated_sent}")
        if len(dets) == 0:
            return GENDER.male
        closest_det = min(dets, key = lambda elem: abs(elem[0] - entity_index))
        identified_gender = closest_det[2]
        return identified_gender

def get_german_determiners(words):
    """
    Get a list of (index, determiner, gender)
    given a list of words.
    """
    determiners = []
    for (word_ind, word) in enumerate(words):
        word = word.lower()
        if word in DE_DETERMINERS:
            determiners.append((word_ind, word, DE_DETERMINERS[word]))
    return determiners

def get_french_determiners(words):
    """
    Get a list of (index, determiner, gender)
    given a list of words.
    """
    pdb.set_trace()
    determiners = []


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
