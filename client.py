from github3 import login


CREDENTIALS_FILE = '.credentials'


def get_token():
    id = token = ''
    with open(CREDENTIALS_FILE, 'r') as cf:
        id = cf.readline().strip()
        token = cf.readline().strip()
    return token


def get_github3_client():
    token = get_token()
    gh = login(token=token)
    return gh
