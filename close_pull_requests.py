#!/usr/bin/env python
"""
    Close PRs on repositories where the master is not on github.

    Provide a closing comment, and print the lock URL if desired
"""

import argparse
import logging
import yaml

from client import get_github3_client

DEFAULT_MESSAGE = 'We do not use Pull Requests on this repo. Please see ' \
                  'CONTRIBUTING or ReadMe file.'
DEFAULT_CONFIG = 'close_pull_requests.yaml'

logger = logging.getLogger(__name__)
exit_code = 0


def update_exit_code(new_code):
    """ Update global exit_code, following rules.

        Current rule is only update if the new value signifies a
        "more severe" error (higher integer value)
    """
    global exit_code
    exit_code = max(exit_code, new_code)


def close_prs(gh, organization=None, repository=None,
              message=None, lock=False, close=False):
    if message is None:
        message = DEFAULT_MESSAGE
    try:
        repo = gh.repository(organization, repository)
        logger.debug("Checking for PRs in %s", repo.name)
        for pr in repo.pull_requests(state='open'):
            logger.debug("Examining PR %s for %s/%s", pr.number,
                            organization, repository)
            if close:
                pr.create_comment(message)
                pr.close()
                logger.info("Closed PR %s for %s/%s", pr.number,
                            organization, repository)
                if lock:
                    print("Lock PR manually: "
                            "https://github.com/%s/%s/pull/%s" %
                            (organization, repository, pr.number))
            else:
                print("PR %s open for %s/%s at: "
                        "https://github.com/%s/%s/pull/%s" % (pr.number,
                                                            organization,
                                                            repository,
                                                            organization,
                                                            repository,
                                                            pr.number))
        else:
            logger.debug("no open PR's in %s!", repo.name)
    except AttributeError:
        logger.error("No access to repository %s/%s", organization, repository)
        update_exit_code(1)


def close_configured_prs(gh, config_file, dry_run=False):
    config = []
    with open(config_file, 'rb') as yaml_file:
        config = yaml.safe_load(yaml_file)
    for repository in config:
        if dry_run:
            repository['lock'] = False
            repository['close'] = False
        close_prs(gh, **repository)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', help="org/repo to use instead of config")
    parser.add_argument('--message', help="comment to add (default '%s')" %
                        DEFAULT_MESSAGE, default=None)
    parser.add_argument('--close', action='store_true', help="Close PR")
    parser.add_argument('--lock', action='store_true', help="Lock PR")
    parser.add_argument('--debug', help="include github3 output",
                        action='store_true')
    parser.add_argument('--config', help="read configs for projects (default "
                        "'%s')" % DEFAULT_CONFIG, default=DEFAULT_CONFIG)
    parser.add_argument('--dry-run', action='store_true',
                        help='Just show, regardless of config')
    return parser.parse_args()


def main():
    args = parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger('github3').setLevel(logging.DEBUG)
    gh = get_github3_client()
    me = gh.me()
    logger.debug("I'm %s (%s)", me.name, me.login)
    if args.only:
        org, repo = args.only.split('/')
        close_prs(gh, organization=org, repository=repo, close=args.close,
                  lock=args.lock, message=args.message)
    else:
        close_configured_prs(gh, args.config, args.dry_run)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    logging.getLogger('github3').setLevel(logging.ERROR)
    main()
    raise SystemExit(exit_code)
