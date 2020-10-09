""" Usage:
    <file-name> --in=INPUT_FILE --out=OUTPUT_FILE [--debug]

Create a table format with delta-G and delta-S from an output of several systems.

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
    lines = [line.strip() for line in open(inp_fn, encoding = "utf8")]
    num_of_lines = len(lines)
    line_ind = 0
    system_names = []
    accs = []
    delta_gs = []
    delta_ss = []
    results = []

    while line_ind < num_of_lines:
        system_name = lines[line_ind]
        all_line, pro_line, ant_line = lines[line_ind + 1 : line_ind + 4]
        assert(all_line.startswith("all"))
        assert(pro_line.startswith("pro"))
        assert(ant_line.startswith("ant"))
        line_ind += 4

        # Process dicts
        all_dict = json.loads(all_line.split(";;;")[1])
        pro_dict = json.loads(pro_line.split(";;;")[1])
        ant_dict = json.loads(ant_line.split(";;;")[1])

        # compute aggregates
        acc = round(all_dict["acc"], 1)
        delta_gs = round(all_dict["f1_male"] - all_dict["f1_female"], 1)
        delta_ss = round(pro_dict["acc"] - ant_dict["acc"], 1)
        results.append([system_name, acc, delta_gs, delta_ss])


    df = pd.DataFrame(columns = ["Translation System", "acc", "delta-G", "delta-S"],
                      data = results)
    df.to_csv(out_fn, index = False)
    # End
    logging.info("DONE")
