import sys
import json
import os
from rhpy import Rhpy

conf_file = './config.json'

prog = os.path.basename(sys.argv[0])
try:
    action = sys.argv[1]
except IndexError:
    print(f"usage: {prog} <login|add|balance|status|validate>")
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
    type = sys.argv[2]
    if type not in ['off', 'cp', 'ho', 'jr']:
        raise ValueError(f"unknown type {type}")
    rhpy = Rhpy(username, password)
    rhpy.login()
    # TODO
    pass

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

print("unknown action")
exit(1)


