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

SPACY_NLP = spacy.load("es", disable = ["parser", "ner"])

def get_gender_es(profession: str) -> GENDER:
    """
    (Spanish)
    Predict gender of an input profession.
    """
    if not profession.strip():
        return GENDER.unknown

    toks = SPACY_NLP(profession)
    observed_genders = [gender for gender in map(get_gender_from_token, toks)
                        if gender is not None]

    if not observed_genders:
        return GENDER.neutral

    common_gender = Counter(observed_genders).most_common()[0][0]
    return common_gender

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
