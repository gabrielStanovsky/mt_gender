""" Usage:
    <file-name> --wmt=WMT_ROOT --en=EN_FILE --prefix=PREFIX --out=OUTPUT_FILE [--debug]

Convert all WMT files which match a given prefix to WinoMT format. written in the output path.

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
from glob import glob
import os

# Local imports


#----


def get_system_name(fn, prefix):
    """
    Extract an mt system's name from the given file name.
    """
    sys_name = ".".join(tail[len(prefix):].split(".")[:-1])
    return sys_name

if __name__ == "__main__":

    # Parse command line arguments
    args = docopt(__doc__)
    wmt_folder = Path(args["--wmt"])
    en_fn = Path(args["--en"])
    prefix = args["--prefix"]
    out_folder = Path(args["--out"])

    # Determine logging level
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    langs = prefix.split(".")[-2]
    logging.info(f"Langs = {langs}")

    # parse English data
    src_sents = [line.split("\t")[2] for line in open(en_fn, encoding = "utf8")]
    num_src_sents = len(src_sents)

    # start computation
    fns = glob(f"{wmt_folder}/{prefix}*")
    for fn in fns:
        # read target sentences
        tgt_sents = [line.strip() for line in open(fn, encoding = "utf8")]
        num_of_tgt_sents = len(tgt_sents)
        if num_of_tgt_sents != num_src_sents:
            logging.info(f"Skipping {fn}: Number of sentences do not match ({num_of_tgt_sents})")

        # construct path
        _, tail = os.path.split(fn)
        sys_name = get_system_name(tail, prefix)
        sys_folder = f"{out_folder}/{sys_name}"
        logging.info(f"Creating folder: {sys_folder}")
        Path.mkdir(Path(sys_folder), parents = False, exist_ok = True)

        # write output file
        wmt_fn = f"{sys_folder}/{langs}.txt"
        logging.info(f"Writing to {wmt_fn}")
        with open(wmt_fn, "w", encoding = "utf8") as fout:
            for src, tgt in zip(src_sents, tgt_sents):
                fout.write(f"{src} ||| {tgt}\n")

    # End
    logging.info("DONE")
