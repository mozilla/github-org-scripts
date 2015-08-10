#!/usr/bin/env python
import urllib

import requests

from client import get_token

if __name__ == '__main__':
    headers = {
        # new api requires new accept per
        # https://developer.github.com/changes/2015-06-24-api-enhancements-for-working-with-organization-permissions/#preview-period
        'Accept': 'application/vnd.github.ironman-preview+json',
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

    # for orgs that don't yet support the new API, the 'role' filter is
    # not honored. Filter those out by checking the 'site_admin' key.
    real_admins = [x for x in bad_admins if x['site_admin']]
    if real_admins:
        print 'The following admins DO NOT HAVE 2FA:'
        for a in real_admins:
            print a['login']
    else:
        print 'Congrats! All admins have 2FA enabled!'
