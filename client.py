from github3 import login


CREDENTIALS_FILE = '.credentials'


def get_github_client():
    id = token = ''
    with open(CREDENTIALS_FILE, 'r') as cf:
        id = cf.readline().strip()
        token = cf.readline().strip()

    gh = login(token=token)
    return gh
