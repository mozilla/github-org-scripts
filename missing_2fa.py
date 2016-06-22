#!/usr/bin/env python
"""
    Check for admins or any member without 2FA enabled.

    List contact information if available for members out of compliance.
"""
import argparse
import logging

from client import get_github3_client

BAD_TEAM = '2fa_disabled'
logger = logging.getLogger(__name__)

def get_user_email(gh, user_login):
    user_info = gh.user(user_login)
    email = user_info.email or "no public email address"
    return email

def update_team_membership(org, new_member_list):
    # assume we're using a team to communicate with these folks, update
    # that team to contain exactly new_member_list members
    # team & repo assignment must be done already
    team = [x for x in org.teams() if x.name == BAD_TEAM][0]
    # get set of current members
    current = set([x.login for x in team.members()])
    # get set of new members
    new = set([x.login for x in new_member_list])
    to_remove = current - new
    to_add = new - current
    no_change = new & current
    update_success = True
    print "%5d alumni" % len(to_remove)
    for login in to_remove:
        if not team.remove_member(login):
            logger.warn("Failed to remove a member"
                    " - you need 'admin:org' permissions")
            update_success = False
            break
    print "%5d new" % len(to_add)
    for login in to_add:
        print("    {} is new".format(login))
        if not team.add_member(login):
            logger.warn("Failed to add a member"
                    " - you need 'admin:org' permissions")
            update_success = False
            break
    print "%5d no change" % len(no_change)
    # if we're running in the ipython notebook, the log message isn't
    # displayed. Output something useful
    if not update_success:
        print "Updates were not made to team '%s' in '%s'." % (BAD_TEAM, org.name)
        print "Make sure your API token has 'admin:org' permissions for that organization."


def check_users(gh, org_name, admins_only=True, update_team=False):

    org = gh.organization(org_name)

    role = 'admin' if admins_only else 'all'
    user_type = 'admins' if admins_only else 'members'
    bad_member = list(org.members(filter='2fa_disabled', role=role))

    if bad_member:
        if update_team:
            print('There are %d %s that DO NOT HAVE 2FA for org %s:' %
                    (len(bad_member), user_type, org_name))
        else:
            print('The following %d %s DO NOT HAVE 2FA for org %s:' %
                    (len(bad_member), user_type, org_name))
            for a in bad_member:
                print a.login, get_user_email(gh, a.login)
    else:
        print('Congrats! All %s have 2FA enabled in %s!' % (user_type,
            org_name))
    if update_team:
        update_team_membership(org, bad_member)

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--admins', action='store_true',
                        help='Report only for admins (default all members)')
    parser.add_argument("orgs", nargs='*', default=['mozilla', ],
                        help='github organizations to check (defaults to mozilla)')
    parser.add_argument("--update-team", action='store_true', 
                        help='update membership of team "%s"' % BAD_TEAM)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.orgs:
        gh = get_github3_client()
        for org in args.orgs:
            check_users(gh, org, args.admins, args.update_team)


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN, format='%(asctime)s %(message)s')
    main()
