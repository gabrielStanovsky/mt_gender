""" Usage:
    <file-name> --in=IN_FILE --out=OUT_FILE [--debug]
"""
# External imports
import logging
import spacy
import pdb
from pprint import pprint
from pprint import pformat
from docopt import docopt
from collections import defaultdict
from operator import itemgetter
from tqdm import tqdm
from enum import Enum
from spacy.tokens.token import Token
from typing import Dict

# Local imports

#=-----

class GENDER(Enum):
    """
    Enumerate possible genders.
    """
    male = 0
    female = 1
    neutral = 2
    unknown = 3


SPACY_GENDER_TYPES = {
    "Masc": GENDER.male,
    "Fem": GENDER.female,
    "Neut": GENDER.neutral # seen in Dutch spacy
}

# Winobias gender type conversion
WB_GENDER_TYPES = {
    "male": GENDER.male,
    "female": GENDER.female,
    "neutral": GENDER.neutral,
}

PYMORPH_GENDER_TYPES = {
    "masc": GENDER.male,
    "femn": GENDER.female,
    "neut": GENDER.neutral,
    None: GENDER.neutral
}


def get_morphology_dict(token: Token) -> Dict:
    """
    Parse a morphology dictionary from spacy token.
    @TODO: No better way to do this?
    """
    if "__" not in token.tag_:
        raise AssertionError("No morphology support?")

    morphology = token.tag_.split("__")[1]

    if morphology == "_":
        return {}

    morphology_dict = dict([prop.split("=") for prop in morphology.split("|")])
    return morphology_dict

def get_gender_from_token(token: Token):
    """
    Get gender indication from spacy token, if it exists
    """
    morph_dict = get_morphology_dict(token)
    if "Gender" not in morph_dict:
        return None

    morph_gender = SPACY_GENDER_TYPES[morph_dict["Gender"]]
    return morph_gender

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

    nlp = spacy.load("es")
    doc = nlp('Las naranjas y las manzanas se parecen')
    logging.info(list(map(get_morphology_dict, doc)))

    logging.info("DONE")
