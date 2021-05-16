""" Usage:
    <file-name> [--in=INPUT_FILE] [--out=OUTPUT_FILE] [--debug]

Options:
  --help                           Show this message and exit
  -i INPUT_FILE --in=INPUT_FILE    Input file
                                   [default: infile.tmp]
  -o INPUT_FILE --out=OUTPUT_FILE  Input file
                                   [default: outfile.tmp]
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
import numpy as np
import json
import pandas as pd

# Local imports


#----


    

if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    inp_fn = Path(args["--in"])
    out_fn = Path(args["--out"])

    # Determine logging level
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    logging.info(f"Input file: {inp_fn}, Output file: {out_fn}.")

    # Start computation
    df = pd.read_csv(inp_fn)

    # with open(out_fn, "w", encoding = "utf8") as fout:
    #     for row_index, row in tqdm(df.iterrows()):
    #         doc_name = f"{GENRE}/{top_doc_name}/{row_index}"
    #         conll = convert_row_to_conll(row, doc_name)
    #         fout.write(f"{conll}\n")
    
    # End
    logging.info("DONE")
