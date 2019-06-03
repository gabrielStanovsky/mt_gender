""" Usage:
    <file-name> --gold=GOLD_FILE --pred=PRED_FILE [--debug]
"""
# External imports
import logging
import pdb
import csv
from pprint import pprint
from pprint import pformat
from docopt import docopt
from collections import defaultdict
from operator import itemgetter
from tqdm import tqdm

# Local imports

#=-----

if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    gold_fn = args["--gold"]
    pred_fn = args["--pred"]
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    gold_rows = [row for row
                 in csv.reader(open(gold_fn, encoding = "utf8"), delimiter=",")][1:]
    pred_rows = [row for row
                 in csv.reader(open(pred_fn, encoding = "utf8"), delimiter=",")][1:]

    indices = map(int, map(itemgetter(0), gold_rows))

    total = 0
    correct = 0

    for (sent_ind, gold_row) in zip(indices, gold_rows):
        pred_row = pred_rows[sent_ind]
        _, entity, gold_sent, valid_flag, gold_gender = gold_row[:5]
        pred_sent, pred_gender = pred_row
        if gold_sent != pred_sent:
            raise AssertionError(f"Mismatch:\n {gold_sent} \n {pred_sent}")
        gold_gender = gold_gender.strip().lower()
        if (gold_gender not in ["m", "f", "n"]) or (valid_flag.lower == "n"):
            logging.warning(f"Missing gold annotation: {gold_row}")
            continue

        total += 1
        if pred_gender[0] == gold_gender:
            correct += 1
        else:
            logging.debug(
                f"""
                Wrong gender prediction:
                GOLD: {gold_row}
                PRED: {pred_row}
                """)

    percent_correct = round(correct / total, 2)
    logging.info(f"%correct = {percent_correct}")

    logging.info("DONE")
