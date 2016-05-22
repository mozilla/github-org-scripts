#!/usr/bin/env python
"""
    Check for admins or any member without 2FA enabled.

    List contact information if available for members out of compliance.
"""
import argparse
import logging

from client import get_github3_client

logger = logging.getLogger(__name__)

def get_user_email(gh, user_login):
    user_info = gh.user(user_login)
    email = user_info.email or "no public email address"
    return email

def check_users(gh, org_name, admins_only=True):

    org = gh.organization(org_name)

    role = 'admin' if admins_only else 'all'
    user_type = 'admins' if admins_only else 'members'
    bad_member = list(org.members(filter='2fa_disabled', role=role))

    if bad_member:
        print('The following %d %s DO NOT HAVE 2FA for org %s:' %
                (len(bad_member), user_type, org_name))
        for a in bad_member:
            print a.login, get_user_email(gh, a.login)
    else:
        print('Congrats! All %s have 2FA enabled in %s!' % (user_type,
            org_name))

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--admins', action='store_true',
                        help='Report only for admins (default all members)')
    parser.add_argument("orgs", nargs='*', default=['mozilla', ],
                        help='github organizations to check (defaults to mozilla)')
    return parser.parse_args()


def main():
    args = parse_args()
    if args.orgs:
        gh = get_github3_client()
        for org in args.orgs:
            check_users(gh, org, args.admins)


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN, format='%(asctime)s %(message)s')
    main()
