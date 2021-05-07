""" Usage:
    <file-name> --in=INPUT_FILE --out=OUTPUT_FILE [--debug]

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
import pandas as pd
import numpy as np
import json
from glob import glob
from collections import defaultdict

# Local imports


#----

MT_COL = "Translation System"
METRICS = ("acc", "delta-G", "delta-S")

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
    fns = glob(str(inp_fn / "*.csv"))
    stats = defaultdict(lambda: defaultdict(list))
    for fn in fns:
        df = pd.read_csv(fn)
        for _, row in df.iterrows():
            cur_mt = row[MT_COL]
            for metric in METRICS:
                stats[cur_mt][metric].append(row[metric])

    out_df = pd.DataFrame(columns = [MT_COL] + list(METRICS), index = range(len(stats)))

    for mt_index, (mt_system, mt_stats) in enumerate(stats.items()):
        avgs = dict([(metric, np.average(vals)) 
                     for metric, vals in mt_stats.items()])
        avgs[MT_COL] = mt_system
        out_df.loc[mt_index] = pd.Series(avgs)

    logging.info(f"Writing output to {out_fn}")
    out_df.to_csv(out_fn, index = False)
            
    
    # End
    logging.info("DONE")
