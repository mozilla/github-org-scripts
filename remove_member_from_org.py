#!/usr/bin/env python

# ## Remove a login from org
#
# The goal is to get the specified login out of the org in the cleanest way
# possible.
#
# Currently includes:
#  - handling the "login is an owner" case
#  - handling the "login is an outside collaborator" case
#
# Not yet handled:
#  - keeping track of when they are team maintainers


import logging
import argparse

import github3
from client import get_github3_client
# hack until https://github.com/sigmavirus24/github3.py/pull/675 merged
from github3.exceptions import ForbiddenError  # NOQA
if not hasattr(github3.orgs.Organization, 'invitations'):
    raise NotImplementedError("Your version of github3.py does not support "
                              "invitations. Try "
                              "https://github.com/hwine/github3.py/tree/invitations")  # NOQA

logger = logging.getLogger(__name__)


def remove_login_from_org(login, org_name):
    org = gh.organization(org_name)
    user = org.membership(login)
    if user:
        if user['role'] in ['admin']:
            logger.warn(f"manually change {login} to a member first")
        else:
            if not dry_run:
                if org.remove_membership(login):
                    logger.info(f"removed {login} from {org_name}")
                else:
                    logger.error("ERROR removing {} from {}".format(login,
                                                                    org_name))
    # remove any outside collaborator settings
    # HACK - no method, so hack the URL and send it directly
    oc_url = org._json_data['issues_url'].replace('issues',
                                                  'outside_collaborators')
    delete_url = oc_url + '/' + login
    if not dry_run:
        response = org._delete(delete_url)
        if response.status_code not in [204, ]:
            logger.error('ERROR: bad result ({}) from {}'
                         .format(response.status_code, delete_url))
    logger.info('removed {} as outside collaborator via {}'.format(login,
                                                                   delete_url))


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("orgs", help='organizations to operate on',
                        default=['mozilla', ], nargs='*')
    parser.add_argument("--login", "-u", help='GitHub user to remove',
                        required=True)
    parser.add_argument("--dry-run", "-n", help='Do not make changes',
                        action='store_false')
    parser.add_argument("--cwd", "-R", help='repo to use', dest='repos',
                        action='append')

# done with per-run setup

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    global dry_run
    dry_run = args.dry_run
    global gh
    gh = get_github3_client()

    for org in args.orgs:
        remove_login_from_org(args.login, org)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    logging.getLogger('github3').setLevel(logging.WARNING)
    main()
