""" Usage:
    <file-name> --in=INPUT_FILE [--out=OUTPUT_FILE] [--debug]

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
import plotly.graph_objects as go
from plotly.graph_objects import Layout
import pandas as pd
from collections import defaultdict

# Local imports
from compute_corpus_level_stats import MT_COL, METRICS
#----




if __name__ == "__main__":

    # Parse command line arguments
    args = docopt(__doc__)
    inp_fns = [Path(corpus_fn) for corpus_fn in args["--in"].split(",")]
    out_fn = Path(args["--out"])

    # Determine logging level
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    logging.info(f"Input files: {inp_fns}, Output file: {out_fn}.")

    # Start computation
    # dictionary from corpus name to its stats
    corpora = [inp_fn.parts[-2] for inp_fn in inp_fns]
    df_dic = dict([(corpus, pd.read_csv(inp_fn))
                   for corpus, inp_fn in zip(corpora, inp_fns)])

    df_dic = defaultdict(dict)
    models = set()
    for inp_fn in inp_fns:
        df = pd.read_csv(inp_fn)
        corpus = inp_fn.parts[-2]
        for _, line in df.iterrows():
            model = line[MT_COL]
            models.add(model)
            df_dic[corpus][model] = dict([(metric, line[metric]) for metric in METRICS])


    layout = Layout(
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis = {
            "zeroline": True,
            "zerolinecolor": "black",
            "tickfont": dict(size=25)

        },
        font=dict(
            family="Courier New, monospace",
            size=30,
            
        )
    )
    
    for metric in METRICS:
        data = [go.Bar(name = model, x = corpora,
                       y = [df_dic[corpus][model][metric]
                            for corpus in corpora])
            for model in models]
        
        fig = go.Figure(data = data,
                        layout = layout)
        fig.update_layout(barmode = "group")
        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(
                size=23,
            ),

        ))
        cur_fn = str(out_fn / f"{metric}.png")
        fig.write_image(cur_fn)
        logging.info(f"Wrote to {cur_fn}")

    # End
    logging.info("DONE")
