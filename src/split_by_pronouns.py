""" Usage:
    <file-name> --in=INPUT_FILE --out=OUTPUT_FILE [--debug]



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
import pandas as pd
import numpy as np

# Local imports


#----

if __name__ == "__main__":

    # Parse command line arguments
    args = docopt(__doc__)
    inp_fn = Path(args["--in"]) if args["--in"] else None
    out_fn = args["--out"]

    # Determine logging level
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    # Start computation
    df = pd.read_csv(inp_fn)
    len_df = len(df)
    logging.info(f"loaded {len_df} lines from {inp_fn}")
    num_of_ps = np.array(list(set(df["num_of_pronouns"])))
    num_of_ps = num_of_ps[num_of_ps > 0]

    for i in num_of_ps:
        cur_out_fn = f"{out_fn}/{i}_pronouns.csv"
        cur_df = df[df["num_of_pronouns"] == i]
        len_cur_df = len(cur_df)
        logging.info(f"writing {len_cur_df} lines to {cur_out_fn}")
        cur_df.to_csv(cur_out_fn, index = False)

    # End
    logging.info("DONE")
