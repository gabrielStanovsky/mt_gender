""" Usage:
    <file-name> --in=IN_FILE --out=OUT_FILE [--debug]
"""
# External imports
import logging
import pdb
from docopt import docopt
from collections import Counter
from ufal.morphodita import *
import re

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
        # initially try to resolve problem based on exact manual rules
        gender = self._get_gender_manual_rules(profession, translated_sent, entity_index, ds_entry)

        if gender in [GENDER.male, GENDER.male, GENDER.male]:
            return gender

        return self._get_gender_automatically(profession, translated_sent, entity_index, ds_entry)

    def _get_gender_manual_rules(self, profession: str, translated_sent = None, entity_index = None, ds_entry = None) -> GENDER:
        # Rules defined by Tom Kocmi
        expected_english_profession = ds_entry[3].lower().replace("the ","").replace("a ","").replace("an ","")
        expected_gender = ds_entry[0] 

        translated_sent = translated_sent.lower()

        found_gender = GENDER.unknown

        male = expected_english_profession + "-male"
        female = expected_english_profession + "-female"
        
        both_possible = False
        if male in self.variants and female in self.variants:
            for form in self.variants[male]:
                if re.search(form, translated_sent):
                    found_gender = GENDER.male
                    break
    
            for form in self.variants[female]:
                if re.search(form, translated_sent):
                    if found_gender is not GENDER.unknown:
                        found_gender = GENDER.unknown
                        both_possible = True
                        break # the form is equal for both female and male
                    found_gender = GENDER.female
                    # do not break, to check for duplicates

        if found_gender == GENDER.unknown:
            if male not in self.variants or female not in self.variants:
                print((expected_gender, expected_english_profession))
            #print(profession.lower())

            profstr = re.sub(r'\W+', '', expected_english_profession)+","+re.sub(r'\W+', '',profession.lower()) +"," + expected_gender
            if not both_possible and profstr not in self.find and expected_gender != "neutral": #and expected_english_profession + "-" + expected_gender not in self.variants:
                self.find.append(profstr)
                #print(' '.join(self.find))
            #print(translated_sent)
            #print(ds_entry[2])
            
            #import ipdb
            #ipdb.set_trace()

        return found_gender

    find = []

    def _get_gender_automatically(self, profession: str, translated_sent = None, entity_index = None, ds_entry = None) -> GENDER:
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
        debug_output = "    "
        for i in range(len(self.lemmas)):
            tag = self.lemmas[i].tag # this has a form NNFS1-----A---- where third letter specifies gender
            gender = tag[2]
            token = self.tokens[i]
            
            substring = text[token.start : token.start + token.length]
            debug_output += "{}-{}".format(tag[0:6], substring)

            if substring not in profession:
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
                #print("{} ....... {}".format(profession, translated_sent))
                #print(debug_output)
                return GENDER.unknown

        # Return the most commonly observed gender
        return Counter(observed_genders).most_common()[0][0]

    variants = {
                'accountant-female': ["účetní"],
                'accountant-male': ["účetní", "účetního", "účetním", "účetnímu"],
                'administrator-female': ["správkyně", "správkyni", "správkyní"],
                'administrator-male': ["správce", "správcem", "správci", "správcovi"],
                'analyst-female': ["analytičce", "analytička", "analytičko", "analytičkou", "analytičku", "analytičky"],
                'analyst-male': ["analytik", "analytika", "analytikem", "analytikovi", "analytiku"],
                'appraiser-female': ["odhadkyně", "odhadkyni", "odhadkyní"],
                'appraiser-male': ["odhadce", "odhadcem", "odhadci", "odhadcovi"],
                'assistant-female': ["asistentce", "asistentka", "asistentko", "asistentkou", "asistentku", "asistentky"],
                'assistant-male': ["asistent", "asistenta", "asistente", "asistentem", "asistentovi", "asistentu"],
                'attendant-female': ["obsluha", "obsluho", "obsluhou", "obsluhu", "obsluhy", "obsluze", "účastnice", "účastnici", "účastnicí"],
                'attendant-male': ["obsluha", "obsluho", "obsluhou", "obsluhu", "obsluhy", "obsluze", "účastník", "účastníka", "účastníkem", "účastníkovi", "účastníku"],
                'auditor-female': ["auditorce", "auditorka", "auditorko", "auditorkou", "auditorku", "auditorky", "revisorce", "revisorka", "revisorko", "revisorkou", "revisorku", "revisorky"],
                'auditor-male': ["auditor", "auditora", "auditore", "auditorem", "auditorovi", "auditoru", "revisor", "revisora", "revisore", "revisorem", "revisorovi", "revisoru", "revizor", "revizora", "revizore", "revizorem", "revizorovi", "revizoru"],
                'baker-female': ["pekařce", "pekařka", "pekařko", "pekařkou", "pekařku", "pekařky"],
                'baker-male': ["pekař", "pekaře", "pekařem", "pekaři", "pekařovi"],
                'broker-female': ["makléřce", "makléřka", "makléřko", "makléřkou", "makléřku", "makléřky"],
                'broker-male': ["makléř", "makléře", "makléřem", "makléři", "makléřovi"],
                'bystander-female': ["kolemjdoucí", "kolemjdoucího", "kolemjdoucím", "kolemjdoucímu"],
                'bystander-male': ["kolemjdoucí", "kolemjdoucího", "kolemjdoucím", "kolemjdoucímu"],
                'carpenter-female': ["tesařce", "tesařka", "tesařko", "tesařkou", "tesařku", "tesařky", "truhlářce", "truhlářka", "truhlářko", "truhlářkou", "truhlářku", "truhlářky"],
                'carpenter-male': ["tesař", "tesaře", "tesařem", "tesaři", "tesařovi", "truhlář", "truhláře", "truhlářem", "truhláři", "truhlářovi"],
                'cashier-female': ["pokladní"],
                'cashier-male': ["pokladník", "pokladníka", "pokladníkem", "pokladníkovi", "pokladníku", "pokladní", "pokladního", "pokladním", "pokladnímu"],
                'ceo-female': ["ředitelce", "ředitelka", "ředitelko", "ředitelkou", "ředitelku", "ředitelky"],
                'ceo-male': ["ředitel", "ředitele", "ředitelem", "řediteli", "ředitelovi"],
                'chemist-female': ["chemičce", "chemička", "chemičko", "chemičkou", "chemičku", "chemičky"],
                'chemist-male': ["chemik", "chemika", "chemikem", "chemikovi", "chemiku"],
                'chief-female': ["šéfce", "šéfka", "šéfko", "šéfkou", "šéfku", "šéfky"],
                'chief-male': ["šéf", "šéfa", "šéfe", "šéfem", "šéfovi", "šéfu"],
                'cleaner-female': ["uklízečce", "uklízečka", "uklízečko", "uklízečkou", "uklízečku", "uklízečky"],
                'cleaner-male': ["uklizeč", "uklízeč", "uklizeče", "uklízeče", "uklizečem", "uklízečem", "uklizeči", "uklízeči", "uklizečovi", "uklízečovi"],
                'clerk-female': ["úřednice", "úřednici", "úřednicí", "prodavačce", "prodavačka", "prodavačko", "prodavačkou", "prodavačku", "prodavačky"],
                'clerk-male': ["úředník", "úředníka", "úředníkem", "úředníkovi", "úředníku", "prodavač", "prodavače", "prodavačem", "prodavači", "prodavačovi"],
                'cook-female': ["kuchařce", "kuchařka", "kuchařko", "kuchařkou", "kuchařku", "kuchařky"],
                'cook-male': ["kuchař", "kuchaře", "kuchařem", "kuchaři", "kuchařovi"],
                'construction worker-female': ["dělnice", "dělnici", "dělnicí"],
                'construction worker-male': ["dělník", "dělníka", "dělníkem", "dělníkovi", "dělníku"],
                'counselor-female': ["poradkyně", "poradkyni", "poradkyní"],
                'counselor-male': ["poradce", "poradcem", "poradci", "poradcovi"],
                'customer-female': ["zákaznice", "zákaznici", "zákaznicí"],
                'customer-male': ["zákazník", "zákazníka", "zákazníkem", "zákazníkovi", "zákazníku"],
                'designer-female': ["návrhářce", "návrhářka", "návrhářko", "návrhářkou", "návrhářku", "návrhářky"],
                'designer-male': ["návrhář", "návrháře", "návrhářem", "návrháři", "návrhářovi"],
                'developer-female': ["developerce", "developerka", "developerko", "developerkou", "developerku", "developerky", "vývojářce", "vývojářka", "vývojářko", "vývojářkou", "vývojářku", "vývojářky", "stavitelce", "stavitelka", "stavitelko", "stavitelkou", "stavitelku", "stavitelky"],
                'developer-male': ["developer", "developera", "developere", "developerem", "developerovi", "developeru", "vývojář", "vývojáře", "vývojářem", "vývojáři", "vývojářovi", "stavitel", "stavitele", "stavitelem", "staviteli", "stavitelovi"],
                'dietitian-female': ["dietoložce", "dietoložka", "dietoložko", "dietoložkou", "dietoložku", "dietoložky"],
                'dietitian-male': ["dietolog", "dietologa", "dietologem", "dietologovi", "dietologu"],
                'doctor-male': ["doktor", "doktora", "doktore", "doktorem", "doktorovi", "doktoru", "dra", "drem", "dru"],
                'doctor-female': ["doktorce", "doktorka", "doktorko", "doktorkou", "doktorku", "doktorky"],
                'driver-female': ["řidičce", "řidička", "řidičko", "řidičkou", "řidičku", "řidičky"],
                'driver-male': ["řidič", "řidiče", "řidičem", "řidiči", "řidičovi"],
                'editor-female': ["redaktorce", "redaktorka", "redaktorko", "redaktorkou", "redaktorku", "redaktorky", "šéfredaktorce", "šéfredaktorka", "šéfredaktorko", "šéfredaktorkou", "šéfredaktorku", "šéfredaktorky"],
                'editor-male': ["redaktor", "redaktora", "redaktore", "redaktorem", "redaktorovi", "redaktoru", "šéfredaktor", "šéfredaktora", "šéfredaktore", "šéfredaktorem", "šéfredaktorovi", "šéfredaktoru"],
                'electrician-female': ["elektrikářce", "elektrikářka", "elektrikářko", "elektrikářkou", "elektrikářku", "elektrikářky"],
                'electrician-male': ["elektrikář", "elektrikáře", "elektrikářem", "elektrikáři", "elektrikářovi"],
                'engineer-female': ["inženýrce", "inženýrka", "inženýrko", "inženýrkou", "inženýrku", "inženýrky"],
                'engineer-male': ["inženýr", "inženýra", "inženýre", "inženýrem", "inženýrovi", "inženýru"],
                'farmer-female': ["farmářce", "farmářka", "farmářko", "farmářkou", "farmářku", "farmářky"],
                'farmer-male': ["farmář", "farmáře", "farmářem", "farmáři", "farmářovi", "sedlák", "sedláka", "sedlákem", "sedlákovi", "sedláku"],
                'firefighter-female': ["hasičce", "hasička", "hasičko", "hasičkou", "hasičku", "hasičky"],
                'firefighter-male': ["hasič", "hasiče", "hasičem", "hasiči", "hasičovi"],
                'guard-female': ["strážná", "strážné", "strážnou", "strážný"],
                'guard-male': ["strážného", "strážnej", "strážném", "strážnému", "strážný", "strážnýho", "strážnym", "strážným", "strážnýmu"],
                'hairdresser-female': ["kadeřnice", "kadeřnici", "kadeřnicí"],
                'hairdresser-male': ["kadeřník", "kadeřníka", "kadeřníkem", "kadeřníkovi", "kadeřníku"],
                'housekeeper-female': ["hospodyně", "hospodyni", "hospodyní"],
                'hygienist-female': ["hygienistce", "hygienistka", "hygienistko", "hygienistkou", "hygienistku", "hygienistky", "hygieničce", "hygienička", "hygieničko", "hygieničkou", "hygieničku", "hygieničky"],
                'hygienist-male': ["hygienik", "hygienika", "hygienikem", "hygienikovi", "hygieniku"],
                'instructor-female': ["instruktorce", "instruktorka", "instruktorko", "instruktorkou", "instruktorku", "instruktorky"],
                'instructor-male': ["instruktor", "instruktora", "instruktore", "instruktorem", "instruktorovi", "instruktoru"],
                'investigator-female': ["vyšetřovatelce", "vyšetřovatelka", "vyšetřovatelko", "vyšetřovatelkou", "vyšetřovatelku", "vyšetřovatelky"],
                'investigator-male': ["vyšetřovatel", "vyšetřovatele", "vyšetřovatelem", "vyšetřovateli", "vyšetřovatelovi"],
                'janitor-female': ["uklízečce", "uklízečka", "uklízečko", "uklízečkou", "uklízečku", "uklízečky", "domovnice", "domovnici", "domovnicí", "správkyně", "správkyni", "správkyní", "údržbářce", "údržbářka", "údržbářko", "údržbářkou", "údržbářku", "údržbářky"],
                'janitor-male': ["domovník", "domovníka", "domovníkem", "domovníkovi", "domovníku", "školník", "školníka", "školníkem", "školníkovi", "školníku", "správce", "správcem", "správci", "správcovi", "údržbář", "údržbáře", "údržbářem", "údržbáři", "údržbářovi", "uklizeč", "uklízeč", "uklizeče", "uklízeče", "uklizečem", "uklízečem", "uklizeči", "uklízeči", "uklizečovi", "uklízečovi"],
                'laborer-female': ["dělnice", "dělnici", "dělnicí"],
                'laborer-male': ["dělník", "dělníka", "dělníkem", "dělníkovi", "dělníku"],
                'lawyer-female': ["advokátce", "advokátka", "advokátko", "advokátkou", "advokátku", "advokátky", "právničce", "právnička", "právničko", "právničkou", "právničku", "právničky"],
                'lawyer-male': ["advokát", "advokáta", "advokáte", "advokátem", "advokátovi", "advokátu", "právník", "právníka", "právníkem", "právníkovi", "právníku"],
                'librarian-female': ["knihovnice", "knihovnici", "knihovnicí"],
                'librarian-male': ["knihovník", "knihovníka", "knihovníkem", "knihovníkovi", "knihovníku"],
                'machinist-female': ["strojnice", "strojnici", "strojnicí"],
                'machinist-male': ["strojník", "strojníka", "strojníkem", "strojníkovi", "strojníku"],
                'manager-female': ["vedoucí", "manažerce", "manažerka", "manažerko", "manažerkou", "manažerku", "manažerky", "ředitelce", "ředitelka", "ředitelko", "ředitelkou", "ředitelku", "ředitelky"],
                'manager-male': ["vedoucí", "manager", "managera", "managere", "managerem", "managerovi", "manageru", "manažer", "manažér", "manažera", "manažéra", "manažere", "manažére", "manažerem", "manažérem", "manažerovi", "manažérovi", "manažeru", "manažéru", "ředitel", "ředitele", "ředitelem", "řediteli", "ředitelovi"],
                'mechanic-female': ["mechaničce", "mechanička", "mechaničko", "mechaničkou", "mechaničku", "mechaničky"],
                'mechanic-male': ["mechanik", "mechanika", "mechanikem", "mechanikovi", "mechaniku"],
                'mover-male': ["stěhovák", "stěhováka", "stěhovákem", "stěhovákovi", "stěhováku"],
                'mover-female': ["stěhovatelce", "stěhovatelka", "stěhovatelko", "stěhovatelkou", "stěhovatelku", "stěhovatelky"],
                'nurse-male': ["ošetřovatel", "ošetřovatele", "ošetřovatelem", "ošetřovateli", "ošetřovatelovi"],
                'nurse-female': ["sestra", "sestře", "sestři", "sestro", "sestrou", "sestru", "sestry", "ošetřovatelce", "ošetřovatelka", "ošetřovatelko", "ošetřovatelkou", "ošetřovatelku", "ošetřovatelky"],
                'officer-male': ["důstojník", "důstojníka", "důstojníkem", "důstojníkovi", "důstojníku", "policista", "policisto", "policistou", "policistovi", "policistu", "policisty", "strážník", "strážníka", "strážníkem", "strážníkovi", "strážníku"],
                'officer-female': ["důstojnice", "důstojnici", "důstojnicí", "policistce", "policistka", "policistko", "policistkou", "policistku", "policistky", "strážnice", "strážnici", "strážnicí"],
                'painter-female': ["malířce", "malířka", "malířko", "malířkou", "malířku", "malířky"],
                'painter-male': ["malíř", "malíře", "malířem", "malíři", "malířovi"],
                'paralegal-female': ["koncipientce", "koncipientka", "koncipientko", "koncipientkou", "koncipientku", "koncipientky"],
                'paralegal-male': ["koncipient", "koncipienta", "koncipiente", "koncipientem", "koncipientovi", "koncipientu"],
                'paramedic-male': ["záchranář", "záchranáře", "záchranářem", "záchranáři", "záchranářovi", "zdravotník", "zdravotníka", "zdravotníkem", "zdravotníkovi", "zdravotníku"],
                'paramedic-female': ["zdravotnice", "zdravotnici", "zdravotnicí", "záchranářce", "záchranářka", "záchranářko", "záchranářkou", "záchranářku", "záchranářky"],
                'pathologist-female': ["patoložce", "patoložka", "patoložko", "patoložkou", "patoložku", "patoložky"],
                'pathologist-male': ["patolog", "patologa", "patologem", "patologovi", "patologu"],
                'patient-female': ["pacientce", "pacientka", "pacientko", "pacientkou", "pacientku", "pacientky"],
                'patient-male': ["pacient", "pacienta", "paciente", "pacientem", "pacientovi", "pacientu"],
                'pharmacist-male': ["lékárník", "lékárníka", "lékárníkem", "lékárníkovi", "lékárníku"],
                'pharmacist-female': ["lékárnice", "lékárnici", "lékárnicí"],
                'physician-female': ["lékařce", "lékařka", "lékařko", "lékařkou", "lékařku", "lékařky"],
                'physician-male': ["lékař", "lékaře", "lékařem", "lékaři", "lékařovi"],
                'planner-female': ["plánovačce", "plánovačka", "plánovačko", "plánovačkou", "plánovačku", "plánovačky"],
                'planner-male': ["plánovač", "plánovače", "plánovačem", "plánovači", "plánovačovi"],
                'plumber-female': ["instalatérce", "instalatérka", "instalatérko", "instalatérkou", "instalatérku", "instalatérky"],
                'plumber-male': ["instalatér", "instalatéra", "instalatére", "instalatérem", "instalatérovi", "instalatéru"],
                'practitioner-female': ["praktikantce", "praktikantka", "praktikantko", "praktikantkou", "praktikantku", "praktikantky"],
                'practitioner-male': ["praktik", "praktika", "praktikem", "praktikovi", "praktiku"],
                'programmer-female': ["programátorce", "programátorka", "programátorko", "programátorkou", "programátorku", "programátorky"],
                'programmer-male': ["programátor", "programátora", "programátore", "programátorem", "programátorovi", "programátoru"],
                'psychologist-female': ["psycholožce", "psycholožka", "psycholožko", "psycholožkou", "psycholožku", "psycholožky"],
                'psychologist-male': ["psycholog", "psychologa", "psychologem", "psychologovi", "psychologu"],
                'salesperson-female': ["prodavačce", "prodavačka", "prodavačko", "prodavačkou", "prodavačku", "prodavačky"],
                'salesperson-male': ["prodavač", "prodavače", "prodavačem", "prodavači", "prodavačovi", "prodejce", "prodejcem", "prodejci", "prodejcovi"],
                'secretary-female': ["sekretářce", "sekretářka", "sekretářko", "sekretářkou", "sekretářku", "sekretářky", "tajemnice", "tajemnici", "tajemnicí"],
                'secretary-male': ["tajemník", "tajemníka", "tajemníkem", "tajemníkovi", "tajemníku", "sekretář", "sekretáře", "sekretářem", "sekretáři", "sekretářovi"],
                'sheriff-female': ["šerifce", "šerifka", "šerifko", "šerifkou", "šerifku", "šerifky"],
                'sheriff-male': ["šerif", "šerifa", "šerife", "šerifem", "šerifovi", "šerifu"],
                'student-male': ["student", "študent", "studenta", "študenta", "studente", "študente", "studentem", "študentem", "studentovi", "študentovi", "studentu", "študentu"],
                'student-female': ["studentce", "studentka", "studentko", "studentkou", "studentku", "studentky"],
                'supervisor-female': ["nadřízená", "nadřízené", "nadřízenou", "nadřízený", "vedoucí""dozorkyně", "dozorkyni", "dozorkyní", "školitelce", "školitelka", "školitelko", "školitelkou", "školitelku", "školitelky", "techničce", "technička", "techničko", "techničkou", "techničku", "techničky"],
                'supervisor-male': ["dozorce", "dozorcem", "dozorci", "dozorcovi", "školitel", "školitele", "školitelem", "školiteli", "školitelovi", "nadřízeného", "nadřízenej", "nadřízeném", "nadřízenému", "nadřízený", "nadřízenýho", "nadřízenym", "nadřízeným", "nadřízenýmu", "vedoucí", "vedoucího", "vedoucím", "vedoucímu"],
                'tailor-female': ["krejčová", "krejčové", "krejčovou", "krejčový", "krejčí"],
                'tailor-male': ["krejčí", "krejčího", "krejčím", "krejčímu"],
                'teacher-female': ["učitelce", "učitelka", "učitelko", "učitelkou", "učitelku", "učitelky"],
                'teacher-male': ["učitel", "učitele", "učitelem", "učiteli", "učitelovi"],
                'technician-male': ["technik", "technika", "technikem", "technikovi", "techniku"],
                'teenager-female': ["teenagerce", "teenagerka", "teenagerko", "teenagerkou", "teenagerku", "teenagerky"],
                'teenager-male': ["mladík", "mladíka", "mladíkem", "mladíkovi", "mladíku", "teenager", "teenagera", "teenagere", "teenagerem", "teenagerovi", "teenageru"],
                'undergraduate-male': ["absolvent", "absolventa", "absolvente", "absolventem", "absolventovi", "absolventu", "student", "študent", "studenta", "študenta", "studente", "študente", "studentem", "študentem", "studentovi", "študentovi", "studentu", "študentu"],
                'undergraduate-female': ["absolventce", "absolventka", "absolventko", "absolventkou", "absolventku", "absolventky", "studentce", "studentka", "studentko", "studentkou", "studentku", "studentky"],
                'veterinarian-female': ["veterinářce", "veterinářka", "veterinářko", "veterinářkou", "veterinářku", "veterinářky"],
                'veterinarian-male': ["veterinář", "veterináře", "veterinářem", "veterináři", "veterinářovi"],
                'visitor-female': ["návštěvnice", "návštěvnici", "návštěvnicí"],
                'visitor-male': ["návštěvník", "návštěvníka", "návštěvníkem", "návštěvníkovi", "návštěvníku"],
                'worker-female': ["pracovnice", "pracovnici", "pracovnicí"],
                'worker-male': ["pracovník", "pracovníka", "pracovníkem", "pracovníkovi", "pracovníku"],
                'writer-female': ["spisovatelce", "spisovatelka", "spisovatelko", "spisovatelkou", "spisovatelku", "spisovatelky"],
                'writer-male': ["spisovatel", "spisovatele", "spisovatelem", "spisovateli", "spisovatelovi"],
            }

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
