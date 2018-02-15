
from datetime import datetime
import time

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


def sleep_if_rate_limited(gh, verbose=False):
    rates = gh.rate_limit()

    if not rates['resources']['search']['remaining']:
        reset_epoch = rates['resources']['search']['reset']

        reset_dt, now = datetime.utcfromtimestamp(reset_epoch), datetime.utcnow()

        if reset_dt > now:
            sleep_secs = (reset_dt - now).seconds + 1

            if verbose:
                print('sleeping for', sleep_secs, 'got rate limit', rates['resources']['search'])

            time.sleep(sleep_secs)
