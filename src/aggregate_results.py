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
from glob import glob
import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt


# Local imports


#----

if __name__ == "__main__":

    # Parse command line arguments
    args = docopt(__doc__)
    inp_fn = args["--in"]
    out_fn = args["--out"]

    # Determine logging level
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    logging.info(f"Input file: {inp_fn}, Output file: {out_fn}.")

    # Start computation
    subdirs = glob(f"{inp_fn}/*")
    res_dic = defaultdict(lambda: defaultdict(list))
    mts = set()
    xs = []
    
    for subdir in subdirs:
        num_of_prons = int(Path(subdir).stem)
        xs.append(num_of_prons)
        fns = glob(f"{subdir}/*.csv")
        for fn in fns:
            df = pd.read_csv(fn)
            for _, row in df.iterrows():
                mt_sys = row["Translation System"]
                mts.add(mt_sys)
                deltag = row["delta-S"]
                res_dic[num_of_prons][mt_sys].append(deltag)

    # plot
    plt.rcParams.update({'font.size': 17})
    xs = sorted(xs)
    ys = {}
    for mt in mts:
        ys[mt] = [np.average(res_dic[x][mt]) for x in xs]

    
    fig, ax = plt.subplots()

    for mt, ys in ys.items():
        plt.plot(xs, ys,
                 label = mt)
        plt.scatter(xs, ys)



    ax.legend(bbox_to_anchor=(1,0), loc='lower right')
    plt.xlabel('Number of pronouns')
    plt.xticks(xs)
    plt.ylabel("∆ s")
    plt.tight_layout()
    plt.savefig(out_fn)

    

        
    
    # End
    logging.info("DONE")
