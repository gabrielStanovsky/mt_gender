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
import boto3
import html

# Local imports

#=-----

AWS_TRANSLATE_CLIENT = boto3.client(service_name='translate', use_ssl=True)

def aws_translate(sents, target_language, source_language):
    """
    Run google translate on a batch of sentences.
    """
    trans = []
    for sent in sents:
        cur_trans = {}
        cur_result = AWS_TRANSLATE_CLIENT.translate_text(Text = sent,
                                                         SourceLanguageCode = source_language,
                                                         TargetLanguageCode = target_language)
        cur_trans["translatedText"] = html.unescape(cur_result["TranslatedText"])
        cur_trans["input"] = sent
        trans.append(cur_trans)
    return trans
