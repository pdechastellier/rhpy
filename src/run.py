from datetime import datetime

from rhpy import Rhpy

username = 'pdechastellier'
password = 'vobziN-piqbyx-2bobfy'

rhpy = Rhpy(username, password, headless=False)
rhpy.login()
# rhpy.submit('tt', datetime.datetime.strptime('01/10/2022', '%d/%m/%Y'),
#            datetime.datetime.strptime('02/10/2022', '%d/%m/%Y'))

#print(rhpy.balance())
#rhpy.team_status(as_of=datetime.strptime('09/09/2022', '%d/%m/%Y'))

rhpy.balance()