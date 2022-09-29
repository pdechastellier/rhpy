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
        # TODO: disable imgs to save the planet
        # chrome_prefs = dict()
        # chrome_prefs["profile.default_content_settings"] = {"images": 2}
        # chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}
        # options.experimental_options["prefs"] = chrome_prefs
        self.driver = webdriver.Chrome(options=options)

    def _check_vpn(self, url):
        myssl = ssl.create_default_context();
        myssl.check_hostname = False
        myssl.verify_mode = ssl.CERT_NONE
        try:
            r = urllib.request.urlopen(url, timeout=3, context=myssl).read()
        except urllib.error.URLError:
            return False
        return r != None

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
            link_text = "Salarié"
        else:
            raise ValueError("Unknown role ", role)

        elmt = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located((By.ID, "user_closed")))
        elmt.click()
        self.driver.find_element(By.LINK_TEXT, link_text).click()
        # TODO: verify role is ok
        elmt = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="entete"]/div[2]/div[3]/div[2]/div[1]/span[2]')))
        if (elmt.text == 'Salarié' and role == 'employee') or  (elmt.text == 'Responsable' and role == 'manager'):
            self._role = role
        else:
            raise ValueError("cannot change profile")

    def submit(self, type, start, end):
        self.role = 'employee'

        # poser des conges - ouverture du menu
        elmt = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located((By.ID, "menuAfficher")))
        elmt.click()
        WebDriverWait(self.driver, self.TIMEOUT).until(EC.element_to_be_clickable((By.ID, "e_ACT_COLL_CEGID"))).click()
        WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.element_to_be_clickable((By.ID, "ACT_COLL_CEGID_WAB010RB_RSP"))).click()

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
            elmt.find_element(By.XPATH, "//option[. = 'Congés payés']").click()
        elif type == 'jr':
            elmt.find_element(By.XPATH, "//option[. = 'Jour de repos (Forfait jour)']").click()
        elif type == 'tt':
            elmt.find_element(By.XPATH, "//option[. = 'Télétravail']").click()
        else:
            raise ValueError("Unknown type ", type)

        self.driver.find_element(By.ID, "dtdeb").send_keys(start.strftime("%d/%m/%Y"))  # "29/03/2022"
        self.driver.find_element(By.ID, "dtfin").send_keys(end.strftime("%d/%m/%Y"))  # "29/03/2022"
        self.driver.find_element(By.XPATH,
                                 '//input[@value="Continuer"]').click()  # By.CSS_SELECTOR, "div > input:nth-child(3)"

        # enregistrement final
        try:
            elmt = WebDriverWait(self.driver, self.TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "button_attacher"))).click()
            alert = self.driver.switch_to.alert
            if alert.text in (
            'Merci de vérifier que vous avez bien respecté le nombre de jours maximum à poser sur la semaine.',
            ):
                # alert.accept()
                pass
            else:
                # alert.accept()
                raise ValueError(alert.text)
        except TimeoutException:
            # Erreur type "Chevauchement avec un événement de même nature"
            elmt = WebDriverWait(self.driver, self.TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "div_errors")))
            msg = elmt.text.replace('Fermer', '').strip()
            self.driver.find_element(By.CSS_SELECTOR, "#div_errors button").click()
            raise ValueError(msg)

    def balance(self):
        self.role = 'employee'

        # ouverture du menu - recapitulatif soldes
        elmt = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located((By.ID, "menuAfficher")))
        elmt.click()
        WebDriverWait(self.driver, self.TIMEOUT).until(EC.element_to_be_clickable((By.ID, "e_ACT_COLL_CEGID"))).click()
        WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.element_to_be_clickable((By.ID, "ACT_COLL_CEGID_WAB050RB"))).click()

        # selection de population
        elmt = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located(
            (By.XPATH, '//input[@value="Appliquer"]')))
        elmt.click()

        # lecture du 1er contrat
        elmt = WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody > tr.ligne_impaire > td:nth-child(6) > span")))
        balance = dict()
        balance['cp'] = float(elmt.text.replace(',', '.'))
        elmt = self.driver.find_element(By.CSS_SELECTOR, "tbody > tr.ligne_impaire > td:nth-child(8) > span")
        balance['jr'] = float(elmt.text.replace(',', '.'))

        return balance

    def validate(self):
        self.role = 'manager'

        # ouverture du menu - traiter les demandes d'absences
        elmt = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located((By.ID, "menuAfficher")))
        elmt.click()
        WebDriverWait(self.driver, self.TIMEOUT).until(EC.element_to_be_clickable((By.ID, "e_ACTIVITE_MAN"))).click()
        WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.element_to_be_clickable((By.ID, "ACTIVITE_MAN_WAB024RB"))).click()


        # selection des demandes
        remaining = -1
        while remaining != 0:
            try:
                # TODO: wait less longer if nothing to validate.
                btn = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located(
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
            duration = (end - start).days
            print(f'{surname} on {type} for {duration} days starting on {start.strftime("%a %d %b")}')
            row.find_element(By.XPATH, './/input').click()

        # validation
        btn = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located(
            (By.XPATH, '//input[@value="Traiter"]')))
        btn.click()g
        alert = self.driver.switch_to.alert
        alert.accept()
        return len(rows)

    def team_planning(self):
        self.role = 'manager'

        # ouverture du menu - planning des absences
        elmt = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located((By.ID, "menuAfficher")))
        elmt.click()
        WebDriverWait(self.driver, self.TIMEOUT).until(EC.element_to_be_clickable((By.ID, "e_ACTIVITE_MAN"))).click()
        WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.element_to_be_clickable((By.ID, "ACTIVITE_MAN_WPL010RB"))).click()

        # selection de population
        elmt = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located(
            (By.XPATH, '//input[@value="Appliquer"]')))
        elmt.click()

        # ajout planning du manager
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

        return(periods)

    @staticmethod
    def _clean_type(str):
        if 'Congés payés' in str:
            return 'cp'
        elif 'Télétravail' in str:
            return 'tt'
        elif 'Jour de repos' in str:
            return 'jr'
        elif 'Jours de repos' in str:
            return 'jr'
        elif 'Maladie' in str:
            return 'ma'
        elif 'Congé sans solde' in str:
            return 'ss'
        else:
            raise ValueError('unknown type for ', str)

    @staticmethod
    def _parse_planning_str(username, str):
        # Congés payés du 07/09/2022 au 19/09/2022   -> ('John Doe', 'cp', datetime(07/09/2022), datetime(19/09/2022) )

        type = Rhpy._clean_type(str)

        patternp = re.compile(r'.* du (\d{2}\/\d{2}\/\d{4}) au (\d{2}\/\d{2}\/\d{4})$')
        patternj = re.compile(r'.* le (\d{2}\/\d{2}\/\d{4})$')
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
        str = re.sub(' \([0-9]+\)', '', str)
        return re.match('(^[A-Z ]+) (.*)$', str).groups()

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
                print(f'{surname} is off tomorrow for {duration} days')
            elif period[2] - as_of <= timedelta(days=10) and duration >= 5:
                print(f'{surname} will be off soon on {period[2].strftime("%a %d %b")} for {duration} days')
            else:
                pass
