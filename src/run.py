import datetime
import json

from rhpy import Rhpy

conf_file = './config.json'
with open(conf_file, 'r') as f:
    conf = json.load(f)
    username = conf['username']
    password = conf['password']


rhpy = Rhpy(username, password, headless=True)
rhpy.login()
# rhpy.submit('cp', datetime.datetime.strptime('28/10/2022', '%d/%m/%Y'),
#             datetime.datetime.strptime('31/10/2022', '%d/%m/%Y'))

print("Balance", rhpy.balance())
#rhpy.team_status(as_of=datetime.strptime('09/09/2022', '%d/%m/%Y'))

#print(rhpy.team_planning())
#print(rhpy.my_planning())
rhpy.validate()
rhpy.team_status()
