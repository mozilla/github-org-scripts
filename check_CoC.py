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


def indent(spaces=4, iterable=None):
    return [" " * spaces + x for x in iterable]


class CoCRepo:
    """
        Has all thebusiness logic
    """
    def __init__(self, repo):
        self.repo = repo
        self.of_interest = False
        self.has_a_coc = False
        self.coc_is_correct = False
        self.plan = []
        self.ignore_reasons = []
        self._update_state()

    def _update_state(self):
        self.of_interest = self._do_we_care()
        if self.of_interest:
            self.has_a_coc = self._find_coc()
        if self.has_a_coc:
            self.coc_is_correct = self._examine_coc()

    def _examine_coc(self):
        """
        read the coc file to see if it meets criteria

        First pass, just check if correct URL exists.
        """
        # TODO: check for url in contents
        return True

    def _find_coc(self):
        # TODO: cache contents of file
        # TODO: really check for file in root.
        # get default branch, then that branches info, which contains the head commit sha, then tree @ sha
        branch_name = self.repo.default_branch
        branch = self.repo.branches(branch_name)
        sha = branch.commit.sha
        tree = self.repo.tree(sha)
        # search tree for case insensitive path of code of conduct.
        xxx
        return False

    def _do_we_care(self):
        ignore_reasons = []
        if self.repo.archived:
            ignore_reasons.append("Repo is archived")
        if self.repo.private:
            ignore_reasons.append("Repo is private")
        if self.repo.fork:
            ignore_reasons.append("Repo is a fork")
        self.ignore_reasons = ignore_reasons

        return len(ignore_reasons) == 0

    def plan_actions(self):
        """
            Figure out what needs to be done
        """
        plan = []
        if not self.of_interest:
            plan.append("Out of scope because:")
            plan.extend(indent(4, self.ignore_reasons))
        elif not self.has_a_coc:
            plan.append("Create missing CoC issue")
            plan.append("Create PR for boilerplate CoC")
        elif not self.coc_is_correct:
            plan.append("Create incorrect CoC issue")
        else:
            plan.append("Everything already correct")
        self.plan = plan

    def show_plan(self):
        """
            Return an array of steps
        """
        return self.plan


class GitHubSession:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.gh = get_github3_client()

    def _process_repo(self, repo):
        repo_stats = CoCRepo(repo)
        repo_stats.plan_actions()
        print("Plan for {}:".format(repo.full_name))
        print('\n'.join(indent(4, repo_stats.show_plan())))
        if not self.dry_run:
            repo_stats.execute_plan()

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
