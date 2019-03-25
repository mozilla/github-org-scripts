#!/usr/bin/env python

"""
    Check every repo for proper presence of a code_of_conduct file.abs

    If not found, create an Issue, and open a PR

"""
# TODO: add rate limiting

from __future__ import print_function

import argparse
import base64
import binascii
import collections
import hashlib
import logging
import requests
import time

from client import get_github3_client
import github3

# additional help text
_epilog = """
"""

APPROVED_ACCOUNT = "mozilla-github-standards"
COC_FILENAME = "CODE_OF_CONDUCT.md"
COC_CONTENTS_URL = "https://github.com/mozilla/repo-templates/raw/master/templates/CODE_OF_CONDUCT.md"
COC_MASTER_URL = "https://www.mozilla.org/about/governance/policies/participation/"
COC_REPORTING_URL = (
    "https://www.mozilla.org/about/governance/policies/participation/reporting/"
)
COC_COMMIT_MESSAGE = """
Add Mozilla Code of Conduct file

Fixes #{}.
""".strip()

logger = logging.getLogger(__name__)
gh = None

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
As of January 1 2019, Mozilla requires that all GitHub projects include this [CODE_OF_CONDUCT.md](https://github.com/mozilla/repo-templates/blob/master/templates/CODE_OF_CONDUCT.md) file in the project root. The file has two parts:

1. Required Text - All text under the headings *Community Participation Guidelines and How to Report*, are required, and should not be altered.
2. Optional Text - The Project Specific Etiquette heading provides a space to speak more specifically about ways people can work effectively and inclusively together. Some examples of those can be found on the [Firefox Debugger](https://github.com/devtools-html/debugger.html/blob/master/CODE_OF_CONDUCT.md) project, and [Common Voice](https://github.com/mozilla/voice-web/blob/master/CODE_OF_CONDUCT.md). (The optional part is commented out in the [raw template file](https://raw.githubusercontent.com/mozilla/repo-templates/blob/master/templates/CODE_OF_CONDUCT.md), and will not be visible until you modify and uncomment that part.)

If you have any questions about this file, or Code of Conduct policies and procedures, please reach out to Mozilla-GitHub-Standards+CoC@mozilla.com.""",
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

As of January 1 2019, Mozilla requires that all GitHub projects include this [CODE_OF_CONDUCT.md](https://github.com/mozilla/repo-templates/blob/master/templates/CODE_OF_CONDUCT.md) file in the project root. The file has two parts:

1. Required Text - All text under the headings *Community Participation Guidelines and How to Report*, are required, and should not be altered.
2. Optional Text - The Project Specific Etiquette heading provides a space to speak more specifically about ways people can work effectively and inclusively together. Some examples of those can be found on the [Firefox Debugger](https://github.com/devtools-html/debugger.html/blob/master/CODE_OF_CONDUCT.md) project, and [Common Voice](https://github.com/mozilla/voice-web/blob/master/CODE_OF_CONDUCT.md). (The optional part is commented out in the [raw template file](https://raw.githubusercontent.com/mozilla/repo-templates/blob/master/templates/CODE_OF_CONDUCT.md), and will not be visible until you modify and uncomment that part.)

If you have any questions about this file, or Code of Conduct policies and procedures, please reach out to Mozilla-GitHub-Standards+CoC@mozilla.com.""",
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
        self.fork_repo = None
        self.already_handled = False
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
        if len(ignore_reasons) == 0:
            # check for already handled (no nagging yet)
            # TODO: we should recheck if incorrect & close, or open PR
            #       if missing and no open PR.
            # NOTE: since pr linked to issue, close of issue closes PR
            my_login = gh.me().login
            for issue in self.repo.issues(state="open"):
                if issue.user.login == my_login:
                    ignore_reasons.append("Already has issue/pr opened")
                    break
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
        body = action.body + "\n\n_(Message {})_".format(action.code)
        issue = self.repo.create_issue(title, body)
        self.issue_number = issue.number
        extra_text = " #{} ({})".format(issue.number, issue.html_url)
        return extra_text

    def _get_fork(self):
        """
        Return forked repo, creating if needed

        For the forked repo name, we hash the full name of the upstream
        repo. This avoids duplicate names of upstream repos. We can't
        "undo" the hash, but GitHub stores that in the fork's metadata.
        """
        if not self.fork_repo:
            #   Corner case - same upstream repo name (append user?) (Change name
            #   to hash of org/repo (to avoid length restrictions))
            fork_hash = hashlib.pbkdf2_hmac('sha256', self.repo.full_name.lower(), b'salt', 100000)
            fork_name = binascii.hexlify(fork_hash)
            my_login = gh.me().login
            try:
                fork_repo = gh.repository(my_login, fork_name)
            except github3.exceptions.NotFoundError:
                fork_repo = None
            if not fork_repo:
                fork_repo = self.repo.create_fork()
                if not fork_repo.edit(name=fork_name):
                    logger.error("Failed to rename fork %s to %s", self.repo.name, fork_name)
            self.fork_repo = fork_repo
        return self.fork_repo

    def _create_commit(self, action):
        """
            Add the CoC file to the repo.
        """
        # Keep the commit simple.
        commit_message = COC_COMMIT_MESSAGE.format(self.issue_number) + "\n\n_(Message {})_".format(action.code)
        success = False
        try:
            self.fork_repo.create_file(COC_FILENAME, commit_message, self.new_contents)
            success = True
        except github3.exceptions.UnprocessableEntity:
            logger.warning("Likely file already in %s", self.fork_repo.full_name)
        except github3.exceptions.GitHubException:
            logger.warning("Likely fork hasn't completed for %s", self.fork_repo.full_name)
        return success

    def _open_pr(self, action):
        # steps:
        #   Check for forked repo, fork if not
        fork_repo = self._get_fork()
        #   Check for existing PR (may be closed, but not merged)
        #   Create commit
        success = self._create_commit(action)
        self.pr_success = success
        #   (re)Open PR
        if not success:
            # TODO: assume fork not finished, and queue this for retry
            msg = "Failed to commit file to {}".format(self.fork_repo.html_url)
            RetryQueue.add_retry(self, action)
        else:
            repo = self.repo
            repo.refresh()  # upgrade from short repository to get default branch
            pr = repo.create_pull("Add Mozilla Code of Conduct",
                    repo.default_branch or "master",
                    "{}:{}".format(self.fork_repo.owner,
                        self.fork_repo.default_branch or "master"),
                        "Fixes #{}\n\n_(Message {})_".format(self.issue_number, action.code))
            msg = " Created PR #{} ({})".format(pr.number, pr.html_url)
            
        return msg

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

    def execute_plan(self, contents=None):
        # cache contents in case needed.
        self.new_contents = contents
        print("Plan for {}:".format(self.repo.full_name))
        no_actions = True
        for a in self.actions:
            extra_text = self._dispatch(a)
            print(indent(4, [a.summary + extra_text])[0])
            no_actions = False
        if no_actions:
            print("\n".join(indent(4, self.show_plan())))


Retriable = collections.namedtuple("Retriable", "repo action max_retries last_time")
class RetryQueue:
    _queue = []

    @classmethod
    def add_retry(cls, repo, action, max_retries=5):
        """
        add an action to retry on repo later
        """
        retriable = Retriable(repo, action, max_retries, int(time.time()))
        cls._queue.append(retriable)

    @classmethod
    def retry_waiting(cls):
        """
        Walk queue, retry each call

        If still not successful, return member to queue
        """
        needs_retry = cls._queue
        # this is an ugly implementation, cls._queue will be refilled :(
        cls._queue = []
        retry = 0
        while needs_retry:
            retry += 1
            remaining = needs_retry
            needs_retry = []
            for r in remaining:
                now = time.time()
                not_before = r["last_time"] + 5 * retry
                if not_before > now:
                    nap_seconds = int(not_before - now) + 1
                    logger.info("waiting {} before retry".format(nap_seconds))
                    time.sleep(nap_seconds)
                msg = repo._dispatch(r.action)
                action = r.action.description
                full_name = r.repo.repo.full_name
                number = r.repo.issue_number
                if not repo.pr_success:
                    # still not ready
                    if retry < r["max_retries"]:
                        needs_retry.append(r)
                    else:
                        # put back on retry list, since not finished
                        needs_retry.append(r)
                        logger.warning("Giving up on {} for issue {} in {}".format(action, nummber, full_name))
                else:
                    logger.info("Succeeded on {} for issue {} in {}".format(action, nummber, full_name))

class GitHubSession:
    def __init__(self, live=True):
        self.live = live
        self.new_contents = ""
        self.gh = get_github3_client()
        global gh
        gh = self.gh
        my_login = gh.me().login
        approved_login = my_login.lower() == APPROVED_ACCOUNT.lower()
        if not approved_login:
            logger.warning("Unapproved user {}, no changes allowed.".format(my_login))
            # don't allow changes
            if live:
                raise SystemExit("Terminating update run. User unapproved")
        if live:
            # Cache the CoC file
            r = requests.get(COC_CONTENTS_URL)
            self.new_contents = r.content
        

    def _process_repo(self, repo):
        repo_stats = CoCRepo(repo)
        repo_stats.plan_actions()
        if self.live:
            repo_stats.execute_plan(self.new_contents)
        else:
            print("Plan for {}:".format(repo.full_name))
            print("\n".join(indent(4, repo_stats.show_plan())))

    def process_repo(self, full_name):
        owner, repo_name = full_name.split("/", 1)
        r = self.gh.repository(owner=owner, repository=repo_name)
        if r:
            self._process_repo(r)
        else:
            logger.error("No such repo %s", full_name)

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
    # process any retry queue entries
    RetryQueue.retry_waiting()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN, format="%(asctime)s %(message)s")
    main()
