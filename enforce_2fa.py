#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public           
# License, v. 2.0. If a copy of the MPL was not distributed with this           
# file, You can obtain one at http://mozilla.org/MPL/2.0/.                      
"""
    Check for admins or any member without 2FA enabled.

    Automatically transition users through a stack of warnings, before
    removing them from the org.
"""

import argparse
import logging

from client import get_github3_client

TRACKER_ISSUE = 2
BAD_TEAM = '2fa_disabled'
UPDATE_GITHUB = False

ISSUE_COMMENT = (r'''To: @mozilla/{} - please enable 2fa for your github'''
''' account. Failure to do so will result in removal from the org.
'''
'''See [this
issue](https://github.com/mozilla/admin_for_mozilla_private/issues/1)
and [these
instructions](https://help.github.com/articles/securing-your-account-with-two-factor-authentication-2fa/)
for additional information.'''
)
ISSUE_OBJECT = None

logger = logging.getLogger(__name__)

def get_user_email(gh, user_login):
    user_info = gh.user(user_login)
    email = user_info.email or "no public email address"
    return email


def get_communication_issue(team):
    '''Get the correct issue object for this org/team/repo

    :param <Team> team: the team to be mentioned
    '''
    global ISSUE_OBJECT
    if ISSUE_OBJECT is None:
        team.refresh()
        # forks of the private repo still belong to the team, so make
        # sure we're working with the one we intend.
        repos = [x for x in team.repositories()
                if x.full_name == u'mozilla/admin_for_mozilla_private']
        assert len(repos) == 1
        repo = repos[0]
        ISSUE_OBJECT = repo.issue(1) # magic number
    return ISSUE_OBJECT

def update_issue(team):
    '''Add a comment mentioning the team to the main issue.

    This will cause Github to contact all team members.

    :param <Team> team: the team to be mentioned
    '''
    # for now, just add a new comment - the issue will be a quick check
    # on how often this is done.
    issue = get_communication_issue(team)
    issue.create_comment(ISSUE_COMMENT.format(team.name))

def update_team_membership(org, new_member_list):
    # assume we're using a team to communicate with these folks, update
    # those teams to for anyone that has left or complied, and sequence
    # teams such that folks are get one step closer to removal each pass
    # team & repo assignment must be done already
    team_stack = [x for x in org.teams() if x.name.startswith(BAD_TEAM)]
    # get set of new members
    new = set([x.login for x in new_member_list])
    
    # assume lexical ordering where 1st team is the one to actually
    # remove.
    team_stack.sort(key=lambda team: team.name)
    update_success = True
    for t in range(len(team_stack)):
        team = team_stack[t]
        # get set of current members
        current = set([x.login for x in team.members()])
        now_in_compliance = current - new
        #to_add = new - current
        to_enforce = new & current
        print "%5d alumni" % len(now_in_compliance)
        for login in now_in_compliance:
            if UPDATE_GITHUB and not team.remove_member(login):
                logger.warn("Failed to remove a member"
                        " - you need 'admin:org' permissions")
                update_success = False
                break
        if t == 0:
            # they've used up all their chances, remove from org
            # and team
            print("%5d being removed from org %s" % (len(to_enforce),
                    org.name))
            for login in to_enforce:
                print("    {} is being removed".format(login))
                if UPDATE_GITHUB and not org.remove_member(login):
                    logger.warn("Failed to remove a member"
                            " - you need 'admin:org' permissions")
                    update_success = False
                    break
                if UPDATE_GITHUB and not team.remove_member(login):
                    logger.warn("Failed to remove a member"
                            " - you need 'admin:org' permissions")
                    update_success = False
                    break
        else:
            # migrate users to the next team
            print("%5d being moved from team %s" % (len(to_enforce),
                    team.name))
            dest_team = team_stack[t-1]
            dest_team.refresh()
            if UPDATE_GITHUB:
                assert len(list(dest_team.members())) == 0, \
                        "Inconsistent state, check manually"

            for login in to_enforce:
                if UPDATE_GITHUB and not dest_team.add_member(login):
                    logger.warn("Failed to add a member"
                            " - you need 'admin:org' permissions")
                    update_success = False
                    break
                if UPDATE_GITHUB and not team.remove_member(login):
                    logger.warn("Failed to remove a member"
                            " - you need 'admin:org' permissions")
                    update_success = False
                    break
            if UPDATE_GITHUB and len(to_enforce):
                update_issue(dest_team)
        # we've dealt with the to_enforce set - remove them from new
        new -= to_enforce
    # now add the remaining new folks to the last list
    dest_team = team_stack[-1]
    dest_team.refresh()
    if UPDATE_GITHUB:
        assert len(list(dest_team.members())) == 0, \
                "Inconsistent state, check manually"
    print("%5d being added to team %s" % (len(new),
            dest_team.name))
    for login in new:
        print("    {} is new".format(login))
        if UPDATE_GITHUB and not dest_team.add_member(login):
            logger.warn("Failed to add a member"
                    " - you need 'admin:org' permissions")
            update_success = False
            break
    if UPDATE_GITHUB and len(new):
        update_issue(dest_team)
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
    parser.add_argument("--dry-run", action='store_true', 
                        help='Do not make changes to github')
    args = parser.parse_args()
    global UPDATE_GITHUB
    UPDATE_GITHUB = not args.dry_run
    return args


def main():
    args = parse_args()
    if args.orgs:
        gh = get_github3_client()
        for org in args.orgs:
            check_users(gh, org, args.admins, args.update_team)


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN, format='%(asctime)s %(message)s')
    main()
