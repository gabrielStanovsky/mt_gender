""" Usage:
    <file-name> --in=IN_FILE --out=OUT_FILE [--debug]
"""

from collections import Counter
import logging
from docopt import docopt
import spacy
from spacy.tokens.token import Token
import re

from languages.util import GENDER, MORFEUSZ_GENDER_TYPES, MORFEUSZ_GENDER_TAG_POSITION


class MorfeuszPredictor:
    """
    Class for Morfeusz -- Polish Morphology Analyzer
    """

    def __init__(self):
        """
        Init spacy with morfeusz2.
        https://github.com/ipipan/spacy-pl
        http://morfeusz.sgjp.pl/
        """
        import morfeusz2
        self.lang = "pl"
        self.cache = {}    # Store calculated professions
        if spacy.util.is_package('pl_spacy_model_morfeusz_big'):
            self.nlp = spacy.load('pl_spacy_model_morfeusz_big', disable=["parser", "ner"])
        elif spacy.util.is_package('pl_spacy_model_morfeusz'):
            self.nlp = spacy.load('pl_spacy_model_morfeusz', disable=["parser", "ner"])
        else:
            raise FileNotFoundError("Spacy model with Morfeusz not found.\n"
                                    "To run analysis for Polish install Morfeusz from: http://morfeusz.sgjp.pl/\n"
                                    "and download Spacy model with Morfeusz from: https://github.com/ipipan/spacy-pl")

    def get_gender(self, profession: str, translated_sent = None, entity_index = None, ds_entry = None) -> GENDER:
        """
        Predict gender of an input profession.
        """

        gold_gender, src_index, src_sent, src_profession = ds_entry
        src_profession = src_profession.lower()
        src_profession_split = src_profession.split(' ')
        if len(src_profession_split) > 1 and src_profession_split[0] in ('a', 'an', 'the'):
            src_profession = ' '.join(src_profession_split[1:])

        if src_profession in ('child', 'someone', 'advisee', 'mover') \
                or gold_gender == GENDER.neutral:
            return GENDER.ignore

        if profession not in self.cache or not profession:
            self.cache[profession] = self._get_gender(profession, translated_sent, gold_gender, src_profession)

        # if self.cache[profession] == GENDER.unknown:
        #     logging.warn(f"Gender unkown for {profession}\nin sentence: `{translated_sent}`")
        #     logging.warn(f"English profession: {ds_entry[3]}")

        return self.cache[profession]

    def _get_gender(self, profession: str, translated_sent: str, gold_gender: GENDER, src_profession: str) -> GENDER:
        # initially try to resolve problem based on exact manual rules
        gender = self._get_gender_manual_rules(translated_sent, gold_gender, src_profession)

        if gender is not GENDER.unknown:
            return gender

        return self._get_gender_automatically(profession)

    def _get_gender_manual_rules(self, translated_sent: str, gold_gender: GENDER, src_profession: str) -> GENDER:
        # Rules defined and checked by Tomasz Limisiewicz

        translated_sent = translated_sent.lower()

        found_gender = GENDER.unknown

        male = src_profession + "-male"
        female = src_profession + "-female"

        both_possible = False
        if male in self.variants:
            for form in self.variants[male]:
                # don't match when profession is preceded by `mrs.` in Polish `pani`, `panią`
                if re.search(form + "[^a-z]", translated_sent) and \
                        not re.search("(pani|panią) " + form + "[^a-z]", translated_sent):
                    found_gender = GENDER.male
                    break
        else:
            logging.warn(f"{male} not in variants")

        if female in self.variants:
            for form in self.variants[female]:
                if re.search(form + "[^a-z]", translated_sent):
                    if found_gender is not GENDER.unknown:
                        found_gender = GENDER.unknown
                        both_possible = True
                        break  # the form is equal for both female and male
                    found_gender = GENDER.female
                    # do not break, to check for duplicates

        # our morphology analysis cannot analyze whole sentence, therefore if both are possible, mark it as correct
        # it is quite uncommon for Polish
        if both_possible:
            if gold_gender == "male":
                return GENDER.male
            else:
                return GENDER.female

        return found_gender

    def _get_gender_automatically(self, profession: str) -> GENDER:
        """
        Predict gender, without using cache
        """
        if not profession.strip():
            # Empty string
            return GENDER.unknown

        tokens = self.nlp(profession)
        observed_genders = [self.get_gender_from_token(tok) for tok in tokens]
        observed_genders = [gender for gender in observed_genders if gender]

        if not observed_genders:
            return GENDER.unknown

        # Return the most commonly observed gender
        return Counter(observed_genders).most_common()[0][0]

    @staticmethod
    def get_gender_from_token(token: Token):
        """
        Get gender indication from spacy token with morfeusz, if it exists
        """
        features = token._.feats.split(':')
        if len(features) < MORFEUSZ_GENDER_TAG_POSITION + 1:
            return None

        morfeusz_gender = features[MORFEUSZ_GENDER_TAG_POSITION]
        if morfeusz_gender not in MORFEUSZ_GENDER_TYPES:
            if features[MORFEUSZ_GENDER_TAG_POSITION - 1] in MORFEUSZ_GENDER_TYPES:
                morfeusz_gender = features[MORFEUSZ_GENDER_TAG_POSITION -1]
            else:
                return GENDER.neutral

        return MORFEUSZ_GENDER_TYPES[morfeusz_gender]

    variants = {
        'ceo-female': ['prezydentko', 'prezydentkę', 'prezydentce', 'pani dyrektor', 'prezeską', 'prezydentki',
                       'prezydentką', 'prezeski', 'panią prezes', 'pani prezes', 'dyrektorka', 'dyrektorkę',
                       'dyrektorką', 'prezydentka', 'pani prezydent', 'prezesko', 'dyrektorki', 'panią prezydent',
                       'dyrektorce', 'prezeskę', 'panią dyrektor', 'dyrektorko', 'prezesce', 'prezeska'],
        'ceo-male': ['prezydentowi', 'prezesa', 'prezes', 'dyrektorze', 'prezesowi', 'dyrektorowi', 'dyrektor',
                     'prezesem', 'prezydent', 'prezydencie', 'dyrektorem', 'dyrektora', 'prezydentem', 'prezesie',
                     'prezydenta'],
        'accountant-female': ['księgowa', 'księgowej', 'księgowo', 'księgową'],
        'accountant-male': ['księgowego', 'księgowy', 'księgowemu', 'księgowym'],
        'administrator-female': ['administratorka', 'administratorkę', 'administratorki', 'administratorce',
                                 'pani administrator', 'panią administrator', 'administratorką', 'administratorko'],
        'administrator-male': ['administratorem', 'administratorowi', 'administratora', 'administratorze',
                               'administrator'],
        'advisee-female': [],
        'advisee-male': [],
        'advisor-female': ['doradczynię', 'doradczynią', 'doradczyni'],
        'advisor-male': ['doradcy', 'doradca', 'doradcą', 'doradcę', 'doradco'],
        'analyst-female': ['analityczko', 'analityczka', 'analityczkę', 'pani analityk', 'analityczki',
                           'panią analityk', 'analityczką', 'analityczce'],
        'analyst-male': ['analityka', 'analitykiem', 'analityk', 'analitykowi', 'analityku'],
        'appraiser-female': ['pani rzeczoznawco', 'panią rzeczoznawcę', 'pani rzeczoznawcy', 'panią rzeczoznawcą',
                             'pani rzeczoznawca'],
        'appraiser-male': ['rzeczoznawco', 'rzeczoznawcę', 'rzeczoznawcy', 'rzeczoznawcą', 'rzeczoznawca'],
        'architect-female': ['architektko', 'pani architekt', 'architektką', 'panią architekt', 'architektki',
                             'architektce', 'architektkę', 'architektka'],
        'architect-male': ['architektowi', 'architekta', 'architekt', 'architektem', 'architekcie'],
        'assistant-female': ['asystentko', 'pomocniczką', 'pomocniczkę', 'asystentki', 'asystentkę', 'asystentka',
                             'pomocniczce', 'pomocniczki', 'pomocniczko', 'asystentce', 'asystentką', 'pomocniczka'],
        'assistant-male': ['asystencie', 'pomocniku', 'pomocnikiem', 'asystentowi', 'pomocnika', 'asystent',
                           'asystentem', 'asystenta', 'pomocnikowi', 'pomocnik'],
        'attendant-female': ['opiekunce', 'asystentko', 'pracownico', 'pracownicą', 'uczestniczkę', 'recepcjonistką',
                             'towarzyszki', 'stewardessą', 'uczestniczce', 'asystentka', 'stewardessę', 'asystentce',
                             'asystentką', 'recepcjonistka', 'stewardessy', 'pracownicę', 'opiekunkę', 'towarzyszce',
                             'towarzyszką', 'stewardesą', 'uczestniczką', 'stewardeso', 'stewardesa', 'opiekunki',
                             'recepcjonistko', 'stewardesie', 'asystentkę', 'recepcjonistce', 'uczestniczki',
                             'stewardesso', 'pracownicy', 'uczestniczka', 'stewardessa', 'stewardesę', 'recepcjonistki',
                             'towarzyszko', 'stewardesy', 'uczestniczko', 'towarzyszkę', 'opiekunka', 'opiekunko',
                             'opiekunką', 'stewardessie', 'asystentki', 'recepcjonistkę', 'towarzyszka', 'pracownica'],
        'attendant-male': ['opiekun', 'asystencie', 'pracownikiem', 'opiekuna', 'służącym', 'pracowniku', 'pomocnika',
                           'asystent', 'uczestniku', 'służącemu', 'służącego', 'pracownika', 'służący', 'stewarda',
                           'asystentem', 'pomocnik', 'steward', 'stewardowi', 'uczestnik', 'opiekunem', 'uczestnikowi',
                           'pracownikowi', 'pomocniku', 'pomocnikiem', 'asystentowi', 'stewardem', 'pracownik',
                           'uczestnikiem', 'asystenta', 'uczestnika', 'stewardzie', 'opiekunie', 'pomocnikowi',
                           'opiekunowi'],
        'auditor-female': ['pani rzecoznawca', 'panią kontroler', 'biegła', 'audytorko', 'kontrolerkę', 'audytorki',
                           'kontrolerki', 'panią rzecoznawca', 'pani kontroler', 'kontrolerka', 'audytorką',
                           'kontrolerką', 'pani audytor', 'audytorkę', 'pani biegły', 'kontrolerce', 'biegłej',
                           'audytorce', 'audytorka', 'kontrolerko', 'panią audytor', 'biegłą', 'panią biegły'],
        'auditor-male': ['kontrolerowi', 'rewident', 'biegłym', 'audytorem', 'kontrolera', 'rewidenta', 'biegłego',
                         'audytorze', 'rewidentem', 'biegły', 'biegłemu', 'audytorowi', 'kontrolerem', 'kontroler',
                         'kontrolerze', 'audytor', 'rewidentowi', 'rewidencie', 'audytora'],
        'baker-female': ['piekarkę', 'piekarka', 'piekarką', 'piekarko', 'piekarce', 'piekarki'],
        'baker-male': ['piekarzu', 'piekarzowi', 'piekarza', 'piekarzem', 'piekarz'],
        'bartender-female': ['barmanki', 'barmankę', 'barmanka', 'barmance', 'barmanką', 'barmanko'],
        'bartender-male': ['barmanie', 'barmana', 'barmanowi', 'barman', 'barmanem'],
        'broker-female': ['pani broker', 'panią broker', 'pośredniczki', 'panią pośrednik', 'pośredniczce',
                          'pośredniczka', 'pośredniczko', 'panią makler', 'pani pośrednik', 'pani makler',
                          'pośredniczkę', 'pośredniczką'],
        'broker-male': ['maklerze', 'brokera', 'brokerze', 'maklerowi', 'maklerem', 'pośredniku', 'pośrednikowi',
                        'pośrednika', 'broker', 'brokerowi', 'maklera', 'pośrednikiem', 'pośrednik', 'makler',
                        'brokerem'],
        'buyer-female': ['kupującej', 'nabywczynię', 'kupującą', 'kupująca', 'nabywczynią', 'nabywczyni'],
        'buyer-male': ['nabywcy', 'kupującym', 'kupiec', 'kupującego', 'kupującemu', 'kupcze', 'kupcowi', 'kupcem',
                       'nabywcą', 'nabywco', 'kupujący', 'nabywca', 'kupca', 'nabywcę', 'kupcu'],
        'bystander-female': ['obserwatorkę', 'obserwatorko', 'obserwatorką', 'obserwatorka', 'obserwatorki',
                             'obserwatorce'],
        'bystander-male': ['obserwatorze', 'obserwatorowi', 'obserwatora', 'obserwatorem', 'obserwator'],
        'carpenter-female': ['stolarce', 'stolarko', 'stolarką', 'stolarki', 'stolarkę', 'stolarka', 'pani cieślo',
                             'pani cieśla', 'pani cieśli', 'panią cieślę', 'panią cieślą'],
        'carpenter-male': ['stolarzem', 'cieślo', 'cieśla', 'cieśli', 'stolarza', 'stolarzowi', 'stolarz', 'cieślę',
                           'cieślą', 'stolarzu'],
        'cashier-female': ['kasjerki', 'kasjerka', 'kasjerko', 'kasjerkę', 'kasjerce', 'kasjerką'],
        'cashier-male': ['kasjer', 'kasjerowi', 'kasjerem', 'kasjerze', 'kasjera'],
        'chef-female': ['szefowa kuchni', 'szefowo kuchni', 'szefową kuchni', 'szefowej kuchni'],
        'chef-male': ['szefowi kuchni', 'szef kuchni', 'szefa kuchni', 'szefie kuchni', 'szefem kuchni'],
        'chemist-female': ['panią chemik', 'chemiczka', 'chemiczką', 'pani chemik', 'chemiczkę', 'chemiczki',
                           'chemiczko', 'chemiczce'],
        'chemist-male': ['chemikiem', 'chemiku', 'chemikowi', 'chemika', 'chemik'],
        'chief-female': ['szefowa', 'naczelniczka', 'naczelniczce', 'komendantko', 'naczelniczko', 'komendantki',
                         'panią naczelnik', 'komendantka', 'szefową', 'pani komendant', 'szefowo', 'komendantce',
                         'szefowej', 'naczelniczką', 'komendantkę', 'panią komendant', 'naczelniczkę', 'komendantką',
                         'pani naczelnik', 'naczelniczki'],
        'chief-male': ['szef', 'wodzu', 'wodzem', 'wójtowi', 'naczelnika', 'komendanta', 'wodzowi', 'komendancie',
                       'naczelnemu', 'komendant', 'naczelny', 'naczelniku', 'wódz', 'wodza', 'wójcie', 'naczelnego',
                       'szefem', 'naczelnik', 'naczelnikowi', 'naczelnikiem', 'szefa', 'naczelnym', 'szefie', 'wójta',
                       'wójt', 'komendantem', 'wójtem', 'komendantowi', 'szefowi'],
        'child-female': [],
        'child-male': [],
        'cleaner-female': ['sprzątaczką', 'sprzątaczka', 'czyścicielki', 'czyścicielkę', 'sprzątaczki', 'czyścicielką',
                           'czyścicielka', 'czyścicielko', 'czyścicielce', 'sprzątaczce', 'sprzątaczko', 'sprzątaczkę'],
        'cleaner-male': ['czyścicielem', 'czyścicielowi', 'sprzątaczem', 'sprzątaczowi', 'sprzątacza', 'czyścicielu',
                         'czyściciela', 'czyściciel', 'sprzątaczu', 'sprzątacz'],
        'clerk-female': ['urzędniczkę', 'ekspedientko', 'urzędniczki', 'urzędniczko', 'ekspedientce', 'ekspedientką',
                         'urzędniczką', 'ekspedientki', 'ekspedientkę', 'urzędniczce', 'ekspedientka', 'urzędniczka'],
        'clerk-male': ['kanceliście', 'kancelistą', 'urzędnika', 'ekspedientowi', 'kancelisty', 'kancelista',
                       'ekspedientem', 'urzędnikiem', 'urzędnik', 'ekspedienta', 'urzędniku', 'ekspedient',
                       'ekspediencie', 'urzędnikowi', 'kancelistę', 'kancelisto'],
        'client-female': ['klientko', 'klientką', 'klientce', 'klientka', 'klientkę', 'klientki'],
        'client-male': ['klienta', 'klientem', 'klientowi', 'kliencie', 'klient'],
        'construction worker-female': ['konstruktorko', 'konstruktorce', 'konstruktorki', 'konstruktorka', 'budowlanka',
                                       'budowlanki', 'budowlanko', 'budowlankę', 'konstruktorkę', 'konstruktorką',
                                       'budowlanką', 'budowlance'],
        'construction worker-male': ['budowlaniec', 'konstruktor', 'budowlany', 'budowlańca', 'konstruktorowi',
                                     'konstruktora', 'budowlańcowi', 'budowlanym', 'budowlańcem', 'budowlańcu',
                                     'budowlanemu', 'budowlanego', 'konstruktorem', 'konstruktorze'],
        'cook-female': ['kucharkę', 'kucharki', 'kucharko', 'kucharce', 'kucharką', 'kucharka'],
        'cook-male': ['kucharzowi', 'kucharzu', 'kucharza', 'kucharz', 'kucharzem'],
        'counselor-female': ['panią konsultant', 'konsultantce', 'doradczyni', 'radną', 'konsultantko', 'panią pedagog',
                             'konsultantkę', 'konsultantka', 'wychowawczynię', 'doradczynię', 'pani pedagog',
                             'pani radny', 'radnej', 'wychowawczynią', 'wychowawczyni', 'pani konsultant',
                             'panią radny', 'konsultantki', 'konsultantką', 'radna', 'doradczynią', 'radczynię',
                             'radczynią', 'radczyni'],
        'counselor-male': ['psychologu', 'doradcy', 'radcy', 'radnym', 'konsultantowi', 'radny', 'konsultanta',
                           'pedagogowi', 'radnemu', 'pedagog', 'radcę', 'radnego', 'pedagogu', 'psychologowi',
                           'doradco', 'pedagoga', 'wychowawco', 'psychologiem', 'konsultancie', 'wychowawcę', 'radco',
                           'pedagogiem', 'doradcę', 'wychowawca', 'psychologa', 'konsultant', 'radca', 'wychowawcą',
                           'wychowawcy', 'doradca', 'doradcą', 'psycholog', 'radcą', 'konsultantem'],
        'customer-female': ['klientko', 'klientką', 'klientce', 'klientka', 'klientkę', 'klientki'],
        'customer-male': ['klienta', 'klientem', 'klientowi', 'kliencie', 'klient'],
        'designer-female': ['projektantkę', 'projektantka', 'projektantko', 'projektantki', 'projektantką',
                            'projektantce'],
        'designer-male': ['projektantem', 'projektanta', 'projektancie', 'projektant', 'projektantowi'],
        'developer-female': ['deweloperkę', 'deweloperce', 'deweloperko', 'programistki', 'programistce',
                             'programistko', 'programistką', 'deweloperka', 'programistka', 'deweloperki',
                             'programistkę', 'deweloperką'],
        'developer-male': ['deweloperowi', 'deweloper', 'programiście', 'programista', 'programistą', 'deweloperem',
                           'deweloperze', 'programisty', 'programistę', 'dewelopera', 'programisto'],
        'dietitian-female': ['dietetyczki', 'dietetyczko', 'dietetyczkę', 'dietetyczką', 'dietetyczka', 'pani dietetyk',
                             'dietetyczce', 'panią dietetyk'],
        'dietitian-male': ['dietetykiem', 'dietetyku', 'dietetyk', 'dietetyka', 'dietetykowi'],
        'dispatcher-female': ['dyspozytorce', 'dyspozytorką', 'dyspozytorka', 'dyspozytorko', 'pani dyspozytor',
                              'panią dyspozytor', 'dyspozytorki', 'dyspozytorkę'],
        'dispatcher-male': ['dyspozytora', 'dyspozytor', 'dyspozytorowi', 'dyspozytorem', 'dyspozytorze'],
        'doctor-female': ['doktorki', 'doktorko', 'panią doktor', 'lekarkę', 'lekarką', 'lekarce', 'lekarki',
                          'pani doktor', 'doktorkę', 'doktorce', 'lekarka', 'doktorka', 'lekarko', 'doktorką'],
        'doctor-male': ['lekarzu', 'lekarzowi', 'lekarzem', 'lekarz', 'doktor', 'doktorze', 'doktorem', 'lekarza',
                        'doktorowi', 'doktora'],
        'driver-female': ['pani kierowco', 'pani kierowca', 'panią kierowcę', 'panią kierowcą', 'pani kierowcy'],
        'driver-male': ['kierowco', 'kierowca', 'kierowcę', 'kierowcą', 'kierowcy'],
        'editor-female': ['redaktorkę', 'redaktorką', 'panią redaktor', 'pani redaktor', 'wydawczyni', 'redaktorce',
                          'wydawczynię', 'pani edytor', 'redaktorki', 'redaktorko', 'redaktorka', 'panią edytor',
                          'wydawczynią'],
        'editor-male': ['wydawca', 'redaktorem', 'edytorowi', 'edytorem', 'wydawco', 'redaktorowi', 'edytora',
                        'redaktor', 'wydawcy', 'redaktorze', 'redaktora', 'wydawcą', 'edytor', 'wydawcę', 'edytorze'],
        'educator-female': ['nauczycielka', 'panią edukator', 'wychowawczynią', 'pani edukator', 'wychowawczyni',
                            'nauczycielką', 'nauczycielko', 'nauczycielce', 'wychowawczynię', 'nauczycielkę',
                            'nauczycielki'],
        'educator-male': ['wychowawco', 'nauczycielu', 'nauczycielem', 'nauczyciel', 'edukatorowi', 'wychowawcę',
                          'nauczyciela', 'wychowawca', 'wychowawcy', 'wychowawcą', 'edukator', 'edukatorze',
                          'edukatorem', 'nauczycielowi', 'edukatora'],
        'electrician-female': ['pani elektryk', 'panią elektryk'],
        'electrician-male': ['elektrykowi', 'elektryka', 'elektryku', 'elektrykiem', 'elektryk'],
        'employee-female': ['pracownicę', 'pracownico', 'pracownicy', 'pracownicą', 'pracownica', 'zatrudniona',
                            'zatrudnioną', 'zatrudnionej'],
        'employee-male': ['pracownikiem', 'pracownikowi', 'zatrudnionego', 'zatrudniony', 'pracowniku', 'pracownik',
                          'zatrudnionym', 'pracownika', 'zatrudnionemu'],
        'engineer-female': ['pani inżynier', 'panią inżynier'],
        'engineer-male': ['inżynier', 'inżynierowi', 'inżynierem', 'inżyniera', 'inżynierze'],
        'examiner-female': ['panią egzaminator', 'pani egzaminator', 'badaczką', 'egzaminatorce', 'egzaminatorko',
                            'egzaminatorką', 'egzaminatorki', 'badaczkę', 'badaczki', 'badaczce', 'badaczko',
                            'egzaminatorkę', 'egzaminatorka', 'badaczka'],
        'examiner-male': ['egzaminatorem', 'badaczu', 'badacza', 'badaczem', 'egzaminatorze', 'badacz',
                          'egzaminatorowi', 'egzaminatora', 'badaczowi', 'egzaminator'],
        'farmer-female': ['farmerka', 'farmerką', 'rolniczkę', 'rolniczko', 'farmerkę', 'rolniczka', 'farmerki',
                          'rolniczki', 'rolniczką', 'farmerko', 'rolniczce', 'farmerce'],
        'farmer-male': ['farmer', 'rolnikiem', 'farmera', 'rolnika', 'rolnikowi', 'rolnik', 'farmerze', 'farmerowi',
                        'farmerem', 'rolniku'],
        'firefighter-female': ['panią strażak', 'pani strażak'],
        'firefighter-male': ['strażaku', 'strażaka', 'strażakowi', 'strażakiem', 'strażak'],
        'guard-female': ['gwardzistka', 'strażniczkę', 'gwardzistkę', 'gwardzistce', 'gwardzistko', 'strażniczką',
                         'strażniczki', 'strażniczka', 'gwardzistką', 'gwardzistki', 'strażniczce', 'pani strażnik',
                         'strażniczko', 'panią strażnik'],
        'guard-male': ['gwardzisty', 'strażnikowi', 'gwardzista', 'strażniku', 'strażnikiem', 'strażnik', 'gwardziście',
                       'gwardzistę', 'gwardzisto', 'gwardzistą', 'strażnika'],
        'guest-female': ['pani gość', 'panią gość'],
        'guest-male': ['gość', 'gościa', 'gościowi', 'gościem', 'gościu',],
        'hairdresser-female': ['fryzjerkę', 'fryzjerko', 'fryzjerką', 'fryzjerce', 'fryzjerki', 'fryzjerka'],
        'hairdresser-male': ['fryzjer', 'fryzjerowi', 'fryzjerze', 'fryzjera', 'fryzjerem'],
        'homeowner-female': ['właścicielka', 'właścicielką', 'właścicielko', 'właścicielce', 'właścicielki',
                             'właścicielkę'],
        'homeowner-male': ['właścicielem', 'właściciela', 'właścicielowi', 'właściciel', 'właścicielu'],
        'housekeeper-female': ['gospodynię', 'gosposiu', 'gospodyni', 'gosposią', 'gosposię', 'gospodynią', 'gosposi',
                               'gosposia'],
        'housekeeper-male': ['gospodarz', 'gospodarzem', 'gospodarzu', 'gospodarzowi', 'gospodarza'],
        'hygienist-female': ['higienistka', 'higienistkę', 'higienistki', 'higienistce', 'higienistką', 'higienistko'],
        'hygienist-male': ['higieniście', 'higienistę', 'higienistą', 'higienisty', 'higienista', 'higienisto'],
        'inspector-female': ['inspektorką', 'pani inspektor', 'inspektorce', 'panią inspektor', 'inspektorki',
                             'inspektorka', 'inspektorkę', 'inspektorko'],
        'inspector-male': ['inspektora', 'inspektorze', 'inspektor', 'inspektorowi', 'inspektorem'],
        'instructor-female': ['panią instruktor', 'instruktorki', 'instruktorko', 'instruktorka', 'instruktorką',
                              'pani instruktor', 'instruktorce', 'instruktorkę'],
        'instructor-male': ['instruktorowi', 'instruktorze', 'instruktor', 'instruktorem', 'instruktora'],
        'investigator-female': ['panią śledczy', 'pani śledczy'],
        'investigator-male': ['śledczym', 'śledczy', 'śledczego', 'śledczemu'],
        'janitor-female': ['sprzątaczką', 'woźna', 'dozorczynię', 'sprzątaczka', 'dozorczynią', 'woźną', 'woźnej',
                           'sprzątaczki', 'sprzątaczce', 'sprzątaczko', 'sprzątaczkę', 'dozorczyni'],
        'janitor-male': ['dozorca', 'woźnemu', 'dozorcy', 'dozorcą', 'sprzątaczem', 'dozorcę', 'woźnego', 'woźny',
                         'woźnym', 'dozorco', 'sprzątaczowi', 'sprzątacza', 'sprzątaczu', 'sprzątacz'],
        'laborer-female': ['pracownicę', 'pracownico', 'pracownicy', 'pracownicą', 'robotnicą', 'pracowniczki',
                           'pracowniczka', 'robotnicę', 'robotnica', 'robotnico', 'pracowniczce', 'robotnicy',
                           'pracownica', 'pracowniczką', 'pracowniczkę', 'pracowniczko'],
        'laborer-male': ['robotnika', 'robotniku', 'pracownikiem', 'pracownikowi', 'pracowniku', 'pracownik',
                         'robotnik', 'pracownika', 'robotnikowi', 'robotnikiem'],
        'lawyer-female': ['adwokatką', 'adwokatki', 'pani adwokat', 'prawniczki', 'adwokatkę', 'adwokatka',
                          'panią adwokat', 'prawniczce', 'adwokatce', 'prawniczko', 'adwokatko', 'prawniczka',
                          'prawniczką', 'prawniczkę'],
        'lawyer-male': ['adwokacie', 'adwokatem', 'prawniku', 'prawnika', 'prawnik', 'adwokata', 'adwokat',
                        'adwokatowi', 'prawnikowi', 'prawnikiem'],
        'librarian-female': ['bibliotekarce', 'bibliotekarko', 'bibliotekarki', 'bibliotekarka', 'bibliotekarkę',
                             'bibliotekarką'],
        'librarian-male': ['bibliotekarzem', 'bibliotekarzu', 'bibliotekarz', 'bibliotekarzowi', 'bibliotekarza'],
        'machinist-female': ['maszynistki', 'maszynistką', 'maszynistka', 'maszynistko', 'maszynistce', 'maszynistkę'],
        'machinist-male': ['maszynisto', 'maszyniście', 'maszynisty', 'maszynistą', 'maszynistę', 'maszynista'],
        'manager-female': ['menadżerce', 'panią menadżer', 'kierowniczce', 'kierowniczkę', 'menedżerko',
                           'pani dyrektor', 'pani kierownik', 'kierowniczki', 'pani menedżer', 'panią kierownik',
                           'kierowniczko', 'menadżerkę', 'kierowniczka', 'kierowniczką', 'menadżerką', 'dyrektorka',
                           'menadżerki', 'menadżerko', 'dyrektorką', 'menedżerkę', 'dyrektorkę', 'dyrektorki',
                           'dyrektorce', 'panią dyrektor', 'dyrektorko', 'panią menedżer', 'pani menadżer',
                           'menedżerki', 'menedżerka', 'menedżerce', 'menadżerka', 'menedżerką'],
        'manager-male': ['kierownikowi', 'dyrektorowi', 'dyrektor', 'menadżerowi', 'menedżer', 'menedżera',
                         'dyrektorem', 'menedżerze', 'dyrektora', 'menadżer', 'kierownikiem', 'menedżerowi',
                         'dyrektorze', 'menedżerem', 'kierownika', 'kierownik', 'kierowniku', 'menadżera', 'menadżerem',
                         'menadżerze'],
        'mechanic-female': ['panią mechanik', 'pani mechanik'],
        'mechanic-male': ['mechanikiem', 'mechaniku', 'mechanika', 'mechanik', 'mechanikowi'],
        'mover-female': [],
        'mover-male': [],
        'nurse-female': ['pielęgniarką', 'pielęgniarki', 'pielęgniarka', 'pielęgniarko', 'pielęgniarkę',
                         'pielęgniarce'],
        'nurse-male': ['pielęgniarza', 'pielęgniarzu', 'pielęgniarzem', 'pielęgniarzowi', 'pielęgniarz'],
        'nutritionist-female': ['dietetyczki', 'dietetyczko', 'dietetyczkę', 'dietetyczką', 'dietetyczka',
                                'pani dietetyk', 'dietetyczce', 'panią dietetyk'],
        'nutritionist-male': ['dietetykiem', 'dietetyku', 'dietetyk', 'dietetyka', 'dietetykowi'],
        'officer-female': ['policjantkę', 'oficerko', 'policjantki', 'oficerki', 'panią policjant', 'pani policjant',
                           'funkcjonariuszce', 'funkcjonariuszką', 'funkcjonariuszkę', 'oficerką', 'policjantką',
                           'pani oficer', 'oficerkę', 'policjantce', 'oficerka', 'funkcjonariuszki', 'oficerce',
                           'policjantko', 'policjantka', 'panią oficer', 'funkcjonariuszko', 'funkcjonariuszka'],
        'officer-male': ['policjanta', 'policjantem', 'policjantowi', 'funkcjonariuszu', 'funkcjonariuszem', 'oficer',
                         'funkcjonariuszowi', 'policjant', 'oficerem', 'oficera', 'oficerowi', 'oficerze',
                         'policjancie', 'funkcjonariusz', 'funkcjonariusza'],
        'onlooker-female': ['obserwatorkę', 'obserwatorko', 'obserwatorką', 'obserwatorka', 'obserwatorki',
                            'obserwatorce'],
        'onlooker-male': ['obserwatorze', 'obserwatorowi', 'obserwatora', 'obserwatorem', 'obserwator'],
        'owner-female': ['właścicielka', 'właścicielką', 'właścicielko', 'właścicielce', 'właścicielki',
                         'właścicielkę'],
        'owner-male': ['właścicielem', 'właściciela', 'właścicielowi', 'właściciel', 'właścicielu'],
        'painter-female': ['malarki', 'malarka', 'malarką', 'malarko', 'malarkę', 'malarce'],
        'painter-male': ['malarza', 'malarzem', 'malarzu', 'malarz', 'malarzowi'],
        'paralegal-female': ['paralegalistka', 'paralegalistki', 'paralegalistce', 'paralegalistkę', 'paralegalistką',
                             'paralegalistko', 'adwokatka', 'adwokatki', 'adwokatce', 'adwokatkę', 'adwokatką', 'adwokatko',
                             'pani adwokat', 'panią adwokat', 'prawniczka', 'prawniczki', 'prawniczce', 'prawniczkę',
                             'prawniczką', 'prawniczko'],
        'paralegal-male': ['paralegalista', 'paralegalisty', 'paralegaliście', 'paralegalistę', 'paralegalistą',
                           'paralegalisto', 'adwokat', 'adwokata', 'adwokatowi', 'adwokatem', 'adwokacie',
                           'prawnik', 'prawniku', 'prawnikowi', 'prawnikiem'],
        'paramedic-female': ['sanitariuszką', 'sanitariuszko', 'ratowniczkę', 'ratowniczko', 'ratowniczce',
                             'sanitariuszkę', 'sanitariuszka', 'ratowniczką', 'ratowniczki', 'ratowniczka',
                             'sanitariuszce', 'sanitariuszki'],
        'paramedic-male': ['ratownikowi', 'ratownika', 'sanitariuszu', 'ratownik', 'sanitariusza', 'ratowniku',
                           'sanitariusz', 'sanitariuszem', 'sanitariuszowi', 'ratownikiem'],
        'passenger-female': ['pasażerkę', 'pasażerko', 'pasażerka', 'pasażerki', 'pasażerce', 'pasażerką'],
        'passenger-male': ['pasażera', 'pasażer', 'pasażerze', 'pasażerem', 'pasażerowi'],
        'pathologist-female': ['panią patolog', 'pani patolog'],
        'pathologist-male': ['patologowi', 'patologiem', 'patolog', 'patologu', 'patologa'],
        'patient-female': ['pacjentka', 'pacjentkę', 'pacjentko', 'pacjentki', 'pacjentką', 'pacjentce'],
        'patient-male': ['pacjentowi', 'pacjenta', 'pacjent', 'pacjentem', 'pacjencie'],
        'pedestrian-female': ['piesza', 'pieszą', 'pieszej'],
        'pedestrian-male': ['pieszemu', 'pieszego', 'pieszym', 'pieszy'],
        'pharmacist-female': ['aptekarką', 'farmaceutką', 'farmaceutka', 'aptekarka', 'farmaceutko', 'aptekarkę',
                              'farmaceutki', 'aptekarko', 'farmaceutce', 'aptekarki', 'aptekarce', 'farmaceutkę',
                              'panią farmaceutą', 'panią farmaceucie', 'pani farmaceuto', 'panią farmaceutę',
                              'pani farmaceuta', 'pani farmaceuty'],
        'pharmacist-male': ['farmaceutą', 'aptekarz', 'aptekarzu', 'farmaceucie', 'aptekarzem', 'farmaceuto',
                            'farmaceutę', 'farmaceuta', 'farmaceuty', 'aptekarza', 'aptekarzowi'],
        'physician-female': ['lekarka', 'lekarkę', 'lekarko', 'lekarką', 'lekarce', 'lekarki'],
        'physician-male': ['lekarzu', 'lekarzowi', 'lekarza', 'lekarzem', 'lekarz'],
        'planner-female': ['planistko', 'planistkę', 'planistce', 'planistką', 'planistki', 'planistka'],
        'planner-male': ['planistę', 'planistą', 'planista', 'planisto', 'planisty', 'planiście'],
        'plumber-female': ['pani hydraulik', 'panią hydraulik'],
        'plumber-male': ['hydrauliku', 'hydraulik', 'hydraulikiem', 'hydraulika', 'hydraulikowi'],
        'practitioner-female': ['praktykantkę', 'praktykantko', 'praktykująca', 'praktykującą', 'praktykantce',
                                'praktykantką', 'praktykującej', 'praktykantka', 'praktykantki'],
        'practitioner-male': ['praktykującego', 'praktykanta', 'praktykującym', 'praktykantem', 'praktykancie',
                              'praktykantowi', 'praktykant', 'praktykujący', 'praktykującemu'],
        'programmer-female': ['programistka', 'programistkę', 'programistki', 'programistce', 'programistko',
                              'programistką'],
        'programmer-male': ['programistę', 'programiście', 'programista', 'programistą', 'programisty', 'programisto'],
        'protester-female': ['demonstrantka', 'demonstrantkę', 'demonstrantko', 'demonstrantce', 'demonstrantką',
                             'demonstrantki'],
        'protester-male': ['demonstranta', 'demonstrantowi', 'demonstrantem', 'demonstrancie', 'demonstrant'],
        'psychologist-female': ['psycholożko', 'psycholożką', 'psycholożce', 'psycholożka', 'pani psycholog',
                                'psycholożki', 'panią psycholog', 'psycholożkę'],
        'psychologist-male': ['psychologu', 'psychologiem', 'psycholog', 'psychologa', 'psychologowi'],
        'receptionist-female': ['recepcjonistko', 'recepcjonistkę', 'recepcjonistką', 'recepcjonistki',
                                'recepcjonistce', 'recepcjonistka'],
        'receptionist-male': ['recepcjonisty', 'recepcjonista', 'recepcjonisto', 'recepcjonistę', 'recepcjoniście',
                              'recepcjonistą'],
        'resident-female': ['rezydentce', 'pani rezydent', 'rezydentką', 'mieszkankę', 'mieszkanką', 'rezydentkę',
                            'rezydentki', 'panią rezydent', 'mieszkanko', 'rezydentko', 'rezydentka', 'mieszkance',
                            'mieszkanki', 'mieszkanka'],
        'resident-male': ['rezydenta', 'mieszkańcowi', 'rezydencie', 'rezydentowi', 'mieszkańcu', 'mieszkańcem',
                          'rezydent', 'mieszkaniec', 'mieszkańca', 'rezydentem'],
        'salesperson-female': ['ekspedientko', 'ekspedientce', 'ekspedientką', 'sprzedawczynię', 'ekspedientki',
                               'ekspedientkę', 'sprzedawczynią', 'sprzedawczyni', 'ekspedientka'],
        'salesperson-male': ['sprzedawcę', 'ekspedientowi', 'sprzedawco', 'ekspedientem', 'sprzedawcy', 'ekspedienta',
                             'sprzedawcą', 'ekspedient', 'ekspediencie', 'sprzedawca'],
        'scientist-female': ['pani naukowiec', 'panią naukowiec'],
        'scientist-male': ['naukowcze', 'naukowcu', 'naukowca', 'naukowiec', 'naukowcowi', 'naukowcem'],
        'secretary-female': ['sekretarko', 'sekretarką', 'sekretarka', 'panią sekretarz', 'pani sekretarz',
                             'sekretarce', 'sekretarki', 'sekretarkę'],
        'secretary-male': ['sekretarz', 'sekretarzowi', 'sekretarzu', 'sekretarzem', 'sekretarza'],
        'sheriff-female': ['pani szeryf', 'panią szeryf'],
        'sheriff-male': ['szeryfem', 'szeryf', 'szeryfowi', 'szeryfa', 'szeryfu', 'szeryfie'],
        'someone-female': [],
        'someone-male': [],
        'specialist-female': ['specjalistkę', 'specjalistka', 'specjalistki', 'specjalistko', 'specjalistce',
                              'specjalistką'],
        'specialist-male': ['specjalista', 'specjalistę', 'specjalistą', 'specjalisto', 'specjalisty', 'specjaliście'],
        'student-female': ['uczennicę', 'uczennico', 'studentki', 'studentka', 'uczennicy', 'uczennica', 'uczennicą',
                           'studentką', 'studentko', 'studentce', 'studentkę'],
        'student-male': ['uczniem', 'studentowi', 'studentem', 'ucznia', 'uczniu', 'uczeń', 'studencie', 'uczniowi',
                         'student', 'studenta'],
        'supervisor-female': ['opiekunce', 'opiekunkę', 'przełożona', 'nadzorczyni', 'przełożonej', 'opiekunko',
                              'opiekunką', 'opiekunki', 'nadzorczynią', 'nadzorczynię', 'przełożoną', 'opiekunka'],
        'supervisor-male': ['nadzorcy', 'przełożonym', 'opiekunem', 'opiekun', 'opiekuna', 'nadzorcę', 'przełożony',
                            'przełożonemu', 'nadzorca', 'nadzorco', 'przełożonego', 'opiekunie', 'nadzorcą',
                            'opiekunowi'],
        'surgeon-female': ['pani chirurg', 'panią chirurg'],
        'surgeon-male': ['chirurgiem', 'chirurga', 'chirurg', 'chirurgowi', 'chirurgu'],
        'tailor-female': ['krawcowej', 'krawcowa', 'krawcową', 'krawcowo'],
        'tailor-male': ['krawiec', 'krawcem', 'krawca', 'krawcu', 'krawcze', 'krawcowi'],
        'taxpayer-female': ['panią podatnik', 'pani podatnik'],
        'taxpayer-male': ['podatniku', 'podatnikowi', 'podatnik', 'podatnika', 'podatnikiem'],
        'teacher-female': ['nauczycielce', 'nauczycielka', 'nauczycielką', 'nauczycielko', 'nauczycielkę',
                           'nauczycielki'],
        'teacher-male': ['nauczycielu', 'nauczycielem', 'nauczyciel', 'nauczyciela', 'nauczycielowi'],
        'technician-female': ['techniczkę', 'techniczka', 'techniczce', 'panią technik', 'techniczki', 'techniczką',
                              'techniczko', 'pani technik'],
        'technician-male': ['technikiem', 'technika', 'technik', 'techniku', 'technikowi'],
        'teenager-female': ['nastolatko', 'nastolatki', 'nastolatkę', 'nastolatce', 'nastolatką', 'nastolatka'],
        'teenager-male': ['nastolatkowi', 'nastolatkiem', 'nastolatku', 'nastolatek', 'nastolatka'],
        'therapist-female': ['terapeutce', 'terapeutko', 'terapeutka', 'terapeutkę', 'terapeutki', 'terapeutką'],
        'therapist-male': ['terapeuta', 'terapeucie', 'terapeuty', 'terapeutę', 'terapeuto', 'terapeutą'],
        'undergraduate-female': ['absolwentki', 'licealistkę', 'absolwentką', 'licealistko', 'maturzystce',
                                 'absolwentkę', 'absolwentko', 'studentki', 'maturzystki', 'absolwentka', 'licealistką',
                                 'studentką', 'maturzystkę', 'studentce', 'absolwentce', 'licealistki', 'studentkę',
                                 'maturzystką', 'licealistce', 'studentka', 'studentko', 'maturzystko', 'maturzystka',
                                 'licealistka'],
        'undergraduate-male': ['licencjata', 'studentowi', 'absolwentem', 'studentem', 'maturzysty', 'licealistą',
                               'maturzystą', 'maturzyście', 'maturzysta', 'licencjatu', 'maturzysto', 'licealista',
                               'licencjat', 'absolwentowi', 'maturzystę', 'licealisto', 'licencjatowi', 'studencie',
                               'absolwent', 'licencjatem', 'absolwenta', 'student', 'licealistę', 'studenta',
                               'licealiście', 'licencjacie', 'absolwencie', 'licealisty'],
        'veterinarian-female': ['pani weterynarz', 'panią weterynarz'],
        'veterinarian-male': ['weterynarza', 'weterynarz', 'weterynarzem', 'weterynarzowi', 'weterynarzu'],
        'victim-female': ['pokrzywdzonej', 'pokrzywdzona', 'poszkodowana', 'poszkodowaną', 'pokrzywdzoną',
                          'poszkodowanej'],
        'victim-male': ['pokrzywdzony', 'poszkodowanemu', 'pokrzywdzonemu', 'pokrzywdzonego', 'poszkodowany',
                        'poszkodowanego', 'pokrzywdzonym', 'poszkodowanym'],
        'visitor-female': ['przybyszce', 'przybyszkę', 'przybyszko', 'przybyszką', 'przybyszka', 'przybyszki'],
        'visitor-male': ['przybysz', 'przybyszu', 'przybysza', 'przybyszowi', 'przybyszem'],
        'witness-female': ['pani świadek', 'panią świadek'],
        'witness-male': ['świadek', 'świadka', 'świadkowi', 'świadkiem', 'świadku'],
        'worker-female': ['pracownicę', 'pracownico', 'pracownicy', 'pracownicą', 'pracownica'],
        'worker-male': ['pracownikiem', 'pracownika', 'pracownikowi', 'pracowniku', 'pracownik'],
        'writer-female': ['pisarce', 'pisarką', 'pisarki', 'pisarko', 'pisarka', 'pisarkę'],
        'writer-male': ['pisarz', 'pisarzu', 'pisarzem', 'pisarza', 'pisarzowi']
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
