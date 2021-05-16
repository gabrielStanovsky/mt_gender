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


# Local imports


#----

def find_cluster_ind(clusters, word_ind):
    """
    find the cluster ind for the given word, or -1 if not found
    """
    found_in_clusters = []
    for cluster_ind, cluster in enumerate(clusters):
        for ent_ind, ent in enumerate(cluster):
            ent_start, ent_end = ent
            if (word_ind >= ent_start) and (word_ind <= ent_end):
                # found a cluster
                found_in_clusters.append(cluster_ind)

    # no cluster found
    return found_in_clusters


def is_correct_pred(line):
    """
    return True iff this line represents a correct prediction.
    """
    pred = line["pred"]
    row = line["row"]
    clusters = pred["clusters"]
    ent_id = find_cluster_ind(clusters, row["profession_first_index"])
    pron_id = find_cluster_ind(clusters, row["g_first_index"])
    
    # prediction is correct if it assigns pronoun and entity to the same cluster
    is_correct = len(set(ent_id).intersection(pron_id))
    
    return is_correct


def get_acc(vals):
    """
    return the accuracy given binary scores
    """
    acc = (sum(vals) / len(vals)) * 100
    return acc

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
    metrics = {"acc": [],
               "ste": [],
               "ant": [],
               "masc": [],
               "femn": []}

    lines = [json.loads(line.strip()) for line in open(inp_fn, encoding = "utf8")]

    for line in tqdm(lines):
        is_correct = is_correct_pred(line)
        row = line["row"]
        metrics["acc"].append(is_correct)
        gender = row["predicted gender"].lower()
        stereotype = row["stereotype"]
        
        if gender == "male":
            metrics["masc"].append(is_correct)
        elif gender == "female":
            metrics["femn"].append(is_correct)

        if stereotype == 1:
            metrics["ste"].append(is_correct)
        elif stereotype == -1:
            metrics["ant"].append(is_correct)
            
        
    acc = get_acc(metrics["acc"])
    delta_g = get_acc(metrics["masc"]) - get_acc(metrics["femn"])
    delta_s = get_acc(metrics["ste"]) - get_acc(metrics["ant"])

    logging.info(f"acc = {acc:.1f}; delta_g = {delta_g:.1f}; delta_s = {delta_s:.1f}")

    
    # End
    logging.info("DONE")
