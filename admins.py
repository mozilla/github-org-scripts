#!/usr/bin/env python
import urllib

import requests

from client import get_token, get_github3_client

if __name__ == '__main__':
    # only using this for members_urlt
    gh = get_github3_client()

    # the rest is raw requests.get
    headers = {
        'Accept': 'application/vnd.github.moondragon+json',
        'Authorization': 'token %s' % get_token()
    }
    params = {'filter': '2fa_disabled',
              'role': 'admin'}

    admins_with_1fa_url = '%s?%s' % (
        gh.organization('mozilla').members_urlt.expand(),
        urllib.urlencode(params)
    )
    resp = requests.get(admins_with_1fa_url, headers=headers)

    bad_admins = resp.json()
    print 'The following admins DO NOT HAVE 2FA:'
    for a in bad_admins:
        print a.username
