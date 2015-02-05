#!/usr/bin/env python
import urllib

import requests

from client import get_token

if __name__ == '__main__':
    headers = {
        'Accept': 'application/vnd.github.sersi-preview+json',
        'Authorization': 'token %s' % get_token()
    }
    params = {}

    org_hooks_url = '%s?%s' % (
        'https://api.github.com/orgs/%s/hooks' % 'mozilla',
        urllib.urlencode(params)
    )
    resp = requests.get(org_hooks_url, headers=headers)

    hooks = resp.json()
    for hook in hooks:
        print hook['config']['url']
