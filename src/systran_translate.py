""" Usage:
    <file-name> --in=IN_FILE --src=SOURCE_LANGUAGE --tgt=TARGET_LANGUAGE --out=OUT_FILE [--debug]
"""
import sys
reload(sys)  # Reload does the trick!
sys.setdefaultencoding('UTF8')

# External imports
import logging
import pdb
from pprint import pprint
from pprint import pformat
from docopt import docopt
from collections import defaultdict
from operator import itemgetter
from tqdm import tqdm

import systran_translation_api
import systran_translation_api.configuration


BATCH_SIZE = 50 # Up to 128 should be fine?

def chunks(l, n):
    """
    Yield successive n-sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield l[i:i + n]

def batch_translate(trans_function, lines, tgt_lang, src_lang = None):
    """
    Translate a list of sentences.
    Take care of batching.
    """
    translations_dicts = []
    for chunk in tqdm(list(chunks(lines, BATCH_SIZE))):
        for out_dict in trans_function(chunk, tgt_lang, src_lang):
            translations_dicts.append(out_dict)
    return translations_dicts

class Systran:
    """
    Systran wrapper.
    """
    def __init__(self, api_key_file):
        """
        Init systran's API
        """
        systran_translation_api.configuration.load_api_key(api_key_file)
        self.api_client = systran_translation_api.ApiClient()
        self.translation_api = systran_translation_api.TranslationApi(self.api_client)

    def translate(self, sents, tgt_lang, src_lang):
        """
        Translate a batch of sentences.
        """
        trans_result = self.translation_api.translation_text_translate_get(source = src_lang,
                                                                           target = tgt_lang,
                                                                           input = sents)

        translated_sents = [cur_output.output
                            for cur_output in trans_result.outputs]
        return translated_sents

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


    lines = [line.strip() for line in open(inp_fn)]
    systran = Systran("api_key.txt")
    translated_sents = batch_translate(systran.translate, lines, tgt_lang, src_lang)
    if len(lines) != len(translated_sents):
        pdb.set_trace()
        raise AssertionError

    with open(out_fn, "w") as fout:
        for orig_sent, translated_sent in zip(lines, translated_sents):
            fout.write("{} ||| {}\n".format(orig_sent,
                                            translated_sent))

    logging.info("DONE")
