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
import re

# Local imports

#=-----

PN_TO_GENDER = {
    "he": "male",
    "him": "male",
    "himself": "male",
    "his": "male",
    "she": "female",
    "her": "female",
    "hers": "female",
    "herself": "female"
}

def get_antecedent_and_pronoun(annots):
    """
    Get antecedent and pronoun from bracketed fields.
    """
    # Sanity checks
    assert len(annots) > 1

    # Make sure the first annotated field is not a pronun
    assert annots[0] not in PN_TO_GENDER

    # Assert that all other fields are pronouns that agree on gender
    pns_gender = [PN_TO_GENDER[annot]
                  for annot in annots[1:]]
    assert(len(set(pns_gender)) == 1)

    return annots[0], annots[1]

def convert_instance(inst: str):
    """
    Convert a single instance.
    """
    logging.debug(inst)

    # Parse
    bracketed_fields = list(re.finditer(r"\[(.+?)\]", inst))
    fields_str = [m.string[m.start() + 1: m.end() - 1] for m in bracketed_fields]
    occupation, pronoun = get_antecedent_and_pronoun(fields_str)
    pronoun = pronoun.lower()

    # Construct a unified format instance
    gender = PN_TO_GENDER[pronoun]
    occupation_word_index = inst[ : bracketed_fields[0].start()].count(" ")

    # Strip determiner
    if fields_str[0].split(" ")[0].lower() in ["the", "a", "an"]:
        occupation_word_index += 1

    # Create a raw sentence and return
    raw_inst = inst.replace("[", "").replace("]", "")

    return f"{gender}\t{occupation_word_index}\t{raw_inst}\t{occupation}"

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

    logging.info(f"Writing converted output to {out_fn}")
    with open(out_fn, "w") as fout:
        for line in tqdm(open(inp_fn)):
            converted_inst = convert_instance(line.strip().split(" ", 1)[1])
            fout.write(f"{converted_inst}\n")

    logging.info("DONE")
