#!/usr/bin/env python
import urllib
import argparse
import logging

import requests

from client import get_token

logger = logging.getLogger(__name__)

def get_user_email(user_login, headers):
    user_url = 'https://api.github.com/users/%s' % user_login
    resp = requests.get(user_url, headers=headers)
    user_info = resp.json()
    email = user_info.get('email', '') or "no public email address"
    return email

def check_admins(org):
    headers = {
        # New API requires new accept per
        # https://developer.github.com/changes/2015-06-24-api-enhancements-for-working-with-organization-permissions/#preview-period
        'Accept': 'application/vnd.github.ironman-preview+json',
        'Authorization': 'token %s' % get_token()
    }
    params = {'filter': '2fa_disabled',
              'role': 'admin'}

    admins_with_1fa_url = '%s?%s' % (
        'https://api.github.com/orgs/%s/members' % org,
        urllib.urlencode(params)
    )
    resp = requests.get(admins_with_1fa_url, headers=headers)
    if resp.status_code not in (200,):
        logging.warn("Failed request for %s (code %d)", org,
                     resp.status_code)
        return

    real_admins = resp.json()

    if real_admins:
        print 'The following admins DO NOT HAVE 2FA for org %s:' % org
        for a in real_admins:
            print a['login'], get_user_email(a['login'], headers)
    else:
        print 'Congrats! All admins have 2FA enabled in %s!' % org


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("orgs", nargs='*', default=['mozilla', ],
                        help='github organizations to check (defaults to mozilla)')
    return parser.parse_args()


def main():
    args = parse_args()
    for org in args.orgs:
        check_admins(org)


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN, format='%(asctime)s %(message)s')
    main()
