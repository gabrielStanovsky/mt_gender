""" Usage:
    <file-name> --in=IN_FILE --src=SOURCE_LANGUAGE --tgt=TARGET_LANGUAGE --out=OUT_FILE [--debug]
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
import os, requests, uuid, json
import html

# Local imports

#=-----

BATCH_SIZE = 10

def bing_translate(sents, target_language, source_language = None):
    """
    Run bing translate on a batch of sentences.
    """
    # Checks to see if the Translator Text subscription key is available as an environment variable.
    if 'BING_TRANSLATOR_TEXT_KEY' in os.environ:
        subscriptionKey = os.environ['BING_TRANSLATOR_TEXT_KEY']
    else:
        logging.error('Environment variable for BING_TRANSLATOR_TEXT_KEY is not set.')
        raise ValueError

    # If you encounter any issues with the base_url or path, make sure
    # that you are using the latest endpoint: https://docs.microsoft.com/azure/cognitive-services/translator/reference/v3-0-translate
    base_url = "https://api.cognitive.microsofttranslator.com"
    path = "/translate?api-version=3.0"
    params = f"&to={target_language}"
    constructed_url = base_url + path + params

    headers = {
        'Ocp-Apim-Subscription-Key': subscriptionKey,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }
    trans = []


    # You can pass more than one object in body.
    body = [{'text' : sent} for sent in sents]
    request = requests.post(constructed_url, headers=headers, json=body)
    response = request.json()

    if (len(response) != len(sents)):
        pdb.set_trace()
        raise AssertionError

    trans = []
    for (cur_resp, sent) in zip(response, sents):
        cur_trans = cur_resp["translations"]
        if len(cur_trans) != 1:
            pdb.set_trace()
            raise AssertionError
        cur_trans = cur_trans[0]
        trans.append({"translatedText": cur_trans["text"],
                      "input": sent})
    return trans

def chunks(l, n):
    """
    Yield successive n-sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield l[i:i + n]

def batch_translate(lines, tgt_lang, src_lang = None):
    """
    Translate a list of sentences.
    Take care of batching.
    """
    translations_dicts = []
    for chunk in tqdm(list(chunks(lines, BATCH_SIZE)), desc=f"size {BATCH_SIZE} chunks"):
        for out_dict in bing_translate(chunk, tgt_lang, src_lang):
            translations_dicts.append(out_dict)
    return translations_dicts

if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    inp_fn = args["--in"]
    src_lang = args["--src"]
    tgt_lang = args["--tgt"]
    out_fn = args["--out"]
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    lines = [line.strip() for line in open(inp_fn, encoding = "utf8")]
    out_dicts = batch_translate(lines, tgt_lang, src_lang)
    with open(out_fn, "w", encoding = "utf8") as fout:
        for out_dict in out_dicts:
            fout.write("{} ||| {}\n".format(out_dict["input"],
                                            out_dict["translatedText"]))

    logging.info("DONE")
