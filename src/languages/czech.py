""" Usage:
    <file-name> --in=IN_FILE --out=OUT_FILE [--debug]
"""
# External imports
import logging
import pdb
from docopt import docopt
from collections import Counter
from ufal.morphodita import *

# Local imports
from languages.util import GENDER, get_gender_from_token
#=-----

class CzechPredictor:
    """
    Class for Czech language.
    """
    def __init__(self):
        self.cache = {}    # Store calculated professions genders
        self.tagger = Tagger.load('../czech-morfflex-pdt-161115/czech-morfflex-pdt-161115.tagger')

        self.tokenizer = self.tagger.newTokenizer()
        self.forms = Forms()
        self.lemmas = TaggedLemmas()
        self.tokens = TokenRanges()
    
    def get_gender(self, profession: str, translated_sent = None, entity_index = None, ds_entry = None) -> GENDER:
        """
        Predict gender of an input profession.
        """
        if profession not in self.cache:
            self.cache[profession] = self._get_gender(profession, translated_sent, entity_index, ds_entry)

        return self.cache[profession]

    def _get_gender(self, profession: str, translated_sent = None, entity_index = None, ds_entry = None) -> GENDER:
        """
        Predict gender, without using cache
        """
        if not profession.strip():
            # Empty string
            return GENDER.unknown

        text = translated_sent
        self.tokenizer.setText(text)
        self.tokenizer.nextSentence(self.forms, self.tokens)
        self.tagger.tag(self.forms, self.lemmas)

        observed_genders = []

        inanimate_masculine = False
        for i in range(len(self.lemmas)):
            tag = self.lemmas[i].tag # this has a form NNFS1-----A---- where third letter specifies gender
            gender = tag[2]
            token = self.tokens[i]
            
            substring = text[token.start : token.start + token.length]
            if substring not in profession or len(substring) < 4:
                # morphodita makes its tokenization ... thus skip most tokens in sentence and look only for profession
                continue

            if tag[0] != 'N' or tag[1] != 'N':
                continue

            if gender == "M":
                observed_genders.append(GENDER.male)
            elif gender == "F":
                observed_genders.append(GENDER.female)
            elif gender == "N":
                observed_genders.append(GENDER.neutral) # child etc
            elif gender == "I":
                # in few cases the profession can have assigned "I" for inanimate
                inanimate_masculine = True 
            else:
                print("unknown gender: {} - {} {}".format(profession, tag, self.lemmas[i].lemma))
                # TODO tag "I" could be used for masculine professions, but its not common (more likely it shows some problems)
        # F   Feminine
        # H   {F, N} - Feminine or Neuter
        # I   Masculine inanimate
        # M   Masculine animate
        # N   Neuter
        # Q   Feminine (with singular only) or Neuter (with plural only); used only with participles and nominal forms of adjectives
        # T   Masculine inanimate or Feminine (plural only); used only with participles and nominal forms of adjectives
        # X   Any
        # Y   {M, I} - Masculine (either animate or inanimate)
        # Z   {M, I, N} - Not fenimine (i.e., Masculine animate/inanimate or Neuter); only for (some) pronoun forms and certain numerals

        if not observed_genders:
            # No observed gendered words - return neutral
            if inanimate_masculine:
                return GENDER.male
            else:
                return GENDER.unknown

        # Return the most commonly observed gender
        return Counter(observed_genders).most_common()[0][0]
        

if __name__ == "__main__":
    # Parse command line arguments
    args = docopt(__doc__)
    inp_fn = args["--in"]
    out_fn = args["--out"]
    debug = args["--debug"]
    if debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    logging.info("DONE")
