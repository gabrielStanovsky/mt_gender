""" Usage:
    <file-name> [--in=INPUT_FILE] [--out=OUTPUT_FILE] --batch=BATCH_SIZE --device=DEVICE_ID [--debug]

Options:
  --help                           Show this message and exit
  -i INPUT_FILE --in=INPUT_FILE    Input file
                                   [default: infile.tmp]
  -o INPUT_FILE --out=OUTPUT_FILE  Input file
                                   [default: outfile.tmp]
  -d DEVICE_ID --device=DEVICE_ID  device id
                                   [default: -1]

  -b BATCH_SIZE --batch=BATCH_SIZE batch size
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
import pandas as pd
import json
from allennlp.predictors.predictor import Predictor


# Local imports


#----

def chunks(l, n):
    """
    Yield successive n-sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield l[i:i + n]

def create_instance(row):
    """
    Convert a sentence into a list of instances.
    """
    # Create instances
    instance = {"document": row["sentence_text"]}

    return instance


if __name__ == "__main__":

    # Parse command line arguments
    args = docopt(__doc__)
    inp_fn = Path(args["--in"])
    out_fn = Path(args["--out"])
    batch_size = int(args["--batch"])
    cuda_device = int(args["--device"])

    # Determine logging level
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    logging.info(f"Input file: {inp_fn}, Output file: {out_fn}.")

    # Start computation
    model_url = 'https://storage.googleapis.com/allennlp-public-models/coref-spanbert-large-2020.02.27.tar.gz'
    predictor = Predictor.from_path(model_url)  # load the model

    # Move model to gpu, if requested
    if cuda_device >= 0:
        model._model.cuda(cuda_device)

    df = pd.read_csv(inp_fn)
    lines = [row for _, row in df.iterrows()]
    num_lines = len(lines)
    with open(out_fn, "w", encoding = "utf8") as fout:
        for chunk in tqdm(chunks(lines, batch_size), total = num_lines / batch_size):
            instances = [create_instance(row) for row in chunk]
            preds = predictor.predict_batch_json(instances)
            for row, pred in zip(chunk, preds):
                cur_json = {"row": json.loads(row.to_json()),
                            "pred": pred}
                json_str = json.dumps(cur_json)
                fout.write(f"{json_str}\n")


    logging.info(f"wrote {num_lines} to {out_fn}")
    
    # End
    logging.info("DONE")
