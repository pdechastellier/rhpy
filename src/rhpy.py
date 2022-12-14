import ssl
import urllib.request
import urllib.error
from datetime import datetime
from datetime import timedelta
import re

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class Rhpy:
    def __init__(self, username, password, headless=True):
        self.username = username
        self.password = password

        self._role = 'unknown'  # manager / employee
        self._logged = False

        self.TIMEOUT = 15
        self.base_url = 'https://cegid-rhpo-vpn.cegid.com/webplace/ceg.jsp'

        if not self._check_vpn(self.base_url):
            raise Exception('No connection. check VPN')

        options = webdriver.ChromeOptions()
        options.add_argument('no-sandbox')
        options.add_argument("--disable-dev-shm-usage")
        options.headless = headless

        # disable imgs to save bandwidth
        chrome_prefs = dict()
        chrome_prefs["profile.default_content_settings"] = {"images": 2}
        chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}
        options.experimental_options["prefs"] = chrome_prefs

        self.driver = webdriver.Chrome(options=options)

    @staticmethod
    def _check_vpn(url):
        myssl = ssl.create_default_context()
        myssl.check_hostname = False
        myssl.verify_mode = ssl.CERT_NONE
        try:
            r = urllib.request.urlopen(url, timeout=3, context=myssl).read()
        except urllib.error.URLError:
            return False
        return r is not None

    def login(self):
        # ## Login page and credentials
        self.driver.get(self.base_url)
        elmt = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located((By.ID, "usr")))
        elmt.send_keys(self.username)
        self.driver.find_element(By.ID, "pwd").send_keys(self.password)
        self.driver.find_element(By.XPATH,
                                 '//input[@value="Connexion"]').click()

        # Welcome page - check top right menu item is present
        try:
            WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located((By.ID, "user_closed")))
        except TimeoutException:
            raise ValueError('bad username or password')
        self._logged = True

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, role):
        if not self._logged:
            raise ConnectionError('Not connected')

        if role == self.role:
            return

        if role == 'manager':
            link_text = "Responsable"
        elif role == 'employee':
            link_text = "Salari??"
        else:
            raise ValueError("Unknown role ", role)

        elmt = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located((By.ID, "user_closed")))
        elmt.click()
        self.driver.find_element(By.LINK_TEXT, link_text).click()

        # verify role is ok
        elmt = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="entete"]/div[2]/div[3]/div[2]/div[1]/span[2]')))
        if (elmt.text == 'Salari??' and role == 'employee') or (elmt.text == 'Responsable' and role == 'manager'):
            self._role = role
        else:
            raise ValueError("cannot change profile")

    def _goto_menu(self, tree):
        # FIXME: blocked sometimes
        if len(tree) != 3:
            raise ValueError('need exactly 3 levels', tree)

        # navigate top left menu using 3 element ID
        WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.presence_of_element_located((By.ID, tree[0]))).click()
        WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.element_to_be_clickable((By.ID, tree[1]))).click()
        WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.element_to_be_clickable((By.ID, tree[2]))).click()

    def submit(self, type, start, end, dry_run=False):
        # TODO: annule 'tt' si pose de conges sur meme periode
        self.role = 'employee'

        # poser des conges - ouverture du menu
        self._goto_menu(("menuAfficher", "e_ACT_COLL_CEGID", "ACT_COLL_CEGID_WAB010RB_RSP"))

        # selection de population
        elmt = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located(
            (By.XPATH, '//input[@value="Appliquer"]')))  # (By.CSS_SELECTOR, "input:nth-child(5)")
        elmt.click()

        # selection du 1er contrat
        elmt = WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody > tr.ligne_impaire > td:nth-child(1) > a")))
        elmt.click()

        # ajout d'un conges
        elmt = WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, '//input[@value="Ajouter"]')))
        elmt.click()

        # parametres du conges
        elmt = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located((By.NAME, "cdmtf")))
        if type == 'cp':
            elmt.find_element(By.XPATH, "//option[. = 'Cong??s pay??s']").click()
        elif type == 'jr':
            elmt.find_element(By.XPATH, "//option[. = 'Jour de repos (Forfait jour)']").click()
        elif type == 'tt':
            elmt.find_element(By.XPATH, "//option[. = 'T??l??travail']").click()
        else:
            raise ValueError("Unknown type ", type)

        self.driver.find_element(By.ID, "dtdeb").send_keys(start.strftime("%d/%m/%Y"))  # "29/03/2022"
        self.driver.find_element(By.ID, "dtfin").send_keys(end.strftime("%d/%m/%Y"))  # "29/03/2022"
        self.driver.find_element(By.XPATH,
                                 '//input[@value="Continuer"]').click()

        # enregistrement final
        if dry_run:
            return
        # TODO: wait less if chevauchement
        try:
            WebDriverWait(self.driver, self.TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "button_attacher"))).click()
            alert = self.driver.switch_to.alert
            if alert.text in (
                    'Merci de v??rifier que vous avez bien respect?? le nombre de jours maximum ?? poser sur la semaine.',
            ):
                alert.accept()
            else:
                alert.accept()
                raise ValueError(alert.text)
        except TimeoutException:
            # Erreur type "Chevauchement avec un ??v??nement de m??me nature"
            # "Chevauchement avec la demande de T??l??travail du 13/10/2022 au 18/10/2022"
            # "Dur??e de l'absence est ??gale ?? 0"
            elmt = WebDriverWait(self.driver, self.TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "div_errors")))
            msg = elmt.text.replace('Fermer', '').strip()
            self.driver.find_element(By.CSS_SELECTOR, "#div_errors button").click()
            raise ValueError(msg)

    def balance(self):
        self.role = 'employee'

        # ouverture du menu - recapitulatif soldes
        self._goto_menu(("menuAfficher", "e_ACT_COLL_CEGID", "ACT_COLL_CEGID_WAB050RB"))

        # selection de population
        elmt = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located(
            (By.XPATH, '//input[@value="Appliquer"]')))
        elmt.click()

        # selection du 1er contrat
        WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody > tr.ligne_impaire > td:nth-child(1)"))).click()

        # lecture du tableau periode en cours et suivance
        table = WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="contenu"]/table/tbody/tr/td[1]/fieldset/table')))
        balance = self._process_balance_table(table)

        table_next = WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="contenu"]/table/tbody/tr/td[2]/fieldset/table')))
        balance_next = self._process_balance_table(table_next)

        for type, bal in balance_next.items():
            if type in balance:
                balance[type] = balance[type] + bal
                # YAGNI what if type exists in next period but not in current period

        return balance

    def _process_balance_table(self, table):
        balance = dict()
        for row in table.find_elements(By.XPATH, './/tr[@class="ligne_impaire" or @class="ligne_paire"]'):
            type = row.find_element(By.XPATH, './/td[1]').text
            acquired = float(row.find_element(By.XPATH, './/td[2]').text.replace(',', '.'))
            taken = float(row.find_element(By.XPATH, './/td[4]').text.replace(',', '.'))

            if acquired == 0 and taken == 0:
                continue
            balance[self._clean_type(type)] = acquired - taken
        return balance

    def validate(self):
        # TODO: traiter les demandes d'annulation d'absences (2eme onglet)
        self.role = 'manager'

        # ouverture du menu - traiter les demandes d'absences
        self._goto_menu(("menuAfficher", "e_ACTIVITE_MAN", "ACTIVITE_MAN_WAB024RB"))

        # selection des demandes
        remaining = -1
        while remaining != 0:
            try:
                # TODO: wait less if nothing to validate
                #  https://stackoverflow.com/questions/36579812/is-it-possible-to-have-a-fluentwait-wait-for-two-conditions

                WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located(
                    (By.XPATH, '//input[@value="Traiter"]')))
                rows = self.driver.find_elements(By.XPATH,
                           '//*[@id="traitement"]/div/table/tbody/tr[@class="ligne_impaire" or @class="ligne_paire"]')
                remaining = len(rows)
                if remaining == 0:
                    return None
                else:
                    self._validate_page(rows)
            except TimeoutException:
                msg = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located(
                    (By.XPATH, '/html/body/div[3]'))).text
                if "Aucune demande d'absence" in msg:
                    return None
                else:
                    raise TimeoutException()

    def _validate_page(self, rows):
        for row in rows:
            name, surname = self._clean_name(row.find_element(By.XPATH, './td[5]').text)
            type = self._clean_type(row.find_element(By.XPATH, './td[6]').text)
            start = datetime.strptime(row.find_element(By.XPATH, './td[7]').text, '%d/%m/%Y')
            end = datetime.strptime(row.find_element(By.XPATH, './td[9]').text, '%d/%m/%Y')
            if type != 'tt':
                duration = (end - start).days + 1
                print(f'{surname}: {type} validated for {duration} day{"s" if duration > 1 else ""} starting on {start.strftime("%a %d %b")}')
            row.find_element(By.XPATH, './/input').click()

        # validation
        btn = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located(
            (By.XPATH, '//input[@value="Traiter"]')))
        btn.click()
        alert = self.driver.switch_to.alert
        alert.accept()
        return len(rows)

    def my_planning(self):
        # TODO: get more than 4 weeks for submit_recurring_tt()
        return self.team_planning(role='employee')

    def team_planning(self, role='manager'):
        self.role = role

        # ouverture du menu - planning des absences
        if role == 'manager':
            self._goto_menu(("menuAfficher", "e_ACTIVITE_MAN", "ACTIVITE_MAN_WPL010RB"))
        else:
            self._goto_menu(("menuAfficher", "e_ACT_COLL_CEGID", "ACT_COLL_CEGID_WPL010RB"))

        # selection de population
        elmt = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located(
            (By.XPATH, '//input[@value="Appliquer"]')))
        elmt.click()

        # ajout planning du manager
        if role == 'manager':
            elmt = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located(
                (By.XPATH, '//input[@value="Rechercher"]')))
            self.driver.find_element(By.NAME, "aff_manager").click()
            elmt.click()

        # lecture des utilisateurs
        WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located(
            (By.XPATH, '//input[@value="Rechercher"]')))
        names = []
        for name_cell in self.driver.find_elements(By.CSS_SELECTOR, "#divg > table:nth-child(2) > tbody > tr > td"):
            names.append(name_cell.text)

        periods = set()
        row_nb = 0
        # lecture des conges
        for row in self.driver.find_elements(By.CSS_SELECTOR, "#divd > table:nth-child(2) > tbody > tr"):
            for col in row.find_elements(By.XPATH, './/td[@title[not(.="")]]'):
                periods.add(self._parse_planning_str(names[row_nb], col.get_attribute('title')))
            row_nb += 1

        return periods

    @staticmethod
    def _clean_type(str):
        if 'Cong??s pay??s' in str:
            return 'cp'
        elif 'Cong??s Pay??s' in str:
            return 'cp'
        elif 'T??l??travail' in str:
            return 'tt'
        elif 'Jour de repos' in str:
            return 'jr'
        elif 'Jours de repos' in str:
            return 'jr'
        elif 'Maladie' in str:
            return 'ma'
        elif 'Cong?? sans solde' in str:
            return 'ss'
        else:
            raise ValueError('unknown type for ', str)

    @staticmethod
    def _parse_planning_str(username, str):
        # Cong??s pay??s du 07/09/2022 au 19/09/2022   -> ('John Doe', 'cp', datetime(07/09/2022), datetime(19/09/2022) )

        type = Rhpy._clean_type(str)

        patternp = re.compile(r'.* du (\d{2}/\d{2}/\d{4}) au (\d{2}/\d{2}/\d{4})$')
        patternj = re.compile(r'.* le (\d{2}/\d{2}/\d{4})$')
        m = patternp.match(str)
        if m is not None:
            return (username, type,
                    datetime.strptime(m.group(1), '%d/%m/%Y'),
                    datetime.strptime(m.group(2), '%d/%m/%Y'))
        m = patternj.match(str)
        if m is not None:
            return (username, type,
                    datetime.strptime(m.group(1), '%d/%m/%Y'),
                    datetime.strptime(m.group(1), '%d/%m/%Y'))
        raise ValueError('cannot get date ', str)

    @staticmethod
    def _clean_name(str):
        # 'DOE John'          -> ('DOE', 'John')
        str = re.sub(r' \([0-9]+\)', '', str)
        return re.match(r'(^[A-Z ]+) (.*)$', str).groups()

    def team_status(self, as_of=datetime.today()):
        planning = self.team_planning()
        for period in planning:
            name, surname = self._clean_name(period[0])
            if period[1] == 'tt':
                continue
            if period[3] < as_of:
                # Event ended in the past
                continue
            duration = (period[3] - period[2]).days + 1
            if period[2] <= as_of and period[3] >= datetime.today():
                print(f'{surname} is off today until {period[3].strftime("%a %d %b")}')
            elif period[2] - as_of <= timedelta(days=2):
                print(f'{surname} is off tomorrow for {duration} day{"s" if duration > 1 else ""}')
            elif period[2] - as_of <= timedelta(days=10) and duration >= 5:
                print(f'{surname} will be off soon on {period[2].strftime("%a %d %b")} for {duration} days')
            else:
                pass
        # TODO: print something if all is clean

    def submit_recurring_tt(self, until=datetime.today() + timedelta(days=60)):
        """set monday and tuesday at homeoffice each week
        from the first week without homeoffice already submitted
        for the next 60 days or until the optional date parameter"""
        # check existing tt - no more than 3 weeks in the future
        leaves = self.my_planning()
        cursor = datetime.today()
        for leave in leaves:
            if leave[1] != 'tt':
                continue
            cursor = max(cursor, leave[3])
        cursor = cursor + timedelta(days=(7 - cursor.weekday()) % 7)  # move to the following monday
        print(f'pos cursor at {cursor.strftime("%a %d %b")}')
        while cursor < until:
            cursor = cursor + timedelta(days=7)
            print(f'added homeoffice for week of {cursor.strftime("%a %d %b")} ')
            self.submit('tt', cursor, cursor + timedelta(days=1))

    def submit_travel_receipt(self):
        # TODO: https://www.tutorialspoint.com/how-to-upload-file-with-selenium-python#
        pass