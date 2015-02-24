#!/usr/bin/env python
import sys

from client import get_github3_client

if __name__ == '__main__':
    gh = get_github3_client()

    # Divvy up into repositories that need/do not need a CONTRIBUTING file.
    good_repos = []
    bad_repos = []

    repos = gh.organization('mozilla').iter_repos(type='sources')
    for repo in repos:
        # All files in this repo's default branch.
        # {'filename.md': Content(), 'filename2.txt': Contents(), ...}
        files = repo.contents('/')

        if files:
            contrib_files = [f for f in files.keys() if
                             f.startswith('CONTRIBUTING')]
        else:
            contrib_files = None

        if contrib_files:
            good_repos.append(repo.name)
        else:
            bad_repos.append(repo.name)

        sys.stderr.write('.')

    good_repos.sort()
    print
    print 'The following repos HAVE a CONTRIBUTING file:'
    for r in good_repos:
        print r

    bad_repos.sort()
    print
    print
    print 'The following repos DO NOT HAVE a CONTRIBUTING file:'
    for r in bad_repos:
        print r
