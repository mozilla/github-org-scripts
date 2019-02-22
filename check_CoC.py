#!/usr/bin/env python

"""
    Check every repo for proper presence of a code_of_conduct file.abs

    If not found, create an Issue, and open a PR

"""
# TODO: add rate limiting
# TODO: add action code to issue, so can be found later (instead of opening
#       another)

from __future__ import print_function

import argparse
import collections
import logging

from client import get_github3_client

# additional help text
_epilog = """
"""

COC_FILENAME = "CODE_OF_CONDUCT.md"
COC_MASTER_URL = "https://www.mozilla.org/about/governance/policies/participation/"
COC_REPORTING_URL = (
    "https://www.mozilla.org/about/governance/policies/participation/reporting/"
)

logger = logging.getLogger(__name__)


def indent(spaces=4, iterable=None):
    return [" " * spaces + x for x in iterable]


# Each action has a unique messgage and description string. Tie them together
Action = collections.namedtuple("Action", "code summary title body")

actions = [
    Action(
        "COC001",
        "Create missing CoC issue",
        "CODE_OF_CONDUCT.md file missing",
        """
As of January 1 2019, Mozilla requires that all Github projects include this [CODE_OF_CONDUCT.md](https://github.com/mozilla/repo-templates/blob/master/templates/CODE_OF_CONDUCT.md) file in the project root. The file has two parts:

1. Required Text - All text under the headings *Community Participation Guidelines and How to Report*, are required, and should not be altered.
2. Optional Text - The Project Specific Etiquette heading provides a space to speak more specifically about ways people can work effectively and inclusively together. Some examples of those can be found on the [Firefox Debugger](https://github.com/devtools-html/debugger.html/blob/master/CODE_OF_CONDUCT.md) project, and [Common Voice](https://github.com/mozilla/voice-web/blob/master/CODE_OF_CONDUCT.md). (The optional part is commented out in the [raw template file](https://raw.githubusercontent.com/mozilla/repo-templates/blob/master/templates/CODE_OF_CONDUCT.md), and will not be visible until you modify and uncomment that part.)

If you have any questions about this file, or Code of Conduct policies and procedures, please reach out to Emma Irwin (eirwin *AT* mozilla *DOT* com).""",
    ),
    Action(
        "COC002", "Create PR for boilerplate CoC", "Add CODE_OF_CONDUCT.md file", ""
    ),
    Action(
        "COC003",
        "Create incorrect CoC issue",
        "CODE_OF_CONDUCT.md isn't correct",
        """
**Your required text does not appear to be correct**

As of January 1 2019, Mozilla requires that all Github projects include this [CODE_OF_CONDUCT.md](https://github.com/mozilla/repo-templates/blob/master/templates/CODE_OF_CONDUCT.md) file in the project root. The file has two parts:

1. Required Text - All text under the headings *Community Participation Guidelines and How to Report*, are required, and should not be altered.
2. Optional Text - The Project Specific Etiquette heading provides a space to speak more specifically about ways people can work effectively and inclusively together. Some examples of those can be found on the [Firefox Debugger](https://github.com/devtools-html/debugger.html/blob/master/CODE_OF_CONDUCT.md) project, and [Common Voice](https://github.com/mozilla/voice-web/blob/master/CODE_OF_CONDUCT.md). (The optional part is commented out in the [raw template file](https://raw.githubusercontent.com/mozilla/repo-templates/blob/master/templates/CODE_OF_CONDUCT.md), and will not be visible until you modify and uncomment that part.)

If you have any questions about this file, or Code of Conduct policies and procedures, please reach out to Emma Irwin (eirwin *AT* mozilla *DOT* com).""",
    ),
    Action("COC004", "Everything already correct", "", ""),
]


class CoCRepo:
    """
        Has all thebusiness logic
    """

    def __init__(self, repo):
        self.repo = repo
        self.of_interest = False
        self.has_a_coc = False
        self.coc_is_correct = False
        self.coc_text = ""
        self.plan = []
        self.actions = []
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

        First pass, just check if correct URLs exists.
        """
        has_urls = (COC_MASTER_URL in self.coc_text) and (
            COC_REPORTING_URL in self.coc_text
        )
        return has_urls

    def _find_coc(self):
        # if anything goes wrong here, it's an empty repo or branch
        try:
            branch_name = self.repo.default_branch
            branch = self.repo.branch(branch_name)
            sha = branch.commit.sha
            tree = self.repo.tree(sha)
        except Exception:
            self.of_interest = False
            self.ignore_reasons.append("Repo's default branch is degenerate.")
            found = False
        else:
            # search tree for case sensitive path of code of conduct.
            found = False
            for hash in tree.tree:
                if hash.type == "blob" and hash.path == COC_FILENAME:
                    found = True
                    # Cache contents of file while we can easily do so
                    blob = self.repo.blob(hash.sha)
                    text = blob.decoded
                    self.coc_text = text
                    break
        return found

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

    def _add_action(self, summary):
        for a in actions:
            if a.summary == summary:
                self.actions.append(a)
                break
        else:
            logger.error("No action for %s", summary)
        return summary

    def _open_issue(self, action):
        title = action.title
        body = action.body
        issue = self.repo.create_issue(title, body)
        self.issue_number = issue.number
        extra_text = " #{} ({})".format(issue.number, issue.html_url)
        return extra_text

    def _open_pr(self, action):
        # TODO: make this work
        logger.error("Don't know how to open PR")
        return ""

    def _no_op(self, action):
        return ""

    def _dispatch(self, action):
        extra_text = ""
        if action.code in ("COC001", "COC003"):
            extra_text = self._open_issue(action)
        elif action.code in ("COC002"):
            extra_text = self._open_pr(action)
        elif action.code in ("COC004"):
            extra_text = self._no_op(action)
        else:
            logger.error("unexpected action %s", action)
        return extra_text

    def plan_actions(self):
        """
            Figure out what needs to be done
        """
        plan = []
        if not self.of_interest:
            plan.append("Out of scope because:")
            plan.extend(indent(4, self.ignore_reasons))
        elif not self.has_a_coc:
            plan.append(self._add_action("Create missing CoC issue"))
            plan.append(self._add_action("Create PR for boilerplate CoC"))
        elif not self.coc_is_correct:
            plan.append(self._add_action("Create incorrect CoC issue"))
        else:
            plan.append(self._add_action("Everything already correct"))
        self.plan = plan

    def show_plan(self):
        """
            Return an array of steps
        """
        return self.plan

    def execute_plan(self):
        print("Plan for {}:".format(self.repo.full_name))
        no_actions = True
        for a in self.actions:
            extra_text = self._dispatch(a)
            print(indent(4, [a.summary + extra_text])[0])
            no_actions = False
        if no_actions:
            print("\n".join(indent(4, self.show_plan())))


class GitHubSession:
    def __init__(self, live=True):
        self.live = live
        self.gh = get_github3_client()

    def _process_repo(self, repo):
        repo_stats = CoCRepo(repo)
        repo_stats.plan_actions()
        if self.live:
            repo_stats.execute_plan()
        else:
            print("Plan for {}:".format(repo.full_name))
            print("\n".join(indent(4, repo_stats.show_plan())))

    def process_repo(self, repo):
        owner, repo_name = repo.split("/", 1)
        r = self.gh.repository(owner=owner, repository=repo_name)
        self._process_repo(r)

    def process_org(self, org):
        o = self.gh.organization(org)
        for repo in o.repositories():
            self._process_repo(repo)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, epilog=_epilog)
    parser.add_argument("--live", action="store_true", help="Actually make changes.")
    parser.add_argument(
        "targets", nargs="+", help="github organizations or org/repos to check"
    )
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    gh = GitHubSession(args.live)
    for target in args.targets:
        if "/" in target:
            gh.process_repo(target)
        else:
            gh.process_org(target)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN, format="%(asctime)s %(message)s")
    main()
