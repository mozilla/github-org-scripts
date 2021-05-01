#!/usr/bin/env python
"""Report and manage pending org invitations."""


# additional help text
_epilog = """
This script uses a preview API, so may cease to function without
warning.

The output always has the GitHub login as first field, so you can get
those with:
    manage_invitations | cut -d ' ' -f1
Or invitee & inviter:
    manage_invitations | awk '!/^Proc/ {print $1 " by " $NF;}'

ToDo:
- Better handling of Security Advisory private repos. These return a 404
  on invitation calls, which are simply reported now. These repos
  usually have a name ending in the string '-ghsa-' followed by hex
  digits.
"""
# hwine believes keeping the doc above together is more important than PEP-8
import argparse  # NOQA
import logging  # NOQA
import arrow  # NOQA

from client import get_github3_client  # NOQA

# hack until invitations are supported upstream
import github3  # NOQA
from github3.exceptions import ForbiddenError  # NOQA

if not hasattr(github3.orgs.Organization, "invitations"):
    raise NotImplementedError(
        "Your version of github3.py does not support "
        "invitations. Try "
        "https://github.com/hwine/github3.py/tree/invitations"
    )  # NOQA
if (1, 3, 0) > github3.__version_info__:
    raise NotImplementedError(
        "Your version of github3.py does not support "
        "collaborator invitations. Version '1.3.0' or later is known to work."
    )


logger = logging.getLogger(__name__)


def get_cutoff_time(cutoff_delta):
    k, v = cutoff_delta.split("=", 2)
    args = {k: int(v)}
    ok_after = arrow.now().replace(**args)
    return ok_after


def check_invites(gh, org_name, cancel=False, cutoff_delta="weeks=-2"):

    org = gh.organization(org_name)
    if not org:
        logger.error("No such org '%s'", org_name)
        return
    cutoff_time = get_cutoff_time(cutoff_delta)
    try:
        for invite in org.invitations():
            extended_at = arrow.get(invite.created_at)
            line_end = ": " if cancel else "\n"
            if extended_at < cutoff_time:
                context = invite.as_dict()
                context["ago"] = extended_at.humanize()
                print(
                    "{login} ({email}) was invited {ago} by "
                    "{inviter[login]}".format(**context),
                    end=line_end,
                )
                if cancel:
                    success = org.remove_membership(invite.id)
                    if success:
                        print("Cancelled")
                    else:
                        print("FAILED to cancel")
                        logger.warning(
                            "Couldn't cancel invite for {login} "
                            "from {created_at}".format(**context)
                        )
    except ForbiddenError:
        logger.error("You don't have 'admin:org' permissions for org '%s'", org_name)
    else:
        # now handle collaborator invitations (GH-57)
        for repo in org.repositories():
            # occasionally get a 404 when looking for invitations.
            # Assume this is a race condition and ignore. That may leave
            # some invites uncanceled, but a 2nd run should catch.
            try:
                for invite in repo.invitations():
                    extended_at = arrow.get(invite.created_at)
                    line_end = ": " if cancel else "\n"
                    if extended_at < cutoff_time:
                        context = invite.as_dict()
                        context["ago"] = extended_at.humanize()
                        context["repo"] = repo.name
                        context["inviter"] = invite.inviter.login
                        context["invitee"] = invite.invitee.login
                        print(
                            "{invitee} was invited to {repo} {ago} by "
                            "{inviter} for {permissions} access.".format(**context),
                            end=line_end,
                        )
                        if cancel:
                            # Deletion not directly supported, so hack url &
                            # use send delete verb directly
                            delete_url = repo.url + "/invitations/" + str(invite.id)
                            success = repo._delete(delete_url)
                            if success:
                                print("Cancelled")
                            else:
                                print("FAILED to cancel")
                                logger.warning(
                                    "Couldn't cancel invite for {login} "
                                    "from {created_at}".format(**context)
                                )
            except (
                github3.exceptions.NotFoundError,
                github3.exceptions.ConnectionError,
            ) as e:
                # just report
                logger.warning(
                    "Got 404 for invitation in {}, may be unhandled inviations. '{}'".format(
                        repo.name, str(e)
                    )
                )


def parse_args():
    # from
    # https://stackoverflow.com/questions/18462610/argumentparser-epilog-and-description-formatting-in-conjunction-with-argumentdef
    class CustomFormatter(
        argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter
    ):
        pass

    parser = argparse.ArgumentParser(
        description=__doc__, epilog=_epilog, formatter_class=CustomFormatter
    )
    parser.add_argument(
        "--cancel", action="store_true", help="Cancel stale invitations"
    )
    parser.add_argument(
        "--cutoff",
        help="When invitations go stale " '(arrow replace syntax; default "weeks=-2")',
        default="weeks=-2",
    )
    parser.add_argument(
        "orgs",
        nargs="*",
        default=[
            "mozilla",
        ],
        help="github organizations to check (defaults to " "mozilla)",
    )
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
                print(f"Processing org {org}")
            check_invites(gh, org, args.cancel, args.cutoff)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN, format="%(asctime)s %(message)s")
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit("\nCancelled by user")
