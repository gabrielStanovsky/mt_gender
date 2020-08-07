from mosestokenizer import *
import sys

# this is a helper script for tokenization of parallel testset in format "english sentence ||| other language sentence"


if len(sys.argv) != 3:
    print("COMMAND: tokenize.py input_file second_language")


input_file = sys.argv[1]
second_language = sys.argv[2]

en_tokenize = MosesTokenizer('en')

assert second_language in ['es', 'fr', 'it', 'ru', 'de', 'pl', 'cs', 'uk', 'he', 'ar']

second_tokenize = MosesTokenizer(second_language)

with open(input_file) as fh:
    for line in fh:
        text = line.rstrip().split(' ||| ')

        assert len(text) == 2, "Check if translated file is properly separated by ` ||| `"

        text[0] = ' '.join(en_tokenize(text[0]))
        text[1] = ' '.join(second_tokenize(text[1]))


        print('{} ||| {}'.format(text[0], text[1]))
