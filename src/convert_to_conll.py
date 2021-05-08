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
import matplotlib.pyplot as plt
import json
import pandas as pd

# Local imports


#----


HEADER = "#begin document ({doc_name}); part 000"
FOOTER = "\n#end document"
BOILER = ["-"] * 5 + ["Speaker#1"] + ["*"] * 4
ENTITY = "(1)"

def convert_row_to_conll(row, doc_name):
    """
    get a conll multi-line string representing a csv row
    """
    # find prof_index
    assert row.profession_first_index == row.profession_last_index
    prof_ind = row.profession_first_index

    # find pronoun
    assert row.g_first_index == row.g_last_index
    pron_ind = row.g_first_index

    # construct conll rows
    conll = []
    words = row.sentence_text.split(" ")
    prof = row["profession"].lower()
    pron = row["g"].lower()
    for word_ind, word in enumerate(words):
        word_lower = word.lower()
        coref_flag = "-"
        
        if word_ind == prof_ind:
            assert (word_lower == prof)
            coref_flag = ENTITY

        elif word_ind == pron_ind:
            assert (word_lower == pron)
            coref_flag = ENTITY
                   
        metadata = list(map(str, [doc_name, 0, word_ind, word]))
        conll_row = metadata + BOILER + [coref_flag]
        conll.append("\t".join(conll_row))


    conll_data_str = "\n".join(conll)
    header = HEADER.format(doc_name = doc_name)
    full_conll = "\n".join([header,conll_data_str,FOOTER])
    return full_conll
    

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
    top_doc_name = out_fn.stem

    with open(out_fn, "w", encoding = "utf8") as fout:
        for row_index, row in tqdm(df.iterrows()):
            doc_name = f"{top_doc_name}/{row_index}"
            conll = convert_row_to_conll(row, doc_name)
            fout.write(f"{conll}\n")
    
    # End
    logging.info("DONE")
