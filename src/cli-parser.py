import datetime
import sys
import json
import os
from rhpy import Rhpy


conf_file = './config.json'

prog = os.path.basename(sys.argv[0])
try:
    action = sys.argv[1]
except IndexError:
    print(f"usage: {prog} <login|add|balance|status|validate|tt>")
    exit(1)


def store_credentials(username, password):
    with open(conf_file, 'w') as f:
        conf = dict()
        conf['username'] = username
        conf['password'] = password
        json.dump(conf, f)


def get_credentials():
    with open(conf_file, 'r') as f:
        conf = json.load(f)
        return conf['username'], conf['password']


if action == 'login':
    if len(sys.argv) != 4:
        print(f"usage: {prog} login <username> <password>")
        exit(1)
    username = sys.argv[2]
    password = sys.argv[3]
    store_credentials(username, password)
    exit(0)

try:
    username, password = get_credentials()
except Exception:
    raise ValueError(f"add credentials first: {prog} login <username> <password>")


if action == 'add':
    """submit a new vacation request
    params:
        type: off, cp, ho, jr
        start: start date as dd/mm/yy (ex: 13/10/22 for Nov 13th, 2022)
        end: end date as dd/mm/yy
    """
    if len(sys.argv) != 5:
        print(f"usage: {prog} add <type> <start> <end>")
        exit(1)
    type = sys.argv[2]
    if type not in ['cp', 'ho', 'jr']:
        raise ValueError(f"unknown type {type}")
    start = datetime.datetime.strptime(sys.argv[3], '%d/%m/%y')
    end = datetime.datetime.strptime(sys.argv[4], '%d/%m/%y')
    rhpy = Rhpy(username, password)
    rhpy.login()
    rhpy.submit(type, start, end)
    exit(0)

if action == 'balance':
    rhpy = Rhpy(username, password)
    rhpy.login()
    b = rhpy.balance()
    print(b)
    exit(0)

if action == 'validate':
    rhpy = Rhpy(username, password)
    rhpy.login()
    rhpy.validate()
    exit(0)

if action == 'status':
    rhpy = Rhpy(username, password)
    rhpy.login()
    rhpy.team_status()
    exit(0)

if action == 'tt':
    rhpy = Rhpy(username, password)
    rhpy.login()
    rhpy.submit_recurring_tt()
    exit(0)

print("unknown action")
exit(1)


