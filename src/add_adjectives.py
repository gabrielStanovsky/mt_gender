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

# Local imports

#=-----

MALE_ADJECTIVE = "handsome"
FEMALE_ADJECTIVE = "pretty"

ADJECTIVES = {
    "male": "handsome",
    "female": "pretty"
}

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

    with open(out_fn, "w", encoding = "utf8") as fout:
        for line in open(inp_fn, encoding = "utf8"):
            gender, word_ind, sentence, entity = line.strip().split("\t")
            sentence = sentence.split(" ")
            word_ind = int(word_ind)
            if gender in ADJECTIVES:
                adjective = ADJECTIVES[gender]
                mod_sent = " ".join(sentence[: word_ind] + [adjective] + sentence[word_ind : ])

            else:
                mod_sent = " ".join(sentence)

            fout.write("\t".join([gender, str(word_ind + 1), mod_sent, entity]) + "\n")

    logging.info("DONE")
