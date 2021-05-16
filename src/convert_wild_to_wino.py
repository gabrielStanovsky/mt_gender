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


def convert_df_to_wino(df):
    """
    convert a dataframe to winomt format
    """
    wino_format = []
    for row_index, row in tqdm(df.iterrows()):
        gender = row["predicted gender"].lower()
        entity_ind = row["profession_first_index"]
        entity = row["profession"].lower()
        sent = row["sentence_text"]
        sent_split = sent.split(" ")
        if sent_split[entity_ind].lower() != entity:
            continue
        wino_format.append("\t".join(map(str,
                                         [gender, entity_ind, sent, entity])))
    return wino_format
        

if __name__ == "__main__":

    # Parse command line arguments
    args = docopt(__doc__)
    inp_fn = Path(args["--in"])
    out_fn = args["--out"]

    # Determine logging level
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    logging.info(f"Input file: {inp_fn}, Output file: {out_fn}.")

    # Start computation
    df = pd.read_csv(inp_fn)
    pdb.set_trace()
    ste_df = df[df["stereotype"] == 1]
    ant_df = df[df["stereotype"] == -1]
    df_wino = convert_df_to_wino(df)
    ste_wino = convert_df_to_wino(ste_df)
    ant_wino = convert_df_to_wino(ant_df)

    wino_fns = [(f"{out_fn}/en.txt", df_wino),
                (f"{out_fn}/en_pro.txt", ste_wino),
                (f"{out_fn}/en_anti.txt", ant_wino)]

    for cur_fn, cur_wino in wino_fns:
        cur_ln = len(cur_wino)
        logging.info(f"writing {cur_ln} lines to {cur_fn}")
        with open(cur_fn, "w", encoding = "utf8") as fout:
            fout.write("\n".join(cur_wino))

                           
    
    
    

    
    # End
    logging.info("DONE")
