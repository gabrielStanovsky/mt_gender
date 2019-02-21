""" Usage:
    <file-name> --ds=DATASET_FILE --bi=BI_FILE --seed=SEED_FILE --out=OUT_FILE [--debug]
"""
# External imports
import logging
import pdb
from pprint import pprint
from pprint import pformat
from docopt import docopt
from collections import defaultdict
from operator import itemgetter
from tqdm import tqdm
import csv
# Local imports

#=-----

if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    ds_fn = args["--ds"]
    bi_fn = args["--bi"]
    seed_fn = args["--seed"]
    out_fn = args["--out"]
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    ds = [line.strip().split("\t") for line in open(ds_fn, encoding = "utf8")]
    bitext = [line.strip().split(" ||| ")
              for line in open(bi_fn, encoding = "utf8")]

    bitext_src_sents, bitext_tgt_sents = zip(*bitext)
    gold_annots, _, ds_src_sents, ds_entities = zip(*ds)

    # Sanity check
    mismatched = [ind for (ind, (ds_src_sent, bitext_src_sent)) in enumerate(zip(ds_src_sents, bitext_src_sents))
                  if ds_src_sent != bitext_src_sent]
    if len(mismatched) != 0:
        raise AssertionError

    indices = map(int, open(seed_fn).read().split(","))
    instances = list(zip(ds_entities, bitext_tgt_sents))

    with open(out_fn, "w", encoding = "utf8") as fout:
        writer = csv.writer(fout, delimiter=",")
        writer.writerow(["Entity", "Sentence", "Find entity? [Y/N]", "Gender? [M/F/N]"])
        for inst_ind in indices:
            writer.writerow(list(instances[inst_ind]) + ["", ""])

    # TODO: write predicted gender for these instances

    logging.info("DONE")
