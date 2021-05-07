""" Usage:
    <file-name> --a1=ANNOTATOR1 --a2=ANNOTATOR2 [--debug]

Options:
  --help                           Show this message and exit
  -a1 ANNOTATOR1 --a1=ANNOTATOR1   prefix for annotator 1 annotations and labels
  -a2 ANNOTATOR2 --a2=ANNOTATOR1   prefix for annotator 2 annotations and labels
  --debug                          Whether to debug
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
from sklearn.metrics import cohen_kappa_score
import pandas as pd


# Local imports


#----

if __name__ == "__main__":

    # Parse command line arguments
    args = docopt(__doc__)
    a1_fn = Path(args["--a1"])
    a2_fn = Path(args["--a2"])

    # Determine logging level
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)


    # Start computation
    a1_annots = pd.read_csv(a1_fn, sep="\t")["validation"]
    a2_annots = pd.read_csv(a2_fn, sep="\t")["validation"]
    kappa = cohen_kappa_score(a1_annots, a2_annots)
    logging.info("kappa = {:.2f}".format(kappa))
    

    
    # End
    logging.info("DONE")
