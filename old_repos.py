#!/usr/bin/env python
import json
import os
import re
from datetime import datetime, timedelta

import requests

from client import get_token

CACHEFILE = 'cache/mozilla_all_repos.json'

if __name__ == '__main__':
    headers = {
        'Accept': 'application/vnd.github.moondragon+json',
        'Authorization': 'token %s' % get_token()
    }

    if os.path.exists(CACHEFILE):
        repos = json.loads(open(CACHEFILE, 'r').read())
        print ('Found cached repository list. Delete %s if you want a new '
               'one.\n' % CACHEFILE)

    else:
        repos = []
        repos_api = 'https://api.github.com/orgs/%s/repos' % 'mozilla'
        while True:
            resp = requests.get(repos_api, headers=headers)
            repos += resp.json()

            # Next page.
            next_match = re.search(r'<([^>]+)>; rel="next"',
                                   resp.headers['Link'])
            if not next_match:
                break
            else:
                repos_api = next_match.group(1)

        open(CACHEFILE, 'w').write(json.dumps(repos))

    # Find small/empty repos.
    small_repos = filter(lambda r: r['size'] < 50, repos)
    small_repos.sort(key=lambda r: r['name'])
    print '## %s small/empty repositories' % len(small_repos)
    for repo in small_repos:
        print repo['name'], ':', repo['size']

    print '\n\n'

    # Find recently untouched repos.
    YEARS = 2
    old_repos = filter(lambda r: (
        datetime.strptime(r['updated_at'], '%Y-%m-%dT%H:%M:%SZ') +
        timedelta(days=(365 * YEARS)) < datetime.now()), repos)
    old_repos.sort(key=lambda r: r['name'])
    print '## %s repos touched less recently than %s years ago.' % (
        len(old_repos), YEARS)
    for repo in old_repos:
        print repo['name'], ':', repo['updated_at']
