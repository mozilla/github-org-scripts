#!/usr/bin/env python
"""
    Report and manage pending org invitations
"""
from __future__ import print_function

# additional help text
_epilog = """
This script uses a preview API, so may cease to function without
warning.

The output always has the GitHub login as first field, so you can get
those with:
    manage_invitations | cut -d ' ' -f1
Or invitee & inviter:
    manage_invitations | awk '!/^Proc/ {print $1 " by " $NF;}'
"""
import argparse
import logging
import arrow

from client import get_github3_client
# hack until invitations are supported upstream
import github3
if not hasattr(github3.orgs.Organization, 'invitations'):
    raise NotImplementedError("Your version of github3.py does not support "
                              "invitations. Try "
                              "https://github.com/hwine/github3.py/tree/invitations")


logger = logging.getLogger(__name__)


def get_cutoff_time(cutoff_delta):
    k, v = cutoff_delta.split('=', 2)
    args = {k: int(v)}
    ok_after = arrow.now().replace(**args)
    return ok_after


def check_invites(gh, org_name, cancel=False, cutoff_delta="weeks=-2"):

    org = gh.organization(org_name)
    cutoff_time = get_cutoff_time(cutoff_delta)
    for invite in org.invitations():
        extended_at = arrow.get(invite['created_at'])
        line_end = ": " if cancel else "\n"
        if extended_at < cutoff_time:
            invite['ago'] = extended_at.humanize()
            print('{login} ({email}) was invited {ago} by {inviter[login]}'.format(**invite),
                  end=line_end)
            if cancel:
                success = org.remove_membership(username=invite['login'])
                if success:
                    print("Cancelled")
                else:
                    print("FAILED to cancel")
                    logger.warning("Couldn't cancel invite for {login} "
                                   "from {created_at}".format(**invite))


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, epilog=_epilog)
    parser.add_argument('--cancel', action='store_true',
                        help='Cancel stale invitations')
    parser.add_argument('--cutoff', help='When invitations go stale '
                        '(arrow replace syntax; default "weeks=-2")',
                        default="weeks=-2")
    parser.add_argument("orgs", nargs='*', default=['mozilla', ],
                        help='github organizations to check (defaults to mozilla)')
    # make sure arrow is happy with the cutoff syntax
    args = parser.parse_args()
    try:
        get_cutoff_time(args.cutoff)
    except (AttributeError, TypeError):
        parser.error("invalid cutoff value")
    return args


def main():
    args = parse_args()
    if args.orgs:
        gh = get_github3_client()
        for org in args.orgs:
            if len(args.orgs) > 1:
                print("Processing org {}".format(org))
            check_invites(gh, org, args.cancel, args.cutoff)


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN, format='%(asctime)s %(message)s')
    main()
