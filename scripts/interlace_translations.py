""" Usage:
    <file-name> --orig=ORIG_FILE --trans=TRANS_FILE --out=OUTPUT_FILE [--debug]
"""
# External imports
import logging
from pprint import pprint
from pprint import pformat
from docopt import docopt

# Local imports

#=-----

if __name__ == "__main__":

    # Parse command line arguments
    args = docopt(__doc__)
    orig_fn = args["--orig"]
    trans_fn = args["--trans"]
    out_fn = args["--out"]
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    orig_lines = [line.strip().split("\t")[2] for line in open(orig_fn, encoding = "utf8")]
    trans_lines = [line.strip() for line in open(trans_fn, encoding = "utf8")]

    assert(len(orig_lines) == len(trans_lines))

    with open(out_fn, "w", encoding = "utf8") as fout:
        fout.write("\n".join([f"{orig_line} ||| {trans_line}"
                              for orig_line, trans_line in zip(orig_lines, trans_lines)]))

    logging.info("DONE")
