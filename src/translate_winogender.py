""" Usage:
    <file-name> --in=IN_FILE --langs=LANGUAGES --out=OUT_FILE [--debug]
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
from google_translate import google_translate
#=-----

if __name__ == "__main__":

    # Parse command line arguments
    args = docopt(__doc__)
    inp_fn = args["--in"]
    langs = args["--langs"].split(",")
    out_fn = args["--out"]
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    logging.info(f"Writing output to {out_fn}")
    with open(out_fn, "w",  encoding = "utf8") as fout:
        fout.write("\t".join(["sentid", "sentence"] + langs) + "\n")
        lines = [line.strip() for line in open(inp_fn, encoding = "utf8")]
        for line in tqdm(lines[1:]):
            sentid, sent = line.strip().split("\t")
            trans = [google_translate([sent], "en", target_lang)[0]["translatedText"]
                     for target_lang in langs]
            fout.write("\t".join([sentid, sent] + trans) + "\n")

    logging.info("DONE")
