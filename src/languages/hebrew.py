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
from spacy.lang.he import Hebrew

# Local imports
from languages.util import GENDER
#=-----

class HebrewPredictor:
    """
    Hebrew morphology heurstics.
    """
    def __init__(self):
        """
        Init tokenizer for Hebrew.
        """
        self.lang = "he"
        self.cache = {}    # Store calculated professions genders
        self.tokenizer = Hebrew().tokenizer

    def get_gender(self, profession: str) -> GENDER:
        """
        Predict gender of an input profession.
        """
        if profession not in self.cache:
            self.cache[profession] = self._get_gender(profession)

        return self.cache[profession]

    def _get_gender(self, profession: str) -> GENDER:
        """
        Predict gender, without using cache.
        Super hacky, based on the last letter.
        """
        if not profession.strip():
            # Empty string is an error in alignment
            return GENDER.unknown

        toks = [w.text for w in self.tokenizer(profession)
                if w.text != "את"]

        if any([tok[-1] in ["ת", "ה"] for tok in toks]):
            return GENDER.female

        return GENDER.male


class ArabicPredictor:
    """
    Hebrew morphology heurstics.
    """
    def __init__(self):
        """
        Init tokenizer for Arabic.
        """
        self.lang = "ar"
        self.cache = {}    # Store calculated professions genders
        self.tokenizer = lambda sent: sent.split() # Might be better with a dedicated Arabic tokenizer

    def get_gender(self, profession: str) -> GENDER:
        """
        Predict gender of an input profession.
        """
        if profession not in self.cache:
            self.cache[profession] = self._get_gender(profession)

        return self.cache[profession]

    def _get_gender(self, profession: str) -> GENDER:
        """
        Predict gender, without using cache.
        Super hacky, based on the last letter being tāʾ marbūṭa.
        """
        if not profession.strip():
            # Empty string is an error in alignment
            return GENDER.unknown

        toks = self.tokenizer(profession)

        if any([("ة" in tok) or ("ﺔ" in tok) for tok in toks]):
            return GENDER.female

        return GENDER.male


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
