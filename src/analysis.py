""" Usage:
    <file-name> --in=IN_FILE --out=OUT_FILE [--debug]
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

def get_predicted_gender(spanish_sent):
    """
    Return the gender of the first entity in the spanish
    translation.
    """
    first_word = spanish_sent.split()[0].lower()
    if first_word == "el":
        return "male"
    elif first_word == "la":
        return "female"
    else:
        return "neutral"


def percentage(part, total):
    """
    Calculate percentage.
    """
    return (part / total) * 100

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

    prof_dict = defaultdict(list)
    conf_dict = defaultdict(lambda: defaultdict(lambda: 0))
    total = defaultdict(lambda: 0)
    pred_cnt = defaultdict(lambda: 0)
    correct_cnt = defaultdict(lambda: 0)
    lines =  [line for line in open(inp_fn, encoding = "utf8")][1:]

    with open(out_fn, "w", encoding = "utf8") as fout:
        for line in lines:
            logging.debug(line)
            sent_id, en_sent, es_sent = line.strip().split("\t")
            profession, _, _, gold_gender, _ = sent_id.split(".")
            fout.write(f"{en_sent} ||| {es_sent}\n")
            if ".0." not in line:
                continue

            total[gold_gender] += 1

            pred_gender = get_predicted_gender(es_sent)
            if pred_gender == gold_gender:
                correct_cnt[gold_gender] += 1

            pred_cnt[pred_gender] += 1

            prof_dict[profession].append((pred_gender, gold_gender))
            conf_dict[gold_gender][pred_gender] += 1

    prof_dict = dict(prof_dict)
    all_total = sum(total.values())
    acc = round((sum(correct_cnt.values()) / all_total) * 100, 2)
    acc_male = round((correct_cnt["male"] / total["male"]) * 100, 2)
    acc_female = round((correct_cnt["female"] / total["female"]) * 100, 2)

    print(f"#total = {all_total}; \n acc = {acc}%; acc_male = {acc_male}; acc_female = {acc_female}")
    print("Gold distribution: male: {}, female: {}, neutral: {}".format(round(percentage(total["male"], all_total), 2),
                                                                        round(percentage(total["female"], all_total),2),
                                                                        round(percentage(total["neutral"], all_total)),2))
    print("Predictions: male: {}, female: {}, neutral: {}".format(round((pred_cnt["male"] / all_total) * 100, 2),
                                                                  round((pred_cnt["female"] / all_total) * 100, 2),
                                                                  round((pred_cnt["neutral"] / all_total) * 100, 2)))


    male_prof = [prof for prof, vals in prof_dict.items()
                 if all(pred_gender == "male"
                        for pred_gender
                        in map(itemgetter(0), vals))]

    female_prof = [prof for prof, vals in prof_dict.items()
                   if all(pred_gender == "female"
                          for pred_gender
                          in map(itemgetter(0), vals))]

    neutral_prof = [prof for prof, vals in prof_dict.items()
                    if all(pred_gender == "neutral"
                           for pred_gender
                           in map(itemgetter(0), vals))]

    amb_prof = [prof for prof, vals in prof_dict.items()
                if len(set(map(itemgetter(0), vals))) != 1]



    print(f"male professions = {male_prof}")
    print(f"female professions = {female_prof}")
    print(f"neutral professions = {neutral_prof}")
    print(f"ambiguous professions = {amb_prof}")


    pprint(conf_dict)

    logging.info("DONE")
