""" Usage:
    <file-name> --bi=IN_FILE --align=ALIGN_FILE [--debug]
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

# Local imports

#=-----

if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    bi_fn = args["--bi"]
    align_fn = args["--align"]
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    bitext = [[sent.split() for sent in line.split(" ||| ")]
              for line in open(bi_fn, encoding = "utf8")]
    alignments = []
    for line in open(align_fn):
        cur_align = defaultdict(list)
        for word in line.split():
            src, tgt = word.split("-")
            cur_align[int(src)].append(int(tgt))
        alignments.append(cur_align)

    assert(len(bitext) == len(alignments))

    fold = []
    for (src_sent, tgt_sent), alignment in tqdm(zip(bitext, alignments)):
        cur_fold = []
        for word_ind, src_word in enumerate(src_sent):
            cur_align = " ".join([tgt_sent[cur_tgt_ind]
                                  for cur_tgt_ind in alignment[word_ind]])
            cur_fold.append((src_word, cur_align))
        fold.append(cur_fold)

    logging.info("DONE")
