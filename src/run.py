import json
from datetime import datetime

from rhpy import Rhpy

conf_file = './config.json'
with open(conf_file, 'r') as f:
    conf = json.load(f)
    username = conf['username']
    password = conf['password']


rhpy = Rhpy(username, password, headless=False)
rhpy.login()
# rhpy.submit('tt', datetime.datetime.strptime('01/10/2022', '%d/%m/%Y'),
#            datetime.datetime.strptime('02/10/2022', '%d/%m/%Y'))

#print(rhpy.balance())
#rhpy.team_status(as_of=datetime.strptime('09/09/2022', '%d/%m/%Y'))

rhpy.balance()