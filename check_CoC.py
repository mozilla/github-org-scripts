#!/usr/bin/env python
"""
    Check every repo for proper presence of a code_of_conduct file.abs

    If not found, create an Issue, and open a PR
"""
from __future__ import print_function

import argparse
import logging

from client import get_github3_client

# additional help text
_epilog = """
"""

logger = logging.getLogger(__name__)


class GitHubSession:
    def __init__(self):
        self.gh = get_github3_client()

    def _process_repo(self, repo):
        print(repo.full_name)

    def process_repo(self, repo):
        owner, repo_name = repo.split('/', 1)
        r = self.gh.repository(owner=owner, repository=repo_name)
        self._process_repo(r)

    def process_org(self, org):
        o = self.gh.organization(org)
        for repo in o.repositories():
            self._process_repo(repo)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, epilog=_epilog)
    parser.add_argument('--dry-run', action='store_true',
                        help='Only show what would be done.')
    parser.add_argument("targets", nargs='+',
                        help='github organizations or org/repos to check')
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    gh = GitHubSession()
    for target in args.targets:
        if '/' in target:
            gh.process_repo(target)
        else:
            gh.process_org(target)


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN, format='%(asctime)s %(message)s')
    main()
