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
        self.tagger = Tagger.load('../czech-morfflex-pdt-161115/czech-morfflex-pdt-161115.tagger')

        self.tokenizer = self.tagger.newTokenizer()
        self.forms = Forms()
        self.lemmas = TaggedLemmas()
        self.tokens = TokenRanges()
    
    def get_gender(self, profession: str, translated_sent = None, entity_index = None, ds_entry = None) -> GENDER:
        """
        Predict gender of an input profession.
        """
        correct_prof = ds_entry[3].lower()
        if ds_entry[0] == "neutral" or "someone" in correct_prof or "child" in correct_prof or "advisee" in correct_prof or "guest" in correct_prof or "mover" in correct_prof or "victim" in correct_prof: 
            # neutral form is not common in Czech (only for words such as child)
            # someone and child cannot be in male nor female form
            # advisee cannot be exactly translated
            # guest, mover do not have female form
            return GENDER.ignore

        gender = self._get_gender(profession, translated_sent, entity_index, ds_entry)

        return gender

    def _get_gender(self, profession: str, translated_sent = None, entity_index = None, ds_entry = None) -> GENDER:
        expected_english_profession = ds_entry[3].lower()
        expected_gender = ds_entry[0]

        # initially try to resolve problem based on exact manual rules
        gender = self._get_gender_manual_rules(profession, translated_sent, entity_index, ds_entry)

        # check if translation doesn't contain common mistakes of translating profession as a place where it happens "hairdresser" > "hair saloon"
        if gender == GENDER.unknown:
            if expected_english_profession in self.common_errors:
                for form in self.common_errors[expected_english_profession]:
                     if re.search(form, translated_sent.lower()):
                         # this is definitelly error, resolve as incorrect label 
                         if expected_gender == "male":
                             gender = GENDER.female
                         else:
                             gender = GENDER.male

        if gender in [GENDER.male, GENDER.female, GENDER.neutral]:
            return gender

        return self._get_gender_automatically(profession, translated_sent, entity_index, ds_entry)

    def _get_gender_manual_rules(self, profession: str, translated_sent = None, entity_index = None, ds_entry = None) -> GENDER:
        # Rules defined and checked by Tom Kocmi
        expected_english_profession = ds_entry[3].lower()
        expected_gender = ds_entry[0] 

        translated_sent = translated_sent.lower()

        found_gender = GENDER.unknown

        male = expected_english_profession + "-male"
        female = expected_english_profession + "-female"
        
        both_possible = False
        if male in self.variants:
            for form in self.variants[male]:
                if re.search(form + "[^a-z]", translated_sent): # male form sometimes is prefix for female form "lékař" "lékařka"
                    found_gender = GENDER.male
                    break
    
        if female in self.variants:
            for form in self.variants[female]:
                if re.search(form + "[^a-z]", translated_sent):
                    if found_gender is GENDER.male:
                        found_gender = GENDER.unknown
                        both_possible = True
                        break # the form is equal for both female and male
                    found_gender = GENDER.female
                    # do not break, to check if other variants can't resolve in "both possible"

        # our morphology analysis cannot analyze whole sentence, therefore if both are possible, mark it as correct
        if both_possible:
            if expected_gender == "male":
                return GENDER.male
            else:
                return GENDER.female

        return found_gender

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
        for i in range(len(self.lemmas)):
            tag = self.lemmas[i].tag # this has a form NNFS1-----A---- where third letter specifies gender
            gender = tag[2]
            token = self.tokens[i]
            
            substring = text[token.start : token.start + token.length]

            if substring not in profession:
                # morphodita makes its tokenization ... thus skip most tokens in sentence and look only for profession
                continue

            if tag[0] != 'N' or tag[1] != 'N':
                continue

            if gender == "M":
                observed_genders.append(GENDER.male)
            elif gender == "F":
                observed_genders.append(GENDER.female)
            elif gender == "I":
                # in few cases the profession can have assigned "I" for inanimate
                inanimate_masculine = True 

        if not observed_genders:
            if inanimate_masculine:
                return GENDER.male
            else:
                return GENDER.unknown

        # Return the most commonly observed gender
        return Counter(observed_genders).most_common()[0][0]

    common_errors = {
            "baker": ["pekařství", "pekařstvím"],
            "carpenter": ["koberce", "koberec"],
            "cashier": ["pokladna", "pokladny", "pokladně", "pokladnu", "pokladno", "pokladnou"],
            "cleaner": ["vysavač", "vysavače", "vysavači", "vysavačem", "čistší"],
            "hairdresser" : ["kadeřnictví", "kadeřnictvím"],
            "janitor": ["janitor"], #not a czech word not even borrowed word 
            "librarian": ["knihovna", "knihovny", "knihovně", "knihovnu", "knihovno", "knihovnou"],

            }

    variants = {
                'accountant-female': ["účetní"],
                'accountant-male': ["účetní", "účetního", "účetním", "účetnímu"],
                'administrator-female': ["správkyně", "správkyni", "správkyní", "administrátorce", "administrátorka", "administrátorko", "administrátorkou", "administrátorku", "administrátorky"],
                'administrator-male': ["správce", "správcem", "správci", "správcovi", "administrátor", "administrátora", "administrátore", "administrátorem", "administrátorovi", "administrátoru"],
                'advisor-female': ["poradkyně", "poradkyni", "poradkyní"],
                'advisor-male': ["poradce", "poradcem", "poradci", "poradcovi"],
                'analyst-female': ["analytičce", "analytička", "analytičko", "analytičkou", "analytičku", "analytičky", "analytice"],
                'analyst-male': ["analytik", "analytika", "analytikem", "analytikovi", "analytiku"],
                'appraiser-female': ["odhadkyně", "odhadkyni", "odhadkyní", "hodnotitelce", "hodnotitelka", "hodnotitelko", "hodnotitelkou", "hodnotitelku", "hodnotitelky"],
                'appraiser-male': ["odhadce", "odhadcem", "odhadci", "odhadcovi", "hodnotitel", "hodnotitele", "hodnotiteli", "hodnotitelovi", "hodnotitelem"],
                'architect-female': ["architektce", "architektka", "architektko", "architektkou", "architektku", "architektky"],
                'architect-male': ["architekt", "architekta", "architekte", "architektem", "architektovi", "architektu"],
                'assistant-female': ["asistentce", "asistentka", "asistentko", "asistentkou", "asistentku", "asistentky", "pomocnice", "pomocnici", "pomocnicí"],
                'assistant-male': ["asistent", "asistenta", "asistente", "asistentem", "asistentovi", "asistentu", "pomocník", "pomocníka", "pomocníkovi", "pomocníku", "pomocníkem"],
                'attendant-female': ["obsluha", "obsluho", "obsluhou", "obsluhu", "obsluhy", "obsluze", "účastnice", "účastnici", "účastnicí", "zřízenkyně", "zřízenkyni", "zřízenkyní", "ošetřovatelka", "ošetřovatelky", "ošetřovatelce", "ošetřovatelku", "ošetřovatelko", "ošetřovatelkou"],
                'attendant-male': ["obsluha", "obsluho", "obsluhou", "obsluhu", "obsluhy", "obsluze", "účastník", "účastníka", "účastníkem", "účastníkovi", "účastníku", "zřízence", "zřízenče", "zřízencem", "zřízenci", "zřízencovi", "zřízenec", "ošetřovatel", "ošetřovatele", "ošetřovateli", "ošetřovatelem"],
                'auditor-female': ["auditorce", "auditorka", "auditorko", "auditorkou", "auditorku", "auditorky", "revisorce", "revisorka", "revisorko", "revisorkou", "revisorku", "revisorky", "revizorce", "revizorka", "revizorko", "revizorkou", "revizorku", "revizorky"],
                'auditor-male': ["auditor", "auditora", "auditore", "auditorem", "auditorovi", "auditoru", "revisor", "revisora", "revisore", "revisorem", "revisorovi", "revisoru", "revizor", "revizora", "revizore", "revizorem", "revizorovi", "revizoru"],
                'baker-female': ["pekařce", "pekařka", "pekařko", "pekařkou", "pekařku", "pekařky"],
                'baker-male': ["pekař", "pekaře", "pekařem", "pekaři", "pekařovi"],
                'bartender-female': ["barmance", "barmanka", "barmanko", "barmankou", "barmanku", "barmanky"],
                'bartender-male': ["barman", "barmana", "barmane", "barmanem", "barmanovi", "barmanu"],
                'broker-female': ["makléřce", "makléřka", "makléřko", "makléřkou", "makléřku", "makléřky"],
                'broker-male': ["makléř", "makléře", "makléřem", "makléři", "makléřovi"],
                'buyer-female': ["kupkyně", "kupkyni", "kupkyní", "kupující"],
                'buyer-male': ["kupce", "kupče", "kupcem", "kupci", "kupcovi", "kupec", "kupující", "kupujícího", "kupujícímu", "kupujícím"],
                'bystander-female': ["kolemjdoucí", "kolemjdoucího", "kolemjdoucím", "kolemjdoucímu","přihlížející"],
                'bystander-male': ["kolemjdoucí", "kolemjdoucího", "kolemjdoucím", "kolemjdoucímu", "přihlížející", "přihlížejícího", "přihlížejícímu", "přihlížejícím"],
                'carpenter-female': ["tesařce", "tesařka", "tesařko", "tesařkou", "tesařku", "tesařky", "truhlářce", "truhlářka", "truhlářko", "truhlářkou", "truhlářku", "truhlářky"],
                'carpenter-male': ["tesař", "tesaře", "tesařem", "tesaři", "tesařovi", "truhlář", "truhláře", "truhlářem", "truhláři", "truhlářovi"],
                'cashier-female': ["pokladní"],
                'cashier-male': ["pokladník", "pokladníka", "pokladníkem", "pokladníkovi", "pokladníku", "pokladní", "pokladního", "pokladním", "pokladnímu"],
                'chef-female': ["šéfkuchařce", "šéfkuchařka", "šéfkuchařko", "šéfkuchařkou", "šéfkuchařku", "šéfkuchařky", "kuchařce", "kuchařka", "kuchařko", "kuchařkou", "kuchařku", "kuchařky"],
                'chef-male': ["šéfkuchař", "šéfkuchaře", "šéfkuchařem", "šéfkuchaři", "šéfkuchařovi", "kuchař", "kuchaře", "kuchařem", "kuchaři", "kuchařovi"],
                'ceo-female': ["ředitelce", "ředitelka", "ředitelko", "ředitelkou", "ředitelku", "ředitelky"],
                'ceo-male': ["ředitel", "ředitele", "ředitelem", "řediteli", "ředitelovi"],
                'chemist-female': ["chemičce", "chemička", "chemičko", "chemičkou", "chemičku", "chemičky", "lékárnice", "lékárnici", "lékárnicí"],
                'chemist-male': ["chemik", "chemika", "chemikem", "chemikovi", "chemiku", "lékárník", "lékárníka", "lékárníkem", "lékárníkovi", "lékárníku"],
                'chief-female': ["šéfce", "šéfka", "šéfko", "šéfkou", "šéfku", "šéfky", "náčelnice", "náčelnici", "náčelnicí"],
                'chief-male': ["šéf", "šéfa", "šéfe", "šéfem", "šéfovi", "šéfu", "náčelník", "náčelníka", "náčelníkem", "náčelníkovi", "náčelníku"],
                'cleaner-female': ["uklízečce", "uklízečka", "uklízečko", "uklízečkou", "uklízečku", "uklízečky"],
                'cleaner-male': ["uklizeč", "uklízeč", "uklizeče", "uklízeče", "uklizečem", "uklízečem", "uklizeči", "uklízeči", "uklizečovi", "uklízečovi", "čistič", "čističe", "čističi", "čističem"],
                'clerk-female': ["úřednice", "úřednici", "úřednicí", "prodavačce", "prodavačka", "prodavačko", "prodavačkou", "prodavačku", "prodavačky", "recepční"],
                'clerk-male': ["úředník", "úředníka", "úředníkem", "úředníkovi", "úředníku", "prodavač", "prodavače", "prodavačem", "prodavači", "prodavačovi", "recepční", "recepčního", "recepčnímu", "recepčním"],
                'client-female': ["klientce", "klientka", "klientko", "klientkou", "klientku", "klientky"],
                'client-male': ["klient", "klienta", "kliente", "klientem", "klientovi", "klientu"],
                'cook-female': ["kuchařce", "kuchařka", "kuchařko", "kuchařkou", "kuchařku", "kuchařky"],
                'cook-male': ["kuchař", "kuchaře", "kuchařem", "kuchaři", "kuchařovi"],
                'construction worker-female': ["dělnice", "dělnici", "dělnicí", "pracovnice", "pracovnici", "pracovnicí"],
                'construction worker-male': ["dělník", "dělníka", "dělníkem", "dělníkovi", "dělníku", "pracovník", "pracovníka", "pracovníkem", "pracovníkovi", "pracovníku"],
                'counselor-female': ["poradkyně", "poradkyni", "poradkyní"],
                'counselor-male': ["poradce", "poradcem", "poradci", "poradcovi"],
                'customer-female': ["zákaznice", "zákaznici", "zákaznicí"],
                'customer-male': ["zákazník", "zákazníka", "zákazníkem", "zákazníkovi", "zákazníku"],
                'designer-female': ["návrhářce", "návrhářka", "návrhářko", "návrhářkou", "návrhářku", "návrhářky", "projektantka", "projektantky", "projektantce", "projektantku", "projektantko", "projektantkou", "konstruktérce", "konstruktérka", "konstruktérko", "konstruktérkou", "konstruktérku", "konstruktérky", "designérka", "designérky", "designérce", "designérku", "designérkou", "designérko"],
                'designer-male': ["návrhář", "návrháře", "návrhářem", "návrháři", "návrhářovi", "projektant", "projektanta", "projektante", "projektantem", "projektantovi", "projektantu", "konstruktér", "konstruktéra", "konstruktére", "konstruktérem", "konstruktérovi", "konstruktéru", "designér", "designéra", "designérovi", "designére", "designérem"],
                'developer-female': ["developerce", "developerka", "developerko", "developerkou", "developerku", "developerky", "vývojářce", "vývojářka", "vývojářko", "vývojářkou", "vývojářku", "vývojářky", "stavitelce", "stavitelka", "stavitelko", "stavitelkou", "stavitelku", "stavitelky"],
                'developer-male': ["developer", "developera", "developere", "developerem", "developerovi", "developeru", "vývojář", "vývojáře", "vývojářem", "vývojáři", "vývojářovi", "stavitel", "stavitele", "stavitelem", "staviteli", "stavitelovi"],
                'dietitian-female': ["dietoložce", "dietoložka", "dietoložko", "dietoložkou", "dietoložku", "dietoložky", "dietářce", "dietářka", "dietářko", "dietářkou", "dietářku", "dietářky"],
                'dietitian-male': ["dietolog", "dietologa", "dietologem", "dietologovi", "dietologu", "dietář", "dietáře", "dietářem", "dietáři", "dietářovi"],
                'dispatcher-female': ["dispečerce", "dispečerka", "dispečerko", "dispečerkou", "dispečerku", "dispečerky"],
                'dispatcher-male': ["dispečer", "dispečera", "dispečere", "dispečerem", "dispečerovi", "dispečeru"],
                'doctor-male': ["doktor", "doktora", "doktore", "doktorem", "doktorovi", "doktoru", "dra", "drem", "dru", "lékař", "lékaře", "lékařem", "lékaři", "lékařovi"],
                'doctor-female': ["doktorce", "doktorka", "doktorko", "doktorkou", "doktorku", "doktorky", "lékařce", "lékařka", "lékařko", "lékařkou", "lékařku", "lékařky"],
                'driver-female': ["řidičce", "řidička", "řidičko", "řidičkou", "řidičku", "řidičky"],
                'driver-male': ["řidič", "řidiče", "řidičem", "řidiči", "řidičovi"],
                'editor-female': ["redaktorce", "redaktorka", "redaktorko", "redaktorkou", "redaktorku", "redaktorky", "šéfredaktorce", "šéfredaktorka", "šéfredaktorko", "šéfredaktorkou", "šéfredaktorku", "šéfredaktorky", "editorce", "editorka", "editorko", "editorkou", "editorku", "editorky"],
                'editor-male': ["redaktor", "redaktora", "redaktore", "redaktorem", "redaktorovi", "redaktoru", "šéfredaktor", "šéfredaktora", "šéfredaktore", "šéfredaktorem", "šéfredaktorovi", "šéfredaktoru", "editor", "editora", "editore", "editorem", "editorovi", "editoru"],
                'educator-female': ["pedagožce", "pedagožka", "pedagožko", "pedagožkou", "pedagožku", "pedagožky", "vychovatelce", "vychovatelka", "vychovatelko", "vychovatelkou", "vychovatelku", "vychovatelky"],
                'educator-male': ["pedagog", "pedagoga", "pedagogem", "pedagogovi", "pedagogu", "vychovatel", "vychovatele", "vychovatelem", "vychovateli", "vychovatelovi"],
                'electrician-female': ["elektrikářce", "elektrikářka", "elektrikářko", "elektrikářkou", "elektrikářku", "elektrikářky"],
                'electrician-male': ["elektrikář", "elektrikáře", "elektrikářem", "elektrikáři", "elektrikářovi"],
                'employee-female': ["zaměstnankyně", "zaměstnankyni", "zaměstnankyní"],
                'employee-male': ["zaměstnance", "zaměstnanče", "zaměstnancem", "zaměstnanci", "zaměstnancovi", "zaměstnanec"],
                'engineer-female': ["zkoušející","inženýrce", "inženýrka", "inženýrko", "inženýrkou", "inženýrku", "inženýrky"],
                'engineer-male': ["inženýr", "inženýra", "inženýre", "inženýrem", "inženýrovi", "inženýru", "zkoušející", "zkoušejícího", "zkoušejícímu", "zkoušejícím"],
                'examiner-male': ["zkoušející","zkoušejícího","zkoušejícímu","zkoušejícím","vyšetřovatel", "vyšetřovatele", "vyšetřovatelem", "vyšetřovateli", "vyšetřovatelovi"],
                'examiner-female': ['zkoušející',"vyšetřovatelce", "vyšetřovatelka", "vyšetřovatelko", "vyšetřovatelkou", "vyšetřovatelku", "vyšetřovatelky"],
                'farmer-female': ["farmářce", "farmářka", "farmářko", "farmářkou", "farmářku", "farmářky", "zemědělkyně", "zemědělkyni", "zemědělkyní"],
                'farmer-male': ["farmář", "farmáře", "farmářem", "farmáři", "farmářovi", "sedlák", "sedláka", "sedlákem", "sedlákovi", "sedláku", "zemědělce", "zemědělče", "zemědělcem", "zemědělci", "zemědělcovi", "zemědělec"],
                'firefighter-female': ["hasičce", "hasička", "hasičko", "hasičkou", "hasičku", "hasičky"],
                'firefighter-male': ["hasič", "hasiče", "hasičem", "hasiči", "hasičovi"],
                'guard-female': ["stráž", "stráže", "stráži", "stráží", "strážná", "strážné", "strážnou", "strážkyně", "strážkyni", "strážkyní", "strážnice", "strážnici", "strážnicí"],
                'guard-male': ["strážného", "strážnej", "strážném", "strážnému", "strážný", "strážnýho", "strážnym", "strážným", "strážnýmu", "strážce", "strážcem", "strážci", "strážcovi", "strážník", "strážníka", "strážníkem", "strážníkovi", "strážníku", "hlídač", "hlídače", "hlídači", "hlídačem"],
                'hairdresser-female': ["kadeřnice", "kadeřnici", "kadeřnicí"],
                'hairdresser-male': ["kadeřník", "kadeřníka", "kadeřníkem", "kadeřníkovi", "kadeřníku"],
                'housekeeper-female': ["hospodyně", "hospodyni", "hospodyní"],
                'housekeeper-male': [], #cannot be translated exactly
                'homeowner-female': ["majitelce", "majitelka", "majitelko", "majitelkou", "majitelku", "majitelky"],
                'homeowner-male': ["majitel", "majitele", "majitelem", "majiteli", "majitelovi"],
                'hygienist-female': ["hygienistce", "hygienistka", "hygienistko", "hygienistkou", "hygienistku", "hygienistky", "hygieničce", "hygienička", "hygieničko", "hygieničkou", "hygieničku", "hygieničky"],
                'hygienist-male': ["hygienik", "hygienika", "hygienikem", "hygienikovi", "hygieniku"],
                'inspector-female': ["inspektorce", "inspektorka", "inspektorko", "inspektorkou", "inspektorku", "inspektorky"],
                'inspector-male': ["inspektor", "inspektora", "inspektore", "inspektorem", "inspektorovi", "inspektoru"],
                'instructor-female': ["instruktorce", "instruktorka", "instruktorko", "instruktorkou", "instruktorku", "instruktorky"],
                'instructor-male': ["instruktor", "instruktora", "instruktore", "instruktorem", "instruktorovi", "instruktoru"],
                'investigator-female': ["vyšetřovatelce", "vyšetřovatelka", "vyšetřovatelko", "vyšetřovatelkou", "vyšetřovatelku", "vyšetřovatelky"],
                'investigator-male': ["vyšetřovatel", "vyšetřovatele", "vyšetřovatelem", "vyšetřovateli", "vyšetřovatelovi"],
                'janitor-female': ["uklízečce", "uklízečka", "uklízečko", "uklízečkou", "uklízečku", "uklízečky", "domovnice", "domovnici", "domovnicí", "správkyně", "správkyni", "správkyní", "údržbářce", "údržbářka", "údržbářko", "údržbářkou", "údržbářku", "údržbářky", "vrátná", "vrátné", "vrátnou", "vrátný"],
                'janitor-male': ["domovník", "domovníka", "domovníkem", "domovníkovi", "domovníku", "školník", "školníka", "školníkem", "školníkovi", "školníku", "správce", "správcem", "správci", "správcovi", "údržbář", "údržbáře", "údržbářem", "údržbáři", "údržbářovi", "uklizeč", "uklízeč", "uklizeče", "uklízeče", "uklizečem", "uklízečem", "uklizeči", "uklízeči", "uklizečovi", "uklízečovi", "vrátného", "vrátnej", "vrátném", "vrátnému", "vrátný", "vrátnýho", "vrátnym", "vrátným", "vrátnýmu"],
                'laborer-female': ["dělnice", "dělnici", "dělnicí", "pracovnice", "pracovnici", "pracovnicí"],
                'laborer-male': ["dělník", "dělníka", "dělníkem", "dělníkovi", "dělníku", "pracovník", "pracovníka", "pracovníkem", "pracovníkovi", "pracovníku"],
                'lawyer-female': ["advokátce", "advokátka", "advokátko", "advokátkou", "advokátku", "advokátky", "právničce", "právnička", "právničko", "právničkou", "právničku", "právničky"],
                'lawyer-male': ["advokát", "advokáta", "advokáte", "advokátem", "advokátovi", "advokátu", "právník", "právníka", "právníkem", "právníkovi", "právníku"],
                'librarian-female': ["knihovnice", "knihovnici", "knihovnicí"],
                'librarian-male': ["knihovník", "knihovníka", "knihovníkem", "knihovníkovi", "knihovníku"],
                'machinist-female': ["strojnice", "strojnici", "strojnicí"],
                'machinist-male': ["strojník", "strojníka", "strojníkem", "strojníkovi", "strojníku"],
                'manager-female': ["vedoucí", "manažerce", "manažerka", "manažerko", "manažerkou", "manažerku", "manažerky", "ředitelce", "ředitelka", "ředitelko", "ředitelkou", "ředitelku", "ředitelky"],
                'manager-male': ["vedoucí","vedoucího","vedoucímu","vedoucím", "manager", "managera", "managere", "managerem", "managerovi", "manageru", "manažer", "manažér", "manažera", "manažéra", "manažere", "manažére", "manažerem", "manažérem", "manažerovi", "manažérovi", "manažeru", "manažéru", "ředitel", "ředitele", "ředitelem", "řediteli", "ředitelovi"],
                'mechanic-female': ["mechaničce", "mechanička", "mechaničko", "mechaničkou", "mechaničku", "mechaničky"],
                'mechanic-male': ["mechanik", "mechanika", "mechanikem", "mechanikovi", "mechaniku"],
                'mover-male': ["stěhovák", "stěhováka", "stěhovákem", "stěhovákovi", "stěhováku", "stěhovač", "stěhovače", "stěhovači", "stěhovačovi", "stěhovačem"],
                'mover-female': ["stěhovatelce", "stěhovatelka", "stěhovatelko", "stěhovatelkou", "stěhovatelku", "stěhovatelky"],
                'nurse-male': ["ošetřovatel", "ošetřovatele", "ošetřovatelem", "ošetřovateli", "ošetřovatelovi"],
                'nurse-female': ["sestra", "sestře", "sestři", "sestro", "sestrou", "sestru", "sestry", "ošetřovatelce", "ošetřovatelka", "ošetřovatelko", "ošetřovatelkou", "ošetřovatelku", "ošetřovatelky"],
                'nutritionist-female': ["odbornice", "odbornici", "odbornicí"],
                'nutritionist-male': ["odborník", "odborníka", "odborníkem", "odborníkovi", "odborníku"],
                'officer-male': ["důstojník", "důstojníka", "důstojníkem", "důstojníkovi", "důstojníku", "policista", "policisto", "policistou", "policistovi", "policistu", "policisty", "strážník", "strážníka", "strážníkem", "strážníkovi", "strážníku"],
                'officer-female': ["důstojnice", "důstojnici", "důstojnicí", "policistce", "policistka", "policistko", "policistkou", "policistku", "policistky", "strážnice", "strážnici", "strážnicí"],
                'onlooker-female': ["přihlížející"],
                'onlooker-male': ["přihlížející", "přihlížejícího", "přihlížejícímu", "přihlížejícím"],
                'owner-female': ["majitelka", "majitelky", "majitelce", "majitelku", "majitelko", "majitelce", "majitelkou"],
                'owner-male': ["majitel", "majitele", "majiteli", "majitelem"],
                'painter-female': ["malířka", "malířky", "malířce", "malířku", "malířko", "malířkou"],
                'painter-male': ["malíř", "malíře", "malířem", "malíři", "malířovi"],
                'paralegal-female': ["koncipientce", "koncipientka", "koncipientko", "koncipientkou", "koncipientku", "koncipientky", "asistentce", "asistentka", "asistentko", "asistentkou", "asistentku", "asistentky"],
                'paralegal-male': ["koncipient", "koncipienta", "koncipiente", "koncipientem", "koncipientovi", "koncipientu", "asistent", "asistenta", "asistente", "asistentem", "asistentovi", "asistentu"],
                'paramedic-male': ["záchranář", "záchranáře", "záchranářem", "záchranáři", "záchranářovi", "zdravotník", "zdravotníka", "zdravotníkem", "zdravotníkovi", "zdravotníku"],
                'paramedic-female': ["zdravotnice", "zdravotnici", "zdravotnicí", "záchranářce", "záchranářka", "záchranářko", "záchranářkou", "záchranářku", "záchranářky"],
                'pathologist-female': ["patoložce", "patoložka", "patoložko", "patoložkou", "patoložku", "patoložky"],
                'pathologist-male': ["patolog", "patologa", "patologem", "patologovi", "patologu"],
                'patient-female': ["pacientce", "pacientka", "pacientko", "pacientkou", "pacientku", "pacientky"],
                'patient-male': ["pacient", "pacienta", "paciente", "pacientem", "pacientovi", "pacientu"],
                'passenger-female': ["cestující", "pasažérce", "pasažérka", "pasažérko", "pasažérkou", "pasažérku", "pasažérky"],
                'passenger-male': ["cestující", "cestujícího", "cestujícím", "cestujícímu", "pasažér", "pasažéra", "pasažére", "pasažérem", "pasažérovi", "pasažéru"],
                'pedestrian-female': ["chodkyně", "chodkyni", "chodkyní"],
                'pedestrian-male': ["chodce", "chodče", "chodcem", "chodci", "chodcovi", "chodec"],
                'pharmacist-male': ["lékárník", "lékárníka", "lékárníkem", "lékárníkovi", "lékárníku"],
                'pharmacist-female': ["lékárnice", "lékárnici", "lékárnicí"],
                'physician-female': ["lékařce", "lékařka", "lékařko", "lékařkou", "lékařku", "lékařky"],
                'physician-male': ["lékař", "lékaře", "lékařem", "lékaři", "lékařovi"],
                'planner-female': ["plánovačce", "plánovačka", "plánovačko", "plánovačkou", "plánovačku", "plánovačky"],
                'planner-male': ["plánovač", "plánovače", "plánovačem", "plánovači", "plánovačovi"],
                'plumber-female': ["instalatérce", "instalatérka", "instalatérko", "instalatérkou", "instalatérku", "instalatérky"],
                'plumber-male': ["instalatér", "instalatéra", "instalatére", "instalatérem", "instalatérovi", "instalatéru"],
                'practitioner-female': ["praktikantce", "praktikantka", "praktikantko", "praktikantkou", "praktikantku", "praktikantky", "lékařce", "lékařka", "lékařko", "lékařkou", "lékařku", "lékařky"],
                'practitioner-male': ["praktik", "praktika", "praktikem", "praktikovi", "praktiku", "lékař", "lékaře", "lékařem", "lékaři", "lékařovi"],
                'programmer-female': ["programátorce", "programátorka", "programátorko", "programátorkou", "programátorku", "programátorky"],
                'programmer-male': ["programátor", "programátora", "programátore", "programátorem", "programátorovi", "programátoru"],
                'protester-female': ["protestující", "demonstrantce", "demonstrantka", "demonstrantko", "demonstrantkou", "demonstrantku", "demonstrantky"],
                'protester-male': ["protestující", "protestujícího", "protestujícímu", "protestujícím", "demonstrant", "demonstranta", "demonstrante", "demonstrantem", "demonstrantovi", "demonstrantu"],
                'psychologist-female': ["psycholožce", "psycholožka", "psycholožko", "psycholožkou", "psycholožku", "psycholožky"],
                'psychologist-male': ["psycholog", "psychologa", "psychologem", "psychologovi", "psychologu"],
                'receptionist-female': ["recepční"],
                'receptionist-male': ["recepční", "recepčního", "recepčnímu", "recepčním"],
                'resident-female': ["obyvatelce", "obyvatelka", "obyvatelko", "obyvatelkou", "obyvatelku", "obyvatelky"],
                'resident-male': ["obyvatel", "obyvatele", "obyvateli", "obyvatelem"],
                'salesperson-female': ["prodavačce", "prodavačka", "prodavačko", "prodavačkou", "prodavačku", "prodavačky", "prodejkyně", "prodejkyni", "prodejkyní", "obchodnice", "obchodnici", "obchodnicí"],
                'salesperson-male': ["prodavač", "prodavače", "prodavačem", "prodavači", "prodavačovi", "prodejce", "prodejcem", "prodejci", "prodejcovi", "prodejce", "prodejcem", "prodejci", "prodejcovi", "obchodník", "obchodníka", "obchodníkem", "obchodníkovi", "obchodníku"],
                'scientist-female': ["vědkyně", "vědkyni", "vědkyní"],
                'scientist-male': ["vědce", "vědče", "vědcem", "vědci", "vědcovi", "vědec"],
                'surgeon-female': [], # nelze přeložit
                'surgeon-male': ["chirurg", "chirurga", "chirurgem", "chirurgovi", "chirurgu"],
                'secretary-female': ["sekretářce", "sekretářka", "sekretářko", "sekretářkou", "sekretářku", "sekretářky", "tajemnice", "tajemnici", "tajemnicí"],
                'secretary-male': ["tajemník", "tajemníka", "tajemníkem", "tajemníkovi", "tajemníku", "sekretář", "sekretáře", "sekretářem", "sekretáři", "sekretářovi"],
                'sheriff-female': ["šerifce", "šerifka", "šerifko", "šerifkou", "šerifku", "šerifky"],
                'sheriff-male': ["šerif", "šerifa", "šerife", "šerifem", "šerifovi", "šerifu"],
                'specialist-female': ["specialistce", "specialistka", "specialistko", "specialistkou", "specialistku", "specialistky"],
                'specialist-male': ["specialista", "specialisto", "specialistou", "specialistovi", "specialistu", "specialisty"],
                'student-male': ["student", "študent", "studenta", "študenta", "studente", "študente", "studentem", "študentem", "studentovi", "študentovi", "studentu", "študentu"],
                'student-female': ["studentce", "studentka", "studentko", "studentkou", "studentku", "studentky"],
                'supervisor-female': ["nadřízená", "nadřízené", "nadřízenou", "nadřízený", "vedoucí""dozorkyně", "dozorkyni", "dozorkyní", "školitelce", "školitelka", "školitelko", "školitelkou", "školitelku", "školitelky", "techničce", "technička", "techničko", "techničkou", "techničku", "techničky"],
                'supervisor-male': ["dozorce", "dozorcem", "dozorci", "dozorcovi", "školitel", "školitele", "školitelem", "školiteli", "školitelovi", "nadřízeného", "nadřízenej", "nadřízeném", "nadřízenému", "nadřízený", "nadřízenýho", "nadřízenym", "nadřízeným", "nadřízenýmu", "vedoucí", "vedoucího", "vedoucím", "vedoucímu"],
                'surgeon-male': ["chirurg", "chirurga", "chirurgem", "chirurgovi", "chirurgu"],
                'taxpayer-female': ["poplatnice", "poplatnici", "poplatnicí", "plátkyně", "plátkyni", "plátkyní"],
                'taxpayer-male': ["poplatníče", "poplatník", "poplatníka", "poplatníkem", "poplatníkovi", "poplatníku", "plátce", "plátcem", "plátci", "plátcovi"],
                'tailor-female': ["krejčová", "krejčové", "krejčovou", "krejčový", "krejčí"],
                'tailor-male': ["krejčí", "krejčího", "krejčím", "krejčímu"],
                'teacher-female': ["učitelce", "učitelka", "učitelko", "učitelkou", "učitelku", "učitelky"],
                'teacher-male': ["učitel", "učitele", "učitelem", "učiteli", "učitelovi"],
                'technician-female': ["techničce", "technička", "techničko", "techničkou", "techničku", "techničky"],
                'technician-male': ["technik", "technika", "technikem", "technikovi", "techniku"],
                'teenager-female': ["teenagerce", "teenagerka", "teenagerko", "teenagerkou", "teenagerku", "teenagerky"],
                'teenager-male': ["mladík", "mladíka", "mladíkem", "mladíkovi", "mladíku", "teenager", "teenagera", "teenagere", "teenagerem", "teenagerovi", "teenageru"],
                'therapist-female': ["terapeutce", "terapeutka", "terapeutko", "terapeutkou", "terapeutku", "terapeutky"],
                'therapist-male': ["terapeut", "terapeuta", "terapeute", "terapeutem", "terapeutovi", "terapeutu"],
                'undergraduate-male': ["absolvent", "absolventa", "absolvente", "absolventem", "absolventovi", "absolventu", "student", "študent", "studenta", "študenta", "studente", "študente", "studentem", "študentem", "studentovi", "študentovi", "studentu", "študentu", "vysokoškolák", "vysokoškoláka", "vysokoškolákem", "vysokoškolákovi", "vysokoškoláku"],
                'undergraduate-female': ["absolventce", "absolventka", "absolventko", "absolventkou", "absolventku", "absolventky", "studentce", "studentka", "studentko", "studentkou", "studentku", "studentky", "vysokoškolačce", "vysokoškolačka", "vysokoškolačko", "vysokoškolačkou", "vysokoškolačku", "vysokoškolačky"],
                'veterinarian-female': ["veterinářce", "veterinářka", "veterinářko", "veterinářkou", "veterinářku", "veterinářky", "lékařka", "lékařky", "lékařce", "lékařku", "lékařko", "lékařkou"],
                'veterinarian-male': ["veterinář", "veterináře", "veterinářem", "veterináři", "veterinářovi", "lékař", "lékaře", "lékaři", "lékařovi", "lékařem"],
                'visitor-female': ["návštěvnice", "návštěvnici", "návštěvnicí"],
                'visitor-male': ["návštěvník", "návštěvníka", "návštěvníkem", "návštěvníkovi", "návštěvníku"],
                'worker-female': ["pracovnice", "pracovnici", "pracovnicí", "dělnice", "dělnici", "dělnicí"],
                'worker-male': ["pracovník", "pracovníka", "pracovníkem", "pracovníkovi", "pracovníku", "dělník", "dělníka", "dělníkem", "dělníkovi", "dělníku"],
                'witness-female': ["svědkyně", "svědkyni", "svědkyní"],
                'witness-male': ["svědek", "svědka", "svědkem", "svědkovi", "svědku"],
                'writer-female': ["spisovatelce", "spisovatelka", "spisovatelko", "spisovatelkou", "spisovatelku", "spisovatelky", "pisatelce", "pisatelka", "pisatelko", "pisatelkou", "pisatelku", "pisatelky"],
                'writer-male': ["spisovatel", "spisovatele", "spisovatelem", "spisovateli", "spisovatelovi", "pisatel", "pisatele", "pisatelem", "pisateli", "pisatelovi"],
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
