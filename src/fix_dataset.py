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
import string

# Local imports

#=-----

PUNCT = '!,.;?'

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

    translator = str.maketrans(PUNCT,
                               ' '*len(PUNCT)) #map punctuation to space

    lines = [line.strip().split("\t")
             for line in open(inp_fn, encoding = "utf8")][1:]

    with open(out_fn, "w") as fout:
        for (annot, sent) in tqdm(lines):
            prof1, prof2, pointer, gender, _ = annot.split(".")

            if prof2 == "unknown":
                target = prof1
            else:
                target = [prof1, prof2][int(pointer)]

            # Remove "the"
            target_words = target.replace("the_", "").replace("a_", "").replace("an_", "")
            target_words = target_words.lower().split("_")

            if len(target_words) > 1:
                logging.warn(f"Multi-word profession: {target}")

            target_word = target_words[0]
            words = [word.lower() for word in sent.translate(translator).split(" ")]

            # Sanity checks
            target_word_indices = [word_ind for word_ind, sent_word in enumerate(words)
                                   if sent_word == target_word]

            if len(target_word_indices) != 1:
                raise AssertionError

            # Write output line (gender, target word index, sentence)
            out_line = "\t".join([gender, str(target_word_indices[0]), sent, target])
            fout.write(f"{out_line}\n")

    logging.info("DONE")
