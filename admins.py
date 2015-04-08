#!/usr/bin/env python
import urllib

import requests

from client import get_token

if __name__ == '__main__':
    headers = {
        'Accept': 'application/vnd.github.moondragon+json',
        'Authorization': 'token %s' % get_token()
    }
    params = {'filter': '2fa_disabled',
              'role': 'admin'}

    admins_with_1fa_url = '%s?%s' % (
        'https://api.github.com/orgs/%s/members' % 'mozilla',
        urllib.urlencode(params)
    )
    resp = requests.get(admins_with_1fa_url, headers=headers)

    bad_admins = resp.json()
    print 'The following admins DO NOT HAVE 2FA:'
    for a in bad_admins:
        print a['login']
