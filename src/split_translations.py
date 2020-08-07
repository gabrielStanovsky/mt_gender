""" Usage:
    <file-name> --pro=PRO_FILE --ant=ANTI_FILE --trans=TRANSLATIONS_FILE [--debug]

Split translations to anti and pro sterotypical.

"""
# External imports
import logging
import pdb
from pprint import pprint
from pprint import pformat
from docopt import docopt
from pathlib import Path
from tqdm import tqdm
import json

# Local imports


#----

if __name__ == "__main__":

    # Parse command line arguments
    args = docopt(__doc__)
    pro_fn = Path(args["--pro"])
    ant_fn = Path(args["--ant"])
    trans_fn = Path(args["--trans"])

    # Determine logging level
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    # Start computation
    pro_sents = [line.split("\t")[2] for line in open(pro_fn, encoding = "utf8")]
    ant_sents = [line.split("\t")[2] for line in open(ant_fn, encoding = "utf8")]
    trans_lines = [line for line in open(trans_fn, encoding = "utf8")]

    out_pro_fn = str(trans_fn)+".pro"
    out_ant_fn = str(trans_fn)+".ant"
    pro_cnt = 0
    ant_cnt = 0

    with open(out_pro_fn, "w", encoding = "utf8") as f_pro, \
         open(out_ant_fn, "w", encoding = "utf8") as f_ant:
        for trans_line in trans_lines:
            en_sent = trans_line.split(" ||| ")[0]
            if en_sent in ant_sents:
                f_ant.write(trans_line)
                ant_cnt += 1

            if en_sent in pro_sents:
                f_pro.write(trans_line)
                pro_cnt += 1

    logging.info(f"found {pro_cnt} pro sents and {ant_cnt} ant sents")

    # End
    logging.info("DONE")
